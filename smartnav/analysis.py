# -*- coding: utf-8 -*-
"""性能分析、统计、基准测试与各类路径指标计算。"""

from __future__ import annotations

import csv
import math
import time
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from .algorithms import AlgorithmFactory
from .models import GridMap, PathResult, Position


class PathValidator:
    """路径合法性校验。

    - :meth:`validate`：适用于网格路径（A*/Dijkstra/BFS…），要求逐格相邻。
    - :meth:`validate_any_angle`：适用于 Theta*、平滑/插值后的任意角度折线，
      沿线段做超覆盖采样，确认不穿越障碍。
    """

    @staticmethod
    def validate(path: List[Position], grid_map: GridMap) -> bool:
        if not path:
            return False
        for pos in path:
            if not grid_map.is_valid_position(pos):
                return False
            if not grid_map.is_walkable(pos):
                return False
        for i in range(len(path) - 1):
            if not PathValidator._is_adjacent(path[i], path[i + 1]):
                return False
        return True

    @staticmethod
    def validate_any_angle(path: List[Position], grid_map: GridMap) -> bool:
        """校验允许任意角度连线的路径（Theta*/平滑路径）。"""
        if not path:
            return False
        for pos in path:
            if not grid_map.is_valid_position(pos) or not grid_map.is_walkable(pos):
                return False
        for i in range(len(path) - 1):
            if PathValidator._segment_blocked(path[i], path[i + 1], grid_map):
                return False
        return True

    @staticmethod
    def _segment_blocked(a: Position, b: Position, grid_map: GridMap) -> bool:
        """线段是否穿墙（与 Theta* 共用 Bresenham 视线判定）。"""
        return not grid_map.has_line_of_sight(a, b)

    @staticmethod
    def _is_adjacent(p1: Position, p2: Position) -> bool:
        dx = abs(p1.x - p2.x)
        dy = abs(p1.y - p2.y)
        return dx <= 1 and dy <= 1 and (dx + dy) > 0


class DistanceCalculator:
    @staticmethod
    def euclidean(p1: Position, p2: Position) -> float:
        return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)
    
    @staticmethod
    def manhattan(p1: Position, p2: Position) -> int:
        return abs(p1.x - p2.x) + abs(p1.y - p2.y)
    
    @staticmethod
    def chebyshev(p1: Position, p2: Position) -> int:
        return max(abs(p1.x - p2.x), abs(p1.y - p2.y))
    
    @staticmethod
    def octile(p1: Position, p2: Position) -> float:
        dx = abs(p1.x - p2.x)
        dy = abs(p1.y - p2.y)
        return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


class HeuristicFactory:
    @staticmethod
    def create(name: str, allow_diagonal: bool = True):
        if name == 'euclidean':
            return lambda p1, p2: DistanceCalculator.euclidean(p1, p2)
        elif name == 'manhattan':
            return lambda p1, p2: float(DistanceCalculator.manhattan(p1, p2))
        elif name == 'chebyshev':
            return lambda p1, p2: float(DistanceCalculator.chebyshev(p1, p2))
        elif name == 'octile':
            return lambda p1, p2: DistanceCalculator.octile(p1, p2)
        elif name == 'diagonal':
            return lambda p1, p2: DistanceCalculator.octile(p1, p2)
        else:
            # 未知名称回退到 0：等价于 Dijkstra，可采纳但不会破坏最优性
            return lambda p1, p2: 0.0


