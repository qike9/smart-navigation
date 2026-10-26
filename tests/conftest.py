# -*- coding: utf-8 -*-
"""pytest 公共 fixture。"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from smartnav import CellType, GridMap, Position  # noqa: E402
from smartnav.maps import MapTemplate  # noqa: E402


@pytest.fixture
def open_map():
    """12x12 无障碍地图。"""
    grid = GridMap(12, 12)
    grid.set_start(Position(1, 1))
    grid.set_end(Position(10, 10))
    return grid


@pytest.fixture
def walled_map():
    """中间一堵带缺口的墙。"""
    grid = GridMap(12, 12)
    for y in range(12):
        if y != 6:
            grid.set_cell(Position(6, y), CellType.OBSTACLE)
    grid.set_start(Position(1, 1))
    grid.set_end(Position(10, 10))
    return grid


@pytest.fixture
def sealed_map():
    """终点被完全封死，必定无解。"""
    grid = GridMap(12, 12)
    for x in range(12):
        grid.set_cell(Position(x, 6), CellType.OBSTACLE)
    grid.set_start(Position(1, 1))
    grid.set_end(Position(10, 10))
    return grid


@pytest.fixture
def maze_map():
    """递归回溯法生成的 21x21 迷宫。"""
    grid = MapTemplate.create_maze_recursive(21, 21)
    grid.set_start(Position(1, 1))
    grid.set_end(Position(19, 19))
    return grid
