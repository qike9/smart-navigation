# config.py
import os
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).parent


class Config:
    """应用配置类"""

    # 数据库配置
    DATABASE_PATH = BASE_DIR / 'data' / 'navigation.db'

    # 加密配置
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '1234567890123456')  # 16字节密钥

    # 应用配置
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

    # 地图模拟数据
    MAP_DATA = {
        'A': {'B': 5, 'C': 10},
        'B': {'A': 5, 'C': 3, 'D': 9},
        'C': {'A': 10, 'B': 3, 'D': 6, 'E': 8},
        'D': {'B': 9, 'C': 6, 'E': 7, 'F': 4},
        'E': {'C': 8, 'D': 7, 'F': 12},
        'F': {'D': 4, 'E': 12}
    }

    # 模拟交通数据
    TRAFFIC_LEVELS = {
        '通畅': {'speed': 1.0, 'delay': 0},
        '缓行': {'speed': 0.6, 'delay': 0.3},
        '拥堵': {'speed': 0.3, 'delay': 0.7},
        '严重拥堵': {'speed': 0.1, 'delay': 1.0}
    }

    @classmethod
    def get_map_data(cls) -> Dict[str, Dict[str, float]]:
        """获取地图数据"""
        return cls.MAP_DATA.copy()

    @classmethod
    def get_traffic_multiplier(cls, traffic_level: str) -> float:
        """根据交通状况获取时间倍数"""
        if traffic_level in cls.TRAFFIC_LEVELS:
            return cls.TRAFFIC_LEVELS[traffic_level]['delay'] + 1
        return 1.0