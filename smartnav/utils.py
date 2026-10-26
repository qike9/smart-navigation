# -*- coding: utf-8 -*-
"""撤销重做栈与坐标变换工具。"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .models import GridMap, Position


class UndoRedoManager:
    def __init__(self, max_history: int = 50):
        self.undo_stack: List[GridMap] = []
        self.redo_stack: List[GridMap] = []
        self.max_history = max_history
    
    def push(self, grid_map: GridMap):
        self.undo_stack.append(grid_map.copy())
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
    
    def undo(self, current_map: GridMap) -> Optional[GridMap]:
        if not self.undo_stack:
            return None
        self.redo_stack.append(current_map.copy())
        return self.undo_stack.pop()
    
    def redo(self, current_map: GridMap) -> Optional[GridMap]:
        if not self.redo_stack:
            return None
        self.undo_stack.append(current_map.copy())
        return self.redo_stack.pop()
    
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0
    
    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()


class CoordinateSystem:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0
    
    def world_to_screen(self, pos: Position) -> Tuple[int, int]:
        screen_x = int((pos.x + self.offset_x) * self.scale)
        screen_y = int((pos.y + self.offset_y) * self.scale)
        return (screen_x, screen_y)
    
    def screen_to_world(self, x: int, y: int) -> Position:
        world_x = int(x / self.scale - self.offset_x)
        world_y = int(y / self.scale - self.offset_y)
        return Position(world_x, world_y)
    
    def pan(self, dx: int, dy: int):
        self.offset_x += dx / self.scale
        self.offset_y += dy / self.scale
    
    def zoom(self, factor: float, center: Tuple[int, int] = None):
        old_scale = self.scale
        self.scale *= factor
        self.scale = max(0.1, min(10.0, self.scale))
        if center:
            cx, cy = center
            self.offset_x = cx / self.scale - (cx / old_scale - self.offset_x)
            self.offset_y = cy / self.scale - (cy / old_scale - self.offset_y)
    
    def reset(self):
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0
