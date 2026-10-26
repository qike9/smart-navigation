#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智能寻路导航系统 —— 图形界面入口。

用法::

    python smart_navigation.py      # 直接运行
    python -m smartnav              # 等价写法
    smart-navigation                # 通过 pip install -e . 安装后

零第三方依赖，Python 3.8+ 自带 tkinter 即可运行。
"""

from __future__ import annotations

import sys

from smartnav.cli import main

if __name__ == "__main__":
    sys.exit(main())
