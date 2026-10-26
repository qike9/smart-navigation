# -*- coding: utf-8 -*-
"""支持 ``python -m smartnav`` 直接启动界面。"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
