# core/user_management.py
from typing import Dict, Any, Optional
from data.database import DatabaseManager
from data.data_encryption import DataEncryptor
import config


class UserManager:
    """用户管理器"""

    def __init__(self, db_manager: DatabaseManager = None):
        """初始化用户管理器

        Args:
            db_manager: 数据库管理器
        """
        self.db = db_manager or DatabaseManager()
        self.current_user: Optional[Dict[str, Any]] = None

    def register(self, username: str, password: str, **kwargs) -> Dict[str, Any]:
        """用户注册

        Args:
            username: 用户名
            password: 密码
            **kwargs: 其他用户信息

        Returns:
            Dict: 注册结果
        """
        try:
            # 验证输入
            if not username or not password:
                return {"success": False, "message": "用户名和密码不能为空"}

            if len(password) < 6:
                return {"success": False, "message": "密码长度至少6位"}

            # 注册用户
            user_id = self.db.register_user(username, password, **kwargs)

            return {
                "success": True,
                "message": "注册成功",
                "user_id": user_id,
                "username": username
            }

        except ValueError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            return {"success": False, "message": f"注册失败: {str(e)}"}

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            Dict: 登录结果
        """
        try:
            # 验证输入
            if not username or not password:
                return {"success": False, "message": "用户名和密码不能为空"}

            # 认证用户
            user = self.db.authenticate_user(username, password)

            if user:
                self.current_user = user
                return {
                    "success": True,
                    "message": "登录成功",
                    "user": {
                        "user_id": user['user_id'],
                        "username": user['username'],
                        "email": user.get('email'),
                        "preferences": user.get('preferences', {})
                    }
                }
            else:
                return {"success": False, "message": "用户名或密码错误"}

        except Exception as e:
            return {"success": False, "message": f"登录失败: {str(e)}"}

    def logout(self):
        """用户登出"""
        self.current_user = None
        return {"success": True, "message": "已登出"}

    def update_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户偏好设置

        Args:
            preferences: 偏好设置字典

        Returns:
            Dict: 更新结果
        """
        if not self.current_user:
            return {"success": False, "message": "请先登录"}

        try:
            # 合并现有偏好
            current_prefs = self.current_user.get('preferences', {})
            current_prefs.update(preferences)

            # 更新到数据库
            self.db.update_user_preferences(self.current_user['user_id'], current_prefs)

            # 更新当前用户
            self.current_user['preferences'] = current_prefs

            return {
                "success": True,
                "message": "偏好设置已更新",
                "preferences": current_prefs
            }

        except Exception as e:
            return {"success": False, "message": f"更新失败: {str(e)}"}

    def get_preferences(self) -> Dict[str, Any]:
        """获取当前用户偏好设置

        Returns:
            Dict: 偏好设置
        """
        if not self.current_user:
            return {"success": False, "message": "请先登录"}

        return {
            "success": True,
            "preferences": self.current_user.get('preferences', {})
        }

    def get_user_info(self) -> Dict[str, Any]:
        """获取当前用户信息

        Returns:
            Dict: 用户信息
        """
        if not self.current_user:
            return {"success": False, "message": "请先登录"}

        return {
            "success": True,
            "user": {
                "user_id": self.current_user['user_id'],
                "username": self.current_user['username'],
                "email": self.current_user.get('email'),
                "phone": self.current_user.get('phone'),
                "created_at": self.current_user.get('created_at')
            }
        }

    def is_logged_in(self) -> bool:
        """检查是否已登录

        Returns:
            bool: 是否已登录
        """
        return self.current_user is not None

    def get_user_id(self) -> Optional[int]:
        """获取当前用户ID

        Returns:
            Optional[int]: 用户ID
        """
        return self.current_user['user_id'] if self.current_user else None


# 测试用户管理功能
if __name__ == "__main__":
    user_manager = UserManager()

    # 测试注册
    result = user_manager.register("alice", "password123", email="alice@example.com")
    print(f"注册结果: {result}")

    # 测试登录
    result = user_manager.login("alice", "password123")
    print(f"登录结果: {result}")

    # 测试偏好设置
    if user_manager.is_logged_in():
        result = user_manager.update_preferences({"voice": True, "theme": "dark"})
        print(f"更新偏好: {result}")

        result = user_manager.get_preferences()
        print(f"获取偏好: {result}")

        result = user_manager.get_user_info()
        print(f"用户信息: {result}")

    # 测试登出
    result = user_manager.logout()
    print(f"登出结果: {result}")