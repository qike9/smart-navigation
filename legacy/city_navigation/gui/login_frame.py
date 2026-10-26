# gui/login_frame.py
import tkinter as tk
from tkinter import ttk


class LoginFrame:
    """登录面板"""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.frame = None
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        self.frame = ttk.Frame(self.parent)

        # 标题
        title = ttk.Label(self.frame, text="用户登录",
                          font=('微软雅黑', 16, 'bold'))
        title.pack(pady=20)

        # 表单容器
        form_frame = ttk.Frame(self.frame)
        form_frame.pack(padx=50, pady=20)

        # 用户名
        ttk.Label(form_frame, text="用户名:").grid(row=0, column=0, padx=10, pady=15, sticky=tk.W)
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=10, pady=15)

        # 密码
        ttk.Label(form_frame, text="密码:").grid(row=1, column=0, padx=10, pady=15, sticky=tk.W)
        self.password_entry = ttk.Entry(form_frame, width=30, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=15)

        # 按钮框架
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=30)

        # 登录按钮
        login_btn = ttk.Button(button_frame, text="登录",
                               command=self.on_login,
                               style='Primary.TButton')
        login_btn.pack(side=tk.LEFT, padx=10)

        # 注册按钮
        register_btn = ttk.Button(button_frame, text="注册",
                                  command=self.on_register)
        register_btn.pack(side=tk.LEFT, padx=10)

        # 绑定回车键
        self.password_entry.bind('<Return>', lambda e: self.on_login())

    def on_login(self):
        """处理登录"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.controller.handle_login(username, password)

    def on_register(self):
        """跳转到注册"""
        self.controller.show_register()

    def clear_fields(self):
        """清空输入字段"""
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)