# -*- coding: utf-8 -*-
"""地图模型（GridMap / Position / Node / PathResult）测试。"""
import math

import pytest

from smartnav.models import CellType, Direction, GridMap, Node, PathResult, Position


class TestPosition:
    def test_distance_to_diagonal(self):
        assert Position(0, 0).distance_to(Position(3, 4)) == pytest.approx(5.0)
        assert Position(0, 0).distance_to(Position(2, 2)) == pytest.approx(2 * math.sqrt(2))

    def test_manhattan_and_chebyshev(self):
        a, b = Position(1, 1), Position(4, 5)
        assert a.manhattan_distance(b) == 7
        assert a.chebyshev_distance(b) == 4

    def test_directions(self):
        origin = Position(5, 5)
        assert origin.get_direction_to(Position(5, 1)) == Direction.NORTH
        assert origin.get_direction_to(Position(9, 5)) == Direction.EAST
        assert origin.get_direction_to(Position(9, 9)) == Direction.SOUTHEAST
        assert origin.get_direction_to(Position(1, 1)) == Direction.NORTHWEST

    def test_hashable_and_ordered(self):
        assert len({Position(1, 2), Position(1, 2), Position(2, 1)}) == 2
        assert Position(1, 2) < Position(1, 3)

    def test_tuple_roundtrip(self):
        pos = Position(7, 9)
        assert Position.from_tuple(pos.to_tuple()) == pos

    def test_copy_is_independent(self):
        pos = Position(1, 1)
        clone = pos.copy()
        clone.x = 99
        assert pos.x == 1


class TestGridMap:
    def test_defaults(self):
        grid = GridMap()
        assert grid.width > 0 and grid.height > 0
        assert grid.start_position is None
        assert not grid.obstacles

    def test_obstacle_bookkeeping(self):
        grid = GridMap(5, 5)
        grid.add_obstacle(Position(1, 1))
        assert (1, 1) in grid.obstacles
        assert not grid.is_walkable(Position(1, 1))

        grid.remove_obstacle(Position(1, 1))
        assert (1, 1) not in grid.obstacles
        assert grid.is_walkable(Position(1, 1))

    def test_toggle_obstacle(self):
        grid = GridMap(5, 5)
        grid.toggle_obstacle(Position(2, 2))
        assert not grid.is_walkable(Position(2, 2))
        grid.toggle_obstacle(Position(2, 2))
        assert grid.is_walkable(Position(2, 2))

    def test_out_of_bounds_is_wall(self):
        grid = GridMap(5, 5)
        assert not grid.is_valid_position(Position(-1, 0))
        assert not grid.is_valid_position(Position(5, 0))
        assert not grid.is_walkable(Position(5, 5))
        assert grid.get_cell(Position(99, 99)) == CellType.OBSTACLE

    def test_start_and_end_are_unique(self):
        grid = GridMap(10, 10)
        grid.set_start(Position(1, 1))
        grid.set_start(Position(3, 3))
        assert grid.start_position == Position(3, 3)
        assert grid.get_cell(Position(1, 1)) == CellType.EMPTY

        grid.set_end(Position(8, 8))
        grid.set_end(Position(6, 6))
        assert grid.end_position == Position(6, 6)
        assert grid.get_cell(Position(8, 8)) == CellType.EMPTY

    def test_waypoints_add_and_remove(self):
        grid = GridMap(10, 10)
        grid.add_waypoint(Position(2, 2))
        grid.add_waypoint(Position(2, 2))
        grid.add_waypoint(Position(4, 4))
        assert len(grid.waypoints) == 2

        grid.remove_waypoint(Position(2, 2))
        assert grid.waypoints == [Position(4, 4)]

    def test_neighbors_block_diagonal_corner_cutting(self):
        grid = GridMap(5, 5)
        grid.add_obstacle(Position(2, 1))
        grid.add_obstacle(Position(1, 2))
        neighbors = grid.get_neighbors(Position(1, 1), allow_diagonal=True)
        assert Position(2, 2) not in neighbors, "不应允许穿过两个障碍物的夹角"

    def test_neighbors_four_direction(self):
        grid = GridMap(5, 5)
        assert len(grid.get_neighbors(Position(2, 2), allow_diagonal=False)) == 4
        assert len(grid.get_neighbors(Position(2, 2), allow_diagonal=True)) == 8

    def test_movement_cost(self):
        grid = GridMap(5, 5)
        assert grid.get_movement_cost(Position(1, 1), Position(2, 1)) == 1.0
        assert grid.get_movement_cost(Position(1, 1), Position(2, 2)) == pytest.approx(1.414)

    def test_line_of_sight(self):
        grid = GridMap(6, 6)
        assert grid.has_line_of_sight(Position(0, 0), Position(5, 5))
        grid.add_obstacle(Position(3, 3))
        assert not grid.has_line_of_sight(Position(0, 0), Position(5, 5))

    def test_json_roundtrip(self):
        grid = GridMap(9, 7)
        grid.add_obstacle(Position(2, 3))
        grid.set_start(Position(1, 1))
        grid.set_end(Position(7, 5))
        grid.add_waypoint(Position(4, 4))

        clone = GridMap.from_dict(grid.to_dict())
        assert (clone.width, clone.height) == (9, 7)
        assert clone.start_position == Position(1, 1)
        assert clone.end_position == Position(7, 5)
        assert clone.waypoints == [Position(4, 4)]
        assert clone.obstacles == grid.obstacles

    def test_copy_is_deep_enough(self):
        grid = GridMap(5, 5)
        grid.set_start(Position(1, 1))
        clone = grid.copy()
        clone.add_obstacle(Position(2, 2))
        assert (2, 2) not in grid.obstacles

    def test_resize_keeps_content(self):
        grid = GridMap(5, 5)
        grid.add_obstacle(Position(1, 1))
        grid.resize(8, 8)
        assert (grid.width, grid.height) == (8, 8)
        assert not grid.is_walkable(Position(1, 1))

    def test_resize_shrinks_and_drops_invalid_points(self):
        grid = GridMap(10, 10)
        grid.set_start(Position(9, 9))
        grid.resize(5, 5)
        assert grid.start_position is None

    def test_clear_path_visualization(self):
        grid = GridMap(5, 5)
        grid.set_cell(Position(1, 1), CellType.PATH)
        grid.set_cell(Position(1, 2), CellType.VISITED)
        grid.clear_path_visualization()
        assert grid.get_cell(Position(1, 1)) == CellType.EMPTY
        assert grid.get_cell(Position(1, 2)) == CellType.EMPTY


