# core/path_planning.py
import heapq
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import random
import config


@dataclass
class Route:
    """路线数据类"""
    nodes: List[str]
    distance: float
    duration: float
    traffic_level: str
    timestamp: datetime

    def __str__(self) -> str:
        return f"路线: {' -> '.join(self.nodes)} | 距离: {self.distance}km | 时间: {self.duration}min | 交通: {self.traffic_level}"


class ImprovedDijkstra:
    """改进的Dijkstra算法"""

    def __init__(self, graph: Dict[str, Dict[str, float]] = None):
        """初始化算法

        Args:
            graph: 图数据结构 {节点: {邻居: 距离}}
        """
        self.graph = graph or config.Config.get_map_data()
        self.traffic_data = self._generate_traffic_data()

    def _generate_traffic_data(self) -> Dict[str, Dict[str, float]]:
        """生成模拟交通数据"""
        traffic = {}
        for node in self.graph:
            traffic[node] = {}
            for neighbor in self.graph[node]:
                # 随机生成交通状况权重
                traffic_levels = list(config.Config.TRAFFIC_LEVELS.keys())
                traffic_level = random.choice(traffic_levels)
                traffic_weight = config.Config.get_traffic_multiplier(traffic_level)
                traffic[node][neighbor] = traffic_weight

        return traffic

    def update_traffic(self):
        """更新交通数据"""
        self.traffic_data = self._generate_traffic_data()

    def shortest_path(self, start: str, end: str,
                      consider_traffic: bool = True,
                      max_paths: int = 3) -> List[Route]:
        """寻找最短路径（支持多条路径）

        Args:
            start: 起点
            end: 终点
            consider_traffic: 是否考虑交通
            max_paths: 最大返回路径数

        Returns:
            List[Route]: 路径列表
        """
        if start not in self.graph or end not in self.graph:
            return []

        # 使用改进的Dijkstra算法找多条路径
        paths = self._k_shortest_paths(start, end, max_paths, consider_traffic)

        # 转换为Route对象
        routes = []
        for path, distance, duration in paths:
            # 确定交通状况
            traffic_level = self._get_path_traffic_level(path)

            route = Route(
                nodes=path,
                distance=round(distance, 2),
                duration=round(duration, 2),
                traffic_level=traffic_level,
                timestamp=datetime.now()
            )
            routes.append(route)

        return routes

    def _k_shortest_paths(self, start: str, end: str, k: int,
                          consider_traffic: bool) -> List[Tuple[List[str], float, float]]:
        """找k条最短路径

        Args:
            start: 起点
            end: 终点
            k: 路径数量
            consider_traffic: 是否考虑交通

        Returns:
            List[Tuple]: [(路径, 距离, 时间), ...]
        """
        # 优先队列: (总成本, 距离, 时间, 路径)
        heap = []
        heapq.heappush(heap, (0, 0, 0, [start]))

        results = []
        visited = {}

        while heap and len(results) < k:
            total_cost, distance, duration, path = heapq.heappop(heap)
            current = path[-1]

            # 到达终点
            if current == end:
                results.append((path, distance, duration))
                continue

            # 访问控制
            if current in visited and visited[current] <= len(path):
                continue
            visited[current] = len(path)

            # 探索邻居
            for neighbor, base_distance in self.graph.get(current, {}).items():
                if neighbor in path:  # 避免循环
                    continue

                # 计算实际距离和时间
                traffic_multiplier = 1.0
                if consider_traffic and current in self.traffic_data:
                    traffic_multiplier = self.traffic_data[current].get(neighbor, 1.0)

                new_distance = distance + base_distance
                new_duration = duration + (base_distance * traffic_multiplier)

                # 总成本 = 距离 * 0.6 + 时间 * 0.4 (可调整)
                total_cost = new_distance * 0.6 + new_duration * 0.4

                new_path = path + [neighbor]
                heapq.heappush(heap, (total_cost, new_distance, new_duration, new_path))

        return results

    def _get_path_traffic_level(self, path: List[str]) -> str:
        """获取路径的总体交通状况

        Args:
            path: 路径节点列表

        Returns:
            str: 交通状况
        """
        if len(path) < 2:
            return "通畅"

        # 计算路径的平均交通权重
        total_weight = 0
        segment_count = 0

        for i in range(len(path) - 1):
            start = path[i]
            end = path[i + 1]

            if start in self.traffic_data and end in self.traffic_data[start]:
                weight = self.traffic_data[start][end]
                total_weight += weight
                segment_count += 1

        if segment_count == 0:
            return "通畅"

        avg_weight = total_weight / segment_count

        # 根据平均权重确定交通状况
        if avg_weight <= 1.2:
            return "通畅"
        elif avg_weight <= 1.6:
            return "缓行"
        elif avg_weight <= 2.0:
            return "拥堵"
        else:
            return "严重拥堵"

    def find_alternative_routes(self, start: str, end: str,
                                avoid_nodes: List[str] = None) -> List[Route]:
        """寻找替代路线（避开特定节点）

        Args:
            start: 起点
            end: 终点
            avoid_nodes: 要避开的节点列表

        Returns:
            List[Route]: 替代路线列表
        """
        # 临时修改图，移除要避开的节点
        original_graph = self.graph.copy()

        if avoid_nodes:
            temp_graph = {}
            for node, neighbors in original_graph.items():
                if node in avoid_nodes:
                    continue
                temp_graph[node] = {
                    n: d for n, d in neighbors.items()
                    if n not in avoid_nodes
                }
            self.graph = temp_graph

        # 寻找路径
        routes = self.shortest_path(start, end)

        # 恢复原图
        self.graph = original_graph

        return routes

    def compare_routes(self, routes: List[Route]) -> Dict[str, Any]:
        """比较多条路线

        Args:
            routes: 路线列表

        Returns:
            Dict: 比较结果
        """
        if not routes:
            return {"success": False, "message": "没有路线可比较"}

        # 找到最短距离和最快时间的路线
        shortest_by_distance = min(routes, key=lambda x: x.distance)
        fastest_by_time = min(routes, key=lambda x: x.duration)

        # 推荐路线（综合最优）
        recommended = min(routes, key=lambda x: x.distance * 0.5 + x.duration * 0.5)

        return {
            "success": True,
            "routes_count": len(routes),
            "shortest_distance": {
                "route": shortest_by_distance.nodes,
                "distance": shortest_by_distance.distance,
                "duration": shortest_by_distance.duration
            },
            "fastest_time": {
                "route": fastest_by_time.nodes,
                "distance": fastest_by_time.distance,
                "duration": fastest_by_time.duration
            },
            "recommended": {
                "route": recommended.nodes,
                "distance": recommended.distance,
                "duration": recommended.duration,
                "traffic": recommended.traffic_level
            },
            "all_routes": [
                {
                    "path": route.nodes,
                    "distance": route.distance,
                    "duration": route.duration,
                    "traffic": route.traffic_level
                }
                for route in routes
            ]
        }


