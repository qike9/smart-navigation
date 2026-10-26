# -*- coding: utf-8 -*-
"""地图画布控件：编辑、绘制与寻路动画。"""

from __future__ import annotations

import tkinter as tk
from typing import List, Optional, Tuple

from ..models import CellType, GridMap, PathResult, Position


class MapEditor(tk.Canvas):
    def __init__(self, parent, grid_map: GridMap, cell_size: int = 15, **kwargs):
        self.cell_size = cell_size
        self.grid_map = grid_map
        self.edit_mode = 'obstacle'
        self.is_drawing = False
        self.show_grid = True
        self.show_coordinates = False
        self.path_result: Optional[PathResult] = None
        self.animation_running = False
        self.animation_index = 0
        self.animation_speed = 50
        self.colors = {
            CellType.EMPTY: '#FFFFFF',
            CellType.OBSTACLE: '#333333',
            CellType.START: '#00FF00',
            CellType.END: '#FF0000',
            CellType.WAYPOINT: '#FFA500',
            CellType.PATH: '#0066FF',
            CellType.VISITED: '#CCCCCC',
            CellType.CURRENT: '#FFFF00'
        }
        canvas_width = grid_map.width * cell_size
        canvas_height = grid_map.height * cell_size
        super().__init__(parent, width=canvas_width, height=canvas_height, bg='white', **kwargs)
        self.bind('<Button-1>', self.on_left_click)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<Button-3>', self.on_right_click)
        self.bind('<Motion>', self.on_mouse_move)
        self.hover_callback = None
        self.draw_map()
    
    def set_edit_mode(self, mode: str):
        self.edit_mode = mode
    
    def set_color(self, cell_type: CellType, color: str):
        self.colors[cell_type] = color
    
    def on_left_click(self, event):
        self.is_drawing = True
        self.handle_edit(event)
    
    def on_drag(self, event):
        if self.is_drawing:
            self.handle_edit(event)
    
    def on_release(self, event):
        self.is_drawing = False
    
    def on_right_click(self, event):
        pos = self.screen_to_grid(event.x, event.y)
        if pos:
            cell = self.grid_map.get_cell(pos)
            if cell == CellType.OBSTACLE:
                self.grid_map.remove_obstacle(pos)
            elif cell == CellType.WAYPOINT:
                self.grid_map.remove_waypoint(pos)
            self.draw_map()
    
    def on_mouse_move(self, event):
        pos = self.screen_to_grid(event.x, event.y)
        if self.hover_callback and pos:
            self.hover_callback(pos)
    
    def handle_edit(self, event):
        pos = self.screen_to_grid(event.x, event.y)
        if not pos:
            return
        if self.edit_mode == 'obstacle':
            if self.grid_map.get_cell(pos) not in [CellType.START, CellType.END]:
                self.grid_map.toggle_obstacle(pos)
        elif self.edit_mode == 'start':
            self.grid_map.set_start(pos)
        elif self.edit_mode == 'end':
            self.grid_map.set_end(pos)
        elif self.edit_mode == 'waypoint':
            if self.grid_map.get_cell(pos) == CellType.EMPTY:
                self.grid_map.add_waypoint(pos)
        elif self.edit_mode == 'erase':
            cell = self.grid_map.get_cell(pos)
            if cell == CellType.OBSTACLE:
                self.grid_map.remove_obstacle(pos)
            elif cell == CellType.WAYPOINT:
                self.grid_map.remove_waypoint(pos)
        self.draw_map()
    
    def screen_to_grid(self, x: int, y: int) -> Optional[Position]:
        grid_x = x // self.cell_size
        grid_y = y // self.cell_size
        if 0 <= grid_x < self.grid_map.width and 0 <= grid_y < self.grid_map.height:
            return Position(grid_x, grid_y)
        return None
    
    def grid_to_screen(self, pos: Position) -> Tuple[int, int]:
        return pos.x * self.cell_size, pos.y * self.cell_size
    
    def draw_map(self):
        self.delete('all')
        for y in range(self.grid_map.height):
            for x in range(self.grid_map.width):
                pos = Position(x, y)
                cell = self.grid_map.get_cell(pos)
                self.draw_cell(pos, self.colors[cell])
        if self.path_result:
            self.draw_path_result()
        if self.show_grid:
            self.draw_grid_lines()
        if self.show_coordinates:
            self.draw_coordinates()
    
    def draw_cell(self, pos: Position, color: str):
        x1, y1 = self.grid_to_screen(pos)
        x2, y2 = x1 + self.cell_size, y1 + self.cell_size
        self.create_rectangle(x1, y1, x2, y2, fill=color, outline='#DDDDDD', width=1)
    
    def draw_grid_lines(self):
        for x in range(0, self.grid_map.width * self.cell_size + 1, self.cell_size):
            self.create_line(x, 0, x, self.grid_map.height * self.cell_size, fill='#EEEEEE')
        for y in range(0, self.grid_map.height * self.cell_size + 1, self.cell_size):
            self.create_line(0, y, self.grid_map.width * self.cell_size, y, fill='#EEEEEE')
    
    def draw_coordinates(self):
        for x in range(0, self.grid_map.width, 5):
            screen_x = x * self.cell_size
            self.create_text(screen_x + 5, 5, text=str(x), font=('Arial', 6), fill='gray')
        for y in range(0, self.grid_map.height, 5):
            screen_y = y * self.cell_size
            self.create_text(5, screen_y + 5, text=str(y), font=('Arial', 6), fill='gray')
    
    def draw_path_result(self):
        if not self.path_result:
            return
        for pos in self.path_result.visited_nodes:
            if self.grid_map.get_cell(pos) == CellType.EMPTY:
                self.draw_cell(pos, self.colors[CellType.VISITED])
        for pos in self.path_result.path:
            if self.grid_map.get_cell(pos) in [CellType.EMPTY, CellType.VISITED]:
                self.draw_cell(pos, self.colors[CellType.PATH])
        if self.grid_map.start_position:
            self.draw_cell(self.grid_map.start_position, self.colors[CellType.START])
        if self.grid_map.end_position:
            self.draw_cell(self.grid_map.end_position, self.colors[CellType.END])
        for wp in self.grid_map.waypoints:
            self.draw_cell(wp, self.colors[CellType.WAYPOINT])
    
    def clear_path(self):
        self.path_result = None
        self.grid_map.clear_path_visualization()
        self.draw_map()
    
    def animate_path(self, callback=None):
        if not self.path_result or not self.path_result.path:
            return
        self.animation_running = True
        self.animation_index = 0
        self._animate_step(callback)
    
    def _animate_step(self, callback):
        if not self.animation_running:
            return
        if self.animation_index < len(self.path_result.visited_nodes):
            pos = self.path_result.visited_nodes[self.animation_index]
            if self.grid_map.get_cell(pos) == CellType.EMPTY:
                self.draw_cell(pos, self.colors[CellType.VISITED])
            self.animation_index += 1
            self.after(self.animation_speed, lambda: self._animate_step(callback))
        elif self.animation_index < len(self.path_result.visited_nodes) + len(self.path_result.path):
            idx = self.animation_index - len(self.path_result.visited_nodes)
            if idx < len(self.path_result.path):
                pos = self.path_result.path[idx]
                self.draw_cell(pos, self.colors[CellType.PATH])
            self.animation_index += 1
            self.after(self.animation_speed, lambda: self._animate_step(callback))
        else:
            self.animation_running = False
            if self.grid_map.start_position:
                self.draw_cell(self.grid_map.start_position, self.colors[CellType.START])
            if self.grid_map.end_position:
                self.draw_cell(self.grid_map.end_position, self.colors[CellType.END])
            if callback:
                callback()
    
    def stop_animation(self):
        self.animation_running = False
    
    def set_animation_speed(self, speed: int):
        self.animation_speed = max(1, min(500, speed))
    
    def resize(self, width: int, height: int):
        self.grid_map.resize(width, height)
        canvas_width = width * self.cell_size
        canvas_height = height * self.cell_size
        self.config(width=canvas_width, height=canvas_height)
        self.draw_map()


