# -*- coding: utf-8 -*-
"""主窗口：菜单、工具栏、状态栏与业务编排。"""

from __future__ import annotations

import json
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional

from ..algorithms import AlgorithmFactory
from ..maps import ExportManager, MapManager
from ..models import (
    DIRECTION_NAMES,
    CellType,
    GridMap,
    PathResult,
    Position,
)
from ..utils import UndoRedoManager
from .canvas import MapEditor
from .dialogs import MultiWaypointDialog, SettingsDialog
from .panels import NavigationPanel, PerformancePanel


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("智能寻路导航系统 v1.0")
        self.geometry("1400x900")
        self.minsize(1200, 700)
        self.settings = {
            'map_width': 50,
            'map_height': 50,
            'cell_size': 15,
            'show_grid': True,
            'show_coordinates': False,
            'default_algorithm': 'A*',
            'allow_diagonal': True,
            'animation_speed': 50,
            'colors': {
                'EMPTY': '#FFFFFF',
                'OBSTACLE': '#333333',
                'START': '#00FF00',
                'END': '#FF0000',
                'WAYPOINT': '#FFA500',
                'PATH': '#0066FF',
                'VISITED': '#CCCCCC'
            }
        }
        self.grid_map = GridMap(self.settings['map_width'], self.settings['map_height'])
        self.map_manager = MapManager()
        self.export_manager = ExportManager()
        self.undo_manager = UndoRedoManager()
        self.current_path_result: Optional[PathResult] = None
        self.setup_ui()
        self.setup_menu()
        self.setup_bindings()
    
    def setup_ui(self):
        self.main_paned = ttk.PanedWindow(self, orient='horizontal')
        self.main_paned.pack(fill='both', expand=True)
        self.left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame, weight=3)
        self.control_frame = ttk.Frame(self.left_frame)
        self.control_frame.pack(fill='x', padx=5, pady=5)
        self.setup_toolbar()
        self.setup_edit_tools()
        self.canvas_frame = ttk.Frame(self.left_frame)
        self.canvas_frame.pack(fill='both', expand=True, padx=5, pady=5)
        canvas_width = self.settings['map_width'] * self.settings['cell_size']
        canvas_height = self.settings['map_height'] * self.settings['cell_size']
        self.canvas = tk.Canvas(self.canvas_frame, width=canvas_width, height=canvas_height, bg='white')
        self.map_editor = MapEditor(self.canvas_frame, self.grid_map, self.settings['cell_size'])
        self.map_editor.pack(fill='both', expand=True)
        self.map_editor.hover_callback = self.on_cell_hover
        self.status_frame = ttk.Frame(self.left_frame)
        self.status_frame.pack(fill='x', padx=5, pady=2)
        self.status_label = ttk.Label(self.status_frame, text="就绪")
        self.status_label.pack(side='left')
        self.position_label = ttk.Label(self.status_frame, text="位置: (-, -)")
        self.position_label.pack(side='right')
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_frame, weight=1)
        self.setup_right_panel()
    
    def setup_toolbar(self):
        toolbar = ttk.Frame(self.control_frame)
        toolbar.pack(fill='x', pady=2)
        ttk.Label(toolbar, text="算法:").pack(side='left', padx=2)
        self.algo_var = tk.StringVar(value=self.settings['default_algorithm'])
        self.algo_combo = ttk.Combobox(toolbar, textvariable=self.algo_var, 
                                       values=AlgorithmFactory.get_algorithm_names(), width=15)
        self.algo_combo.pack(side='left', padx=2)
        self.diagonal_var = tk.BooleanVar(value=self.settings['allow_diagonal'])
        ttk.Checkbutton(toolbar, text="对角移动", variable=self.diagonal_var).pack(side='left', padx=5)
        ttk.Button(toolbar, text="寻路", command=self.find_path).pack(side='left', padx=2)
        ttk.Button(toolbar, text="动画演示", command=self.animate_path).pack(side='left', padx=2)
        ttk.Button(toolbar, text="清除路径", command=self.clear_path).pack(side='left', padx=2)
        ttk.Button(toolbar, text="比较算法", command=self.compare_algorithms).pack(side='left', padx=2)
    
    def setup_edit_tools(self):
        tools_frame = ttk.LabelFrame(self.control_frame, text="编辑工具")
        tools_frame.pack(fill='x', pady=5)
        self.edit_mode_var = tk.StringVar(value='obstacle')
        modes = [
            ('obstacle', '障碍物'),
            ('start', '起点'),
            ('end', '终点'),
            ('waypoint', '途经点'),
            ('erase', '橡皮擦')
        ]
        for mode, label in modes:
            ttk.Radiobutton(tools_frame, text=label, variable=self.edit_mode_var, 
                           value=mode, command=self.on_edit_mode_change).pack(side='left', padx=5)
        ttk.Separator(tools_frame, orient='vertical').pack(side='left', fill='y', padx=10)
        ttk.Button(tools_frame, text="随机障碍", command=self.generate_random_obstacles).pack(side='left', padx=2)
        ttk.Button(tools_frame, text="迷宫生成", command=self.generate_maze).pack(side='left', padx=2)
        ttk.Button(tools_frame, text="清空地图", command=self.clear_map).pack(side='left', padx=2)
    
    def setup_right_panel(self):
        notebook = ttk.Notebook(self.right_frame)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        nav_frame = ttk.Frame(notebook)
        notebook.add(nav_frame, text="导航")
        self.nav_panel = NavigationPanel(nav_frame)
        self.nav_panel.pack(fill='both', expand=True)
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text="性能分析")
        self.perf_panel = PerformancePanel(perf_frame)
        self.perf_panel.pack(fill='both', expand=True)
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="路径信息")
        self.setup_info_panel(info_frame)
        help_frame = ttk.Frame(notebook)
        notebook.add(help_frame, text="帮助")
        self.setup_help_panel(help_frame)
    
    def setup_info_panel(self, parent):
        self.info_text = tk.Text(parent, wrap='word', height=20)
        self.info_text.pack(fill='both', expand=True, padx=5, pady=5)
        scrollbar = ttk.Scrollbar(self.info_text, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
    
    def setup_help_panel(self, parent):
        help_text = tk.Text(parent, wrap='word', height=20)
        help_text.pack(fill='both', expand=True, padx=5, pady=5)
        help_content = """
智能寻路导航系统 使用说明

【基本操作】
1. 左键点击/拖动：根据当前编辑模式添加/切换元素
2. 右键点击：删除障碍物或途经点

【编辑模式】
- 障碍物：点击添加或移除障碍物
- 起点：设置路径起点（绿色）
- 终点：设置路径终点（红色）
- 途经点：添加必须经过的点（橙色）
- 橡皮擦：删除障碍物和途经点

【寻路算法】
- A*：启发式搜索，效率高
- Dijkstra：保证最短路径
- BFS：广度优先，无权最短
- DFS：深度优先，可能非最优
- Greedy Best-First：贪心搜索，速度快
- 双向BFS：双向搜索，效率高
- Jump Point Search：跳点搜索，优化A*
- Theta*：支持任意角度路径

【功能说明】
- 寻路：使用选定算法计算路径
- 动画演示：可视化搜索过程
- 清除路径：清除当前路径显示
- 比较算法：比较所有算法性能
- 导航：模拟导航过程

【快捷键】
Ctrl+N：新建地图
Ctrl+O：打开地图
Ctrl+S：保存地图
Ctrl+Q：退出程序
F5：开始寻路
F6：动画演示
F7：清除路径
        """
        help_text.insert('1.0', help_content)
        help_text.config(state='disabled')
    
    def setup_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建地图", command=self.new_map, accelerator="Ctrl+N")
        file_menu.add_command(label="打开地图...", command=self.open_map, accelerator="Ctrl+O")
        file_menu.add_command(label="保存地图...", command=self.save_map, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="导出路径...", command=self.export_path)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit, accelerator="Ctrl+Q")
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="清空地图", command=self.clear_map)
        edit_menu.add_command(label="清除路径", command=self.clear_path)
        edit_menu.add_separator()
        edit_menu.add_command(label="随机障碍物", command=self.generate_random_obstacles)
        edit_menu.add_command(label="生成迷宫", command=self.generate_maze)
        edit_menu.add_separator()
        edit_menu.add_command(label="撤销", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="重做", command=self.redo, accelerator="Ctrl+Y")
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        self.show_grid_var = tk.BooleanVar(value=self.settings['show_grid'])
        view_menu.add_checkbutton(label="显示网格", variable=self.show_grid_var, command=self.toggle_grid)
        self.show_coords_var = tk.BooleanVar(value=self.settings['show_coordinates'])
        view_menu.add_checkbutton(label="显示坐标", variable=self.show_coords_var, command=self.toggle_coordinates)
        view_menu.add_separator()
        view_menu.add_command(label="缩放+", command=lambda: self.zoom(1.2))
        view_menu.add_command(label="缩放-", command=lambda: self.zoom(0.8))
        algo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="算法", menu=algo_menu)
        for name in AlgorithmFactory.get_algorithm_names():
            algo_menu.add_command(label=name, command=lambda n=name: self.run_single_algorithm(n))
        algo_menu.add_separator()
        algo_menu.add_command(label="比较所有算法", command=self.compare_algorithms)
        algo_menu.add_command(label="多途经点规划...", command=self.plan_multi_waypoint)
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="首选项...", command=self.open_settings)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def setup_bindings(self):
        """所有快捷键集中由 KeyboardShortcutManager 注册，避免两处维护。"""
        self.shortcuts = KeyboardShortcutManager(self)

    def on_edit_mode_change(self):
        mode = self.edit_mode_var.get()
        self.map_editor.set_edit_mode(mode)
    
    def on_cell_hover(self, pos: Position):
        self.position_label.config(text=f"位置: ({pos.x}, {pos.y})")
    
    def find_path(self):
        if not self.grid_map.start_position or not self.grid_map.end_position:
            messagebox.showwarning("警告", "请先设置起点和终点！")
            return
        self.map_editor.stop_animation()
        self.map_editor.clear_path()
        algorithm_name = self.algo_var.get()
        allow_diagonal = self.diagonal_var.get()
        algorithm = AlgorithmFactory.create_algorithm(algorithm_name, self.grid_map, allow_diagonal)
        self.status_label.config(text=f"正在使用 {algorithm_name} 寻路...")
        self.update()
        start_time = time.time()
        result = algorithm.find_path(self.grid_map.start_position, self.grid_map.end_position)
        end_time = time.time()
        self.current_path_result = result
        self.map_editor.path_result = result
        self.map_editor.draw_map()
        self.update_path_info(result)
        self.perf_panel.add_result(result)
        if result.success:
            self.status_label.config(text=f"寻路完成！路径长度: {result.path_length:.2f}, 耗时: {(end_time-start_time)*1000:.2f}ms")
            self.nav_panel.set_path(result.path, self.grid_map)
        else:
            self.status_label.config(text="未找到有效路径")
            messagebox.showinfo("提示", "未找到有效路径，请检查地图设置。")
    
    def animate_path(self):
        if not self.grid_map.start_position or not self.grid_map.end_position:
            messagebox.showwarning("警告", "请先设置起点和终点！")
            return
        self.map_editor.clear_path()
        algorithm_name = self.algo_var.get()
        allow_diagonal = self.diagonal_var.get()
        algorithm = AlgorithmFactory.create_algorithm(algorithm_name, self.grid_map, allow_diagonal)
        self.status_label.config(text=f"正在使用 {algorithm_name} 演示寻路过程...")
        self.update()
        result = algorithm.find_path(self.grid_map.start_position, self.grid_map.end_position)
        self.current_path_result = result
        self.map_editor.path_result = result
        self.map_editor.set_animation_speed(self.settings['animation_speed'])
        self.map_editor.animate_path(callback=self.on_animation_complete)
        self.update_path_info(result)
        self.perf_panel.add_result(result)
    
    def on_animation_complete(self):
        if self.current_path_result and self.current_path_result.success:
            self.status_label.config(text=f"动画演示完成！路径长度: {self.current_path_result.path_length:.2f}")
            self.nav_panel.set_path(self.current_path_result.path, self.grid_map)
    
    def clear_path(self):
        self.map_editor.stop_animation()
        self.map_editor.clear_path()
        self.current_path_result = None
        self.nav_panel.set_path([], self.grid_map)
        self.info_text.delete('1.0', 'end')
        self.status_label.config(text="路径已清除")
    
    def compare_algorithms(self):
        if not self.grid_map.start_position or not self.grid_map.end_position:
            messagebox.showwarning("警告", "请先设置起点和终点！")
            return
        self.map_editor.clear_path()
        allow_diagonal = self.diagonal_var.get()
        self.status_label.config(text="正在比较所有算法...")
        self.update()
        results = {}
        for name in AlgorithmFactory.get_algorithm_names():
            algorithm = AlgorithmFactory.create_algorithm(name, self.grid_map, allow_diagonal)
            result = algorithm.find_path(self.grid_map.start_position, self.grid_map.end_position)
            results[name] = result
        self.perf_panel.add_results(results)
        best_algo = min(results.items(), key=lambda x: x[1].execution_time if x[1].success else float('inf'))
        self.status_label.config(text=f"算法比较完成！最快算法: {best_algo[0]}")
        messagebox.showinfo("算法比较", f"算法比较完成！\n最快算法: {best_algo[0]}\n耗时: {best_algo[1].execution_time*1000:.2f}ms")
    
    def run_single_algorithm(self, name: str):
        self.algo_var.set(name)
        self.find_path()
    
    def update_path_info(self, result: PathResult):
        self.info_text.delete('1.0', 'end')
        info = f"""算法: {result.algorithm_name}
状态: {'成功' if result.success else '失败'}
{'='*40}
路径长度: {result.path_length:.2f}
搜索节点数: {result.nodes_explored}
执行时间: {result.execution_time*1000:.2f} ms
{'='*40}
"""
        if result.success and result.path:
            info += "\n路径方向指引:\n"
            directions = result.get_directions()
            for i, (direction, distance, pos) in enumerate(directions, 1):
                info += f"{i}. {DIRECTION_NAMES[direction]} - {distance:.2f} 单位\n"
            info += f"\n总步数: {len(result.path)}\n"
            info += f"起点: ({result.path[0].x}, {result.path[0].y})\n"
            info += f"终点: ({result.path[-1].x}, {result.path[-1].y})\n"
        self.info_text.insert('1.0', info)
    
    def generate_random_obstacles(self):
        density = 0.3
        self.undo_manager.push(self.grid_map)
        self.grid_map.generate_random_obstacles(density)
        self.map_editor.draw_map()
        self.status_label.config(text=f"已生成随机障碍物 (密度: {density*100}%)")
    
    def generate_maze(self):
        self.undo_manager.push(self.grid_map)
        self.grid_map.generate_maze()
        self.map_editor.draw_map()
        self.status_label.config(text="已生成迷宫地图")
    
    def clear_map(self):
        self.undo_manager.push(self.grid_map)
        self.grid_map.reset()
        self.map_editor.clear_path()
        self.map_editor.draw_map()
        self.status_label.config(text="地图已清空")
    
    def new_map(self):
        self.undo_manager.push(self.grid_map)
        self.grid_map.reset()
        self.map_editor.clear_path()
        self.map_editor.draw_map()
        self.status_label.config(text="新建地图")
    
    def undo(self):
        """撤销上一次批量地图操作（新建/清空/随机障碍/迷宫生成）。"""
        if not self.undo_manager.can_undo():
            self.status_label.config(text="没有可撤销的操作")
            return
        restored = self.undo_manager.undo(self.grid_map)
        self._apply_map(restored)
        self.status_label.config(text="已撤销")

    def redo(self):
        """重做被撤销的地图操作。"""
        if not self.undo_manager.can_redo():
            self.status_label.config(text="没有可重做的操作")
            return
        restored = self.undo_manager.redo(self.grid_map)
        self._apply_map(restored)
        self.status_label.config(text="已重做")

    def _apply_map(self, grid_map: GridMap):
        """把一张地图接管为当前地图，并同步画布与关联面板。"""
        self.grid_map = grid_map
        self.map_editor.grid_map = grid_map
        self.map_editor.clear_path()
        self.map_editor.draw_map()
        self.current_path_result = None
        self.nav_panel.set_path([], grid_map)

    def plan_multi_waypoint(self):
        """打开多途经点规划对话框，并对结果做可视化。"""
        if not self.grid_map.start_position or not self.grid_map.end_position:
            messagebox.showinfo("提示", "请先设置起点和终点。")
            return
        if not self.grid_map.waypoints:
            messagebox.showinfo("提示", "请先用左侧「途经点」工具添加至少一个途经点。")
            return

        dialog = MultiWaypointDialog(self, self.grid_map)
        self.wait_window(dialog)
        result = dialog.result
        if result is None:
            return
        if not result.success:
            messagebox.showwarning("规划失败", result.message or "途经点之间不可达")
            return

        self.current_path_result = result
        self.map_editor.path_result = result
        self.map_editor.draw_map()
        self.update_path_info(result)
        self.nav_panel.set_path(result.path, self.grid_map)
        self.status_label.config(
            text=f"多途经点规划完成：{len(self.grid_map.waypoints)} 个途经点，总长 {result.path_length:.2f}"
        )

    def open_map(self):
        filename = filedialog.askopenfilename(
            title="打开地图",
            initialdir=self.map_manager.save_directory,
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            loaded_map = self.map_manager.load_map(os.path.basename(filename))
            if loaded_map:
                self.undo_manager.push(self.grid_map)
                self._apply_map(loaded_map)
                self.status_label.config(text=f"已打开地图: {os.path.basename(filename)}")
            else:
                messagebox.showerror("错误", "无法加载地图文件")
    
    def save_map(self):
        filename = filedialog.asksaveasfilename(
            title="保存地图",
            initialdir=self.map_manager.save_directory,
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            if self.map_manager.save_map(self.grid_map, os.path.basename(filename)):
                self.status_label.config(text=f"地图已保存: {os.path.basename(filename)}")
            else:
                messagebox.showerror("错误", "保存地图失败")
    
    def export_path(self):
        if not self.current_path_result or not self.current_path_result.success:
            messagebox.showwarning("警告", "没有可导出的路径！")
            return
        filename = filedialog.asksaveasfilename(
            title="导出路径",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            try:
                if filename.endswith('.json'):
                    data = {
                        'algorithm': self.current_path_result.algorithm_name,
                        'path': [(p.x, p.y) for p in self.current_path_result.path],
                        'path_length': self.current_path_result.path_length,
                        'nodes_explored': self.current_path_result.nodes_explored,
                        'execution_time': self.current_path_result.execution_time
                    }
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"算法: {self.current_path_result.algorithm_name}\n")
                        f.write(f"路径长度: {self.current_path_result.path_length:.2f}\n")
                        f.write(f"搜索节点: {self.current_path_result.nodes_explored}\n")
                        f.write(f"执行时间: {self.current_path_result.execution_time*1000:.2f}ms\n")
                        f.write("\n路径坐标:\n")
                        for i, pos in enumerate(self.current_path_result.path):
                            f.write(f"{i+1}. ({pos.x}, {pos.y})\n")
                self.status_label.config(text=f"路径已导出: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
    
    def toggle_grid(self):
        self.map_editor.show_grid = self.show_grid_var.get()
        self.map_editor.draw_map()
    
    def toggle_coordinates(self):
        self.map_editor.show_coordinates = self.show_coords_var.get()
        self.map_editor.draw_map()
    
    def zoom(self, factor: float):
        new_size = int(self.settings['cell_size'] * factor)
        new_size = max(5, min(50, new_size))
        self.settings['cell_size'] = new_size
        self.map_editor.cell_size = new_size
        canvas_width = self.grid_map.width * new_size
        canvas_height = self.grid_map.height * new_size
        self.map_editor.config(width=canvas_width, height=canvas_height)
        self.map_editor.draw_map()
    
    def open_settings(self):
        dialog = SettingsDialog(self, self.settings)
        self.wait_window(dialog)
        if dialog.result:
            self.settings.update(dialog.result)
            if 'colors' in dialog.result:
                for key, color in dialog.result['colors'].items():
                    cell_type = CellType[key]
                    self.map_editor.set_color(cell_type, color)
            self.map_editor.show_grid = self.settings.get('show_grid', True)
            self.map_editor.show_coordinates = self.settings.get('show_coordinates', False)
            self.map_editor.set_animation_speed(self.settings.get('animation_speed', 50))
            self.map_editor.draw_map()
            self.status_label.config(text="设置已更新")
    
    def show_help(self):
        messagebox.showinfo("帮助", "请查看右侧帮助面板获取详细使用说明。")
    
    def show_about(self):
        messagebox.showinfo("关于", 
            "智能寻路导航系统 v1.0\n\n"
            "本软件实现了多种经典寻路算法，\n"
            "支持地图编辑、路径可视化、导航模拟等功能。\n\n"
            "支持的算法:\n"
            "- A* 算法\n"
            "- Dijkstra 算法\n"
            "- BFS 广度优先搜索\n"
            "- DFS 深度优先搜索\n"
            "- Greedy Best-First 贪心搜索\n"
            "- 双向 BFS\n"
            "- Jump Point Search\n"
            "- Theta* 算法"
        )


class KeyboardShortcutManager:
    """快捷键注册表。

    ``MainWindow`` 启动时创建一次；新增快捷键只需在 :meth:`default_shortcuts`
    里加一行，界面与文档都不必改动别处。
    """

    def __init__(self, main_window: MainWindow):
        self.main_window = main_window
        self.shortcuts: Dict[str, callable] = {}
        self.setup_default_shortcuts()

    def default_shortcuts(self) -> Dict[str, callable]:
        window = self.main_window
        return {
            "<Control-n>": window.new_map,
            "<Control-o>": window.open_map,
            "<Control-s>": window.save_map,
            "<Control-e>": window.export_path,
            "<Control-z>": window.undo,
            "<Control-y>": window.redo,
            "<Control-g>": window.toggle_grid,
            "<Control-Shift-G>": window.toggle_coordinates,
            "<Control-plus>": lambda: window.zoom(1.2),
            "<Control-equal>": lambda: window.zoom(1.2),
            "<Control-minus>": lambda: window.zoom(1 / 1.2),
            "<F1>": window.show_help,
            "<F5>": window.find_path,
            "<F6>": window.animate_path,
            "<F7>": window.clear_path,
            "<Escape>": lambda: window.map_editor.stop_animation(),
            "<Control-q>": window.quit,
        }

    def setup_default_shortcuts(self):
        for key, callback in self.default_shortcuts().items():
            self.register(key, callback)

    def register(self, key: str, callback: callable):
        self.shortcuts[key] = callback
        self.main_window.bind(key, lambda event: callback())

    def unregister(self, key: str):
        if key in self.shortcuts:
            del self.shortcuts[key]
            self.main_window.unbind(key)
