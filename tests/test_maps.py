# -*- coding: utf-8 -*-
"""地图读写、格式转换与地图分析测试。"""
import json

from smartnav import GridMap, Position
from smartnav.algorithms import AlgorithmFactory
from smartnav.analysis import PathValidator
from smartnav.maps import (
    ExportManager,
    MapAnalyzer,
    MapConverter,
    MapManager,
    MapStatistics,
    MapTemplate,
    MapValidator,
)


class TestMapManager:
    def test_save_load_roundtrip(self, tmp_path, open_map):
        manager = MapManager(str(tmp_path))
        open_map.add_obstacle(Position(3, 3))
        open_map.add_waypoint(Position(4, 4))

        assert manager.save_map(open_map, "demo.json")
        assert "demo.json" in manager.list_maps()

        loaded = manager.load_map("demo.json")
        assert loaded is not None
        assert loaded.width == open_map.width
        assert loaded.start_position == open_map.start_position
        assert loaded.waypoints == open_map.waypoints
        assert (3, 3) in loaded.obstacles

    def test_saved_file_is_readable_json(self, tmp_path, open_map):
        manager = MapManager(str(tmp_path))
        manager.save_map(open_map, "demo.json")
        data = json.loads((tmp_path / "demo.json").read_text(encoding="utf-8"))
        assert data["width"] == open_map.width

    def test_load_missing_file_returns_none(self, tmp_path):
        assert MapManager(str(tmp_path)).load_map("nope.json") is None

    def test_load_corrupted_file_returns_none(self, tmp_path):
        manager = MapManager(str(tmp_path))
        (tmp_path / "bad.json").write_text("{ not json", encoding="utf-8")
        assert manager.load_map("bad.json") is None

    def test_delete_map(self, tmp_path, open_map):
        manager = MapManager(str(tmp_path))
        manager.save_map(open_map, "demo.json")
        assert manager.delete_map("demo.json")
        assert manager.list_maps() == []

    def test_directory_is_created(self, tmp_path):
        target = tmp_path / "nested" / "maps"
        MapManager(str(target))
        assert target.exists()