class PathPlanner:
    """路径规划器"""

    def __init__(self, user_manager=None):
        """初始化路径规划器

        Args:
            user_manager: 用户管理器
        """
        self.dijkstra = ImprovedDijkstra()
        self.user_manager = user_manager

    def plan_route(self, start: str, end: str,
                   preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """规划路线

        Args:
            start: 起点
            end: 终点
            preferences: 用户偏好

        Returns:
            Dict: 规划结果
        """
        try:
            # 更新交通数据
            self.dijkstra.update_traffic()

            # 获取用户偏好
            if self.user_manager and self.user_manager.is_logged_in():
                user_prefs = self.user_manager.get_preferences()
                if user_prefs.get("success"):
                    preferences = user_prefs.get("preferences", {})

            # 确定是否考虑交通
            consider_traffic = preferences.get("consider_traffic", True) if preferences else True

            # 寻找多条路径
            routes = self.dijkstra.shortest_path(start, end, consider_traffic)

            if not routes:
                return {
                    "success": False,
                    "message": f"无法找到从 {start} 到 {end} 的路径"
                }

            # 比较路线
            comparison = self.dijkstra.compare_routes(routes)

            # 保存路线历史到数据库
            if self.user_manager and self.user_manager.is_logged_in():
                user_id = self.user_manager.get_user_id()
                if user_id and routes:
                    best_route = routes[0]
                    self.user_manager.db.save_route_history(
                        user_id, start, end,
                        {"path": best_route.nodes},
                        best_route.distance,
                        best_route.duration,
                        best_route.traffic_level
                    )

            return {
                "success": True,
                "message": f"找到 {len(routes)} 条路线",
                "start": start,
                "end": end,
                "routes": routes,
                "comparison": comparison
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"路径规划失败: {str(e)}"
            }

    def find_alternative(self, start: str, end: str,
                         avoid: List[str] = None) -> Dict[str, Any]:
        """寻找替代路线

        Args:
            start: 起点
            end: 终点
            avoid: 要避开的节点

        Returns:
            Dict: 替代路线结果
        """
        try:
            routes = self.dijkstra.find_alternative_routes(start, end, avoid)

            if not routes:
                return {
                    "success": False,
                    "message": f"无法找到避开 {avoid} 的替代路线"
                }

            return {
                "success": True,
                "message": f"找到 {len(routes)} 条替代路线",
                "avoid": avoid,
                "routes": routes
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"寻找替代路线失败: {str(e)}"
            }

    def get_traffic_info(self, location: str = None) -> Dict[str, Any]:
        """获取交通信息

        Args:
            location: 特定位置

        Returns:
            Dict: 交通信息
        """
        try:
            if location:
                # 获取特定位置的交通状况
                traffic = {}
                if location in self.dijkstra.traffic_data:
                    for neighbor, weight in self.dijkstra.traffic_data[location].items():
                        # 将权重转换为交通状况描述
                        if weight <= 1.2:
                            level = "通畅"
                        elif weight <= 1.6:
                            level = "缓行"
                        elif weight <= 2.0:
                            level = "拥堵"
                        else:
                            level = "严重拥堵"

                        traffic[neighbor] = {
                            "level": level,
                            "weight": weight
                        }

                return {
                    "success": True,
                    "location": location,
                    "traffic": traffic
                }
            else:
                # 获取整体交通概况
                all_traffic = {}
                for node in self.dijkstra.traffic_data:
                    for neighbor, weight in self.dijkstra.traffic_data[node].items():
                        edge = f"{node}-{neighbor}"
                        all_traffic[edge] = weight

                return {
                    "success": True,
                    "total_edges": len(all_traffic),
                    "traffic_overview": all_traffic
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"获取交通信息失败: {str(e)}"
            }


# 测试路径规划功能
if __name__ == "__main__":
    planner = PathPlanner()

    # 测试路径规划
    result = planner.plan_route("A", "F")
    print("路径规划结果:")
    if result["success"]:
        for i, route in enumerate(result["routes"]):
            print(f"  路线{i + 1}: {route}")

        comparison = result["comparison"]
        print(f"\n路线比较:")
        print(
            f"  最短距离: {comparison['shortest_distance']['route']} ({comparison['shortest_distance']['distance']}km)")
        print(f"  最快时间: {comparison['fastest_time']['route']} ({comparison['fastest_time']['duration']}min)")
        print(f"  推荐路线: {comparison['recommended']['route']}")

    # 测试替代路线
    print("\n替代路线测试:")
    result = planner.find_alternative("A", "F", ["C"])
    if result["success"]:
        for i, route in enumerate(result["routes"]):
            print(f"  替代路线{i + 1}: {route}")

    # 测试交通信息
    print("\n交通信息:")
    result = planner.get_traffic_info("A")
    if result["success"]:
        for neighbor, info in result["traffic"].items():
            print(f"  A -> {neighbor}: {info['level']} (权重: {info['weight']:.2f})")