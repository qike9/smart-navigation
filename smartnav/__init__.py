# -*- coding: utf-8 -*-
"""智能寻路导航系统 —— 核心包。

Smart Navigation System: an interactive pathfinding / navigation playground
supporting eight classic search algorithms, map editing, search animation and
side-by-side performance comparison.
"""

from __future__ import annotations

from .algorithms import (
    AlgorithmFactory,
    AStarAlgorithm,
    BFSAlgorithm,
    BidirectionalBFSAlgorithm,
    DFSAlgorithm,
    DijkstraAlgorithm,
    GreedyBestFirstAlgorithm,
    JumpPointSearchAlgorithm,
    PathfindingAlgorithm,
    ThetaStarAlgorithm,
)
from .models import CellType, Direction, GridMap, Node, PathResult, Position

__version__ = "1.0.0"
__author__ = "qike9"
__license__ = "MIT"

__all__ = [
    "ALGORITHM_NAMES",
    "AStarAlgorithm",
    "AlgorithmFactory",
    "BFSAlgorithm",
    "BidirectionalBFSAlgorithm",
    "CellType",
    "DFSAlgorithm",
    "Direction",
    "DijkstraAlgorithm",
    "GridMap",
    "GreedyBestFirstAlgorithm",
    "JumpPointSearchAlgorithm",
    "Node",
    "PathResult",
    "PathfindingAlgorithm",
    "Position",
    "ThetaStarAlgorithm",
    "__version__",
]

ALGORITHM_NAMES = AlgorithmFactory.get_algorithm_names()
