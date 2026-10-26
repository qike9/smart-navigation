# -*- coding: utf-8 -*-
"""地图文件读写、模板生成、格式转换与导出。"""

from __future__ import annotations

import json
import os
import random
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .analysis import AccessibilityChecker
from .models import CellType, GridMap, PathResult, Position


def default_maps_directory() -> str:
    """用户地图的默认存放目录。

    优先读取环境变量 ``SMARTNAV_MAPS_DIR``，否则落在 ``~/SmartNavigation/maps``，
    避免把用户数据写进项目目录或依赖当前工作目录。
    """
    override = os.environ.get("SMARTNAV_MAPS_DIR")
    if override:
        return override
    return str(Path.home() / "SmartNavigation" / "maps")


def default_output_directory() -> str:
    """导出文件的默认目录，可通过 ``SMARTNAV_OUTPUT_DIR`` 覆盖。"""
    override = os.environ.get("SMARTNAV_OUTPUT_DIR")
    if override:
        return override
    return str(Path.home() / "SmartNavigation" / "output")


class MapManager:
    def __init__(self, save_directory: str = None):
        self.save_directory = save_directory or default_maps_directory()
        self.ensure_directory()
    
    def ensure_directory(self):
        os.makedirs(self.save_directory, exist_ok=True)
    
    def save_map(self, grid_map: GridMap, filename: str) -> bool:
        try:
            filepath = os.path.join(self.save_directory, filename)
            data = grid_map.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except OSError as e:
            print(f"保存地图失败: {e}")
            return False
    
    def load_map(self, filename: str) -> Optional[GridMap]:
        try:
            filepath = os.path.join(self.save_directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return GridMap.from_dict(data)
        except (OSError, ValueError, KeyError) as e:
            print(f"加载地图失败: {e}")
            return None
    
    def list_maps(self) -> List[str]:
        try:
            files = os.listdir(self.save_directory)
            return [f for f in files if f.endswith('.json')]
        except Exception:
            return []
    
    def delete_map(self, filename: str) -> bool:
        try:
            filepath = os.path.join(self.save_directory, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            return True
        except Exception:
            return False


class MapTemplate:
    @staticmethod
    def create_empty(width: int, height: int) -> GridMap:
        return GridMap(width, height)
    
    @staticmethod
    def create_border_obstacles(width: int, height: int) -> GridMap:
        grid_map = GridMap(width, height)
        for x in range(width):
            grid_map.add_obstacle(Position(x, 0))
            grid_map.add_obstacle(Position(x, height - 1))
        for y in range(height):
            grid_map.add_obstacle(Position(0, y))
            grid_map.add_obstacle(Position(width - 1, y))
        return grid_map
    
    @staticmethod
    def create_corridor(width: int, height: int) -> GridMap:
        grid_map = GridMap(width, height)
        mid_y = height // 2
        for x in range(width):
            for y in range(height):
                if y < mid_y - 2 or y > mid_y + 2:
                    grid_map.add_obstacle(Position(x, y))
        return grid_map
    
    @staticmethod
    def create_rooms(width: int, height: int, num_rooms: int = 4) -> GridMap:
        """竖井式房间：等分成 num_rooms 列，列之间是带门的墙。"""
        grid_map = GridMap(width, height)
        num_rooms = max(1, min(num_rooms, max(1, width // 4)))
        room_width = width // num_rooms
        for i in range(1, num_rooms):
            wall_x = i * room_width
            door_y = random.randrange(1, max(2, height - 1))
            for y in range(height):
                if y != door_y:
                    grid_map.add_obstacle(Position(wall_x, y))
        return grid_map

    @staticmethod
    def create_maze_recursive(width: int, height: int) -> GridMap:
        """完美迷宫，实现见 :meth:`GridMap.generate_maze`。"""
        grid_map = GridMap(width, height)
        grid_map.generate_maze()
        return grid_map


class MapConverter:
    @staticmethod
    def to_ascii(grid_map: GridMap) -> str:
        symbols = {
            CellType.EMPTY: '.',
            CellType.OBSTACLE: '#',
            CellType.START: 'S',
            CellType.END: 'E',
            CellType.WAYPOINT: 'W',
            CellType.PATH: '*',
            CellType.VISITED: 'o',
            CellType.CURRENT: 'C'
        }
        lines = []
        for y in range(grid_map.height):
            line = ''
            for x in range(grid_map.width):
                cell = grid_map.get_cell(Position(x, y))
                line += symbols.get(cell, '.')
            lines.append(line)
        return '\n'.join(lines)
    
    @staticmethod
    def from_ascii(ascii_map: str) -> GridMap:
        lines = ascii_map.strip().split('\n')
        height = len(lines)
        width = max(len(line) for line in lines) if lines else 0
        grid_map = GridMap(width, height)
        symbol_to_cell = {
            '.': CellType.EMPTY,
            '#': CellType.OBSTACLE,
            'S': CellType.START,
            'E': CellType.END,
            'W': CellType.WAYPOINT
        }
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char in symbol_to_cell:
                    grid_map.set_cell(Position(x, y), symbol_to_cell[char])
        return grid_map
    
    @staticmethod
    def to_csv(grid_map: GridMap, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(','.join(str(x) for x in range(grid_map.width + 1)) + '\n')
            for y in range(grid_map.height):
                row = [str(y)] + [str(grid_map.get_cell(Position(x, y)).value) for x in range(grid_map.width)]
                f.write(','.join(row) + '\n')
    
    @staticmethod
    def from_csv(filename: str) -> GridMap:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if len(lines) < 2:
            return GridMap()
        width = len(lines[0].strip().split(',')) - 1
        height = len(lines) - 1
        grid_map = GridMap(width, height)
        for y, line in enumerate(lines[1:]):
            values = line.strip().split(',')[1:]
            for x, val in enumerate(values):
                try:
                    cell_value = int(val)
                    grid_map.set_cell(Position(x, y), CellType(cell_value))
                except ValueError:
                    pass
        return grid_map


class ExportManager:
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or default_output_directory()
        self.ensure_directory()
    
    def ensure_directory(self):
        os.makedirs(self.output_dir, exist_ok=True)
    
    def export_path_as_text(self, path: List[Position], filename: str):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            for i, pos in enumerate(path):
                f.write(f"{i},{pos.x},{pos.y}\n")
    
    def export_path_as_json(self, path: List[Position], result: PathResult, filename: str):
        filepath = os.path.join(self.output_dir, filename)
        data = {
            'algorithm': result.algorithm_name,
            'success': result.success,
            'path_length': result.path_length,
            'nodes_explored': result.nodes_explored,
            'execution_time': result.execution_time,
            'path': [{'x': p.x, 'y': p.y} for p in path]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def export_map_as_image(self, grid_map: GridMap, filename: str, cell_size: int = 10):
        try:
            from PIL import Image, ImageDraw
            img_width = grid_map.width * cell_size
            img_height = grid_map.height * cell_size
            img = Image.new('RGB', (img_width, img_height), 'white')
            draw = ImageDraw.Draw(img)
            colors = {
                CellType.EMPTY: (255, 255, 255),
                CellType.OBSTACLE: (51, 51, 51),
                CellType.START: (0, 255, 0),
                CellType.END: (255, 0, 0),
                CellType.WAYPOINT: (255, 165, 0),
                CellType.PATH: (0, 102, 255),
                CellType.VISITED: (204, 204, 204)
            }
            for y in range(grid_map.height):
                for x in range(grid_map.width):
                    cell = grid_map.get_cell(Position(x, y))
                    color = colors.get(cell, (255, 255, 255))
                    x1, y1 = x * cell_size, y * cell_size
                    x2, y2 = x1 + cell_size - 1, y1 + cell_size - 1
                    draw.rectangle([x1, y1, x2, y2], fill=color, outline=(200, 200, 200))
            filepath = os.path.join(self.output_dir, filename)
            img.save(filepath)
        except ImportError:
            pass


class MapStatistics:
    @staticmethod
    def calculate(grid_map: GridMap) -> Dict:
        total_cells = grid_map.width * grid_map.height
        obstacle_count = len(grid_map.obstacles)
        empty_count = total_cells - obstacle_count
        return {
            'width': grid_map.width,
            'height': grid_map.height,
            'total_cells': total_cells,
            'obstacle_count': obstacle_count,
            'empty_count': empty_count,
            'obstacle_density': obstacle_count / total_cells if total_cells > 0 else 0,
            'has_start': grid_map.start_position is not None,
            'has_end': grid_map.end_position is not None,
            'waypoint_count': len(grid_map.waypoints)
        }


class MapValidator:
    @staticmethod
    def validate(grid_map: GridMap) -> Tuple[bool, List[str]]:
        errors = []
        if grid_map.width <= 0 or grid_map.height <= 0:
            errors.append("地图尺寸无效")
        if grid_map.width > 500 or grid_map.height > 500:
            errors.append("地图尺寸过大")
        if not grid_map.start_position:
            errors.append("未设置起点")
        if not grid_map.end_position:
            errors.append("未设置终点")
        if grid_map.start_position and not grid_map.is_valid_position(grid_map.start_position):
            errors.append("起点位置无效")
        if grid_map.end_position and not grid_map.is_valid_position(grid_map.end_position):
            errors.append("终点位置无效")
        if grid_map.start_position and grid_map.end_position:
            if grid_map.start_position == grid_map.end_position:
                errors.append("起点和终点不能相同")
        for wp in grid_map.waypoints:
            if not grid_map.is_valid_position(wp):
                errors.append(f"途经点 ({wp.x}, {wp.y}) 位置无效")
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_path(path: List[Position], grid_map: GridMap) -> Tuple[bool, List[str]]:
        errors = []
        if not path:
            errors.append("路径为空")
            return False, errors
        for i, pos in enumerate(path):
            if not grid_map.is_valid_position(pos):
                errors.append(f"路径点 {i} 位置无效: ({pos.x}, {pos.y})")
            elif not grid_map.is_walkable(pos):
                errors.append(f"路径点 {i} 不可通行: ({pos.x}, {pos.y})")
        for i in range(len(path) - 1):
            dx = abs(path[i].x - path[i+1].x)
            dy = abs(path[i].y - path[i+1].y)
            if dx > 1 or dy > 1:
                errors.append(f"路径点 {i} 到 {i+1} 不相邻")
        return len(errors) == 0, errors


class MapAnalyzer:
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
    
    def analyze_complexity(self) -> Dict:
        total_cells = self.grid_map.width * self.grid_map.height
        obstacle_count = len(self.grid_map.obstacles)
        obstacle_density = obstacle_count / total_cells if total_cells > 0 else 0
        checker = AccessibilityChecker(self.grid_map)
        components = checker.find_connected_components()
        num_components = len(components)
        avg_component_size = sum(len(c) for c in components) / num_components if num_components > 0 else 0
        return {
            'total_cells': total_cells,
            'obstacle_count': obstacle_count,
            'obstacle_density': obstacle_density,
            'num_components': num_components,
            'avg_component_size': avg_component_size,
            'complexity_score': obstacle_density * num_components
        }
    
    def find_bottlenecks(self) -> List[Position]:
        bottlenecks = []
        for y in range(1, self.grid_map.height - 1):
            for x in range(1, self.grid_map.width - 1):
                pos = Position(x, y)
                if self.grid_map.is_walkable(pos):
                    neighbors = self.grid_map.get_neighbors(pos, False)
                    if len(neighbors) == 2:
                        n1, n2 = neighbors[0], neighbors[1]
                        if (n1.x == n2.x or n1.y == n2.y):
                            bottlenecks.append(pos)
        return bottlenecks
    
    def find_open_areas(self, min_size: int = 10) -> List[Set[Position]]:
        visited = set()
        open_areas = []
        for y in range(self.grid_map.height):
            for x in range(self.grid_map.width):
                pos = Position(x, y)
                if pos not in visited and self.grid_map.is_walkable(pos):
                    area = self._flood_fill_open(pos, visited)
                    if len(area) >= min_size:
                        open_areas.append(area)
        return open_areas
    
    def _flood_fill_open(self, start: Position, visited: Set[Position]) -> Set[Position]:
        area = set()
        queue = deque([start])
        visited.add(start)
        area.add(start)
        while queue:
            current = queue.popleft()
            for neighbor in self.grid_map.get_neighbors(current, False):
                if neighbor not in visited and self.grid_map.is_walkable(neighbor):
                    visited.add(neighbor)
                    area.add(neighbor)
                    queue.append(neighbor)
        return area
    
    def calculate_average_distance(self) -> float:
        walkable = []
        for y in range(self.grid_map.height):
            for x in range(self.grid_map.width):
                pos = Position(x, y)
                if self.grid_map.is_walkable(pos):
                    walkable.append(pos)
        if len(walkable) < 2:
            return 0.0
        total_distance = 0.0
        count = 0
        for i in range(min(100, len(walkable))):
            for j in range(i + 1, min(100, len(walkable))):
                total_distance += walkable[i].distance_to(walkable[j])
                count += 1
        return total_distance / count if count > 0 else 0.0
