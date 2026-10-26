# data/database.py
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from .data_encryption import DataEncryptor
import config


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = None, encryptor: DataEncryptor = None):
        """初始化数据库管理器

        Args:
            db_path: 数据库路径
            encryptor: 数据加密器
        """
        self.db_path = db_path or str(config.Config.DATABASE_PATH)
        self.encryptor = encryptor or DataEncryptor(config.Config.ENCRYPTION_KEY)

        # 确保数据库目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 创建用户表
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS users
                           (
                               user_id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               username
                               TEXT
                               UNIQUE
                               NOT
                               NULL,
                               password_hash
                               TEXT
                               NOT
                               NULL,
                               email
                               TEXT,
                               phone
                               TEXT,
                               preferences
                               TEXT, -- 加密存储的偏好设置
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               last_login
                               TIMESTAMP
                           )
                           ''')

            # 创建路线历史表
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS route_history
                           (
                               route_id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               user_id
                               INTEGER,
                               start_location
                               TEXT
                               NOT
                               NULL,
                               end_location
                               TEXT
                               NOT
                               NULL,
                               route_data
                               TEXT
                               NOT
                               NULL, -- 加密存储的路线数据
                               distance
                               REAL,
                               duration
                               REAL,
                               traffic_level
                               TEXT,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               FOREIGN
                               KEY
                           (
                               user_id
                           ) REFERENCES users
                           (
                               user_id
                           )
                               )
                           ''')

            # 创建POI收藏表
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS poi_favorites
                           (
                               poi_id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               user_id
                               INTEGER,
                               poi_name
                               TEXT
                               NOT
                               NULL,
                               poi_type
                               TEXT,
                               location
                               TEXT,
                               notes
                               TEXT, -- 加密存储的备注
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               FOREIGN
                               KEY
                           (
                               user_id
                           ) REFERENCES users
                           (
                               user_id
                           )
                               )
                           ''')

            conn.commit()

    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def register_user(self, username: str, password: str,
                      email: str = None, phone: str = None) -> int:
        """注册新用户

        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            phone: 电话

        Returns:
            int: 用户ID

        Raises:
            ValueError: 用户名已存在
        """
        # 检查用户名是否存在
        if self.get_user_by_username(username):
            raise ValueError(f"用户名 '{username}' 已存在")

        # 简单密码哈希（实际应用中应该使用更安全的哈希算法）
        password_hash = self._hash_password(password)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO users (username, password_hash, email, phone)
                           VALUES (?, ?, ?, ?)
                           ''', (username, password_hash, email, phone))

            user_id = cursor.lastrowid
            conn.commit()

            return user_id

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证

        Args:
            username: 用户名
            password: 密码

        Returns:
            Optional[Dict]: 用户信息或None
        """
        user = self.get_user_by_username(username)
        if user and user['password_hash'] == self._hash_password(password):
            # 更新最后登录时间
            self.update_last_login(user['user_id'])
            return user
        return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户信息

        Args:
            username: 用户名

        Returns:
            Optional[Dict]: 用户信息或None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()

            if row:
                columns = [description[0] for description in cursor.description]
                user = dict(zip(columns, row))

                # 解密偏好设置
                if user.get('preferences'):
                    try:
                        user['preferences'] = self.encryptor.decrypt(user['preferences'])
                    except:
                        user['preferences'] = {}

                return user
            return None

    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]):
        """更新用户偏好设置

        Args:
            user_id: 用户ID
            preferences: 偏好设置字典
        """
        # 加密偏好设置
        encrypted_prefs = self.encryptor.encrypt(preferences)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           UPDATE users
                           SET preferences = ?
                           WHERE user_id = ?
                           ''', (encrypted_prefs, user_id))
            conn.commit()

    def save_route_history(self, user_id: int, start: str, end: str,
                           route_data: Dict[str, Any], distance: float,
                           duration: float, traffic_level: str = None):
        """保存路线历史

        Args:
            user_id: 用户ID
            start: 起点
            end: 终点
            route_data: 路线数据
            distance: 距离
            duration: 时间
            traffic_level: 交通状况
        """
        # 加密路线数据
        encrypted_data = self.encryptor.encrypt(route_data)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO route_history
                           (user_id, start_location, end_location, route_data, distance, duration, traffic_level)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           ''', (user_id, start, end, encrypted_data, distance, duration, traffic_level))
            conn.commit()

    def get_route_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户路线历史

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            List[Dict]: 路线历史列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           SELECT *
                           FROM route_history
                           WHERE user_id = ?
                           ORDER BY created_at DESC LIMIT ?
                           ''', (user_id, limit))

            routes = []
            for row in cursor.fetchall():
                columns = [description[0] for description in cursor.description]
                route = dict(zip(columns, row))

                # 解密路线数据
                if route.get('route_data'):
                    try:
                        route['route_data'] = self.encryptor.decrypt(route['route_data'])
                    except:
                        route['route_data'] = {}

                routes.append(route)

            return routes

    def add_poi_favorite(self, user_id: int, poi_name: str, poi_type: str = None,
                         location: str = None, notes: str = None) -> int:
        """添加POI收藏

        Args:
            user_id: 用户ID
            poi_name: POI名称
            poi_type: POI类型
            location: 位置
            notes: 备注

        Returns:
            int: POI收藏ID
        """
        # 加密备注
        encrypted_notes = self.encryptor.encrypt(notes) if notes else None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           INSERT INTO poi_favorites
                               (user_id, poi_name, poi_type, location, notes)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (user_id, poi_name, poi_type, location, encrypted_notes))

            poi_id = cursor.lastrowid
            conn.commit()

            return poi_id

    def get_poi_favorites(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户POI收藏

        Args:
            user_id: 用户ID

        Returns:
            List[Dict]: POI收藏列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           SELECT *
                           FROM poi_favorites
                           WHERE user_id = ?
                           ORDER BY created_at DESC
                           ''', (user_id,))

            pois = []
            for row in cursor.fetchall():
                columns = [description[0] for description in cursor.description]
                poi = dict(zip(columns, row))

                # 解密备注
                if poi.get('notes'):
                    try:
                        poi['notes'] = self.encryptor.decrypt(poi['notes'])
                    except:
                        poi['notes'] = ''

                pois.append(poi)

            return pois

    def update_last_login(self, user_id: int):
        """更新最后登录时间

        Args:
            user_id: 用户ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                           UPDATE users
                           SET last_login = CURRENT_TIMESTAMP
                           WHERE user_id = ?
                           ''', (user_id,))
            conn.commit()

    def _hash_password(self, password: str) -> str:
        """简单密码哈希函数

        Args:
            password: 原始密码

        Returns:
            str: 哈希后的密码

        Note: 实际应用中应该使用bcrypt或argon2等安全哈希算法
        """
        # 简单示例，实际应用中使用安全哈希
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

    def close(self):
        """关闭数据库连接"""
        pass  # SQLite会自动管理连接


# 测试数据库功能
if __name__ == "__main__":
    db = DatabaseManager(":memory:")  # 使用内存数据库测试

    # 测试用户注册
    user_id = db.register_user("testuser", "password123", "test@example.com")
    print(f"注册用户ID: {user_id}")

    # 测试用户认证
    user = db.authenticate_user("testuser", "password123")
    print(f"认证用户: {user}")

    # 测试更新偏好设置
    db.update_user_preferences(user_id, {"voice": True, "theme": "dark"})

    # 测试保存路线历史
    route_data = {"path": ["A", "B", "C"], "distance": 15.5}
    db.save_route_history(user_id, "A", "C", route_data, 15.5, 30.0, "通畅")

    # 测试获取路线历史
    history = db.get_route_history(user_id)
    print(f"路线历史: {history}")

    # 测试POI收藏
    poi_id = db.add_poi_favorite(user_id, "中央公园", "公园", "40.7829,-73.9654", "周末好去处")
    print(f"POI收藏ID: {poi_id}")