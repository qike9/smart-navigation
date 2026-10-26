# -*- coding: utf-8 -*-
"""核心数据模型：坐标、方向、格子类型、地图与路径结果。"""

from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Tuple


class CellType(Enum):
    EMPTY = 0
    OBSTACLE = 1
    START = 2
    END = 3
    WAYPOINT = 4
    PATH = 5
    VISITED = 6
    CURRENT = 7


class Direction(Enum):
    NORTH = 0
    NORTHEAST = 1
    EAST = 2
    SOUTHEAST = 3
    SOUTH = 4
    SOUTHWEST = 5
    WEST = 6
    NORTHWEST = 7


DIRECTION_ARROWS = {
    Direction.NORTH: "↑",
    Direction.NORTHEAST: "↗",
    Direction.EAST: "→",
    Direction.SOUTHEAST: "↘",
    Direction.SOUTH: "↓",
    Direction.SOUTHWEST: "↙",
    Direction.WEST: "←",
    Direction.NORTHWEST: "↖"
}

DIRECTION_NAMES = {
    Direction.NORTH: "向北",
    Direction.NORTHEAST: "向东北",
    Direction.EAST: "向东",
    Direction.SOUTHEAST: "向东南",
    Direction.SOUTH: "向南",
    Direction.SOUTHWEST: "向西南",
    Direction.WEST: "向西",
    Direction.NORTHWEST: "向西北"
}


@dataclass
class Position:
    x: int
    y: int
    
    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __lt__(self, other):
        return (self.x, self.y) < (other.x, other.y)
    
    def distance_to(self, other: 'Position') -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def manhattan_distance(self, other: 'Position') -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def chebyshev_distance(self, other: 'Position') -> int:
        return max(abs(self.x - other.x), abs(self.y - other.y))
    
    def get_direction_to(self, other: 'Position') -> Direction:
        dx = other.x - self.x
        dy = other.y - self.y
        if dx == 0 and dy < 0:
            return Direction.NORTH
        elif dx > 0 and dy < 0:
            return Direction.NORTHEAST
        elif dx > 0 and dy == 0:
            return Direction.EAST
        elif dx > 0 and dy > 0:
            return Direction.SOUTHEAST
        elif dx == 0 and dy > 0:
            return Direction.SOUTH
        elif dx < 0 and dy > 0:
            return Direction.SOUTHWEST
        elif dx < 0 and dy == 0:
            return Direction.WEST
        elif dx < 0 and dy < 0:
            return Direction.NORTHWEST
        return Direction.EAST
    
    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)
    
    @classmethod
    def from_tuple(cls, t: Tuple[int, int]) -> 'Position':
        return cls(t[0], t[1])
    
    def copy(self) -> 'Position':
        return Position(self.x, self.y)


@dataclass(order=True)
class Node:
    position: Position = field(compare=False)
    g_cost: float = float('inf')
    h_cost: float = 0.0
    f_cost: float = field(default=float('inf'), compare=True)
    parent: Optional['Node'] = field(default=None, compare=False)
    
    def __post_init__(self):
        self.f_cost = self.g_cost + self.h_cost
    
    def update_costs(self, g_cost: float, h_cost: float):
        self.g_cost = g_cost
        self.h_cost = h_cost
        self.f_cost = g_cost + h_cost
    
    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.position == other.position
    
    def __hash__(self):
        return hash(self.position)


