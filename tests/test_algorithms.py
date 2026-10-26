# -*- coding: utf-8 -*-
"""八种寻路算法的正确性测试。"""
import math

import pytest

from smartnav.algorithms import AlgorithmFactory
from smartnav.models import Direction, GridMap, Position

ALL_ALGORITHMS = AlgorithmFactory.get_algorithm_names()
OPTIMAL_ALGORITHMS = ["A*", "Dijkstra", "BFS", "双向BFS", "Jump Point Search"]

DIAGONAL = math.sqrt(2)


def straight_length(a: Position, b: Position) -> float:
    """八向最短距离（octile）。"""
    dx = abs(a.x - b.x)
    dy = abs(a.y - b.y)
    return (dx + dy) + (DIAGONAL - 2) * min(dx, dy)


@pytest.mark.parametrize("name", ALL_ALGORITHMS)
def test_finds_path_on_open_map(name, open_map):
    algo = AlgorithmFactory.create_algorithm(name, open_map, allow_diagonal=True)
    result = algo.find_path(open_map.start_position, open_map.end_position)

    assert result.success, f"{name} 未找到路径"
    assert result.path[0] == open_map.start_position
    assert result.path[-1] == open_map.end_position
    assert result.visited_nodes, "未记录搜索过程，动画演示会空白"
    assert result.execution_time >= 0


@pytest.mark.parametrize("name", OPTIMAL_ALGORITHMS)
def test_path_cost_is_optimal(name, open_map):
    algo = AlgorithmFactory.create_algorithm(name, open_map, allow_diagonal=True)
    result = algo.find_path(open_map.start_position, open_map.end_position)
    expected = straight_length(open_map.start_position, open_map.end_position)

    assert result.path_length == pytest.approx(expected, rel=1e-3)


@pytest.mark.parametrize("name", ALL_ALGORITHMS)
def test_finds_path_through_gap(name, walled_map):
    algo = AlgorithmFactory.create_algorithm(name, walled_map, allow_diagonal=True)
    result = algo.find_path(walled_map.start_position, walled_map.end_position)

    assert result.success, f"{name} 无法穿过墙体缺口"
    assert all(walled_map.is_walkable(pos) for pos in result.path)


@pytest.mark.parametrize("name", ALL_ALGORITHMS)
def test_reports_failure_on_sealed_map(name, sealed_map):
    algo = AlgorithmFactory.create_algorithm(name, sealed_map, allow_diagonal=True)
    result = algo.find_path(sealed_map.start_position, sealed_map.end_position)

    assert not result.success
    assert result.path == []


@pytest.mark.parametrize("name", ALL_ALGORITHMS)
def test_start_equals_end(name, open_map):
    start = Position(3, 3)
    algo = AlgorithmFactory.create_algorithm(name, open_map, allow_diagonal=True)
    result = algo.find_path(start, start)

    assert result.success
    assert result.path == [start]


@pytest.mark.parametrize("name", ALL_ALGORITHMS)
def test_four_direction_mode_has_no_diagonal_steps(name, open_map):
    algo = AlgorithmFactory.create_algorithm(name, open_map, allow_diagonal=False)
    result = algo.find_path(open_map.start_position, open_map.end_position)

    assert result.success
    for a, b in zip(result.path, result.path[1:]):
        assert abs(a.x - b.x) + abs(a.y - b.y) == 1, f"{name} 在四向模式下走了斜线"


def test_allow_diagonal_makes_path_shorter(open_map):
    diag = AlgorithmFactory.create_algorithm("A*", open_map, allow_diagonal=True)
    orth = AlgorithmFactory.create_algorithm("A*", open_map, allow_diagonal=False)

    diag_result = diag.find_path(open_map.start_position, open_map.end_position)
    orth_result = orth.find_path(open_map.start_position, open_map.end_position)

    assert diag_result.path_length < orth_result.path_length


