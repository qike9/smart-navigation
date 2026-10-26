# -*- coding: utf-8 -*-
"""八种寻路算法的实现与工厂。"""

from __future__ import annotations

import heapq
import math
import random
import time
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from .models import GridMap, Node, PathResult, Position


class PathfindingAlgorithm:
    def __init__(self, grid_map: GridMap, allow_diagonal: bool = True):
        self.grid_map = grid_map
        self.allow_diagonal = allow_diagonal
        self.heuristic_weight = 1.0
    
    def heuristic(self, pos: Position, goal: Position) -> float:
        if self.allow_diagonal:
            dx = abs(pos.x - goal.x)
            dy = abs(pos.y - goal.y)
            return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)
        else:
            return pos.manhattan_distance(goal)
    
    def find_path(self, start: Position, end: Position) -> PathResult:
        raise NotImplementedError
    
    def reconstruct_path(self, node: Node) -> List[Position]:
        path = []
        current = node
        while current:
            path.append(current.position)
            current = current.parent
        return list(reversed(path))


class AStarAlgorithm(PathfindingAlgorithm):
    def __init__(self, grid_map: GridMap, allow_diagonal: bool = True):
        super().__init__(grid_map, allow_diagonal)
        self.name = "A*"
    
    def find_path(self, start: Position, end: Position) -> PathResult:
        result = PathResult()
        result.algorithm_name = self.name
        start_time = time.time()
        open_set = []
        closed_set: Set[Position] = set()
        nodes: Dict[Position, Node] = {}
        start_node = Node(position=start, g_cost=0, h_cost=self.heuristic(start, end))
        start_node.f_cost = start_node.g_cost + start_node.h_cost
        nodes[start] = start_node
        heapq.heappush(open_set, start_node)
        result.visited_nodes.append(start)
        while open_set:
            current = heapq.heappop(open_set)
            if current.position in closed_set:
                continue
            closed_set.add(current.position)
            if current.position == end:
                result.path = self.reconstruct_path(current)
                result.success = True
                break
            neighbors = self.grid_map.get_neighbors(current.position, self.allow_diagonal)
            for neighbor_pos in neighbors:
                if neighbor_pos in closed_set:
                    continue
                tentative_g = current.g_cost + self.grid_map.get_movement_cost(
                    current.position, neighbor_pos
                )
                if neighbor_pos not in nodes:
                    neighbor_node = Node(position=neighbor_pos)
                    nodes[neighbor_pos] = neighbor_node
                else:
                    neighbor_node = nodes[neighbor_pos]
                if tentative_g < neighbor_node.g_cost:
                    neighbor_node.parent = current
                    h_cost = self.heuristic(neighbor_pos, end) * self.heuristic_weight
                    neighbor_node.update_costs(tentative_g, h_cost)
                    heapq.heappush(open_set, neighbor_node)
                    if neighbor_pos not in result.visited_nodes:
                        result.visited_nodes.append(neighbor_pos)
        result.nodes_explored = len(closed_set)
        result.execution_time = time.time() - start_time
        if result.success:
            result.calculate_path_length()
            result.message = f"找到路径，长度: {result.path_length:.2f}"
        else:
            result.message = "未找到有效路径"
        return result


class DijkstraAlgorithm(PathfindingAlgorithm):
    def __init__(self, grid_map: GridMap, allow_diagonal: bool = True):
        super().__init__(grid_map, allow_diagonal)
        self.name = "Dijkstra"
    
    def find_path(self, start: Position, end: Position) -> PathResult:
        result = PathResult()
        result.algorithm_name = self.name
        start_time = time.time()
        open_set = []
        closed_set: Set[Position] = set()
        nodes: Dict[Position, Node] = {}
        start_node = Node(position=start, g_cost=0, h_cost=0)
        start_node.f_cost = 0
        nodes[start] = start_node
        heapq.heappush(open_set, start_node)
        result.visited_nodes.append(start)
        while open_set:
            current = heapq.heappop(open_set)
            if current.position in closed_set:
                continue
            closed_set.add(current.position)
            if current.position == end:
                result.path = self.reconstruct_path(current)
                result.success = True
                break
            neighbors = self.grid_map.get_neighbors(current.position, self.allow_diagonal)
            for neighbor_pos in neighbors:
                if neighbor_pos in closed_set:
                    continue
                tentative_g = current.g_cost + self.grid_map.get_movement_cost(
                    current.position, neighbor_pos
                )
                if neighbor_pos not in nodes:
                    neighbor_node = Node(position=neighbor_pos)
                    nodes[neighbor_pos] = neighbor_node
                else:
                    neighbor_node = nodes[neighbor_pos]
                if tentative_g < neighbor_node.g_cost:
                    neighbor_node.parent = current
                    neighbor_node.update_costs(tentative_g, 0)
                    heapq.heappush(open_set, neighbor_node)
                    if neighbor_pos not in result.visited_nodes:
                        result.visited_nodes.append(neighbor_pos)
        result.nodes_explored = len(closed_set)
        result.execution_time = time.time() - start_time
        if result.success:
            result.calculate_path_length()
            result.message = f"找到路径，长度: {result.path_length:.2f}"
        else:
            result.message = "未找到有效路径"
        return result