class TestMapConverter:
    def test_ascii_roundtrip(self, walled_map):
        ascii_map = MapConverter.to_ascii(walled_map)
        restored = MapConverter.from_ascii(ascii_map)

        assert restored.width == walled_map.width
        assert restored.height == walled_map.height
        assert restored.obstacles == walled_map.obstacles
        assert restored.start_position == walled_map.start_position

    def test_ascii_symbols(self, open_map):
        open_map.add_obstacle(Position(0, 0))
        ascii_map = MapConverter.to_ascii(open_map)
        assert ascii_map.splitlines()[0][0] == "#"
        assert "S" in ascii_map and "E" in ascii_map

    def test_csv_roundtrip(self, tmp_path, walled_map):
        csv_file = tmp_path / "map.csv"
        MapConverter.to_csv(walled_map, str(csv_file))
        restored = MapConverter.from_csv(str(csv_file))

        assert restored.width == walled_map.width
        assert restored.height == walled_map.height
        assert restored.obstacles == walled_map.obstacles

    def test_from_csv_too_short(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("0\n", encoding="utf-8")
        assert MapConverter.from_csv(str(csv_file)) is not None


class TestExportManager:
    def test_export_path_as_text(self, tmp_path, open_map):
        exporter = ExportManager(str(tmp_path))
        result = AlgorithmFactory.create_algorithm("A*", open_map, True).find_path(
            open_map.start_position, open_map.end_position
        )
        exporter.export_path_as_text(result.path, "path.txt")

        lines = (tmp_path / "path.txt").read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == len(result.path)
        assert lines[0].startswith("0,")

    def test_export_path_as_json(self, tmp_path, open_map):
        exporter = ExportManager(str(tmp_path))
        result = AlgorithmFactory.create_algorithm("A*", open_map, True).find_path(
            open_map.start_position, open_map.end_position
        )
        exporter.export_path_as_json(result.path, result, "path.json")

        data = json.loads((tmp_path / "path.json").read_text(encoding="utf-8"))
        assert data["algorithm"] == "A*"
        assert data["success"] is True
        assert len(data["path"]) == len(result.path)

    def test_image_export_is_optional(self, tmp_path, open_map):
        """未安装 Pillow 时应静默跳过，不应崩溃。"""
        exporter = ExportManager(str(tmp_path))
        exporter.export_map_as_image(open_map, "map.png", cell_size=4)


class TestMapValidator:
    def test_valid_map(self, open_map):
        valid, errors = MapValidator.validate(open_map)
        assert valid, errors

    def test_missing_endpoints(self):
        valid, errors = MapValidator.validate(GridMap(10, 10))
        assert not valid
        assert any("起点" in e for e in errors)
        assert any("终点" in e for e in errors)

    def test_start_equals_end(self):
        grid = GridMap(10, 10)
        grid.set_start(Position(1, 1))
        grid.set_end(Position(1, 1))
        valid, errors = MapValidator.validate(grid)
        assert not valid
        assert any("不能相同" in e for e in errors)

    def test_too_large_map(self):
        valid, errors = MapValidator.validate(GridMap(501, 501))
        assert not valid
        assert any("过大" in e for e in errors)

    def test_path_validation(self, open_map):
        result = AlgorithmFactory.create_algorithm("A*", open_map, True).find_path(
            open_map.start_position, open_map.end_position
        )
        valid, errors = MapValidator.validate_path(result.path, open_map)
        assert valid, errors

        valid, errors = MapValidator.validate_path([], open_map)
        assert not valid

        valid, errors = MapValidator.validate_path(
            [Position(1, 1), Position(5, 5)], open_map
        )
        assert not valid
        assert any("不相邻" in e for e in errors)


class TestMapTemplate:
    def test_empty(self):
        assert not MapTemplate.create_empty(8, 8).obstacles

    def test_border_obstacles(self):
        grid = MapTemplate.create_border_obstacles(10, 10)
        for x in range(10):
            assert not grid.is_walkable(Position(x, 0))
            assert not grid.is_walkable(Position(x, 9))
        assert grid.is_walkable(Position(5, 5))

    def test_corridor(self):
        grid = MapTemplate.create_corridor(20, 10)
        assert grid.is_walkable(Position(5, 5))
        assert not grid.is_walkable(Position(5, 0))

    def test_rooms_are_connected(self):
        grid = MapTemplate.create_rooms(20, 20, num_rooms=4)
        grid.set_start(Position(1, 10))
        grid.set_end(Position(19, 10))
        result = AlgorithmFactory.create_algorithm("A*", grid, False).find_path(
            Position(1, 10), Position(19, 10)
        )
        assert result.success, "房间之间的门应当让地图保持连通"

    def test_maze_template(self):
        grid = MapTemplate.create_maze_recursive(21, 21)
        assert len(grid.obstacles) > 0
        assert len(grid._walkable_components()) == 1

    def test_maze_is_solvable(self):
        grid = MapTemplate.create_maze_recursive(21, 21)
        start, end = Position(1, 1), Position(19, 19)
        result = AlgorithmFactory.create_algorithm("A*", grid, False).find_path(start, end)
        assert result.success
        assert PathValidator.validate(result.path, grid)


class TestMapStatistics:
    def test_statistics(self, walled_map):
        stats = MapStatistics.calculate(walled_map)
        assert stats["total_cells"] == 144
        assert stats["obstacle_count"] == 11
        assert stats["has_start"] and stats["has_end"]
        assert 0 < stats["obstacle_density"] < 1

    def test_empty_statistics(self):
        stats = MapStatistics.calculate(GridMap(5, 5))
        assert stats["obstacle_density"] == 0
        assert not stats["has_start"]


class TestMapAnalyzer:
    def test_complexity(self, walled_map):
        report = MapAnalyzer(walled_map).analyze_complexity()
        assert report["total_cells"] == 144
        assert report["num_components"] == 1  # 墙上有缺口，全图仍连通
        assert report["complexity_score"] >= 0

    def test_bottlenecks(self):
        grid = GridMap(9, 9)
        for y in range(9):
            if y != 4:
                grid.add_obstacle(Position(4, y))
        bottlenecks = MapAnalyzer(grid).find_bottlenecks()
        assert Position(4, 4) in bottlenecks

    def test_open_areas(self):
        grid = GridMap(20, 20)
        areas = MapAnalyzer(grid).find_open_areas(min_size=10)
        assert len(areas) == 1
        assert len(areas[0]) == 400

    def test_average_distance(self, open_map):
        assert MapAnalyzer(open_map).calculate_average_distance() > 0