def test_jps_explores_fewer_nodes_than_astar(open_map):
    """跳点搜索应当显著减少扩展节点数。"""
    jps = AlgorithmFactory.create_algorithm("Jump Point Search", open_map, True)
    astar = AlgorithmFactory.create_algorithm("A*", open_map, True)

    jps_result = jps.find_path(open_map.start_position, open_map.end_position)
    astar_result = astar.find_path(open_map.start_position, open_map.end_position)

    assert not jps_result.fallback_used or len(open_map.obstacles) == 0
    assert len(jps_result.visited_nodes) <= len(astar_result.visited_nodes)


def test_greedy_is_not_slower_than_dijkstra(maze_map):
    """贪心最佳优先通常扩展更少节点（同图同起终点）。"""
    greedy = AlgorithmFactory.create_algorithm("Greedy Best-First", maze_map, True)
    dijkstra = AlgorithmFactory.create_algorithm("Dijkstra", maze_map, True)

    greedy_result = greedy.find_path(maze_map.start_position, maze_map.end_position)
    dijkstra_result = dijkstra.find_path(maze_map.start_position, maze_map.end_position)

    assert greedy_result.success and dijkstra_result.success
    assert len(greedy_result.visited_nodes) <= len(dijkstra_result.visited_nodes)


def test_directions_are_reported(open_map):
    algo = AlgorithmFactory.create_algorithm("A*", open_map, allow_diagonal=True)
    result = algo.find_path(Position(1, 1), Position(5, 5))
    directions = result.get_directions()

    assert directions
    assert all(isinstance(d, Direction) for d, _, _ in directions)
    assert sum(length for _, length, _ in directions) == pytest.approx(result.path_length)


def test_unknown_algorithm_raises(open_map):
    with pytest.raises(ValueError):
        AlgorithmFactory.create_algorithm("不存在的算法", open_map)


def test_factory_exposes_all_eight_algorithms():
    assert len(ALL_ALGORITHMS) == 8
    assert "A*" in ALL_ALGORITHMS
    assert "Theta*" in ALL_ALGORITHMS


def test_theta_star_produces_any_angle_shortcut(open_map):
    theta = AlgorithmFactory.create_algorithm("Theta*", open_map, allow_diagonal=True)
    result = theta.find_path(Position(1, 1), Position(10, 10))

    assert result.success
    # 空地图上应能拉直成一条斜线（节点数远少于逐格 A*）
    assert len(result.path) < len(open_map.get_neighbors(Position(1, 1))) + 10
    assert result.path_length == pytest.approx(
        straight_length(Position(1, 1), Position(10, 10)), rel=1e-3
    )


def test_grid_map_is_not_mutated_by_search(walled_map):
    before = walled_map.to_dict()
    for name in ALL_ALGORITHMS:
        AlgorithmFactory.create_algorithm(name, walled_map, True).find_path(
            walled_map.start_position, walled_map.end_position
        )
    assert walled_map.to_dict() == before


def test_heuristic_is_admissible(open_map):
    algo = AlgorithmFactory.create_algorithm("A*", open_map, allow_diagonal=True)
    a, b = Position(0, 0), Position(9, 7)
    assert algo.heuristic(a, b) <= straight_length(a, b) + 1e-9


def test_random_maps_always_consistent():
    """随机地图上，A* 与 Dijkstra 的代价必须一致，且路径合法。"""
    import random

    from smartnav.analysis import PathValidator

    rng = random.Random(20261026)
    for _ in range(20):
        grid = GridMap(15, 15)
        for x in range(15):
            for y in range(15):
                if rng.random() < 0.25:
                    grid.add_obstacle(Position(x, y))
        grid.set_start(Position(1, 1))
        grid.set_end(Position(13, 13))

        astar = AlgorithmFactory.create_algorithm("A*", grid, True).find_path(
            Position(1, 1), Position(13, 13)
        )
        dijkstra = AlgorithmFactory.create_algorithm("Dijkstra", grid, True).find_path(
            Position(1, 1), Position(13, 13)
        )

        assert astar.success == dijkstra.success
        if astar.success:
            assert astar.path_length == pytest.approx(dijkstra.path_length, rel=1e-9)
            assert PathValidator.validate(astar.path, grid)