class BFSAlgorithm(PathfindingAlgorithm):
    def __init__(self, grid_map: GridMap, allow_diagonal: bool = True):
        super().__init__(grid_map, allow_diagonal)
        self.name = "BFS"
    
    def find_path(self, start: Position, end: Position) -> PathResult:
        result = PathResult()
        result.algorithm_name = self.name
        start_time = time.time()
        queue = deque()
        visited: Set[Position] = set()
        parent_map: Dict[Position, Position] = {}
        queue.append(start)
        visited.add(start)
        result.visited_nodes.append(start)
        found = False
        while queue and not found:
            current = queue.popleft()
            if current == end:
                found = True
                break
            neighbors = self.grid_map.get_neighbors(current, self.allow_diagonal)
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent_map[neighbor] = current
                    queue.append(neighbor)
                    result.visited_nodes.append(neighbor)
                    if neighbor == end:
                        found = True
                        break
        result.nodes_explored = len(visited)
        result.execution_time = time.time() - start_time
        if found:
            path = []
            current = end
            while current != start:
                path.append(current)
                current = parent_map[current]
            path.append(start)
            result.path = list(reversed(path))
            result.success = True
            result.calculate_path_length()
            result.message = f"找到路径，长度: {result.path_length:.2f}"
        else:
            result.message = "未找到有效路径"
        return result


class DFSAlgorithm(PathfindingAlgorithm):
    def __init__(self, grid_map: GridMap, allow_diagonal: bool = True):
        super().__init__(grid_map, allow_diagonal)
        self.name = "DFS"
    
    def find_path(self, start: Position, end: Position) -> PathResult:
        result = PathResult()
        result.algorithm_name = self.name
        start_time = time.time()
        stack = []
        visited: Set[Position] = set()
        parent_map: Dict[Position, Position] = {}
        stack.append(start)
        visited.add(start)
        result.visited_nodes.append(start)
        found = False
        while stack and not found:
            current = stack.pop()
            if current == end:
                found = True
                break
            neighbors = self.grid_map.get_neighbors(current, self.allow_diagonal)
            random.shuffle(neighbors)
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent_map[neighbor] = current
                    stack.append(neighbor)
                    result.visited_nodes.append(neighbor)
                    if neighbor == end:
                        found = True
                        break
        result.nodes_explored = len(visited)
        result.execution_time = time.time() - start_time
        if found:
            path = []
            current = end
            while current != start:
                path.append(current)
                current = parent_map[current]
            path.append(start)
            result.path = list(reversed(path))
            result.success = True
            result.calculate_path_length()
            result.message = f"找到路径，长度: {result.path_length:.2f}"
        else:
            result.message = "未找到有效路径"
        return result


