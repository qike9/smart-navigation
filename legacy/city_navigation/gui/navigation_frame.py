# gui/navigation_frame.py
import tkinter as tk
from tkinter import ttk, scrolledtext


class NavigationFrame:
    """实时导航面板"""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.frame = None
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        self.frame = ttk.Frame(self.parent)

        # 标题
        title = ttk.Label(self.frame, text="实时导航",
                          font=('微软雅黑', 16, 'bold'))
        title.pack(pady=10)

        # 导航控制面板
        nav_control_frame = ttk.Frame(self.frame)
        nav_control_frame.pack(padx=10, pady=10, fill=tk.X)

        # 起点输入
        ttk.Label(nav_control_frame, text="起点:").grid(row=0, column=0, padx=5, pady=10)
        self.start_entry = ttk.Entry(nav_control_frame, width=20)
        self.start_entry.grid(row=0, column=1, padx=5, pady=10)

        # 终点输入
        ttk.Label(nav_control_frame, text="终点:").grid(row=0, column=2, padx=5, pady=10)
        self.end_entry = ttk.Entry(nav_control_frame, width=20)
        self.end_entry.grid(row=0, column=3, padx=5, pady=10)

        # 导航控制按钮
        self.start_btn = ttk.Button(nav_control_frame, text="开始导航",
                                    command=self.on_start_navigation,
                                    style='Success.TButton')
        self.start_btn.grid(row=0, column=4, padx=5, pady=10)

        self.stop_btn = ttk.Button(nav_control_frame, text="停止导航",
                                   command=self.on_stop_navigation,
                                   style='Danger.TButton',
                                   state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=5, padx=5, pady=10)

        # 语音开关
        self.voice_var = tk.BooleanVar(value=True)
        voice_check = ttk.Checkbutton(nav_control_frame, text="语音播报",
                                      variable=self.voice_var,
                                      command=self.on_toggle_voice)
        voice_check.grid(row=0, column=6, padx=10, pady=10)

        # 导航状态显示
        status_frame = ttk.LabelFrame(self.frame, text="导航状态", padding=10)
        status_frame.pack(padx=10, pady=5, fill=tk.X)

        # 状态信息文本框
        self.status_info = tk.Text(status_frame, height=4, font=('微软雅黑', 10))
        self.status_info.pack(fill=tk.X)

        # 进度条
        progress_frame = ttk.Frame(status_frame)
        progress_frame.pack(fill=tk.X, pady=5)

        ttk.Label(progress_frame, text="进度:").pack(side=tk.LEFT)
        self.progress_bar = ttk.Progressbar(progress_frame, length=300, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 指令显示区域
        instruction_frame = ttk.LabelFrame(self.frame, text="导航指令", padding=10)
        instruction_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.instruction_text = scrolledtext.ScrolledText(instruction_frame,
                                                          height=8,
                                                          font=('微软雅黑', 11))
        self.instruction_text.pack(fill=tk.BOTH, expand=True)

        # 交通信息显示
        traffic_frame = ttk.LabelFrame(self.frame, text="实时交通", padding=10)
        traffic_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        self.traffic_text = tk.Text(traffic_frame, height=4, font=('Consolas', 9))
        self.traffic_text.pack(fill=tk.BOTH, expand=True)

    def on_start_navigation(self):
        """开始导航"""
        start = self.start_entry.get()
        end = self.end_entry.get()
        self.controller.handle_start_navigation(start, end)

    def on_stop_navigation(self):
        """停止导航"""
        self.controller.handle_stop_navigation()

    def on_toggle_voice(self):
        """切换语音播报"""
        enabled = self.voice_var.get()
        self.controller.toggle_voice(enabled)

    def update_navigation_status(self, status):
        """更新导航状态"""
        self.status_info.delete(1.0, tk.END)

        if status["is_navigating"]:
            status_text = f"导航进行中 - {status['progress']}%\n"
            status_text += f"当前位置: {status['current_location']}\n"
            status_text += f"下一位置: {status['next_location']}\n"
            status_text += f"剩余距离: {status['remaining_distance']}km\n"
            status_text += f"预计到达: {status['estimated_arrival'].strftime('%H:%M')}"

            # 更新进度条
            self.progress_bar['value'] = status["progress"]
        else:
            status_text = "未在导航"
            self.progress_bar['value'] = 0

        self.status_info.insert(tk.END, status_text)

    def add_instruction(self, instruction):
        """添加导航指令"""
        self.instruction_text.insert(tk.END, instruction + "\n")
        self.instruction_text.see(tk.END)

    def update_traffic_info(self, info):
        """更新交通信息"""
        self.traffic_text.delete(1.0, tk.END)
        self.traffic_text.insert(tk.END, info)

    def set_navigation_controls(self, navigating):
        """设置导航控制按钮状态"""
        if navigating:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def clear_all(self):
        """清空所有显示"""
        self.status_info.delete(1.0, tk.END)
        self.instruction_text.delete(1.0, tk.END)
        self.traffic_text.delete(1.0, tk.END)
        self.progress_bar['value'] = 0