class TestMapGeneration:
    def test_empty_map(self):
        grid = GridMap(6, 6)
        assert not grid.obstacles

    def test_random_obstacles_density(self):
        grid = GridMap(40, 40)
        grid.generate_random_obstacles(0.2)
        density = len(grid.obstacles) / (40 * 40)
        assert 0.12 < density < 0.28

    def test_random_obstacles_can_be_forced_connected(self):
        grid = GridMap(30, 30)
        grid.generate_random_obstacles(0.35, ensure_connected=True)
        assert len(grid._walkable_components()) == 1

    def test_maze_is_perfect(self):
        """完美迷宫：N 个格子的房间之间恰好有 N-1 条通道（树）。"""
        grid = GridMap(21, 21)
        grid.generate_maze()
        rooms = ((grid.width - 1) // 2) * ((grid.height - 1) // 2)
        free = grid.width * grid.height - len(grid.obstacles)
        assert free == rooms + (rooms - 1)
        assert len(grid._walkable_components()) == 1

    def test_maze_border_is_wall(self):
        grid = GridMap(15, 15)
        grid.generate_maze()
        for x in range(grid.width):
            assert not grid.is_walkable(Position(x, 0))
        for y in range(grid.height):
            assert not grid.is_walkable(Position(0, y))

    def test_maze_handles_even_dimensions(self):
        grid = GridMap(20, 20)
        grid.generate_maze()
        assert len(grid._walkable_components()) == 1

    def test_ensure_connectivity_carves_corridors(self):
        grid = GridMap(7, 7)
        for y in range(7):
            grid.add_obstacle(Position(3, y))
        assert len(grid._walkable_components()) == 2
        carved = grid.ensure_connectivity()
        assert carved > 0
        assert len(grid._walkable_components()) == 1

    def test_tiny_map_generation_is_safe(self):
        grid = GridMap(2, 2)
        grid.generate_maze()
        assert grid.width == 2


class TestNodeAndResult:
    def test_node_cost_update(self):
        node = Node(position=Position(0, 0))
        node.update_costs(3.0, 4.0)
        assert node.f_cost == pytest.approx(7.0)

    def test_node_ordering_by_f_cost(self):
        near = Node(position=Position(0, 0))
        near.update_costs(1.0, 1.0)
        far = Node(position=Position(1, 1))
        far.update_costs(5.0, 5.0)
        assert near < far

    def test_path_result_length(self):
        result = PathResult()
        result.path = [Position(0, 0), Position(1, 0), Position(2, 0)]
        result.calculate_path_length()
        assert result.path_length == pytest.approx(2.0)

    def test_path_result_directions(self):
        result = PathResult()
        result.path = [Position(0, 0), Position(1, 0), Position(2, 0), Position(2, 1)]
        result.calculate_path_length()
        directions = result.get_directions()
        assert [d for d, _, _ in directions] == [Direction.EAST, Direction.SOUTH]
        assert sum(length for _, length, _ in directions) == pytest.approx(3.0)

    def test_empty_path_result(self):
        result = PathResult()
        assert result.get_directions() == []
        assert result.fallback_used is False