class GreedyBestFirstAlgorithm(PathfindingAlgorithm):
    def __init__(self, grid_map: GridMap, allow_diagonal: bool = True):
        super().__init__(grid_map, allow_diagonal)
        self.name = "Greedy Best-First"
    
    def find_path(self, start: Position, end: Position) -> PathResult:
        result = PathResult()
        result.algorithm_name = self.name
        start_time = time.time()
        open_set = []
        closed_set: Set[Position] = set()
        nodes: Dict[Position, Node] = {}
        start_node = Node(position=start, g_cost=0, h_cost=self.heuristic(start, end))
        start_node.f_cost = start_node.h_cost
        nodes[start] = start_node
        heapq.heappush(open_set, start_node)
        result.visited_nodes.append(start)
        while open_set:
            current = heapq.heappop(open_set)
            if current.position in closed_set:
                continue
            closed_set.add(current.position)
            if current.position == end:
                result.path = self.reconstruct_path(current)
                result.success = True
                break
            neighbors = self.grid_map.get_neighbors(current.position, self.allow_diagonal)
            for neighbor_pos in neighbors:
                if neighbor_pos in closed_set:
                    continue
                if neighbor_pos not in nodes:
                    h_cost = self.heuristic(neighbor_pos, end)
                    neighbor_node = Node(position=neighbor_pos, h_cost=h_cost)
                    neighbor_node.f_cost = h_cost
                    neighbor_node.parent = current
                    nodes[neighbor_pos] = neighbor_node
                    heapq.heappush(open_set, neighbor_node)
                    if neighbor_pos not in result.visited_nodes:
                        result.visited_nodes.append(neighbor_pos)
        result.nodes_explored = len(closed_set)
        result.execution_time = time.time() - start_time
        if result.success:
            result.calculate_path_length()
            result.message = f"找到路径，长度: {result.path_length:.2f}"
        else:
            result.message = "未找到有效路径"
        return result


class BidirectionalBFSAlgorithm(PathfindingAlgorithm):
    """双向广度优先搜索。

    从起点和终点同时逐层扩张，两个搜索波前相遇即得路径。相比单向 BFS 只搜索
    O(b^(d/2)) 个节点，在开阔地图上的优势非常明显。

    注意：BFS 系列优化的是「步数」而非「加权代价」，因此在允许斜向移动（斜走
    代价 1.414）时，路径步数最少但总长度可能略大于 A*。
    """

    def __init__(self, grid_map: GridMap, allow_diagonal: bool = True):
        super().__init__(grid_map, allow_diagonal)
        self.name = "双向BFS"

    def find_path(self, start: Position, end: Position) -> PathResult:
        result = PathResult()
        result.algorithm_name = self.name
        start_time = time.time()

        if start == end:
            result.path = [start]
            result.success = True
            result.visited_nodes.append(start)
            result.nodes_explored = 1
            result.execution_time = time.time() - start_time
            result.calculate_path_length()
            result.message = "起点与终点相同"
            return result

        forward_parent: Dict[Position, Optional[Position]] = {start: None}
        backward_parent: Dict[Position, Optional[Position]] = {end: None}
        forward_front: Set[Position] = {start}
        backward_front: Set[Position] = {end}
        result.visited_nodes.extend([start, end])
        meeting: Optional[Position] = None

        while forward_front and backward_front and meeting is None:
            # 每次展开较小的一侧整整一层，保证相遇时步数最优
            if len(forward_front) <= len(backward_front):
                meeting = self._expand_layer(forward_front, forward_parent, backward_parent, result)
            else:
                meeting = self._expand_layer(backward_front, backward_parent, forward_parent, result)

        result.nodes_explored = len(forward_parent) + len(backward_parent)
        result.execution_time = time.time() - start_time

        if meeting is not None:
            head = []
            node: Optional[Position] = meeting
            while node is not None:
                head.append(node)
                node = forward_parent[node]
            head.reverse()
            tail = []
            node = backward_parent[meeting]
            while node is not None:
                tail.append(node)
                node = backward_parent[node]
            result.path = head + tail
            result.success = True
            result.calculate_path_length()
            result.message = f"找到路径，长度: {result.path_length:.2f}"
        else:
            result.message = "未找到有效路径"
        return result

    def _expand_layer(
        self,
        front: Set[Position],
        own_parent: Dict[Position, Optional[Position]],
        other_parent: Dict[Position, Optional[Position]],
        result: PathResult,
    ) -> Optional[Position]:
        """把一层波前整体向外推一步；与另一侧波前相交时返回相遇点。"""
        next_front: Set[Position] = set()
        hit: Optional[Position] = None
        for node in front:
            for neighbor in self.grid_map.get_neighbors(node, self.allow_diagonal):
                if neighbor in own_parent:
                    continue
                own_parent[neighbor] = node
                result.visited_nodes.append(neighbor)
                if neighbor in other_parent:
                    hit = neighbor
                    break
                next_front.add(neighbor)
            if hit is not None:
                break
        front.clear()
        front.update(next_front)
        return hit


