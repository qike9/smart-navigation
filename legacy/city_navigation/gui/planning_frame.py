# gui/planning_frame.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import config


class PlanningFrame:
    """路径规划面板"""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.frame = None
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        self.frame = ttk.Frame(self.parent)

        # 标题
        title = ttk.Label(self.frame, text="路径规划",
                          font=('微软雅黑', 16, 'bold'))
        title.pack(pady=10)

        # 控制面板
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(padx=10, pady=10, fill=tk.X)

        # 起点输入
        ttk.Label(control_frame, text="起点:").grid(row=0, column=0, padx=5, pady=10)
        self.start_entry = ttk.Entry(control_frame, width=20)
        self.start_entry.grid(row=0, column=1, padx=5, pady=10)

        # 终点输入
        ttk.Label(control_frame, text="终点:").grid(row=0, column=2, padx=5, pady=10)
        self.end_entry = ttk.Entry(control_frame, width=20)
        self.end_entry.grid(row=0, column=3, padx=5, pady=10)

        # 可用位置提示
        map_data = config.Config.get_map_data()
        locations = ", ".join(map_data.keys())
        ttk.Label(control_frame, text=f"可用位置: {locations}").grid(
            row=1, column=0, columnspan=4, padx=5, pady=5
        )

        # 规划按钮
        self.plan_btn = ttk.Button(control_frame, text="规划路线",
                                   command=self.on_plan,
                                   style='Primary.TButton')
        self.plan_btn.grid(row=0, column=4, padx=10, pady=10)

        # 结果显示区域
        result_frame = ttk.LabelFrame(self.frame, text="路线结果", padding=10)
        result_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 创建文本显示区域
        self.result_text = scrolledtext.ScrolledText(result_frame,
                                                     height=15,
                                                     font=('Consolas', 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 地图可视化区域
        map_frame = ttk.LabelFrame(self.frame, text="路线图", padding=10)
        map_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 简单的文本地图显示
        self.map_text = tk.Text(map_frame, height=10, font=('Consolas', 9))
        self.map_text.pack(fill=tk.BOTH, expand=True)

        # 初始化地图显示
        self.show_map_data()

    def show_map_data(self):
        """显示地图数据"""
        map_data = config.Config.get_map_data()

        self.map_text.delete(1.0, tk.END)
        self.map_text.insert(tk.END, "地图连接关系:\n\n")

        for node, connections in map_data.items():
            self.map_text.insert(tk.END, f"{node} 连接至:\n")
            for neighbor, distance in connections.items():
                self.map_text.insert(tk.END, f"  → {neighbor} ({distance}km)\n")
            self.map_text.insert(tk.END, "\n")

    def on_plan(self):
        """处理路径规划"""
        start = self.start_entry.get().upper()
        end = self.end_entry.get().upper()

        self.controller.handle_plan_route(start, end)

    def display_results(self, result):
        """显示规划结果"""
        self.result_text.delete(1.0, tk.END)

        if not result["success"]:
            self.result_text.insert(tk.END, f"错误: {result['message']}")
            return

        # 显示结果
        self.result_text.insert(tk.END, f"从 {result['start']} 到 {result['end']}\n")
        self.result_text.insert(tk.END, f"找到 {len(result['routes'])} 条路线:\n\n")

        for i, route in enumerate(result["routes"], 1):
            self.result_text.insert(tk.END, f"路线 {i}:\n")
            self.result_text.insert(tk.END, f"  路径: {' → '.join(route.nodes)}\n")
            self.result_text.insert(tk.END, f"  距离: {route.distance} 公里\n")
            self.result_text.insert(tk.END, f"  时间: {route.duration} 分钟\n")
            self.result_text.insert(tk.END, f"  交通: {route.traffic_level}\n\n")

        # 显示推荐路线
        comparison = result["comparison"]
        if comparison["success"]:
            self.result_text.insert(tk.END, "⭐ 推荐路线:\n")
            self.result_text.insert(tk.END, f"  {' → '.join(comparison['recommended']['route'])}\n")
            self.result_text.insert(tk.END, f"  距离: {comparison['recommended']['distance']}km\n")
            self.result_text.insert(tk.END, f"  时间: {comparison['recommended']['duration']}min\n")
            self.result_text.insert(tk.END, f"  交通: {comparison['recommended']['traffic']}\n")

        # 在底部显示结果数量
        self.result_text.insert(tk.END, f"\n{'=' * 50}\n")
        self.result_text.insert(tk.END, f"共找到 {len(result['routes'])} 条可行路线")

    def set_planning_button_state(self, enabled=True):
        """设置规划按钮状态"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.plan_btn.config(state=state)