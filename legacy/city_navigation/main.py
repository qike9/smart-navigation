# main.py
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from core.user_management import UserManager
from core.path_planning import PathPlanner
from core.real_time_navigation import RealTimeNavigator
from data.database import DatabaseManager
import config


class SmartNavigationSystem:
    """智能导航系统主类"""

    def __init__(self):
        """初始化导航系统"""
        print("=" * 50)
        print("智能导航系统 v1.0")
        print("=" * 50)

        # 初始化组件
        self.db = DatabaseManager()
        self.user_manager = UserManager(self.db)
        self.path_planner = PathPlanner(self.user_manager)
        self.navigator = RealTimeNavigator(self.path_planner)

        self.running = True

    def run(self):
        """运行导航系统"""
        while self.running:
            self.show_main_menu()
            choice = input("请选择操作 (1-8): ").strip()

            if choice == "1":
                self.register_user()
            elif choice == "2":
                self.login_user()
            elif choice == "3":
                self.plan_route()
            elif choice == "4":
                self.start_navigation()
            elif choice == "5":
                self.view_route_history()
            elif choice == "6":
                self.view_poi_favorites()
            elif choice == "7":
                self.update_preferences()
            elif choice == "8":
                self.exit_system()
            else:
                print("无效选择，请重新输入")

            print()  # 空行

    def show_main_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 30)
        print("主菜单")
        print("=" * 30)

        if self.user_manager.is_logged_in():
            user_info = self.user_manager.get_user_info()
            if user_info["success"]:
                user = user_info["user"]
                print(f"当前用户: {user['username']} (ID: {user['user_id']})")

        print("1. 用户注册")
        print("2. 用户登录")
        print("3. 路径规划")
        print("4. 实时导航")
        print("5. 路线历史")
        print("6. POI收藏")
        print("7. 偏好设置")
        print("8. 退出系统")

    def register_user(self):
        """用户注册"""
        print("\n" + "-" * 20)
        print("用户注册")
        print("-" * 20)

        username = input("请输入用户名: ").strip()
        password = input("请输入密码: ").strip()
        email = input("请输入邮箱 (可选): ").strip() or None
        phone = input("请输入电话 (可选): ").strip() or None

        result = self.user_manager.register(username, password, email=email, phone=phone)

        if result["success"]:
            print(f"✓ 注册成功！用户ID: {result['user_id']}")
        else:
            print(f"✗ 注册失败: {result['message']}")

    def login_user(self):
        """用户登录"""
        print("\n" + "-" * 20)
        print("用户登录")
        print("-" * 20)

        if self.user_manager.is_logged_in():
            print("您已登录，请先登出")
            return

        username = input("请输入用户名: ").strip()
        password = input("请输入密码: ").strip()

        result = self.user_manager.login(username, password)

        if result["success"]:
            print(f"✓ 登录成功！欢迎 {result['user']['username']}")
        else:
            print(f"✗ 登录失败: {result['message']}")

    def plan_route(self):
        """路径规划"""
        print("\n" + "-" * 20)
        print("路径规划")
        print("-" * 20)

        if not self.user_manager.is_logged_in():
            print("请先登录以使用路径规划功能")
            return

        # 显示可用节点
        map_data = config.Config.get_map_data()
        print(f"可用位置: {', '.join(map_data.keys())}")

        start = input("请输入起点: ").strip().upper()
        end = input("请输入终点: ").strip().upper()

        if start not in map_data:
            print(f"错误: 起点 '{start}' 不存在")
            return
        if end not in map_data:
            print(f"错误: 终点 '{end}' 不存在")
            return

        print("\n正在规划路线...")
        result = self.path_planner.plan_route(start, end)

        if result["success"]:
            print(f"✓ 找到 {len(result['routes'])} 条路线:")

            for i, route in enumerate(result["routes"], 1):
                print(f"\n路线 {i}:")
                print(f"  路径: {' → '.join(route.nodes)}")
                print(f"  距离: {route.distance} 公里")
                print(f"  时间: {route.duration} 分钟")
                print(f"  交通: {route.traffic_level}")

            # 显示推荐路线
            comparison = result["comparison"]
            if comparison["success"]:
                print(f"\n⭐ 推荐路线: {' → '.join(comparison['recommended']['route'])}")
                print(f"  距离: {comparison['recommended']['distance']}km")
                print(f"  时间: {comparison['recommended']['duration']}min")
                print(f"  交通: {comparison['recommended']['traffic']}")
        else:
            print(f"✗ 路径规划失败: {result['message']}")

    def start_navigation(self):
        """开始实时导航"""
        print("\n" + "-" * 20)
        print("实时导航")
        print("-" * 20)

        if not self.user_manager.is_logged_in():
            print("请先登录以使用导航功能")
            return

        # 显示可用节点
        map_data = config.Config.get_map_data()
        print(f"可用位置: {', '.join(map_data.keys())}")

        start = input("请输入起点: ").strip().upper()
        end = input("请输入终点: ").strip().upper()

        if start not in map_data:
            print(f"错误: 起点 '{start}' 不存在")
            return
        if end not in map_data:
            print(f"错误: 终点 '{end}' 不存在")
            return

        print("\n正在启动导航...")

        # 先规划路线
        result = self.path_planner.plan_route(start, end)
        if not result["success"]:
            print(f"✗ 无法规划路线: {result['message']}")
            return

        # 使用第一条路线开始导航
        route = result["routes"][0]

        # 设置导航回调
        def on_step_change(step):
            print(f"\n[导航] {step.instruction}")
            print(f"      距离下一站: {step.distance_to_next}km")
            print(f"      预计时间: {step.estimated_time:.1f}min")
            print(f"      交通: {step.traffic_info['traffic_level']}")

        def on_arrival(data):
            print(f"\n🎉 已到达目的地: {data['destination']}")
            print(f"   总距离: {data['total_distance']}km")
            print(f"   总时间: {data['total_duration']}min")

        self.navigator.register_callback('on_step_change', on_step_change)
        self.navigator.register_callback('on_arrival', on_arrival)

        # 开始导航
        result = self.navigator.start_navigation(start, end, route)

        if result["success"]:
            print(f"✓ 导航已开始")
            print(f"路线: {' → '.join(route.nodes)}")
            print(f"总距离: {route.distance}km, 预计时间: {route.duration}min")

            # 模拟导航过程
            print("\n导航进行中... (按Enter键停止)")

            # 在新的线程中等待用户输入
            import threading
            stop_event = threading.Event()

            def wait_for_stop():
                input()  # 等待用户按Enter
                stop_event.set()

            stop_thread = threading.Thread(target=wait_for_stop, daemon=True)
            stop_thread.start()

            # 监控导航状态
            while not stop_event.is_set() and self.navigator.is_navigating:
                status = self.navigator.get_navigation_status()
                if status["is_navigating"]:
                    print(f"\r进度: {status['progress']}% | "
                          f"当前位置: {status['current_location']} | "
                          f"剩余距离: {status['remaining_distance']}km", end="")
                    time.sleep(1)
                else:
                    break

            # 停止导航
            self.navigator.stop_navigation()
            print("\n\n导航已停止")
        else:
            print(f"✗ 导航启动失败: {result['message']}")

    def view_route_history(self):
        """查看路线历史"""
        print("\n" + "-" * 20)
        print("路线历史")
        print("-" * 20)

        if not self.user_manager.is_logged_in():
            print("请先登录以查看路线历史")
            return

        user_id = self.user_manager.get_user_id()
        history = self.db.get_route_history(user_id)

        if not history:
            print("暂无路线历史")
            return

        print(f"找到 {len(history)} 条历史记录:")
        print("-" * 60)

        for i, record in enumerate(history, 1):
            print(f"\n记录 {i}:")
            print(f"  时间: {record['created_at']}")
            print(f"  路线: {record['start_location']} → {record['end_location']}")
            print(f"  距离: {record['distance']}km")
            print(f"  时间: {record['duration']}min")
            print(f"  交通: {record['traffic_level'] or '未知'}")

    def view_poi_favorites(self):
        """查看POI收藏"""
        print("\n" + "-" * 20)
        print("POI收藏")
        print("-" * 20)

        if not self.user_manager.is_logged_in():
            print("请先登录以查看POI收藏")
            return

        user_id = self.user_manager.get_user_id()
        pois = self.db.get_poi_favorites(user_id)

        if not pois:
            print("暂无POI收藏")
            return

        print(f"找到 {len(pois)} 个收藏点:")
        print("-" * 60)

        for i, poi in enumerate(pois, 1):
            print(f"\nPOI {i}:")
            print(f"  名称: {poi['poi_name']}")
            print(f"  类型: {poi['poi_type'] or '未分类'}")
            print(f"  位置: {poi['location'] or '未知'}")
            if poi.get('notes'):
                print(f"  备注: {poi['notes']}")
            print(f"  收藏时间: {poi['created_at']}")

        # 提供添加新POI的选项
        print("\n是否添加新POI? (y/n): ", end="")
        choice = input().strip().lower()

        if choice == 'y':
            self.add_poi_favorite()

    def add_poi_favorite(self):
        """添加POI收藏"""
        print("\n添加POI收藏:")

        poi_name = input("POI名称: ").strip()
        if not poi_name:
            print("POI名称不能为空")
            return

        poi_type = input("POI类型 (可选): ").strip() or None
        location = input("位置 (可选): ").strip() or None
        notes = input("备注 (可选): ").strip() or None

        user_id = self.user_manager.get_user_id()
        poi_id = self.db.add_poi_favorite(user_id, poi_name, poi_type, location, notes)

        print(f"✓ POI收藏添加成功! ID: {poi_id}")

    def update_preferences(self):
        """更新偏好设置"""
        print("\n" + "-" * 20)
        print("偏好设置")
        print("-" * 20)

        if not self.user_manager.is_logged_in():
            print("请先登录以设置偏好")
            return

        # 获取当前偏好
        current = self.user_manager.get_preferences()
        if current["success"]:
            print("当前偏好设置:")
            for key, value in current["preferences"].items():
                print(f"  {key}: {value}")
        else:
            print("无法获取当前偏好设置")

        print("\n设置选项:")
        print("1. 语音导航")
        print("2. 界面主题")
        print("3. 交通考虑")
        print("4. 其他设置")

        choice = input("请选择设置项 (1-4): ").strip()

        preferences = {}

        if choice == "1":
            voice = input("启用语音导航? (y/n): ").strip().lower()
            preferences["voice_navigation"] = (voice == 'y')
        elif choice == "2":
            theme = input("界面主题 (light/dark): ").strip().lower()
            if theme in ["light", "dark"]:
                preferences["theme"] = theme
        elif choice == "3":
            traffic = input("考虑实时交通? (y/n): ").strip().lower()
            preferences["consider_traffic"] = (traffic == 'y')
        elif choice == "4":
            print("其他设置待实现")
            return
        else:
            print("无效选择")
            return

        # 更新偏好设置
        result = self.user_manager.update_preferences(preferences)

        if result["success"]:
            print("✓ 偏好设置已更新")
            print("新的偏好设置:")
            for key, value in result["preferences"].items():
                print(f"  {key}: {value}")
        else:
            print(f"✗ 更新失败: {result['message']}")

    def exit_system(self):
        """退出系统"""
        print("\n感谢使用智能导航系统，再见！")
        self.running = False


def main():
    """主函数"""
    try:
        system = SmartNavigationSystem()
        system.run()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()