class JumpPointSearchAlgorithm(PathfindingAlgorithm):
    """跳点搜索（JPS）。

    A* 的剪枝变体：不再逐格扩展，而是沿直线/对角线「跳跃」到下一个必须决策的
    跳点。核心是三步——剪枝自然邻居、识别强制邻居、递归式跳跃扫描。

    与 :meth:`GridMap.get_neighbors` 保持同一套「禁止穿墙角」规则，保证本算法
    找到的路径与 A* 完全一致。
    """

    def __init__(self, grid_map: GridMap, allow_diagonal: bool = True):
        super().__init__(grid_map, allow_diagonal)
        self.name = "Jump Point Search"

    # ------------------------------------------------------------------ #
    # 基础判定
    # ------------------------------------------------------------------ #
    def _walkable(self, x: int, y: int) -> bool:
        pos = Position(x, y)
        return self.grid_map.is_valid_position(pos) and self.grid_map.is_walkable(pos)

    def _step_ok(self, pos: Position, dx: int, dy: int) -> bool:
        """沿 (dx, dy) 走一步是否合法（越界/障碍/穿墙角）。"""
        nx, ny = pos.x + dx, pos.y + dy
        if not self._walkable(nx, ny):
            return False
        if dx != 0 and dy != 0:
            if not self._walkable(pos.x + dx, pos.y):
                return False
            if not self._walkable(pos.x, pos.y + dy):
                return False
        return True

    # ------------------------------------------------------------------ #
    # 剪枝与强制邻居
    # ------------------------------------------------------------------ #
    def _forced_neighbors(self, pos: Position, dx: int, dy: int) -> List[Position]:
        forced: List[Position] = []
        x, y = pos.x, pos.y
        if dx != 0 and dy != 0:
            if not self._walkable(x - dx, y) and self._walkable(x - dx, y + dy):
                forced.append(Position(x - dx, y + dy))
            if not self._walkable(x, y - dy) and self._walkable(x + dx, y - dy):
                forced.append(Position(x + dx, y - dy))
        elif dx != 0:
            if not self._walkable(x, y - 1) and self._walkable(x + dx, y - 1):
                forced.append(Position(x + dx, y - 1))
            if not self._walkable(x, y + 1) and self._walkable(x + dx, y + 1):
                forced.append(Position(x + dx, y + 1))
        else:
            if not self._walkable(x - 1, y) and self._walkable(x - 1, y + dy):
                forced.append(Position(x - 1, y + dy))
            if not self._walkable(x + 1, y) and self._walkable(x + 1, y + dy):
                forced.append(Position(x + 1, y + dy))
        return forced

    def _natural_neighbors(self, pos: Position, dx: int, dy: int) -> List[Position]:
        """不含强制邻居时仍需考虑的「自然邻居」。"""
        result: List[Position] = []
        if dx == 0 and dy == 0:  # 起点：八个方向都可尝试
            for ddx, ddy in self._directions():
                if self._step_ok(pos, ddx, ddy):
                    result.append(Position(pos.x + ddx, pos.y + ddy))
            return result
        if dx != 0 and dy != 0:
            if not self._step_ok(pos, dx, dy):
                return result
            result.append(Position(pos.x + dx, pos.y + dy))
            if self._step_ok(pos, dx, 0):
                result.append(Position(pos.x + dx, pos.y))
            if self._step_ok(pos, 0, dy):
                result.append(Position(pos.x, pos.y + dy))
        else:
            if self._step_ok(pos, dx, dy):
                result.append(Position(pos.x + dx, pos.y + dy))
        return result

    def _directions(self) -> List[Tuple[int, int]]:
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if self.allow_diagonal:
            dirs.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        return dirs

    # ------------------------------------------------------------------ #
    # 跳跃扫描
    # ------------------------------------------------------------------ #
    def _jump(self, pos: Position, dx: int, dy: int, goal: Position) -> Optional[Position]:
        """从 pos 沿 (dx, dy) 跳跃，返回遇到的第一个跳点/目标。"""
        current = pos
        while True:
            if not self._step_ok(current, dx, dy):
                return None
            current = Position(current.x + dx, current.y + dy)
            if current == goal:
                return current
            if self._forced_neighbors(current, dx, dy):
                return current
            if dx != 0 and dy != 0:
                # 对角线移动时，两个正方向若存在跳点，则当前点也是跳点
                if self._jump(current, dx, 0, goal) is not None:
                    return current
                if self._jump(current, 0, dy, goal) is not None:
                    return current

    def _successors(self, current: Node, goal: Position) -> List[Position]:
        pos = current.position
        parent = current.parent
        if parent is None:
            return self._natural_neighbors(pos, 0, 0)
        dx = pos.x - parent.position.x
        dy = pos.y - parent.position.y
        # 父节点可能不是相邻格（跳点之间的跨度），归一化到单位方向
        dx = (dx > 0) - (dx < 0)
        dy = (dy > 0) - (dy < 0)
        if dx != 0 and dy != 0 and not self.allow_diagonal:
            dx, dy = 0, 0
        candidates = self._forced_neighbors(pos, dx, dy) + self._natural_neighbors(pos, dx, dy)
        successors = []
        for cand in candidates:
            sdx = (cand.x - pos.x)
            sdy = (cand.y - pos.y)
            sdx = (sdx > 0) - (sdx < 0)
            sdy = (sdy > 0) - (sdy < 0)
            jp = self._jump(pos, sdx, sdy, goal)
            if jp is not None:
                successors.append(jp)
        return successors

    # ------------------------------------------------------------------ #
    # 主流程
    # ------------------------------------------------------------------ #
    def find_path(self, start: Position, end: Position) -> PathResult:
        """先用跳点搜索求路；极端地形下若跳点搜索无解则回退 A*。

        1 格宽的墙缝（例如迷宫）会让「禁止穿墙角」的跳点剪枝失效，此时标准 JPS
        可能漏掉唯一通路。为保证结果永远与 A* 一致，这里做一次透明回退，并在
        ``message`` 与 ``fallback_used`` 中标注。
        """
        result = self._jps_search(start, end)
        if result.success:
            return result

        fallback = AStarAlgorithm(self.grid_map, self.allow_diagonal).find_path(start, end)
        fallback.algorithm_name = self.name
        if fallback.success:
            fallback.fallback_used = True
            fallback.message = "跳点剪枝未覆盖该地形，已回退 A*（路径最优性不受影响）"
            fallback.nodes_explored += result.nodes_explored
        else:
            fallback.message = "未找到有效路径"
        return fallback

    def _jps_search(self, start: Position, end: Position) -> PathResult:
        result = PathResult()
        result.algorithm_name = self.name
        start_time = time.time()

        if start == end:
            result.path = [start]
            result.success = True
            result.execution_time = time.time() - start_time
            result.calculate_path_length()
            result.message = "起点与终点相同"
            return result

        open_set: List[Node] = []
        closed_set: Set[Position] = set()
        nodes: Dict[Position, Node] = {}

        start_node = Node(position=start)
        start_node.update_costs(0.0, self.heuristic(start, end))
        nodes[start] = start_node
        heapq.heappush(open_set, start_node)
        result.visited_nodes.append(start)

        while open_set:
            current = heapq.heappop(open_set)
            if current.position in closed_set:
                continue
            closed_set.add(current.position)
            if current.position == end:
                result.path = self.reconstruct_path(current)
                result.success = True
                break

            for jp in self._successors(current, end):
                if jp in closed_set:
                    continue
                tentative_g = current.g_cost + self._jump_cost(current.position, jp)
                if jp not in nodes or tentative_g < nodes[jp].g_cost:
                    node = Node(position=jp)
                    node.parent = current
                    node.update_costs(tentative_g, self.heuristic(jp, end))
                    nodes[jp] = node
                    heapq.heappush(open_set, node)
                    if jp not in result.visited_nodes:
                        result.visited_nodes.append(jp)

        result.nodes_explored = len(closed_set)
        result.execution_time = time.time() - start_time
        if result.success:
            result.calculate_path_length()
            result.message = f"找到路径，长度: {result.path_length:.2f}"
        else:
            result.message = "未找到有效路径"
        return result

    @staticmethod
    def _jump_cost(a: Position, b: Position) -> float:
        """两跳点之间的八向距离（octile）。"""
        dx = abs(a.x - b.x)
        dy = abs(a.y - b.y)
        return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)


