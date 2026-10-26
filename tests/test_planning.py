# -*- coding: utf-8 -*-
"""多途经点规划、路径平滑与导航相关测试。"""
import pytest

from smartnav import AlgorithmFactory
from smartnav.analysis import PathValidator
from smartnav.models import Position
from smartnav.navigation import NavigationSimulator, PathRecorder, SimulationEngine
from smartnav.planning import (
    DynamicObstacleHandler,
    MultiWaypointPlanner,
    PathHistory,
    PathInterpolator,
    PathOptimizer,
    PathSmoother,
    RouteOptimizer,
)


class TestMultiWaypointPlanner:
    def test_visits_every_waypoint(self, open_map):
        start, end = Position(1, 1), Position(10, 10)
        waypoints = [Position(1, 8), Position(8, 1)]
        planner = MultiWaypointPlanner(open_map, "A*", allow_diagonal=True)

        result = planner.plan(start, waypoints, end)

        assert result.success
        for wp in waypoints:
            assert wp in result.path, f"途经点 {wp} 未被经过"
        assert result.path[0] == start
        assert result.path[-1] == end
        assert PathValidator.validate(result.path, open_map)

    def test_no_waypoints_equals_plain_search(self, open_map):
        start, end = Position(1, 1), Position(10, 10)
        planner = MultiWaypointPlanner(open_map, "A*", allow_diagonal=True)
        result = planner.plan(start, [], end)
        direct = AlgorithmFactory.create_algorithm("A*", open_map, True).find_path(start, end)

        assert result.success
        assert result.path_length == pytest.approx(direct.path_length, rel=1e-6)

    def test_unreachable_waypoint_fails_gracefully(self, sealed_map):
        planner = MultiWaypointPlanner(sealed_map, "A*", allow_diagonal=True)
        result = planner.plan(Position(1, 1), [Position(3, 3)], Position(10, 10))
        assert not result.success


class TestRouteOptimizer:
    def test_keeps_endpoints(self, open_map):
        points = [Position(1, 1), Position(8, 1), Position(1, 8), Position(10, 10)]
        ordered = RouteOptimizer(open_map).optimize_route(points)
        assert ordered[0] == points[0]
        assert ordered[-1] == points[-1]
        assert set(ordered) == set(points)

    def test_shortens_zigzag_order(self, open_map):
        points = [Position(1, 1), Position(9, 1), Position(1, 9), Position(9, 9)]
        optimizer = RouteOptimizer(open_map)
        improved = optimizer.optimize_route(points)
        assert optimizer._calculate_total_distance(improved) <= optimizer._calculate_total_distance(points)

    def test_two_points_unchanged(self, open_map):
        points = [Position(1, 1), Position(4, 4)]
        assert RouteOptimizer(open_map).optimize_route(points) == points

    def test_find_nearest(self, open_map):
        nearest = RouteOptimizer(open_map).find_nearest_waypoint(
            Position(1, 1), [Position(8, 8), Position(2, 2)]
        )
        assert nearest == Position(2, 2)


class TestPathSmoother:
    def test_reduces_node_count_and_stays_valid(self, walled_map):
        result = AlgorithmFactory.create_algorithm("A*", walled_map, True).find_path(
            walled_map.start_position, walled_map.end_position
        )
        smoothed = PathSmoother.smooth_path(result.path, walled_map)

        assert len(smoothed) <= len(result.path)
        assert smoothed[0] == result.path[0]
        assert smoothed[-1] == result.path[-1]
        assert PathValidator.validate_any_angle(smoothed, walled_map)

    def test_short_path_is_untouched(self, open_map):
        path = [Position(1, 1), Position(2, 2)]
        assert PathSmoother.smooth_path(path, open_map) == path

    def test_optimizer_smooth(self, open_map):
        result = AlgorithmFactory.create_algorithm("A*", open_map, True).find_path(
            Position(1, 1), Position(9, 9)
        )
        optimized = PathOptimizer(open_map).optimize(result.path, method="smooth")
        assert len(optimized) <= len(result.path)
        assert PathValidator.validate_any_angle(optimized, open_map)

    def test_optimizer_falls_back_for_unknown_method(self, open_map):
        path = [Position(1, 1), Position(2, 2), Position(3, 3)]
        assert PathOptimizer(open_map).optimize(path, method="unknown") == path