class PerformanceAnalyzer:
    def __init__(self):
        self.results: Dict[str, List[PathResult]] = {}
    
    def add_result(self, algorithm_name: str, result: PathResult):
        if algorithm_name not in self.results:
            self.results[algorithm_name] = []
        self.results[algorithm_name].append(result)
    
    def compare_algorithms(self, grid_map: GridMap, start: Position, end: Position,
                          algorithm_names: List[str], allow_diagonal: bool = True) -> Dict[str, PathResult]:
        comparison_results = {}
        for name in algorithm_names:
            try:
                algorithm = AlgorithmFactory.create_algorithm(name, grid_map, allow_diagonal)
                result = algorithm.find_path(start, end)
                comparison_results[name] = result
                self.add_result(name, result)
            except Exception as e:
                print(f"算法 {name} 执行失败: {e}")
        return comparison_results
    
    def get_statistics(self, algorithm_name: str) -> Dict:
        if algorithm_name not in self.results or not self.results[algorithm_name]:
            return {}
        results = self.results[algorithm_name]
        successful = [r for r in results if r.success]
        if not successful:
            return {
                'total_runs': len(results),
                'success_rate': 0,
                'avg_time': 0,
                'avg_nodes': 0,
                'avg_path_length': 0
            }
        return {
            'total_runs': len(results),
            'success_rate': len(successful) / len(results) * 100,
            'avg_time': sum(r.execution_time for r in successful) / len(successful),
            'avg_nodes': sum(r.nodes_explored for r in successful) / len(successful),
            'avg_path_length': sum(r.path_length for r in successful) / len(successful)
        }
    
    def clear_results(self):
        self.results.clear()


