# -*- coding: utf-8 -*-
"""多途经点规划、路径平滑/优化、插值与历史记录。"""

from __future__ import annotations

import json
import time
from typing import Dict, List, Optional, Tuple

from .algorithms import AlgorithmFactory
from .models import GridMap, PathResult, Position


class MultiWaypointPlanner:
    def __init__(self, grid_map: GridMap, algorithm_name: str = 'A*', allow_diagonal: bool = True):
        self.grid_map = grid_map
        self.algorithm_name = algorithm_name
        self.allow_diagonal = allow_diagonal
    
    def plan(self, start: Position, waypoints: List[Position], end: Position) -> PathResult:
        result = PathResult()
        result.algorithm_name = f"多途经点-{self.algorithm_name}"
        start_time = time.time()
        if not waypoints:
            algorithm = AlgorithmFactory.create_algorithm(
                self.algorithm_name, self.grid_map, self.allow_diagonal
            )
            return algorithm.find_path(start, end)
        all_points = [start] + waypoints + [end]
        distance_matrix = self._build_distance_matrix(all_points)
        best_order = self._solve_tsp(distance_matrix, 0, len(all_points) - 1)
        ordered_points = [all_points[i] for i in best_order]
        full_path = []
        all_visited = []
        for i in range(len(ordered_points) - 1):
            algorithm = AlgorithmFactory.create_algorithm(
                self.algorithm_name, self.grid_map, self.allow_diagonal
            )
            segment_result = algorithm.find_path(ordered_points[i], ordered_points[i + 1])
            if not segment_result.success:
                result.success = False
                result.message = f"无法找到从 {ordered_points[i]} 到 {ordered_points[i + 1]} 的路径"
                return result
            if full_path:
                full_path.extend(segment_result.path[1:])
            else:
                full_path = segment_result.path.copy()
            all_visited.extend(segment_result.visited_nodes)
        result.path = full_path
        result.visited_nodes = all_visited
        result.success = True
        result.calculate_path_length()
        result.nodes_explored = len(set(all_visited))
        result.execution_time = time.time() - start_time
        result.message = f"找到多途经点路径，总长度: {result.path_length:.2f}"
        return result
    
    def _build_distance_matrix(self, points: List[Position]) -> List[List[float]]:
        n = len(points)
        matrix = [[float('inf')] * n for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 0
            for j in range(n):
                if i != j:
                    matrix[i][j] = points[i].distance_to(points[j])
        return matrix
    
    def _solve_tsp(self, distance_matrix: List[List[float]], start_idx: int, end_idx: int) -> List[int]:
        n = len(distance_matrix)
        if n <= 2:
            return [start_idx, end_idx]
        middle_indices = [i for i in range(n) if i != start_idx and i != end_idx]
        best_order = None
        best_distance = float('inf')
        from itertools import permutations
        for perm in permutations(middle_indices):
            order = [start_idx] + list(perm) + [end_idx]
            distance = 0
            for i in range(len(order) - 1):
                distance += distance_matrix[order[i]][order[i + 1]]
            if distance < best_distance:
                best_distance = distance
                best_order = order
        return best_order if best_order else [start_idx, end_idx]


class RouteOptimizer:
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
    
    def optimize_route(self, waypoints: List[Position]) -> List[Position]:
        if len(waypoints) <= 2:
            return waypoints
        best_order = waypoints.copy()
        best_distance = self._calculate_total_distance(best_order)
        improved = True
        while improved:
            improved = False
            for i in range(1, len(best_order) - 1):
                for j in range(i + 1, len(best_order)):
                    new_order = best_order.copy()
                    new_order[i:j] = reversed(new_order[i:j])
                    new_distance = self._calculate_total_distance(new_order)
                    if new_distance < best_distance:
                        best_order = new_order
                        best_distance = new_distance
                        improved = True
        return best_order
    
    def _calculate_total_distance(self, waypoints: List[Position]) -> float:
        total = 0.0
        for i in range(len(waypoints) - 1):
            total += waypoints[i].distance_to(waypoints[i + 1])
        return total
    
    def find_nearest_waypoint(self, current: Position, waypoints: List[Position]) -> Optional[Position]:
        if not waypoints:
            return None
        nearest = min(waypoints, key=lambda p: current.distance_to(p))
        return nearest
    
    def find_optimal_insertion_point(self, path: List[Position], new_point: Position) -> int:
        if len(path) < 2:
            return len(path)
        best_index = 0
        best_increase = float('inf')
        for i in range(len(path) - 1):
            original_dist = path[i].distance_to(path[i + 1])
            new_dist = path[i].distance_to(new_point) + new_point.distance_to(path[i + 1])
            increase = new_dist - original_dist
            if increase < best_increase:
                best_increase = increase
                best_index = i + 1
        return best_index


class PathSmoother:
    @staticmethod
    def smooth_path(path: List[Position], grid_map: GridMap) -> List[Position]:
        if len(path) <= 2:
            return path
        smoothed = [path[0]]
        i = 0
        while i < len(path) - 1:
            j = len(path) - 1
            while j > i + 1:
                if PathSmoother._has_line_of_sight(path[i], path[j], grid_map):
                    break
                j -= 1
            smoothed.append(path[j])
            i = j
        return smoothed
    
    @staticmethod
    def _has_line_of_sight(start: Position, end: Position, grid_map: GridMap) -> bool:
        x0, y0 = start.x, start.y
        x1, y1 = end.x, end.y
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if not grid_map.is_walkable(Position(x0, y0)):
                return False
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        return True


class PathOptimizer:
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
    
    def optimize(self, path: List[Position], method: str = 'smooth') -> List[Position]:
        if method == 'smooth':
            return PathSmoother.smooth_path(path, self.grid_map)
        elif method == 'shortcut':
            return self._apply_shortcuts(path)
        elif method == 'catmull_rom':
            return self._catmull_rom_spline(path)
        return path
    
    def _apply_shortcuts(self, path: List[Position]) -> List[Position]:
        if len(path) <= 2:
            return path
        result = [path[0]]
        for i in range(1, len(path) - 1):
            prev = result[-1]
            curr = path[i]
            next_pos = path[i + 1]
            dx1 = curr.x - prev.x
            dy1 = curr.y - prev.y
            dx2 = next_pos.x - curr.x
            dy2 = next_pos.y - curr.y
            if dx1 != dx2 or dy1 != dy2:
                result.append(curr)
        result.append(path[-1])
        return result
    
    def _catmull_rom_spline(self, path: List[Position], segments: int = 10) -> List[Position]:
        if len(path) < 4:
            return path
        result = []
        for i in range(len(path) - 1):
            p0 = path[max(0, i - 1)]
            p1 = path[i]
            p2 = path[min(len(path) - 1, i + 1)]
            p3 = path[min(len(path) - 1, i + 2)]
            for t in range(segments):
                s = t / segments
                result.append(self._catmull_rom_point(p0, p1, p2, p3, s))
        result.append(path[-1])
        return self._discretize_path(result)
    
    def _catmull_rom_point(self, p0: Position, p1: Position, p2: Position, p3: Position, t: float) -> Position:
        t2 = t * t
        t3 = t2 * t
        x = 0.5 * ((2 * p1.x) + (-p0.x + p2.x) * t + 
                   (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 + 
                   (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3)
        y = 0.5 * ((2 * p1.y) + (-p0.y + p2.y) * t + 
                   (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 + 
                   (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3)
        return Position(int(round(x)), int(round(y)))
    
    def _discretize_path(self, path: List[Position]) -> List[Position]:
        result = []
        for pos in path:
            if not result or pos != result[-1]:
                if self.grid_map.is_valid_position(pos) and self.grid_map.is_walkable(pos):
                    result.append(pos)
        return result


class PathInterpolator:
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
    
    def interpolate_linear(self, path: List[Position], step: float = 0.5) -> List[Tuple[float, float]]:
        if len(path) < 2:
            return [(p.x, p.y) for p in path]
        interpolated = []
        for i in range(len(path) - 1):
            p1 = path[i]
            p2 = path[i + 1]
            distance = p1.distance_to(p2)
            num_steps = max(1, int(distance / step))
            for j in range(num_steps):
                t = j / num_steps
                x = p1.x + (p2.x - p1.x) * t
                y = p1.y + (p2.y - p1.y) * t
                interpolated.append((x, y))
        interpolated.append((path[-1].x, path[-1].y))
        return interpolated
    
    def interpolate_bezier(self, path: List[Position], segments: int = 20) -> List[Tuple[float, float]]:
        if len(path) < 2:
            return [(p.x, p.y) for p in path]
        control_points = self._generate_control_points(path)
        interpolated = []
        for i in range(len(control_points) - 1):
            for t in range(segments):
                point = self._bezier_point(control_points[i:i+4], t / segments)
                if point:
                    interpolated.append(point)
        interpolated.append((path[-1].x, path[-1].y))
        return interpolated
    
    def _generate_control_points(self, path: List[Position]) -> List[Tuple[float, float]]:
        points = [(path[0].x, path[0].y)]
        for i in range(1, len(path) - 1):
            prev = path[i - 1]
            curr = path[i]
            next_p = path[i + 1]
            cp1 = (curr.x - (next_p.x - prev.x) * 0.2, curr.y - (next_p.y - prev.y) * 0.2)
            cp2 = (curr.x + (next_p.x - prev.x) * 0.2, curr.y + (next_p.y - prev.y) * 0.2)
            points.append(cp1)
            points.append((curr.x, curr.y))
            points.append(cp2)
        points.append((path[-1].x, path[-1].y))
        return points
    
    def _bezier_point(self, points: List[Tuple[float, float]], t: float) -> Optional[Tuple[float, float]]:
        if len(points) < 4:
            return None
        p0, p1, p2, p3 = points[0], points[1], points[2], points[3]
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        x = mt3 * p0[0] + 3 * mt2 * t * p1[0] + 3 * mt * t2 * p2[0] + t3 * p3[0]
        y = mt3 * p0[1] + 3 * mt2 * t * p1[1] + 3 * mt * t2 * p2[1] + t3 * p3[1]
        return (x, y)


class DynamicObstacleHandler:
    def __init__(self, grid_map: GridMap, algorithm_name: str = 'A*'):
        self.grid_map = grid_map
        self.algorithm_name = algorithm_name
        self.current_path: List[Position] = []
        self.current_index = 0
    
    def set_path(self, path: List[Position]):
        self.current_path = path
        self.current_index = 0
    
    def add_dynamic_obstacle(self, pos: Position) -> Optional[PathResult]:
        if pos in self.current_path:
            self.grid_map.add_obstacle(pos)
            return self.replan()
        self.grid_map.add_obstacle(pos)
        return None
    
    def replan(self) -> Optional[PathResult]:
        if not self.grid_map.start_position or not self.grid_map.end_position:
            return None
        if self.current_index < len(self.current_path):
            current_pos = self.current_path[self.current_index]
            algorithm = AlgorithmFactory.create_algorithm(self.algorithm_name, self.grid_map)
            result = algorithm.find_path(current_pos, self.grid_map.end_position)
            if result.success:
                self.current_path = result.path
                self.current_index = 0
            return result
        return None
    
    def advance(self) -> bool:
        if self.current_index < len(self.current_path) - 1:
            self.current_index += 1
            return True
        return False
    
    def get_current_position(self) -> Optional[Position]:
        if self.current_index < len(self.current_path):
            return self.current_path[self.current_index]
        return None


class PathHistory:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.history: List[Dict] = []
    
    def add_entry(self, algorithm: str, start: Position, end: Position, 
                  path: List[Position], execution_time: float):
        entry = {
            'algorithm': algorithm,
            'start': (start.x, start.y),
            'end': (end.x, end.y),
            'path_length': len(path),
            'execution_time': execution_time,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.history.append(entry)
        if len(self.history) > self.max_size:
            self.history.pop(0)
    
    def get_recent(self, count: int = 10) -> List[Dict]:
        return self.history[-count:]
    
    def get_by_algorithm(self, algorithm: str) -> List[Dict]:
        return [e for e in self.history if e['algorithm'] == algorithm]
    
    def get_statistics(self) -> Dict:
        if not self.history:
            return {}
        total = len(self.history)
        avg_time = sum(e['execution_time'] for e in self.history) / total
        avg_length = sum(e['path_length'] for e in self.history) / total
        algorithm_counts = {}
        for e in self.history:
            algo = e['algorithm']
            algorithm_counts[algo] = algorithm_counts.get(algo, 0) + 1
        return {
            'total_searches': total,
            'average_time': avg_time,
            'average_path_length': avg_length,
            'algorithm_usage': algorithm_counts
        }
    
    def clear(self):
        self.history.clear()
    
    def export(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
