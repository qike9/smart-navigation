# -*- coding: utf-8 -*-
"""导航模拟：单路径导航、多智能体仿真与路径录制。"""

from __future__ import annotations

from typing import Dict, List, Optional

from .models import Direction, GridMap, Position


class NavigationSimulator:
    def __init__(self, path: List[Position], grid_map: GridMap):
        self.path = path
        self.grid_map = grid_map
        self.current_index = 0
        self.speed = 1.0
        self.is_running = False
        self.is_paused = False
    
    def get_current_position(self) -> Optional[Position]:
        if not self.path or self.current_index >= len(self.path):
            return None
        return self.path[self.current_index]
    
    def get_next_position(self) -> Optional[Position]:
        if not self.path or self.current_index >= len(self.path) - 1:
            return None
        return self.path[self.current_index + 1]
    
    def get_direction(self) -> Optional[Direction]:
        current = self.get_current_position()
        next_pos = self.get_next_position()
        if current and next_pos:
            return current.get_direction_to(next_pos)
        return None
    
    def get_remaining_distance(self) -> float:
        if not self.path or self.current_index >= len(self.path):
            return 0.0
        distance = 0.0
        for i in range(self.current_index, len(self.path) - 1):
            distance += self.path[i].distance_to(self.path[i + 1])
        return distance
    
    def get_progress(self) -> float:
        if not self.path:
            return 0.0
        return (self.current_index + 1) / len(self.path) * 100
    
    def advance(self) -> bool:
        if self.current_index < len(self.path) - 1:
            self.current_index += 1
            return True
        return False
    
    def reset(self):
        self.current_index = 0
        self.is_running = False
        self.is_paused = False
    
    def is_finished(self) -> bool:
        return self.current_index >= len(self.path) - 1


class SimulationEngine:
    def __init__(self, grid_map: GridMap):
        self.grid_map = grid_map
        self.agents: List[Dict] = []
        self.time_step = 0
    
    def add_agent(self, agent_id: str, start: Position, end: Position, speed: float = 1.0):
        agent = {
            'id': agent_id,
            'position': start.copy(),
            'start': start.copy(),
            'end': end.copy(),
            'speed': speed,
            'path': [],
            'path_index': 0,
            'arrived': False
        }
        self.agents.append(agent)
    
    def set_agent_path(self, agent_id: str, path: List[Position]):
        for agent in self.agents:
            if agent['id'] == agent_id:
                agent['path'] = path.copy()
                agent['path_index'] = 0
                break
    
    def step(self) -> List[Dict]:
        updates = []
        for agent in self.agents:
            if agent['arrived'] or not agent['path']:
                continue
            agent['path_index'] += agent['speed']
            idx = int(agent['path_index'])
            if idx >= len(agent['path']):
                agent['position'] = agent['path'][-1].copy()
                agent['arrived'] = True
            else:
                agent['position'] = agent['path'][idx].copy()
            updates.append({
                'id': agent['id'],
                'position': (agent['position'].x, agent['position'].y),
                'arrived': agent['arrived']
            })
        self.time_step += 1
        return updates
    
    def run_until_complete(self, max_steps: int = 10000) -> bool:
        for _ in range(max_steps):
            if all(agent['arrived'] for agent in self.agents):
                return True
            self.step()
        return False
    
    def reset(self):
        for agent in self.agents:
            agent['position'] = agent['start'].copy()
            agent['path_index'] = 0
            agent['arrived'] = False
        self.time_step = 0
    
    def clear_agents(self):
        self.agents.clear()
        self.time_step = 0
    
    def get_agent_positions(self) -> Dict[str, Position]:
        return {agent['id']: agent['position'].copy() for agent in self.agents}


class PathRecorder:
    def __init__(self):
        self.recordings: Dict[str, List[Position]] = {}
        self.current_recording: Optional[str] = None
        self.current_path: List[Position] = []
    
    def start_recording(self, name: str):
        self.current_recording = name
        self.current_path = []
    
    def record_position(self, pos: Position):
        if self.current_recording:
            self.current_path.append(pos.copy())
    
    def stop_recording(self) -> Optional[List[Position]]:
        if self.current_recording:
            self.recordings[self.current_recording] = self.current_path.copy()
            result = self.current_path.copy()
            self.current_recording = None
            self.current_path = []
            return result
        return None
    
    def get_recording(self, name: str) -> Optional[List[Position]]:
        return self.recordings.get(name)
    
    def list_recordings(self) -> List[str]:
        return list(self.recordings.keys())
    
    def delete_recording(self, name: str):
        if name in self.recordings:
            del self.recordings[name]
    
    def clear_all(self):
        self.recordings.clear()
        self.current_recording = None
        self.current_path = []