class StatisticsCollector:
    def __init__(self):
        self.runs: List[Dict] = []
    
    def record_run(self, algorithm: str, map_size: Tuple[int, int], 
                   obstacle_density: float, result: PathResult):
        self.runs.append({
            'algorithm': algorithm,
            'map_width': map_size[0],
            'map_height': map_size[1],
            'obstacle_density': obstacle_density,
            'success': result.success,
            'path_length': result.path_length,
            'nodes_explored': result.nodes_explored,
            'execution_time': result.execution_time,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def get_summary(self) -> Dict:
        if not self.runs:
            return {}
        successful = [r for r in self.runs if r['success']]
        return {
            'total_runs': len(self.runs),
            'successful_runs': len(successful),
            'success_rate': len(successful) / len(self.runs) * 100,
            'avg_execution_time': sum(r['execution_time'] for r in successful) / len(successful) if successful else 0,
            'avg_path_length': sum(r['path_length'] for r in successful) / len(successful) if successful else 0,
            'avg_nodes_explored': sum(r['nodes_explored'] for r in successful) / len(successful) if successful else 0
        }
    
    def export_to_csv(self, filename: str):
        if not self.runs:
            return
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.runs[0].keys())
            writer.writeheader()
            writer.writerows(self.runs)
    
    def clear(self):
        self.runs.clear()


class AlgorithmBenchmark:
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
        self.results: Dict[str, List[PathResult]] = {}
    
    def run_benchmark(self, algorithm_names: List[str], iterations: int = 10,
                     allow_diagonal: bool = True) -> Dict[str, Dict]:
        if not self.grid_map.start_position or not self.grid_map.end_position:
            return {}
        benchmark_results = {}
        for name in algorithm_names:
            times = []
            nodes = []
            path_lengths = []
            successes = 0
            for _ in range(iterations):
                algorithm = AlgorithmFactory.create_algorithm(name, self.grid_map, allow_diagonal)
                result = algorithm.find_path(self.grid_map.start_position, self.grid_map.end_position)
                times.append(result.execution_time)
                nodes.append(result.nodes_explored)
                if result.success:
                    successes += 1
                    path_lengths.append(result.path_length)
            benchmark_results[name] = {
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'avg_nodes': sum(nodes) / len(nodes),
                'success_rate': successes / iterations * 100,
                'avg_path_length': sum(path_lengths) / len(path_lengths) if path_lengths else 0
            }
        self.results = benchmark_results
        return benchmark_results

    def get_best_algorithm(self, metric: str = 'time') -> Tuple[str, Dict]:
        if not self.results:
            return (None, None)
        best_name = None
        best_value = float('inf')
        for name, data in self.results.items():
            if metric == 'time':
                value = data.get('avg_time', float('inf'))
            elif metric == 'nodes':
                value = data.get('avg_nodes', float('inf'))
            else:
                value = data.get('avg_time', float('inf'))
            if value < best_value:
                best_value = value
                best_name = name
        return (best_name, self.results.get(best_name))


class AccessibilityChecker:
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
    
    def check_reachability(self, start: Position, end: Position) -> bool:
        if not self.grid_map.is_valid_position(start) or not self.grid_map.is_valid_position(end):
            return False
        if not self.grid_map.is_walkable(start) or not self.grid_map.is_walkable(end):
            return False
        visited = set()
        queue = deque([start])
        visited.add(start)
        while queue:
            current = queue.popleft()
            if current == end:
                return True
            for neighbor in self.grid_map.get_neighbors(current, True):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False
    
    def find_connected_components(self) -> List[Set[Position]]:
        visited = set()
        components = []
        for y in range(self.grid_map.height):
            for x in range(self.grid_map.width):
                pos = Position(x, y)
                if pos not in visited and self.grid_map.is_walkable(pos):
                    component = self._bfs_component(pos, visited)
                    components.append(component)
        return components
    
    def _bfs_component(self, start: Position, visited: Set[Position]) -> Set[Position]:
        component = set()
        queue = deque([start])
        visited.add(start)
        component.add(start)
        while queue:
            current = queue.popleft()
            for neighbor in self.grid_map.get_neighbors(current, True):
                if neighbor not in visited and self.grid_map.is_walkable(neighbor):
                    visited.add(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        return component
    
    def get_isolated_areas(self) -> List[Position]:
        components = self.find_connected_components()
        if len(components) <= 1:
            return []
        largest = max(components, key=len)
        isolated = []
        for component in components:
            if component != largest:
                isolated.extend(component)
        return isolated
    
    def calculate_accessibility_score(self) -> float:
        total_cells = self.grid_map.width * self.grid_map.height
        obstacle_count = len(self.grid_map.obstacles)
        walkable = total_cells - obstacle_count
        if walkable == 0:
            return 0.0
        components = self.find_connected_components()
        if not components:
            return 0.0
        largest = max(components, key=len)
        return len(largest) / walkable


class HeatmapGenerator:
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
        self.heatmap: List[List[float]] = [
            [0.0 for _ in range(grid_map.width)] for _ in range(grid_map.height)
        ]
    
    def add_path(self, path: List[Position], weight: float = 1.0):
        for pos in path:
            if self.grid_map.is_valid_position(pos):
                self.heatmap[pos.y][pos.x] += weight
    
    def add_visited(self, visited: List[Position], weight: float = 0.5):
        for pos in visited:
            if self.grid_map.is_valid_position(pos):
                self.heatmap[pos.y][pos.x] += weight
    
    def apply_gaussian_blur(self, sigma: float = 1.0):
        kernel_size = int(sigma * 3) * 2 + 1
        kernel = self._create_gaussian_kernel(kernel_size, sigma)
        new_heatmap = [
            [0.0 for _ in range(self.grid_map.width)] for _ in range(self.grid_map.height)
        ]
        for y in range(self.grid_map.height):
            for x in range(self.grid_map.width):
                value = 0.0
                for ky in range(kernel_size):
                    for kx in range(kernel_size):
                        nx = x + kx - kernel_size // 2
                        ny = y + ky - kernel_size // 2
                        if 0 <= nx < self.grid_map.width and 0 <= ny < self.grid_map.height:
                            value += self.heatmap[ny][nx] * kernel[ky][kx]
                new_heatmap[y][x] = value
        self.heatmap = new_heatmap
    
    def _create_gaussian_kernel(self, size: int, sigma: float) -> List[List[float]]:
        kernel = [[0.0 for _ in range(size)] for _ in range(size)]
        center = size // 2
        total = 0.0
        for y in range(size):
            for x in range(size):
                dx = x - center
                dy = y - center
                value = math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma))
                kernel[y][x] = value
                total += value
        for y in range(size):
            for x in range(size):
                kernel[y][x] /= total
        return kernel
    
    def normalize(self):
        max_val = max(max(row) for row in self.heatmap)
        if max_val > 0:
            for y in range(self.grid_map.height):
                for x in range(self.grid_map.width):
                    self.heatmap[y][x] /= max_val
    
    def get_hotspots(self, threshold: float = 0.7) -> List[Position]:
        hotspots = []
        for y in range(self.grid_map.height):
            for x in range(self.grid_map.width):
                if self.heatmap[y][x] >= threshold:
                    hotspots.append(Position(x, y))
        return hotspots
    
    def clear(self):
        self.heatmap = [
            [0.0 for _ in range(self.grid_map.width)] for _ in range(self.grid_map.height)
        ]