class GridMap:
    def __init__(self, width: int = 50, height: int = 50):
        self.width = width
        self.height = height
        self.grid: List[List[CellType]] = [
            [CellType.EMPTY for _ in range(width)] for _ in range(height)
        ]
        self.start_position: Optional[Position] = None
        self.end_position: Optional[Position] = None
        self.waypoints: List[Position] = []
        self.obstacles: Set[Tuple[int, int]] = set()
        self.modified = False
    
    def reset(self):
        self.grid = [
            [CellType.EMPTY for _ in range(self.width)] for _ in range(self.height)
        ]
        self.start_position = None
        self.end_position = None
        self.waypoints = []
        self.obstacles = set()
        self.modified = False
    
    def resize(self, new_width: int, new_height: int):
        new_grid = [
            [CellType.EMPTY for _ in range(new_width)] for _ in range(new_height)
        ]
        for y in range(min(self.height, new_height)):
            for x in range(min(self.width, new_width)):
                new_grid[y][x] = self.grid[y][x]
        self.grid = new_grid
        self.width = new_width
        self.height = new_height
        self._validate_positions()
        self.modified = True
    
    def _validate_positions(self):
        if self.start_position:
            if not self.is_valid_position(self.start_position):
                self.start_position = None
        if self.end_position:
            if not self.is_valid_position(self.end_position):
                self.end_position = None
        self.waypoints = [wp for wp in self.waypoints if self.is_valid_position(wp)]
        self.obstacles = {
            (x, y) for x, y in self.obstacles 
            if 0 <= x < self.width and 0 <= y < self.height
        }
    
    def is_valid_position(self, pos: Position) -> bool:
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height
    
    def get_cell(self, pos: Position) -> CellType:
        if not self.is_valid_position(pos):
            return CellType.OBSTACLE
        return self.grid[pos.y][pos.x]
    
    def set_cell(self, pos: Position, cell_type: CellType):
        if not self.is_valid_position(pos):
            return
        old_type = self.grid[pos.y][pos.x]
        self.grid[pos.y][pos.x] = cell_type
        if cell_type == CellType.START:
            if self.start_position and self.start_position != pos:
                self.grid[self.start_position.y][self.start_position.x] = CellType.EMPTY
            self.start_position = pos
        elif cell_type == CellType.END:
            if self.end_position and self.end_position != pos:
                self.grid[self.end_position.y][self.end_position.x] = CellType.EMPTY
            self.end_position = pos
        elif cell_type == CellType.OBSTACLE:
            self.obstacles.add((pos.x, pos.y))
        elif cell_type == CellType.WAYPOINT:
            if pos not in self.waypoints:
                self.waypoints.append(pos)
        if old_type == CellType.OBSTACLE and cell_type != CellType.OBSTACLE:
            self.obstacles.discard((pos.x, pos.y))
        if old_type == CellType.WAYPOINT and cell_type != CellType.WAYPOINT:
            if pos in self.waypoints:
                self.waypoints.remove(pos)
        self.modified = True
    
    def is_walkable(self, pos: Position) -> bool:
        cell = self.get_cell(pos)
        return cell != CellType.OBSTACLE
    
    def get_neighbors(self, pos: Position, allow_diagonal: bool = True) -> List[Position]:
        neighbors = []
        directions = [
            (0, -1), (1, 0), (0, 1), (-1, 0)
        ]
        if allow_diagonal:
            directions.extend([
                (1, -1), (1, 1), (-1, 1), (-1, -1)
            ])
        for dx, dy in directions:
            new_pos = Position(pos.x + dx, pos.y + dy)
            if self.is_valid_position(new_pos) and self.is_walkable(new_pos):
                if abs(dx) == 1 and abs(dy) == 1:
                    pos1 = Position(pos.x + dx, pos.y)
                    pos2 = Position(pos.x, pos.y + dy)
                    if self.is_walkable(pos1) and self.is_walkable(pos2):
                        neighbors.append(new_pos)
                else:
                    neighbors.append(new_pos)
        return neighbors
    
    def has_line_of_sight(self, a: Position, b: Position) -> bool:
        """Bresenham 视线检测：a 与 b 之间是否全程可通行。

        Theta* 的任意角度连线与路径校验器共用同一套判定标准，避免"算法认为
        可见、校验器认为穿墙"的不一致。
        """
        x0, y0 = a.x, a.y
        x1, y1 = b.x, b.y
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if not self.is_walkable(Position(x0, y0)):
                return False
            if x0 == x1 and y0 == y1:
                return True
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def get_movement_cost(self, from_pos: Position, to_pos: Position) -> float:
        dx = abs(to_pos.x - from_pos.x)
        dy = abs(to_pos.y - from_pos.y)
        if dx + dy == 2:
            return 1.414
        return 1.0
    
    def add_obstacle(self, pos: Position):
        self.set_cell(pos, CellType.OBSTACLE)
    
    def remove_obstacle(self, pos: Position):
        if self.get_cell(pos) == CellType.OBSTACLE:
            self.set_cell(pos, CellType.EMPTY)
    
    def toggle_obstacle(self, pos: Position):
        if self.get_cell(pos) == CellType.OBSTACLE:
            self.set_cell(pos, CellType.EMPTY)
        else:
            self.set_cell(pos, CellType.OBSTACLE)
    
    def set_start(self, pos: Position):
        self.set_cell(pos, CellType.START)
    
    def set_end(self, pos: Position):
        self.set_cell(pos, CellType.END)
    
    def add_waypoint(self, pos: Position):
        if pos not in self.waypoints:
            self.set_cell(pos, CellType.WAYPOINT)
    
    def remove_waypoint(self, pos: Position):
        if pos in self.waypoints:
            self.waypoints.remove(pos)
            if self.get_cell(pos) == CellType.WAYPOINT:
                self.set_cell(pos, CellType.EMPTY)
    
    def clear_path_visualization(self):
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if cell in [CellType.PATH, CellType.VISITED, CellType.CURRENT]:
                    self.grid[y][x] = CellType.EMPTY
    
    def generate_random_obstacles(self, density: float = 0.3, ensure_connected: bool = False):
        """随机撒障碍物。

        :param density: 障碍物占比，0~1。
        :param ensure_connected: 为 True 时自动打通隔离区域，保证处处可达。
        """
        self.reset()
        density = min(max(density, 0.0), 1.0)
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < density:
                    self.add_obstacle(Position(x, y))
        if ensure_connected:
            self.ensure_connectivity()
        self.modified = True

    def generate_maze(self):
        """用递归回溯法生成「完美迷宫」（任意两点间只有一条通路）。

        墙体落在偶数坐标上，通道落在奇数坐标上；地图最外圈保持为墙。偶数尺寸
        会自动向内收缩一格，保证奇偶对齐。
        """
        self.reset()
        max_x = self.width - 2 if (self.width - 2) % 2 == 1 else self.width - 3
        max_y = self.height - 2 if (self.height - 2) % 2 == 1 else self.height - 3
        if max_x < 1 or max_y < 1:
            return

        for y in range(self.height):
            for x in range(self.width):
                self.set_cell(Position(x, y), CellType.OBSTACLE)

        origin = Position(1, 1)
        self.set_cell(origin, CellType.EMPTY)
        visited = {origin}
        stack = [origin]
        steps = ((2, 0), (-2, 0), (0, 2), (0, -2))

        while stack:
            current = stack[-1]
            candidates = []
            for dx, dy in steps:
                nx, ny = current.x + dx, current.y + dy
                if 1 <= nx <= max_x and 1 <= ny <= max_y:
                    target = Position(nx, ny)
                    if target not in visited:
                        candidates.append((target, Position(current.x + dx // 2, current.y + dy // 2)))
            if not candidates:
                stack.pop()
                continue
            target, wall = random.choice(candidates)
            self.set_cell(wall, CellType.EMPTY)
            self.set_cell(target, CellType.EMPTY)
            visited.add(target)
            stack.append(target)

        self.modified = True

    def ensure_connectivity(self, anchor: Position = None) -> int:
        """把所有互不相通的可通行区域连成一片，返回新打通的格子数。

        做法：以 ``anchor`` 所在（或面积最大）的区域为主干，其余区域各自朝主干
        打通一条 L 形走廊。用于「随机障碍物」这类可能把地图撕碎的场景。
        """
        walkable = [
            Position(x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.is_walkable(Position(x, y))
        ]
        if not walkable:
            return 0

        components = self._walkable_components()
        if len(components) <= 1:
            return 0

        def component_of(pos: Position):
            for comp in components:
                if pos in comp:
                    return comp
            return None

        if anchor is not None and anchor in walkable:
            main = component_of(anchor) or max(components, key=len)
        else:
            main = max(components, key=len)

        carved = 0
        hub = min(main)
        for comp in components:
            if comp is main:
                continue
            start = min(comp)
            carved += self._carve_corridor(start, hub)
        self.modified = True
        return carved

    def _carve_corridor(self, a: Position, b: Position) -> int:
        """沿 L 形路径把两点之间的障碍物打通，返回打通格数。"""
        carved = 0
        x, y = a.x, a.y
        while x != b.x:
            x += 1 if b.x > x else -1
            pos = Position(x, y)
            if not self.is_walkable(pos):
                self.set_cell(pos, CellType.EMPTY)
                carved += 1
        while y != b.y:
            y += 1 if b.y > y else -1
            pos = Position(x, y)
            if not self.is_walkable(pos):
                self.set_cell(pos, CellType.EMPTY)
                carved += 1
        return carved

    def _walkable_components(self) -> List[Set[Position]]:
        """返回所有四连通的可通行区域。"""
        seen: Set[Position] = set()
        components: List[Set[Position]] = []
        for y in range(self.height):
            for x in range(self.width):
                start = Position(x, y)
                if start in seen or not self.is_walkable(start):
                    continue
                comp: Set[Position] = set()
                queue = deque([start])
                seen.add(start)
                while queue:
                    current = queue.popleft()
                    comp.add(current)
                    for neighbor in self.get_neighbors(current, False):
                        if neighbor not in seen:
                            seen.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)
        return components

    def generate_room_obstacles(self, num_rooms: int = 5):
        self.reset()
        room_width = self.width // (num_rooms + 1)
        room_height = self.height // (num_rooms + 1)
        for i in range(1, num_rooms + 1):
            for j in range(1, num_rooms + 1):
                rx = random.randint((i-1) * room_width + 2, i * room_width - 2)
                ry = random.randint((j-1) * room_height + 2, j * room_height - 2)
                rw = random.randint(3, room_width - 2)
                rh = random.randint(3, room_height - 2)
                for dx in range(rw):
                    for dy in range(rh):
                        if dx == 0 or dx == rw - 1 or dy == 0 or dy == rh - 1:
                            self.add_obstacle(Position(rx + dx, ry + dy))
        self.modified = True
    
    def to_dict(self) -> dict:
        return {
            'width': self.width,
            'height': self.height,
            'grid': [[cell.value for cell in row] for row in self.grid],
            'start': (self.start_position.x, self.start_position.y) if self.start_position else None,
            'end': (self.end_position.x, self.end_position.y) if self.end_position else None,
            'waypoints': [(wp.x, wp.y) for wp in self.waypoints],
            'obstacles': list(self.obstacles)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GridMap':
        grid_map = cls(data['width'], data['height'])
        grid_map.grid = [
            [CellType(cell) for cell in row] for row in data['grid']
        ]
        if data['start']:
            grid_map.start_position = Position(data['start'][0], data['start'][1])
        if data['end']:
            grid_map.end_position = Position(data['end'][0], data['end'][1])
        grid_map.waypoints = [Position(wp[0], wp[1]) for wp in data['waypoints']]
        grid_map.obstacles = set(tuple(o) for o in data['obstacles'])
        return grid_map
    
    def copy(self) -> 'GridMap':
        new_map = GridMap(self.width, self.height)
        new_map.grid = [[cell for cell in row] for row in self.grid]
        new_map.start_position = self.start_position.copy() if self.start_position else None
        new_map.end_position = self.end_position.copy() if self.end_position else None
        new_map.waypoints = [wp.copy() for wp in self.waypoints]
        new_map.obstacles = set(self.obstacles)
        return new_map


class PathResult:
    def __init__(self):
        self.path: List[Position] = []
        self.visited_nodes: List[Position] = []
        self.path_length: float = 0.0
        self.nodes_explored: int = 0
        self.execution_time: float = 0.0
        self.algorithm_name: str = ""
        self.success: bool = False
        self.message: str = ""
        #: 是否在专用算法失效后回退到 A*（目前仅 JPS 会用到）
        self.fallback_used: bool = False
    
    def calculate_path_length(self):
        self.path_length = 0.0
        for i in range(len(self.path) - 1):
            self.path_length += self.path[i].distance_to(self.path[i + 1])
    
    def get_directions(self) -> List[Tuple[Direction, float, Position]]:
        directions = []
        if len(self.path) < 2:
            return directions
        current_idx = 0
        while current_idx < len(self.path) - 1:
            current_pos = self.path[current_idx]
            next_idx = current_idx + 1
            direction = current_pos.get_direction_to(self.path[next_idx])
            segment_length = 0.0
            while next_idx < len(self.path):
                next_direction = current_pos.get_direction_to(self.path[next_idx])
                if next_direction != direction:
                    break
                segment_length += current_pos.distance_to(self.path[next_idx])
                current_pos = self.path[next_idx]
                next_idx += 1
            if next_idx == current_idx + 1:
                segment_length = self.path[current_idx].distance_to(self.path[next_idx])
                current_idx = next_idx
            else:
                current_idx = next_idx - 1
            directions.append((direction, segment_length, self.path[current_idx]))
        return directions
