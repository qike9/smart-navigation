# -*- coding: utf-8 -*-
"""设置对话框与多途经点对话框。"""

from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, messagebox, ttk

from ..algorithms import AlgorithmFactory
from ..models import GridMap
from ..planning import MultiWaypointPlanner


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings: dict):
        super().__init__(parent)
        self.title("设置")
        self.settings = settings
        self.result = None
        self.geometry("400x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.setup_ui()
    
    def setup_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        map_frame = ttk.Frame(notebook)
        notebook.add(map_frame, text="地图设置")
        ttk.Label(map_frame, text="地图宽度:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.width_var = tk.IntVar(value=self.settings.get('map_width', 50))
        ttk.Spinbox(map_frame, from_=10, to=200, textvariable=self.width_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(map_frame, text="地图高度:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.height_var = tk.IntVar(value=self.settings.get('map_height', 50))
        ttk.Spinbox(map_frame, from_=10, to=200, textvariable=self.height_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(map_frame, text="格子大小:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.cell_size_var = tk.IntVar(value=self.settings.get('cell_size', 15))
        ttk.Spinbox(map_frame, from_=5, to=50, textvariable=self.cell_size_var, width=10).grid(row=2, column=1, padx=5, pady=5)
        self.show_grid_var = tk.BooleanVar(value=self.settings.get('show_grid', True))
        ttk.Checkbutton(map_frame, text="显示网格线", variable=self.show_grid_var).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky='w')
        self.show_coords_var = tk.BooleanVar(value=self.settings.get('show_coordinates', False))
        ttk.Checkbutton(map_frame, text="显示坐标", variable=self.show_coords_var).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky='w')
        algo_frame = ttk.Frame(notebook)
        notebook.add(algo_frame, text="算法设置")
        ttk.Label(algo_frame, text="默认算法:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.algo_var = tk.StringVar(value=self.settings.get('default_algorithm', 'A*'))
        algo_combo = ttk.Combobox(algo_frame, textvariable=self.algo_var, values=AlgorithmFactory.get_algorithm_names(), width=15)
        algo_combo.grid(row=0, column=1, padx=5, pady=5)
        self.diagonal_var = tk.BooleanVar(value=self.settings.get('allow_diagonal', True))
        ttk.Checkbutton(algo_frame, text="允许对角移动", variable=self.diagonal_var).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky='w')
        ttk.Label(algo_frame, text="动画速度(ms):").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.anim_speed_var = tk.IntVar(value=self.settings.get('animation_speed', 50))
        ttk.Spinbox(algo_frame, from_=1, to=500, textvariable=self.anim_speed_var, width=10).grid(row=2, column=1, padx=5, pady=5)
        color_frame = ttk.Frame(notebook)
        notebook.add(color_frame, text="颜色设置")
        self.color_vars = {}
        colors = [
            ('EMPTY', '空白', '#FFFFFF'),
            ('OBSTACLE', '障碍物', '#333333'),
            ('START', '起点', '#00FF00'),
            ('END', '终点', '#FF0000'),
            ('WAYPOINT', '途经点', '#FFA500'),
            ('PATH', '路径', '#0066FF'),
            ('VISITED', '已访问', '#CCCCCC')
        ]
        for i, (key, label, default) in enumerate(colors):
            ttk.Label(color_frame, text=f"{label}:").grid(row=i, column=0, padx=5, pady=3, sticky='w')
            color_value = self.settings.get('colors', {}).get(key, default)
            var = tk.StringVar(value=color_value)
            self.color_vars[key] = var
            entry = ttk.Entry(color_frame, textvariable=var, width=10)
            entry.grid(row=i, column=1, padx=5, pady=3)
            btn = ttk.Button(color_frame, text="选择", command=lambda k=key: self.choose_color(k))
            btn.grid(row=i, column=2, padx=5, pady=3)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(btn_frame, text="确定", command=self.on_ok).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="取消", command=self.on_cancel).pack(side='right', padx=5)
    
    def choose_color(self, key):
        color = colorchooser.askcolor(title="选择颜色", color=self.color_vars[key].get())
        if color[1]:
            self.color_vars[key].set(color[1])
    
    def on_ok(self):
        self.result = {
            'map_width': self.width_var.get(),
            'map_height': self.height_var.get(),
            'cell_size': self.cell_size_var.get(),
            'show_grid': self.show_grid_var.get(),
            'show_coordinates': self.show_coords_var.get(),
            'default_algorithm': self.algo_var.get(),
            'allow_diagonal': self.diagonal_var.get(),
            'animation_speed': self.anim_speed_var.get(),
            'colors': {k: v.get() for k, v in self.color_vars.items()}
        }
        self.destroy()
    
    def on_cancel(self):
        self.destroy()


class MultiWaypointDialog(tk.Toplevel):
    def __init__(self, parent, grid_map: GridMap):
        super().__init__(parent)
        self.title("多途经点路径规划")
        self.grid_map = grid_map
        self.result = None
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.setup_ui()
    
    def setup_ui(self):
        ttk.Label(self, text="途经点列表:").pack(anchor='w', padx=10, pady=5)
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.waypoint_list = tk.Listbox(list_frame, height=10)
        self.waypoint_list.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.waypoint_list.yview)
        self.waypoint_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        for i, wp in enumerate(self.grid_map.waypoints):
            self.waypoint_list.insert('end', f"途经点 {i+1}: ({wp.x}, {wp.y})")
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=10)
        ttk.Label(btn_frame, text="算法:").pack(side='left', padx=5)
        self.algo_var = tk.StringVar(value='A*')
        ttk.Combobox(btn_frame, textvariable=self.algo_var, 
                    values=AlgorithmFactory.get_algorithm_names(), width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="规划路径", command=self.plan_path).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side='right', padx=5)
    
    def plan_path(self):
        if not self.grid_map.start_position or not self.grid_map.end_position:
            messagebox.showwarning("警告", "请先设置起点和终点！")
            return
        if not self.grid_map.waypoints:
            messagebox.showwarning("警告", "请添加至少一个途经点！")
            return
        planner = MultiWaypointPlanner(self.grid_map, self.algo_var.get())
        result = planner.plan(
            self.grid_map.start_position,
            self.grid_map.waypoints,
            self.grid_map.end_position
        )
        self.result = result
        self.destroy()