class ThetaStarAlgorithm(PathfindingAlgorithm):
    def __init__(self, grid_map: GridMap, allow_diagonal: bool = True):
        super().__init__(grid_map, allow_diagonal)
        self.name = "Theta*"
    
    def find_path(self, start: Position, end: Position) -> PathResult:
        if not self.allow_diagonal:
            # 四向模式没有「任意角度」可言，直接退化为 A*（同样是八向代价模型）
            fallback = AStarAlgorithm(self.grid_map, allow_diagonal=False).find_path(start, end)
            fallback.algorithm_name = self.name
            if fallback.success:
                fallback.message = "四向模式下 Theta* 退化为 A*（无斜线可拉直）"
            return fallback

        result = PathResult()
        result.algorithm_name = self.name
        start_time = time.time()
        open_set = []
        closed_set: Set[Position] = set()
        nodes: Dict[Position, Node] = {}
        start_node = Node(position=start, g_cost=0, h_cost=self.heuristic(start, end))
        start_node.f_cost = start_node.g_cost + start_node.h_cost
        nodes[start] = start_node
        heapq.heappush(open_set, start_node)
        result.visited_nodes.append(start)
        while open_set:
            current = heapq.heappop(open_set)
            if current.position in closed_set:
                continue
            closed_set.add(current.position)
            if current.position == end:
                result.path = self.reconstruct_path(current)
                result.success = True
                break
            neighbors = self.grid_map.get_neighbors(current.position, self.allow_diagonal)
            for neighbor_pos in neighbors:
                if neighbor_pos in closed_set:
                    continue
                if current.parent and self._line_of_sight(current.parent.position, neighbor_pos):
                    tentative_g = current.parent.g_cost + current.parent.position.distance_to(neighbor_pos)
                    if neighbor_pos not in nodes or tentative_g < nodes[neighbor_pos].g_cost:
                        neighbor_node = nodes.get(neighbor_pos, Node(position=neighbor_pos))
                        neighbor_node.parent = current.parent
                        h_cost = self.heuristic(neighbor_pos, end)
                        neighbor_node.update_costs(tentative_g, h_cost)
                        nodes[neighbor_pos] = neighbor_node
                        heapq.heappush(open_set, neighbor_node)
                else:
                    tentative_g = current.g_cost + self.grid_map.get_movement_cost(
                        current.position, neighbor_pos
                    )
                    if neighbor_pos not in nodes or tentative_g < nodes[neighbor_pos].g_cost:
                        neighbor_node = nodes.get(neighbor_pos, Node(position=neighbor_pos))
                        neighbor_node.parent = current
                        h_cost = self.heuristic(neighbor_pos, end)
                        neighbor_node.update_costs(tentative_g, h_cost)
                        nodes[neighbor_pos] = neighbor_node
                        heapq.heappush(open_set, neighbor_node)
                if neighbor_pos not in result.visited_nodes:
                    result.visited_nodes.append(neighbor_pos)
        result.nodes_explored = len(closed_set)
        result.execution_time = time.time() - start_time
        if result.success:
            result.calculate_path_length()
            result.message = f"找到路径，长度: {result.path_length:.2f}"
        else:
            result.message = "未找到有效路径"
        return result
    
    def _line_of_sight(self, from_pos: Position, to_pos: Position) -> bool:
        """两点间是否可视（委托给 GridMap，保持全局判定一致）。"""
        return self.grid_map.has_line_of_sight(from_pos, to_pos)


class AlgorithmFactory:
    ALGORITHMS = {
        'A*': AStarAlgorithm,
        'Dijkstra': DijkstraAlgorithm,
        'BFS': BFSAlgorithm,
        'DFS': DFSAlgorithm,
        'Greedy Best-First': GreedyBestFirstAlgorithm,
        '双向BFS': BidirectionalBFSAlgorithm,
        'Jump Point Search': JumpPointSearchAlgorithm,
        'Theta*': ThetaStarAlgorithm
    }
    
    @classmethod
    def get_algorithm_names(cls) -> List[str]:
        return list(cls.ALGORITHMS.keys())
    
    @classmethod
    def create_algorithm(cls, name: str, grid_map: GridMap, allow_diagonal: bool = True) -> PathfindingAlgorithm:
        if name not in cls.ALGORITHMS:
            raise ValueError(f"未知算法: {name}")
        return cls.ALGORITHMS[name](grid_map, allow_diagonal)
