# -*- coding: utf-8 -*-
"""性能分析、指标计算与可达性相关测试。"""

import pytest

from smartnav import AlgorithmFactory, GridMap, Position
from smartnav.analysis import (
    AccessibilityChecker,
    AlgorithmBenchmark,
    CollisionDetector,
    DistanceCalculator,
    GradientCalculator,
    HeatmapGenerator,
    HeuristicFactory,
    MetricsCalculator,
    PathValidator,
    PerformanceAnalyzer,
    StatisticsCollector,
)


class TestPathValidator:
    def test_accepts_valid_path(self, open_map):
        result = AlgorithmFactory.create_algorithm("A*", open_map, True).find_path(
            open_map.start_position, open_map.end_position
        )
        assert PathValidator.validate(result.path, open_map)

    def test_rejects_empty_and_detached_paths(self, open_map):
        assert not PathValidator.validate([], open_map)
        assert not PathValidator.validate([Position(1, 1), Position(4, 4)], open_map)

    def test_rejects_path_through_wall(self, open_map):
        open_map.add_obstacle(Position(2, 1))
        assert not PathValidator.validate([Position(1, 1), Position(2, 1), Position(3, 1)], open_map)

    def test_any_angle_allows_long_segments(self, open_map):
        assert PathValidator.validate_any_angle([Position(0, 0), Position(5, 5)], open_map)

    def test_any_angle_rejects_segment_through_wall(self, open_map):
        for y in range(11):
            open_map.add_obstacle(Position(5, y))
        assert not PathValidator.validate_any_angle([Position(0, 0), Position(10, 0)], open_map)


class TestDistanceCalculator:
    def test_metrics(self):
        a, b = Position(0, 0), Position(3, 4)
        assert DistanceCalculator.euclidean(a, b) == pytest.approx(5.0)
        assert DistanceCalculator.manhattan(a, b) == 7
        assert DistanceCalculator.chebyshev(a, b) == 4
        # octile 不超过欧氏距离的合理上界
        diagonal = Position(0, 0), Position(2, 2)
        assert DistanceCalculator.octile(*diagonal) == pytest.approx(2 * 2 ** 0.5)


class TestHeuristicFactory:
    @pytest.mark.parametrize("name", ["euclidean", "manhattan", "chebyshev", "octile", "zero"])
    def test_returns_callable(self, name):
        fn = HeuristicFactory.create(name, allow_diagonal=True)
        assert callable(fn)
        assert fn(Position(0, 0), Position(3, 4)) >= 0

    def test_unknown_falls_back_to_zero(self):
        fn = HeuristicFactory.create("nope", allow_diagonal=True)
        assert fn(Position(0, 0), Position(9, 9)) == 0.0


class TestMetricsCalculator:
    def test_efficiency_bounds(self, open_map):
        path = [Position(0, 0), Position(1, 0), Position(2, 0)]
        assert MetricsCalculator.calculate_path_efficiency(
            path, Position(0, 0), Position(2, 0)
        ) == pytest.approx(1.0)
        assert MetricsCalculator.calculate_path_efficiency([], Position(0, 0), Position(1, 1)) == 0.0

    def test_smoothness(self):
        straight = [Position(0, 0), Position(1, 0), Position(2, 0)]
        zigzag = [Position(0, 0), Position(1, 1), Position(2, 0)]
        assert MetricsCalculator.calculate_path_smoothness(straight) == 1.0
        assert MetricsCalculator.calculate_path_smoothness(zigzag) < 1.0

    def test_exploration_ratio(self, open_map):
        visited = [Position(0, 0), Position(0, 0), Position(1, 1)]
        ratio = MetricsCalculator.calculate_exploration_ratio(visited, open_map)
        assert 0 < ratio < 1


class TestPerformanceAnalyzer:
    def test_compare_all_algorithms(self, open_map):
        analyzer = PerformanceAnalyzer()
        results = analyzer.compare_algorithms(
            open_map, open_map.start_position, open_map.end_position,
            ["A*", "Dijkstra", "BFS"],
        )
        assert set(results) == {"A*", "Dijkstra", "BFS"}
        assert all(r.success for r in results.values())

        statistics = analyzer.get_statistics("A*")
        assert statistics["total_runs"] == 1
        assert statistics["success_rate"] == 100.0
        assert statistics["avg_nodes"] > 0

    def test_clear_results(self, open_map):
        analyzer = PerformanceAnalyzer()
        analyzer.compare_algorithms(
            open_map, open_map.start_position, open_map.end_position, ["A*"]
        )
        analyzer.clear_results()
        assert analyzer.get_statistics("A*") == {}