class SearchVisualizer:
    def __init__(self, canvas: MapEditor):
        self.canvas = canvas
        self.visualization_steps: List[Tuple[Position, str]] = []
        self.current_step = 0
        self.is_playing = False
    
    def add_step(self, pos: Position, action: str):
        self.visualization_steps.append((pos, action))
    
    def clear_steps(self):
        self.visualization_steps.clear()
        self.current_step = 0
    
    def play(self, speed: int = 50, callback: callable = None):
        if not self.visualization_steps:
            return
        self.is_playing = True
        self._play_step(speed, callback)
    
    def _play_step(self, speed: int, callback: callable):
        if not self.is_playing or self.current_step >= len(self.visualization_steps):
            self.is_playing = False
            if callback:
                callback()
            return
        pos, action = self.visualization_steps[self.current_step]
        if action == 'visit':
            if self.canvas.grid_map.get_cell(pos) == CellType.EMPTY:
                self.canvas.draw_cell(pos, self.canvas.colors[CellType.VISITED])
        elif action == 'path':
            self.canvas.draw_cell(pos, self.canvas.colors[CellType.PATH])
        self.current_step += 1
        self.canvas.after(speed, lambda: self._play_step(speed, callback))
    
    def stop(self):
        self.is_playing = False
    
    def pause(self):
        self.is_playing = False
    
    def resume(self, speed: int = 50, callback: callable = None):
        self.is_playing = True
        self._play_step(speed, callback)