class CollisionDetector:
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
    
    def check_path_collision(self, path: List[Position]) -> List[Position]:
        collisions = []
        for pos in path:
            if not self.grid_map.is_walkable(pos):
                collisions.append(pos)
        return collisions
    
    def check_agent_collision(self, agents: List[Dict]) -> List[Tuple[str, str, Position]]:
        collisions = []
        positions = {}
        for agent in agents:
            pos = agent['position']
            key = (pos.x, pos.y)
            if key in positions:
                collisions.append((positions[key], agent['id'], pos))
            else:
                positions[key] = agent['id']
        return collisions
    
    def predict_collision(self, path1: List[Position], path2: List[Position], 
                         start_time1: int = 0, start_time2: int = 0) -> Optional[Tuple[int, Position]]:
        min_len = min(len(path1), len(path2))
        for t in range(min_len):
            idx1 = t + start_time1
            idx2 = t + start_time2
            if idx1 < len(path1) and idx2 < len(path2):
                if path1[idx1] == path2[idx2]:
                    return (t, path1[idx1])
        return None
    
    def find_collision_free_alternative(self, path: List[Position], 
                                        blocked_positions: Set[Position]) -> Optional[List[Position]]:
        for i, pos in enumerate(path):
            if pos in blocked_positions:
                neighbors = self.grid_map.get_neighbors(pos, True)
                for neighbor in neighbors:
                    if neighbor not in blocked_positions:
                        alternative = path[:i] + [neighbor] + path[i+1:]
                        if not self.check_path_collision(alternative):
                            return alternative
        return None


class GradientCalculator:
    @staticmethod
    def calculate_gradient(grid_map: GridMap, pos: Position) -> Tuple[float, float]:
        neighbors = grid_map.get_neighbors(pos, True)
        if not neighbors:
            return (0.0, 0.0)
        gx = 0.0
        gy = 0.0
        for neighbor in neighbors:
            dx = neighbor.x - pos.x
            dy = neighbor.y - pos.y
            if grid_map.is_walkable(neighbor):
                gx += dx
                gy += dy
            else:
                gx -= dx
                gy -= dy
        magnitude = math.sqrt(gx * gx + gy * gy)
        if magnitude > 0:
            gx /= magnitude
            gy /= magnitude
        return (gx, gy)
    
    @staticmethod
    def calculate_potential_field(grid_map: GridMap, goal: Position) -> List[List[float]]:
        potential = [
            [float('inf') for _ in range(grid_map.width)] for _ in range(grid_map.height)
        ]
        queue = deque()
        if grid_map.is_valid_position(goal) and grid_map.is_walkable(goal):
            potential[goal.y][goal.x] = 0.0
            queue.append(goal)
        while queue:
            current = queue.popleft()
            current_potential = potential[current.y][current.x]
            for neighbor in grid_map.get_neighbors(current, True):
                new_potential = current_potential + grid_map.get_movement_cost(current, neighbor)
                if new_potential < potential[neighbor.y][neighbor.x]:
                    potential[neighbor.y][neighbor.x] = new_potential
                    queue.append(neighbor)
        return potential


class MetricsCalculator:
    @staticmethod
    def calculate_path_efficiency(path: List[Position], start: Position, end: Position) -> float:
        if not path:
            return 0.0
        actual_length = sum(
            path[i].distance_to(path[i + 1]) for i in range(len(path) - 1)
        )
        optimal_length = start.distance_to(end)
        if optimal_length == 0:
            return 1.0
        return optimal_length / actual_length if actual_length > 0 else 0.0
    
    @staticmethod
    def calculate_path_smoothness(path: List[Position]) -> float:
        if len(path) < 3:
            return 1.0
        direction_changes = 0
        for i in range(len(path) - 2):
            d1 = path[i].get_direction_to(path[i + 1])
            d2 = path[i + 1].get_direction_to(path[i + 2])
            if d1 != d2:
                direction_changes += 1
        return 1.0 - (direction_changes / (len(path) - 2))
    
    @staticmethod
    def calculate_exploration_ratio(visited: List[Position], grid_map: GridMap) -> float:
        total_walkable = sum(
            1 for y in range(grid_map.height) for x in range(grid_map.width)
            if grid_map.is_walkable(Position(x, y))
        )
        if total_walkable == 0:
            return 0.0
        return len(set(visited)) / total_walkable