class TestStatisticsCollector:
    def test_summary_and_csv(self, open_map, tmp_path):
        collector = StatisticsCollector()
        result = AlgorithmFactory.create_algorithm("A*", open_map, True).find_path(
            open_map.start_position, open_map.end_position
        )
        collector.record_run("A*", (12, 12), 0.1, result)

        summary = collector.get_summary()
        assert summary["total_runs"] == 1
        assert summary["success_rate"] == 100.0

        csv_file = tmp_path / "stats.csv"
        collector.export_to_csv(str(csv_file))
        assert csv_file.exists()
        assert "algorithm" in csv_file.read_text(encoding="utf-8")

    def test_empty_summary(self):
        assert StatisticsCollector().get_summary() == {}


class TestAlgorithmBenchmark:
    def test_benchmark_returns_all_algorithms(self, open_map):
        benchmark = AlgorithmBenchmark(open_map)
        results = benchmark.run_benchmark(["A*", "BFS"], iterations=2)
        assert set(results) == {"A*", "BFS"}
        assert results["A*"]["avg_time"] >= 0
        assert results["A*"]["success_rate"] == 100.0

    def test_best_algorithm(self, open_map):
        benchmark = AlgorithmBenchmark(open_map)
        benchmark.run_benchmark(AlgorithmFactory.get_algorithm_names(), iterations=1)
        name, stats = benchmark.get_best_algorithm("nodes")
        assert name in AlgorithmFactory.get_algorithm_names()
        assert isinstance(stats, dict)

    def test_best_algorithm_without_runs(self, open_map):
        assert AlgorithmBenchmark(open_map).get_best_algorithm() == (None, None)


class TestAccessibilityChecker:
    def test_reachability(self, walled_map):
        checker = AccessibilityChecker(walled_map)
        assert checker.check_reachability(walled_map.start_position, walled_map.end_position)

    def test_sealed_region(self, sealed_map):
        checker = AccessibilityChecker(sealed_map)
        assert not checker.check_reachability(
            sealed_map.start_position, sealed_map.end_position
        )
        assert len(checker.find_connected_components()) == 2


class TestHeatmapGenerator:
    def test_normalized_values(self, open_map):
        heatmap = HeatmapGenerator(open_map)
        heatmap.add_path([Position(1, 1), Position(2, 2), Position(3, 3)])
        heatmap.add_visited([Position(1, 2)], weight=0.5)
        heatmap.apply_gaussian_blur(1.0)
        heatmap.normalize()

        values = [v for row in heatmap.heatmap for v in row]
        assert values
        assert max(values) == pytest.approx(1.0)
        assert min(values) >= 0.0
        assert heatmap.get_hotspots(0.5)

    def test_clear(self, open_map):
        heatmap = HeatmapGenerator(open_map)
        heatmap.add_path([Position(1, 1)])
        heatmap.clear()
        assert max(v for row in heatmap.heatmap for v in row) == 0.0


class TestCollisionDetector:
    def test_detects_obstacles_in_path(self, open_map):
        open_map.add_obstacle(Position(2, 2))
        collisions = CollisionDetector(open_map).check_path_collision(
            [Position(1, 1), Position(2, 2), Position(3, 3)]
        )
        assert collisions == [Position(2, 2)]

    def test_agent_collision(self, open_map):
        detector = CollisionDetector(open_map)
        agents = [
            {"id": "a", "position": Position(1, 1)},
            {"id": "b", "position": Position(1, 1)},
        ]
        collisions = detector.check_agent_collision(agents)
        assert collisions


class TestGradientCalculator:
    def test_open_space_is_balanced(self, open_map):
        gx, gy = GradientCalculator.calculate_gradient(open_map, Position(5, 5))
        assert abs(gx) < 1e-6 and abs(gy) < 1e-6

    def test_wall_produces_gradient(self):
        grid = GridMap(9, 9)
        for y in range(9):
            grid.add_obstacle(Position(4, y))
        gx, _ = GradientCalculator.calculate_gradient(grid, Position(3, 4))
        assert gx < 0, "左侧有墙时应产生指向空地的梯度"
