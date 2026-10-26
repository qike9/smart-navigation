#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""无界面算法基准测试。

在不打开图形界面的情况下，把八种算法跑一遍并打印对比表格，适合放进 CI、
写进 README，或者用来评估新算法的性能。

用法::

    python tools/benchmark.py
    python tools/benchmark.py --size 81 --density 0.25 --repeat 5
    python tools/benchmark.py --map examples/maps/maze-41x41.json
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from smartnav import AlgorithmFactory, GridMap, Position  # noqa: E402
from smartnav.maps import MapManager, MapTemplate  # noqa: E402


def build_map(args) -> GridMap:
    if args.map_file:
        grid = MapManager(str(Path(args.map_file).parent)).load_map(Path(args.map_file).name)
        if grid is None:
            raise SystemExit(f"无法读取地图文件: {args.map_file}")
        return grid

    if args.maze:
        grid = MapTemplate.create_maze_recursive(args.size, args.size)
        grid.set_start(Position(1, 1))
        grid.set_end(Position(grid.width - 2, grid.height - 2))
        return grid

    grid = GridMap(args.size, args.size)
    grid.generate_random_obstacles(args.density)
    # 保证起终点可通行
    grid.set_start(Position(1, 1))
    grid.set_end(Position(args.size - 2, args.size - 2))
    return grid


def run(grid: GridMap, repeat: int, diagonal: bool) -> list[dict]:
    rows = []
    for name in AlgorithmFactory.get_algorithm_names():
        times, nodes, lengths, visited = [], [], [], []
        success = 0
        for _ in range(repeat):
            algorithm = AlgorithmFactory.create_algorithm(name, grid, diagonal)
            result = algorithm.find_path(grid.start_position, grid.end_position)
            times.append(result.execution_time * 1000)
            nodes.append(result.nodes_explored)
            visited.append(len(result.visited_nodes))
            if result.success:
                success += 1
                lengths.append(result.path_length)
        rows.append(
            {
                "算法": name,
                "成功率": f"{success / repeat * 100:.0f}%",
                "平均耗时(ms)": statistics.mean(times),
                "搜索节点": statistics.mean(nodes),
                "路径长度": statistics.mean(lengths) if lengths else float("nan"),
            }
        )
    return rows


def print_table(rows: list[dict]) -> None:
    headers = list(rows[0].keys())
    formatted = []
    for row in rows:
        line = []
        for key in headers:
            value = row[key]
            if isinstance(value, float):
                line.append("—" if value != value else f"{value:.2f}")
            else:
                line.append(str(value))
        formatted.append(line)

    widths = [max(len(h), *(len(r[i]) for r in formatted)) for i, h in enumerate(headers)]
    sep = "  "
    print(sep.join(h.ljust(w) for h, w in zip(headers, widths)))
    print(sep.join("-" * w for w in widths))
    for line in formatted:
        print(sep.join(cell.ljust(w) for cell, w in zip(line, widths)))


def main() -> int:
    parser = argparse.ArgumentParser(description="智能寻路导航系统 · 算法基准测试")
    parser.add_argument("--size", type=int, default=51, help="地图边长（默认 51）")
    parser.add_argument("--density", type=float, default=0.28, help="随机障碍物密度（默认 0.28）")
    parser.add_argument("--repeat", type=int, default=3, help="每个算法重复次数（默认 3）")
    parser.add_argument("--maze", action="store_true", help="改用完美迷宫地图")
    parser.add_argument("--map-file", type=str, help="直接载入 .json 地图")
    parser.add_argument("--no-diagonal", action="store_true", help="禁止斜向移动")
    args = parser.parse_args()

    grid = build_map(args)
    diagonal = not args.no_diagonal
    density = len(grid.obstacles) / (grid.width * grid.height)

    print(f"地图: {grid.width}x{grid.height}  障碍密度: {density:.1%}  斜向移动: {'是' if diagonal else '否'}")
    print(f"起点: ({grid.start_position.x}, {grid.start_position.y})  "
          f"终点: ({grid.end_position.x}, {grid.end_position.y})  重复: {args.repeat}\n")

    started = time.perf_counter()
    rows = run(grid, args.repeat, diagonal)
    print_table(rows)
    print(f"\n总耗时 {time.perf_counter() - started:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
