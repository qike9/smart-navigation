# main_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path
import threading

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from core.user_management import UserManager
from core.path_planning import PathPlanner
from core.real_time_navigation import RealTimeNavigator
from data.database import DatabaseManager
import config

# 导入GUI模块
from gui.login_frame import LoginFrame
from gui.register_frame import RegisterFrame
from gui.navigation_frame import NavigationFrame
from gui.planning_frame import PlanningFrame
from gui.preferences_frame import PreferencesFrame


class SmartNavigationGUI:
    """智能导航系统GUI主类"""

    def __init__(self):
        """初始化GUI"""
        self.root = tk.Tk()
        self.root.title("智能导航系统 v1.0")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)

        # 设置窗口图标
        try:
            self.root.iconbitmap("assets/icons/app.ico")
        except:
            pass

        # 初始化系统组件
        self.db = DatabaseManager()
        self.user_manager = UserManager(self.db)
        self.path_planner = PathPlanner(self.user_manager)
        self.navigator = RealTimeNavigator(self.path_planner)

        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # 配置样式
        self.configure_styles()

        # 创建主容器
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 状态栏
        self.setup_status_bar()

        # 创建菜单
        self.setup_menu()

        # 创建GUI框架
        self.frames = {}
        self.create_frames()

        # 显示登录界面
        self.show_login()

    def configure_styles(self):
        """配置GUI样式"""
        # 主要颜色
        self.colors = {
            'primary': '#3498db',
            'success': '#2ecc71',
            'danger': '#e74c3c',
            'warning': '#f39c12'
        }

        # 配置按钮样式
        self.style.configure('Primary.TButton',
                             background=self.colors['primary'],
                             foreground='white',
                             font=('微软雅黑', 10, 'bold'))

        self.style.configure('Success.TButton',
                             background=self.colors['success'],
                             foreground='white',
                             font=('微软雅黑', 10, 'bold'))

        self.style.configure('Danger.TButton',
                             background=self.colors['danger'],
                             foreground='white',
                             font=('微软雅黑', 10, 'bold'))

    def setup_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 状态标签
        self.status_label = ttk.Label(self.status_bar, text="就绪")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # 用户状态
        self.user_status_label = ttk.Label(self.status_bar, text="未登录")
        self.user_status_label.pack(side=tk.RIGHT, padx=10)

        # 进度条
        self.progress_bar = ttk.Progressbar(self.status_bar, mode='indeterminate')

    def setup_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.on_exit)

        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="路径规划", command=self.show_planning)
        view_menu.add_command(label="实时导航", command=self.show_navigation)
        view_menu.add_command(label="路线历史", command=self.show_history)
        view_menu.add_separator()
        view_menu.add_command(label="偏好设置", command=self.show_preferences)

        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="交通信息", command=self.show_traffic_info)
        tools_menu.add_command(label="地图查看", command=self.show_map)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)

    def create_frames(self):
        """创建所有GUI框架"""
        # 登录框架
        self.frames['login'] = LoginFrame(self.main_container, self)
        self.frames['login'].frame.pack(fill=tk.BOTH, expand=True)

        # 注册框架
        self.frames['register'] = RegisterFrame(self.main_container, self)
        self.frames['register'].frame.pack_forget()  # 先隐藏

        # 路径规划框架
        self.frames['planning'] = PlanningFrame(self.main_container, self)
        self.frames['planning'].frame.pack_forget()

        # 导航框架
        self.frames['navigation'] = NavigationFrame(self.main_container, self)
        self.frames['navigation'].frame.pack_forget()

        # 偏好设置框架
        self.frames['preferences'] = PreferencesFrame(self.main_container, self)
        self.frames['preferences'].frame.pack_forget()

    def show_frame(self, frame_name):
        """显示指定框架"""
        # 隐藏所有框架
        for name, frame_obj in self.frames.items():
            frame_obj.frame.pack_forget()

        # 显示指定框架
        if frame_name in self.frames:
            self.frames[frame_name].frame.pack(fill=tk.BOTH, expand=True)

    def show_login(self):
        """显示登录界面"""
        self.show_frame('login')
        self.update_status("请登录或注册")

    def show_register(self):
        """显示注册界面"""
        self.show_frame('register')
        self.update_status("用户注册")

    def show_planning(self):
        """显示路径规划界面"""
        if not self.user_manager.is_logged_in():
            messagebox.showwarning("需要登录", "请先登录以使用路径规划功能")
            self.show_login()
            return

        self.show_frame('planning')
        self.update_status("路径规划模式")

    def show_navigation(self):
        """显示实时导航界面"""
        if not self.user_manager.is_logged_in():
            messagebox.showwarning("需要登录", "请先登录以使用导航功能")
            self.show_login()
            return

        self.show_frame('navigation')
        self.update_status("导航模式")

    def show_preferences(self):
        """显示偏好设置界面"""
        if not self.user_manager.is_logged_in():
            messagebox.showwarning("需要登录", "请先登录以设置偏好")
            self.show_login()
            return

        # 加载当前用户的偏好设置
        result = self.user_manager.get_preferences()
        if result["success"]:
            self.frames['preferences'].load_preferences(result["preferences"])

        self.show_frame('preferences')
        self.update_status("偏好设置")

    def show_history(self):
        """显示路线历史"""
        if not self.user_manager.is_logged_in():
            messagebox.showwarning("需要登录", "请先登录以查看历史")
            self.show_login()
            return

        # 获取历史数据
        user_id = self.user_manager.get_user_id()
        history = self.db.get_route_history(user_id, limit=20)

        # 创建历史窗口
        history_window = tk.Toplevel(self.root)
        history_window.title("路线历史")
        history_window.geometry("600x400")

        # 创建Treeview显示历史
        tree = ttk.Treeview(history_window,
                            columns=("时间", "起点", "终点", "距离", "用时"),
                            show="headings")

        tree.heading("时间", text="时间")
        tree.heading("起点", text="起点")
        tree.heading("终点", text="终点")
        tree.heading("距离", text="距离(km)")
        tree.heading("用时", text="用时(min)")

        tree.column("时间", width=150)
        tree.column("起点", width=100)
        tree.column("终点", width=100)
        tree.column("距离", width=80)
        tree.column("用时", width=80)

        # 添加数据
        for record in history:
            tree.insert("", tk.END, values=(
                record['created_at'],
                record['start_location'],
                record['end_location'],
                record['distance'],
                record['duration']
            ))

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(history_window,
                                  orient=tk.VERTICAL,
                                  command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def show_traffic_info(self):
        """显示交通信息"""
        result = self.path_planner.get_traffic_info()

        if not result["success"]:
            messagebox.showerror("错误", result["message"])
            return

        # 创建交通信息窗口
        traffic_window = tk.Toplevel(self.root)
        traffic_window.title("交通信息")
        traffic_window.geometry("500x300")

        text = tk.Text(traffic_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        text.insert(tk.END, "实时交通信息:\n\n")

        if 'location' in result:
            text.insert(tk.END, f"位置: {result['location']}\n\n")
            for neighbor, info in result['traffic'].items():
                text.insert(tk.END, f"→ {neighbor}: {info['level']}\n")
        else:
            text.insert(tk.END, f"监控路段: {result['total_edges']}条\n\n")

            # 统计交通状况
            traffic_counts = {}
            for edge, weight in result['traffic_overview'].items():
                if weight <= 1.2:
                    level = "通畅"
                elif weight <= 1.6:
                    level = "缓行"
                elif weight <= 2.0:
                    level = "拥堵"
                else:
                    level = "严重拥堵"

                traffic_counts[level] = traffic_counts.get(level, 0) + 1

            for level, count in traffic_counts.items():
                text.insert(tk.END, f"{level}: {count}条\n")

        text.config(state=tk.DISABLED)

    def show_map(self):
        """显示地图"""
        map_data = config.Config.get_map_data()

        map_window = tk.Toplevel(self.root)
        map_window.title("地图查看")
        map_window.geometry("600x400")

        text = tk.Text(map_window, wrap=tk.NONE)
        text.pack(fill=tk.BOTH, expand=True)

        text.insert(tk.END, "智能导航系统地图\n")
        text.insert(tk.END, "=" * 30 + "\n\n")

        text.insert(tk.END, "节点列表:\n")
        for node in sorted(map_data.keys()):
            text.insert(tk.END, f"  {node}\n")

        text.insert(tk.END, "\n连接关系:\n")
        for node, connections in map_data.items():
            text.insert(tk.END, f"\n{node} 连接至:\n")
            for neighbor, distance in connections.items():
                text.insert(tk.END, f"  → {neighbor} ({distance}km)\n")

        text.config(state=tk.DISABLED)

    def show_help(self):
        """显示帮助"""
        help_text = """
智能导航系统使用说明:

1. 用户管理
   - 首次使用请先注册账号
   - 注册后使用用户名密码登录

2. 路径规划
   - 输入起点和终点位置
   - 系统将显示多条可行路线
   - 选择最适合的路线

3. 实时导航
   - 规划路线后可以开始导航
   - 系统提供语音和文字导航指令
   - 实时显示交通状况
   - 自动重新规划避开拥堵

4. 偏好设置
   - 设置语音播报开关
   - 选择是否考虑实时交通
   - 配置界面主题

可用位置: A, B, C, D, E, F
        """

        messagebox.showinfo("使用说明", help_text)

    def show_about(self):
        """显示关于信息"""
        about_text = """
智能导航系统 v1.0

功能:
- 用户注册与登录
- 智能路径规划
- 实时导航
- 交通状况监控
- 路线历史记录

技术特点:
- 改进的Dijkstra算法
- 实时交通模拟
- 动态路线重新规划
- 数据加密存储
- 多路线对比

开发团队: 智能导航系统开发组
        """

        messagebox.showinfo("关于", about_text)

    def handle_login(self, username, password):
        """处理登录"""
        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        self.show_progress("正在登录...")

        def login_thread():
            result = self.user_manager.login(username, password)
            self.root.after(0, lambda: self.on_login_complete(result))

        threading.Thread(target=login_thread, daemon=True).start()

    def on_login_complete(self, result):
        """登录完成处理"""
        self.hide_progress()

        if result["success"]:
            messagebox.showinfo("成功", result["message"])

            # 更新用户状态
            self.update_user_status(result["user"]["username"])

            # 显示主功能面板
            self.show_planning()
        else:
            messagebox.showerror("登录失败", result["message"])

    def handle_register(self, entries):
        """处理注册"""
        data = {name: widget.get() for name, widget in entries.items()}

        # 验证
        if not data['username'] or not data['password']:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        if data['password'] != data['confirm_password']:
            messagebox.showerror("错误", "两次输入的密码不一致")
            return

        self.show_progress("正在注册...")

        def register_thread():
            result = self.user_manager.register(
                data['username'],
                data['password'],
                email=data.get('email'),
                phone=data.get('phone')
            )

            self.root.after(0, lambda: self.on_register_complete(result))

        threading.Thread(target=register_thread, daemon=True).start()

    def on_register_complete(self, result):
        """注册完成处理"""
        self.hide_progress()

        if result["success"]:
            messagebox.showinfo("成功", result["message"])
            self.show_login()
        else:
            messagebox.showerror("注册失败", result["message"])

    def handle_plan_route(self, start, end):
        """处理路径规划"""
        if not start or not end:
            messagebox.showerror("错误", "请输入起点和终点")
            return

        start = start.upper()
        end = end.upper()

        map_data = config.Config.get_map_data()
        if start not in map_data:
            messagebox.showerror("错误", f"起点 '{start}' 不存在")
            return
        if end not in map_data:
            messagebox.showerror("错误", f"终点 '{end}' 不存在")
            return

        self.show_progress("正在规划路线...")
        self.frames['planning'].set_planning_button_state(False)

        def plan_thread():
            result = self.path_planner.plan_route(start, end)
            self.root.after(0, lambda: self.on_plan_complete(result))

        threading.Thread(target=plan_thread, daemon=True).start()

    def on_plan_complete(self, result):
        """路径规划完成处理"""
        self.hide_progress()
        self.frames['planning'].set_planning_button_state(True)

        if not result["success"]:
            messagebox.showerror("规划失败", result["message"])
            return

        # 显示结果
        self.frames['planning'].display_results(result)
        messagebox.showinfo("成功", f"找到 {len(result['routes'])} 条路线")

    def handle_start_navigation(self, start, end):
        """开始导航"""
        if not start or not end:
            messagebox.showerror("错误", "请输入起点和终点")
            return

        start = start.upper()
        end = end.upper()

        map_data = config.Config.get_map_data()
        if start not in map_data or end not in map_data:
            messagebox.showerror("错误", "起点或终点无效")
            return

        # 设置语音
        voice_enabled = self.frames['navigation'].voice_var.get()
        self.navigator.toggle_voice(voice_enabled)

        self.show_progress("正在启动导航...")

        def plan_and_navigate():
            result = self.path_planner.plan_route(start, end)

            if not result["success"] or not result["routes"]:
                self.root.after(0, lambda: messagebox.showerror("错误", "无法规划路线"))
                self.root.after(0, self.hide_progress)
                return

            # 开始导航
            route = result["routes"][0]
            nav_result = self.navigator.start_navigation(start, end, route)

            self.root.after(0, lambda: self.on_navigation_start(nav_result, route))

        threading.Thread(target=plan_and_navigate, daemon=True).start()

    def on_navigation_start(self, result, route):
        """导航开始处理"""
        self.hide_progress()

        if not result["success"]:
            messagebox.showerror("导航失败", result["message"])
            return

        # 更新导航界面
        self.frames['navigation'].clear_all()
        self.frames['navigation'].set_navigation_controls(True)

        # 显示初始信息
        status_text = f"导航已开始\n路线: {' → '.join(route.nodes)}\n"
        status_text += f"总距离: {route.distance}km\n预计时间: {route.duration}min\n"
        self.frames['navigation'].add_instruction(status_text)

        # 注册回调
        self.navigator.register_callback('on_step_change', self.on_navigation_step)
        self.navigator.register_callback('on_reroute', self.on_navigation_reroute)
        self.navigator.register_callback('on_arrival', self.on_navigation_arrival)

        # 启动监控
        self.monitor_navigation()

        messagebox.showinfo("导航开始", "导航已开始，请查看导航指令")

    def handle_stop_navigation(self):
        """停止导航"""
        result = self.navigator.stop_navigation()

        self.frames['navigation'].set_navigation_controls(False)
        self.frames['navigation'].add_instruction("\n导航已停止")

        messagebox.showinfo("导航停止", "导航已停止")

    def toggle_voice(self, enabled):
        """切换语音播报"""
        self.navigator.toggle_voice(enabled)

        status = "启用" if enabled else "禁用"
        self.update_status(f"语音播报已{status}")

    def on_navigation_step(self, step):
        """处理导航步骤更新"""
        instruction = f"{step.instruction}\n"
        instruction += f"下一站: {step.next_location} | 距离: {step.distance_to_next}km | 预计: {step.estimated_time:.1f}min\n"
        instruction += f"交通: {step.traffic_info['traffic_level']} - {step.traffic_info['suggestion']}\n"
        instruction += "-" * 50 + "\n"

        self.frames['navigation'].add_instruction(instruction)

        # 更新交通信息
        traffic_text = f"当前路段: {step.current_location} → {step.next_location}\n"
        traffic_text += f"交通状况: {step.traffic_info['traffic_level']}\n"
        traffic_text += f"建议: {step.traffic_info['suggestion']}\n"

        self.frames['navigation'].update_traffic_info(traffic_text)

    def on_navigation_reroute(self, data):
        """处理重新规划路线"""
        warning = f"⚠  {data['reason']}\n"
        warning += f"新路线: {' → '.join(data['new_route'].nodes)}\n\n"

        self.frames['navigation'].add_instruction(warning)

        # 更新状态
        status_text = f"已重新规划路线\n新路线: {' → '.join(data['new_route'].nodes)}\n"
        status_text += f"总距离: {data['new_route'].distance}km\n"
        status_text += f"预计时间: {data['new_route'].duration}min\n"
        self.frames['navigation'].add_instruction(status_text)

    def on_navigation_arrival(self, data):
        """处理到达目的地"""
        arrival_msg = f"🎉 已到达目的地: {data['destination']}\n"
        arrival_msg += f"总行驶距离: {data['total_distance']}km\n"
        arrival_msg += f"总用时: {data['total_duration']}min\n"
        arrival_msg += f"到达时间: {data['arrival_time'].strftime('%H:%M:%S')}\n\n"

        self.frames['navigation'].add_instruction(arrival_msg)

        # 更新按钮状态
        self.frames['navigation'].set_navigation_controls(False)

        messagebox.showinfo("到达目的地", f"已安全到达 {data['destination']}")

    def monitor_navigation(self):
        """监控导航状态"""
        if not self.navigator.is_navigating:
            return

        # 获取当前状态
        status = self.navigator.get_navigation_status()

        if status["is_navigating"]:
            # 更新导航界面
            self.frames['navigation'].update_navigation_status(status)

            # 继续监控
            self.root.after(2000, self.monitor_navigation)

    def save_preferences(self, preferences):
        """保存偏好设置"""
        result = self.user_manager.update_preferences(preferences)

        if result["success"]:
            messagebox.showinfo("成功", "偏好设置已保存")
        else:
            messagebox.showerror("错误", f"保存失败: {result['message']}")

    def reset_preferences(self):
        """重置偏好设置"""
        messagebox.showinfo("重置", "已重置为默认设置")

    def update_user_status(self, username):
        """更新用户状态显示"""
        self.user_status_label.config(text=f"用户: {username}")

    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)

    def show_progress(self, message):
        """显示进度条"""
        self.update_status(message)
        self.progress_bar.pack(side=tk.RIGHT, padx=10)
        self.progress_bar.start()

    def hide_progress(self):
        """隐藏进度条"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.update_status("就绪")

    def on_exit(self):
        """退出程序"""
        if messagebox.askyesno("退出", "确定要退出智能导航系统吗？"):
            # 停止导航
            if self.navigator.is_navigating:
                self.navigator.stop_navigation()

            # 关闭数据库
            self.db.close()

            # 退出
            self.root.quit()
            self.root.destroy()

    def run(self):
        """运行GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.root.mainloop()


def main():
    """主函数"""
    try:
        app = SmartNavigationGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("启动错误", f"程序启动失败:\n{str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()