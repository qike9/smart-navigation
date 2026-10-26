# core/real_time_navigation.py
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
from .path_planning import PathPlanner, Route


@dataclass
class NavigationStep:
    """导航步骤"""
    instruction: str
    distance_to_next: float
    estimated_time: float
    current_location: str
    next_location: str
    traffic_info: Dict[str, Any]


class RealTimeNavigator:
    """实时导航器"""

    def __init__(self, path_planner: PathPlanner = None):
        """初始化导航器

        Args:
            path_planner: 路径规划器
        """
        self.path_planner = path_planner or PathPlanner()
        self.current_route: Optional[Route] = None
        self.current_step = 0
        self.is_navigating = False
        self.navigation_thread = None
        self.voice_enabled = True
        self.update_interval = 5  # 秒
        self.callbacks = {
            'on_step_change': [],
            'on_reroute': [],
            'on_arrival': [],
            'on_voice_instruction': []
        }

    def start_navigation(self, start: str, end: str,
                         route: Route = None) -> Dict[str, Any]:
        """开始导航

        Args:
            start: 起点
            end: 终点
            route: 指定路线（可选）

        Returns:
            Dict: 导航开始结果
        """
        try:
            if self.is_navigating:
                return {"success": False, "message": "导航已在进行中"}

            # 如果没有指定路线，则规划一条
            if not route:
                result = self.path_planner.plan_route(start, end)
                if not result["success"]:
                    return result
                route = result["routes"][0]  # 使用第一条路线

            self.current_route = route
            self.current_step = 0
            self.is_navigating = True

            # 启动导航线程
            self.navigation_thread = threading.Thread(
                target=self._navigation_loop,
                daemon=True
            )
            self.navigation_thread.start()

            # 发出开始导航的语音指令
            if self.voice_enabled:
                self._speak(f"开始导航，从{start}到{end}，全程{route.distance}公里，预计需要{route.duration}分钟")

            return {
                "success": True,
                "message": "导航已开始",
                "route": route,
                "total_steps": len(route.nodes) - 1
            }

        except Exception as e:
            return {"success": False, "message": f"开始导航失败: {str(e)}"}

    def stop_navigation(self) -> Dict[str, Any]:
        """停止导航"""
        self.is_navigating = False
        if self.navigation_thread:
            self.navigation_thread.join(timeout=1)

        if self.voice_enabled:
            self._speak("导航已结束")

        return {"success": True, "message": "导航已停止"}

    def _navigation_loop(self):
        """导航主循环"""
        if not self.current_route:
            return

        total_steps = len(self.current_route.nodes) - 1

        while self.is_navigating and self.current_step < total_steps:
            # 获取当前步骤
            current_node = self.current_route.nodes[self.current_step]
            next_node = self.current_route.nodes[self.current_step + 1]

            # 获取实时交通信息
            traffic_info = self._get_real_time_traffic(current_node, next_node)

            # 创建导航步骤
            step = NavigationStep(
                instruction=self._generate_instruction(current_node, next_node, self.current_step),
                distance_to_next=self._get_distance(current_node, next_node),
                estimated_time=self._get_estimated_time(current_node, next_node, traffic_info),
                current_location=current_node,
                next_location=next_node,
                traffic_info=traffic_info
            )

            # 触发回调
            self._trigger_callbacks('on_step_change', step)

            if self.voice_enabled:
                self._speak(step.instruction)
                self._trigger_callbacks('on_voice_instruction', step.instruction)

            # 模拟移动到下一个节点
            time.sleep(self.update_interval)

            # 检查是否需要重新规划路线
            if self._should_reroute():
                self._perform_reroute()
                break

            # 移动到下一步
            self.current_step += 1

            # 检查是否到达终点
            if self.current_step >= total_steps:
                self._on_arrival()
                break

    def _generate_instruction(self, current: str, next_node: str, step_index: int) -> str:
        """生成导航指令

        Args:
            current: 当前位置
            next_node: 下一个节点
            step_index: 步骤索引

        Returns:
            str: 导航指令
        """
        instructions = [
            f"从{current}出发，前往{next_node}",
            f"继续前行，下一站{next_node}",
            f"保持方向，前往{next_node}",
            f"前方即将到达{next_node}"
        ]

        if step_index == 0:
            return f"从{current}出发，开始导航"
        elif step_index < len(self.current_route.nodes) - 2:
            return instructions[step_index % len(instructions)]
        else:
            return f"即将到达目的地{next_node}，导航即将结束"

    def _get_distance(self, from_node: str, to_node: str) -> float:
        """获取两个节点之间的距离

        Args:
            from_node: 起始节点
            to_node: 目标节点

        Returns:
            float: 距离
        """
        graph = self.path_planner.dijkstra.graph
        if from_node in graph and to_node in graph[from_node]:
            return graph[from_node][to_node]
        return 0.0

    def _get_estimated_time(self, from_node: str, to_node: str,
                            traffic_info: Dict[str, Any]) -> float:
        """获取预计时间

        Args:
            from_node: 起始节点
            to_node: 目标节点
            traffic_info: 交通信息

        Returns:
            float: 预计时间（分钟）
        """
        base_distance = self._get_distance(from_node, to_node)

        # 考虑交通状况
        traffic_multiplier = traffic_info.get('traffic_multiplier', 1.0)

        # 假设平均速度60km/h
        base_time = (base_distance / 60) * 60  # 转换为分钟

        return base_time * traffic_multiplier

    def _get_real_time_traffic(self, from_node: str, to_node: str) -> Dict[str, Any]:
        """获取实时交通信息

        Args:
            from_node: 起始节点
            to_node: 目标节点

        Returns:
            Dict: 交通信息
        """
        # 模拟实时交通数据
        traffic_levels = ["通畅", "缓行", "拥堵", "严重拥堵"]
        level = random.choice(traffic_levels)

        # 获取交通权重
        traffic_data = self.path_planner.dijkstra.traffic_data
        multiplier = 1.0
        if from_node in traffic_data and to_node in traffic_data[from_node]:
            multiplier = traffic_data[from_node][to_node]

        return {
            'traffic_level': level,
            'traffic_multiplier': multiplier,
            'update_time': datetime.now().isoformat(),
            'suggestion': self._get_traffic_suggestion(level)
        }

    def _get_traffic_suggestion(self, traffic_level: str) -> str:
        """获取交通建议

        Args:
            traffic_level: 交通状况

        Returns:
            str: 建议
        """
        suggestions = {
            "通畅": "道路畅通，请保持当前速度",
            "缓行": "前方缓行，请保持车距",
            "拥堵": "前方拥堵，预计通过时间较长",
            "严重拥堵": "严重拥堵，建议考虑绕行"
        }
        return suggestions.get(traffic_level, "请谨慎驾驶")

    def _should_reroute(self) -> bool:
        """判断是否需要重新规划路线

        Returns:
            bool: 是否需要重新规划
        """
        if not self.current_route or self.current_step >= len(self.current_route.nodes) - 2:
            return False

        # 模拟检测到交通状况变化
        current_node = self.current_route.nodes[self.current_step]
        next_node = self.current_route.nodes[self.current_step + 1]

        traffic_info = self._get_real_time_traffic(current_node, next_node)

        # 如果交通状况为严重拥堵，则考虑重新规划
        return traffic_info['traffic_level'] == "严重拥堵"

    def _perform_reroute(self):
        """执行重新规划路线"""
        if not self.current_route:
            return

        current_node = self.current_route.nodes[self.current_step]
        destination = self.current_route.nodes[-1]

        # 避开当前拥堵路段
        avoid_node = self.current_route.nodes[self.current_step + 1]

        # 寻找替代路线
        result = self.path_planner.find_alternative(current_node, destination, [avoid_node])

        if result["success"] and result["routes"]:
            new_route = result["routes"][0]

            # 触发重新规划回调
            self._trigger_callbacks('on_reroute', {
                'old_route': self.current_route,
                'new_route': new_route,
                'reason': '检测到严重拥堵'
            })

            if self.voice_enabled:
                self._speak(f"检测到前方严重拥堵，已为您重新规划路线")

            # 更新当前路线
            self.current_route = new_route
            self.current_step = 0

        else:
            if self.voice_enabled:
                self._speak("无法找到替代路线，请继续按照原路线行驶")

    def _on_arrival(self):
        """到达目的地处理"""
        self.is_navigating = False

        if self.voice_enabled:
            self._speak("已到达目的地，导航结束")

        # 触发到达回调
        self._trigger_callbacks('on_arrival', {
            'destination': self.current_route.nodes[-1] if self.current_route else '',
            'arrival_time': datetime.now(),
            'total_distance': self.current_route.distance if self.current_route else 0,
            'total_duration': self.current_route.duration if self.current_route else 0
        })

    def _speak(self, text: str):
        """语音播报（模拟）

        Args:
            text: 播报文本
        """
        print(f"[语音播报] {text}")

    def register_callback(self, event: str, callback: Callable):
        """注册事件回调

        Args:
            event: 事件名称
            callback: 回调函数
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def _trigger_callbacks(self, event: str, data: Any):
        """触发回调函数

        Args:
            event: 事件名称
            data: 回调数据
        """
        for callback in self.callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                print(f"回调函数执行失败: {e}")

    def get_navigation_status(self) -> Dict[str, Any]:
        """获取导航状态

        Returns:
            Dict: 导航状态
        """
        if not self.current_route or not self.is_navigating:
            return {
                "is_navigating": False,
                "message": "未在导航"
            }

        total_steps = len(self.current_route.nodes) - 1
        progress = (self.current_step / total_steps) * 100 if total_steps > 0 else 0

        return {
            "is_navigating": True,
            "current_step": self.current_step,
            "total_steps": total_steps,
            "progress": round(progress, 1),
            "current_location": self.current_route.nodes[self.current_step] if self.current_step < len(
                self.current_route.nodes) else "",
            "next_location": self.current_route.nodes[self.current_step + 1] if self.current_step + 1 < len(
                self.current_route.nodes) else "",
            "remaining_distance": self._calculate_remaining_distance(),
            "estimated_arrival": self._calculate_eta()
        }

    def _calculate_remaining_distance(self) -> float:
        """计算剩余距离

        Returns:
            float: 剩余距离
        """
        if not self.current_route or self.current_step >= len(self.current_route.nodes) - 1:
            return 0.0

        remaining_nodes = self.current_route.nodes[self.current_step:]
        total_distance = 0.0

        for i in range(len(remaining_nodes) - 1):
            from_node = remaining_nodes[i]
            to_node = remaining_nodes[i + 1]
            total_distance += self._get_distance(from_node, to_node)

        return round(total_distance, 2)

    def _calculate_eta(self) -> datetime:
        """计算预计到达时间

        Returns:
            datetime: 预计到达时间
        """
        if not self.current_route or not self.is_navigating:
            return datetime.now()

        remaining_time = 0.0

        for i in range(self.current_step, len(self.current_route.nodes) - 1):
            from_node = self.current_route.nodes[i]
            to_node = self.current_route.nodes[i + 1]

            # 模拟获取交通信息
            traffic_info = self._get_real_time_traffic(from_node, to_node)
            segment_time = self._get_estimated_time(from_node, to_node, traffic_info)

            remaining_time += segment_time

        return datetime.now() + timedelta(minutes=remaining_time)

    def toggle_voice(self, enabled: bool = None) -> bool:
        """切换语音播报

        Args:
            enabled: 是否启用（None表示切换）

        Returns:
            bool: 切换后的状态
        """
        if enabled is None:
            self.voice_enabled = not self.voice_enabled
        else:
            self.voice_enabled = enabled

        return self.voice_enabled


# 测试实时导航功能
if __name__ == "__main__":
    # 创建路径规划器
    planner = PathPlanner()

    # 创建导航器
    navigator = RealTimeNavigator(planner)


    # 定义回调函数
    def on_step_change(step):
        print(f"[导航步骤] {step.instruction}")
        print(f"          距离下一站: {step.distance_to_next}km, 预计时间: {step.estimated_time:.1f}min")
        print(f"          交通状况: {step.traffic_info['traffic_level']} - {step.traffic_info['suggestion']}")


    def on_reroute(data):
        print(f"[重新规划] {data['reason']}")
        print(f"          新路线: {' -> '.join(data['new_route'].nodes)}")


    def on_arrival(data):
        print(f"[到达目的地] {data['destination']}")
        print(f"           总距离: {data['total_distance']}km")
        print(f"           总时间: {data['total_duration']}min")
        print(f"           到达时间: {data['arrival_time'].strftime('%H:%M:%S')}")


    # 注册回调
    navigator.register_callback('on_step_change', on_step_change)
    navigator.register_callback('on_reroute', on_reroute)
    navigator.register_callback('on_arrival', on_arrival)

    # 开始导航
    print("开始导航测试...")
    result = navigator.start_navigation("A", "F")

    if result["success"]:
        print(f"导航开始: {result['route']}")
        print(f"总步骤数: {result['total_steps']}")

        # 模拟导航过程
        for i in range(10):  # 最多监控10个更新周期
            if not navigator.is_navigating:
                break

            status = navigator.get_navigation_status()
            print(f"\n导航状态: {status['progress']}% 完成")
            print(f"当前位置: {status['current_location']}")
            print(f"下一位置: {status['next_location']}")
            print(f"剩余距离: {status['remaining_distance']}km")
            print(f"预计到达: {status['estimated_arrival'].strftime('%H:%M:%S')}")

            time.sleep(3)  # 等待3秒

        # 停止导航
        navigator.stop_navigation()
        print("\n导航测试结束")
    else:
        print(f"导航开始失败: {result['message']}")