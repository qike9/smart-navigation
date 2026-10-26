# gui/register_frame.py
import tkinter as tk
from tkinter import ttk, messagebox


class RegisterFrame:
    """注册面板"""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.frame = None
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        self.frame = ttk.Frame(self.parent)

        # 标题
        title = ttk.Label(self.frame, text="用户注册",
                          font=('微软雅黑', 16, 'bold'))
        title.pack(pady=20)

        # 表单容器
        form_frame = ttk.Frame(self.frame)
        form_frame.pack(padx=50, pady=20)

        # 表单字段
        self.entries = {}
        fields = [
            ("用户名:", "username"),
            ("密码:", "password", True),
            ("确认密码:", "confirm_password", True),
            ("邮箱:", "email"),
            ("电话:", "phone")
        ]

        for i, (label_text, field_name, *args) in enumerate(fields):
            show_asterisk = args and args[0]

            ttk.Label(form_frame, text=label_text).grid(
                row=i, column=0, padx=10, pady=10, sticky=tk.W
            )

            entry = ttk.Entry(form_frame, width=30,
                              show="*" if show_asterisk else "")
            entry.grid(row=i, column=1, padx=10, pady=10)
            self.entries[field_name] = entry

        # 按钮框架
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=30)

        # 注册按钮
        register_btn = ttk.Button(button_frame, text="注册",
                                  command=self.on_register,
                                  style='Primary.TButton')
        register_btn.pack(side=tk.LEFT, padx=10)

        # 返回登录按钮
        back_btn = ttk.Button(button_frame, text="返回登录",
                              command=self.on_back)
        back_btn.pack(side=tk.LEFT, padx=10)

    def on_register(self):
        """处理注册"""
        data = {name: widget.get() for name, widget in self.entries.items()}

        # 验证
        if not data['username'] or not data['password']:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        if data['password'] != data['confirm_password']:
            messagebox.showerror("错误", "两次输入的密码不一致")
            return

        self.controller.handle_register(self.entries)

    def on_back(self):
        """返回登录"""
        self.clear_fields()
        self.controller.show_login()

    def clear_fields(self):
        """清空输入字段"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)