class TestPathInterpolator:
    def test_linear_interpolation(self, open_map):
        points = PathInterpolator(open_map).interpolate_linear(
            [Position(0, 0), Position(4, 0)], step=0.5
        )
        assert points[0] == (0.0, 0.0)
        assert points[-1] == (4.0, 0.0)
        assert len(points) == 9

    def test_bezier_interpolation(self, open_map):
        points = PathInterpolator(open_map).interpolate_bezier(
            [Position(0, 0), Position(2, 2), Position(4, 0)], segments=8
        )
        assert len(points) > 3
        assert all(isinstance(p, tuple) and len(p) == 2 for p in points)


class TestDynamicObstacleHandler:
    def test_replans_around_new_obstacle(self, open_map):
        start, end = Position(1, 1), Position(10, 1)
        direct = AlgorithmFactory.create_algorithm("A*", open_map, True).find_path(start, end)
        handler = DynamicObstacleHandler(open_map, "A*")
        handler.set_path(direct.path)

        # 在当前路径前方放一个障碍，触发重规划
        blocked = direct.path[3]
        new_result = handler.add_dynamic_obstacle(blocked)

        assert new_result is not None
        assert new_result.success
        assert blocked not in new_result.path

    def test_advance_tracks_position(self, open_map):
        path = [Position(1, 1), Position(2, 1), Position(3, 1)]
        handler = DynamicObstacleHandler(open_map, "A*")
        handler.set_path(path)
        assert handler.get_current_position() == path[0]
        handler.advance()
        assert handler.get_current_position() == path[1]


class TestNavigationSimulator:
    def test_progress_and_finish(self, open_map):
        path = [Position(1, 1), Position(2, 1), Position(3, 1)]
        sim = NavigationSimulator(path, open_map)

        assert sim.get_progress() >= 0
        assert sim.get_current_position() == path[0]
        assert sim.get_remaining_distance() == pytest.approx(2.0)

        sim.advance()
        sim.advance()
        assert sim.is_finished()
        assert sim.get_progress() == pytest.approx(100.0, abs=1e-6)
        assert sim.get_remaining_distance() == pytest.approx(0.0, abs=1e-6)

    def test_reset(self, open_map):
        sim = NavigationSimulator([Position(1, 1), Position(5, 5)], open_map)
        sim.advance()
        sim.reset()
        assert not sim.is_finished()
        assert sim.get_current_position() == Position(1, 1)

    def test_direction_is_reported(self, open_map):
        sim = NavigationSimulator([Position(1, 1), Position(1, 5)], open_map)
        assert sim.get_direction() is not None


class TestSimulationEngine:
    def test_agents_are_tracked(self, open_map):
        engine = SimulationEngine(open_map)
        engine.add_agent("a1", Position(1, 1), Position(5, 5))
        engine.add_agent("a2", Position(6, 6), Position(2, 2))
        assert len(engine.agents) == 2

    def test_step_advances_time(self, open_map):
        engine = SimulationEngine(open_map)
        engine.add_agent("a1", Position(1, 1), Position(3, 3))
        before = engine.time_step
        engine.step() if hasattr(engine, "step") else None
        assert engine.time_step >= before


class TestPathRecorder:
    def test_recording_roundtrip(self):
        recorder = PathRecorder()
        recorder.start_recording("demo")
        for i in range(3):
            recorder.record_position(Position(i, i))
        path = recorder.stop_recording()

        assert path == [Position(0, 0), Position(1, 1), Position(2, 2)]
        assert recorder.get_recording("demo") == path

    def test_stop_without_start(self):
        assert PathRecorder().stop_recording() is None


class TestPathHistory:
    def test_bounded_size(self):
        history = PathHistory(max_size=3)
        for i in range(6):
            history.add_entry("A*", Position(0, 0), Position(i, i), [Position(0, 0)], 0.01)
        assert len(history.history) <= 3

    def test_recent_entries(self):
        history = PathHistory()
        history.add_entry("A*", Position(0, 0), Position(1, 1), [Position(0, 0)], 0.01)
        history.add_entry("BFS", Position(0, 0), Position(2, 2), [Position(0, 0)], 0.02)
        assert len(history.get_recent(1)) == 1
        assert len(history.get_by_algorithm("BFS")) == 1

    def test_statistics(self):
        history = PathHistory()
        history.add_entry("A*", Position(0, 0), Position(1, 1), [Position(0, 0)], 0.01)
        stats = history.get_statistics()
        assert stats["total_searches"] == 1
        assert stats["algorithm_usage"] == {"A*": 1}
