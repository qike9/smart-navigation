# -*- coding: utf-8 -*-
"""右侧功能面板：导航模拟面板与性能分析面板。"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional

from ..analysis import PerformanceAnalyzer
from ..models import DIRECTION_ARROWS, DIRECTION_NAMES, GridMap, PathResult, Position
from ..navigation import NavigationSimulator


class NavigationPanel(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.simulator: Optional[NavigationSimulator] = None
        self.animation_id = None
        self.is_navigating = False
        self.setup_ui()

    def setup_ui(self):
        self.direction_label = ttk.Label(self, text="等待导航", font=('Arial', 24))
        self.direction_label.pack(pady=20)
        self.arrow_label = ttk.Label(self, text="", font=('Arial', 48))
        self.arrow_label.pack(pady=10)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100, length=200)
        self.progress_bar.pack(pady=10, padx=20)
        self.info_frame = ttk.LabelFrame(self, text="导航信息")
        self.info_frame.pack(fill='x', padx=10, pady=10)
        self.distance_label = ttk.Label(self.info_frame, text="剩余距离: --")
        self.distance_label.pack(anchor='w', padx=5, pady=2)
        self.position_label = ttk.Label(self.info_frame, text="当前位置: --")
        self.position_label.pack(anchor='w', padx=5, pady=2)
        self.step_label = ttk.Label(self.info_frame, text="步数: --")
        self.step_label.pack(anchor='w', padx=5, pady=2)
        self.control_frame = ttk.Frame(self)
        self.control_frame.pack(fill='x', padx=10, pady=10)
        self.start_btn = ttk.Button(self.control_frame, text="开始导航", command=self.start_navigation)
        self.start_btn.pack(side='left', padx=5)
        self.pause_btn = ttk.Button(self.control_frame, text="暂停", command=self.pause_navigation, state='disabled')
        self.pause_btn.pack(side='left', padx=5)
        self.reset_btn = ttk.Button(self.control_frame, text="重置", command=self.reset_navigation)
        self.reset_btn.pack(side='left', padx=5)
        self.speed_frame = ttk.Frame(self)
        self.speed_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(self.speed_frame, text="速度:").pack(side='left')
        self.speed_scale = ttk.Scale(self.speed_frame, from_=1, to=10, orient='horizontal',
                                     command=self.on_speed_change)
        self.speed_scale.set(5)
        self.speed_scale.pack(side='left', fill='x', expand=True, padx=5)
        self.speed_label = ttk.Label(self.speed_frame, text="5x")
        self.speed_label.pack(side='left')
        self.speed = 5

    def set_path(self, path: List[Position], grid_map: GridMap):
        if path:
            self.simulator = NavigationSimulator(path, grid_map)
            self.update_display()
        else:
            self.simulator = None
            self.direction_label.config(text="无有效路径")
            self.arrow_label.config(text="")

    def start_navigation(self):
        if not self.simulator:
            return
        self.is_navigating = True
        self.simulator.is_running = True
        self.simulator.is_paused = False
        self.start_btn.config(state='disabled')
        self.pause_btn.config(state='normal')
        self._navigate_step()

    def pause_navigation(self):
        if self.simulator:
            self.simulator.is_paused = not self.simulator.is_paused
            if self.simulator.is_paused:
                self.pause_btn.config(text="继续")
            else:
                self.pause_btn.config(text="暂停")
                self._navigate_step()

    def reset_navigation(self):
        self.is_navigating = False
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None
        if self.simulator:
            self.simulator.reset()
        self.start_btn.config(state='normal')
        self.pause_btn.config(state='disabled', text="暂停")
        self.update_display()

    def _navigate_step(self):
        if not self.simulator or not self.is_navigating:
            return
        if self.simulator.is_paused:
            return
        if self.simulator.is_finished():
            self.direction_label.config(text="到达目的地!")
            self.arrow_label.config(text="★")
            self.start_btn.config(state='normal')
            self.pause_btn.config(state='disabled')
            self.is_navigating = False
            return
        self.simulator.advance()
        self.update_display()
        delay = int(500 / self.speed)
        self.animation_id = self.after(delay, self._navigate_step)

    def update_display(self):
        if not self.simulator:
            return
        direction = self.simulator.get_direction()
        if direction:
            self.direction_label.config(text=DIRECTION_NAMES.get(direction, ""))
            self.arrow_label.config(text=DIRECTION_ARROWS.get(direction, ""))
        else:
            self.direction_label.config(text="导航完成")
            self.arrow_label.config(text="★")
        self.progress_var.set(self.simulator.get_progress())
        remaining = self.simulator.get_remaining_distance()
        self.distance_label.config(text=f"剩余距离: {remaining:.2f}")
        current = self.simulator.get_current_position()
        if current:
            self.position_label.config(text=f"当前位置: ({current.x}, {current.y})")
        self.step_label.config(text=f"步数: {self.simulator.current_index + 1}/{len(self.simulator.path)}")

    def on_speed_change(self, value):
        self.speed = int(float(value))
        if hasattr(self, 'speed_label'):
            self.speed_label.config(text=f"{self.speed}x")


class PerformancePanel(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.analyzer = PerformanceAnalyzer()
        self.setup_ui()
    
    def setup_ui(self):
        self.tree = ttk.Treeview(self, columns=('algorithm', 'time', 'nodes', 'length', 'success'), show='headings', height=8)
        self.tree.heading('algorithm', text='算法')
        self.tree.heading('time', text='耗时(ms)')
        self.tree.heading('nodes', text='搜索节点')
        self.tree.heading('length', text='路径长度')
        self.tree.heading('success', text='状态')
        self.tree.column('algorithm', width=120)
        self.tree.column('time', width=80)
        self.tree.column('nodes', width=80)
        self.tree.column('length', width=80)
        self.tree.column('success', width=60)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(fill='x', pady=5)
        self.clear_btn = ttk.Button(self.btn_frame, text="清除结果", command=self.clear_results)
        self.clear_btn.pack(side='left', padx=5)
        self.export_btn = ttk.Button(self.btn_frame, text="导出报告", command=self.export_report)
        self.export_btn.pack(side='left', padx=5)
    
    def add_result(self, result: PathResult):
        self.tree.insert('', 'end', values=(
            result.algorithm_name,
            f"{result.execution_time * 1000:.2f}",
            result.nodes_explored,
            f"{result.path_length:.2f}" if result.success else "--",
            "成功" if result.success else "失败"
        ))
        self.analyzer.add_result(result.algorithm_name, result)
    
    def add_results(self, results: Dict[str, PathResult]):
        for name, result in results.items():
            self.add_result(result)
    
    def clear_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.analyzer.clear_results()
    
    def export_report(self):
        pass
