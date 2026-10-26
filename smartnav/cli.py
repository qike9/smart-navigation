# -*- coding: utf-8 -*-
"""命令行入口。"""

from __future__ import annotations

import sys


def main() -> int:
    """启动图形界面。"""
    try:
        from .ui import MainWindow
    except ImportError as exc:  # pragma: no cover - 依赖系统环境
        print("启动失败：未找到 tkinter。", file=sys.stderr)
        print("Windows/macOS 官方 Python 自带；Debian/Ubuntu 可执行：", file=sys.stderr)
        print("    sudo apt install python3-tk", file=sys.stderr)
        print(f"原始错误: {exc}", file=sys.stderr)
        return 1

    app = MainWindow()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
