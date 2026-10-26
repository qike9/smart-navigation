# gui/preferences_frame.py
import tkinter as tk
from tkinter import ttk


class PreferencesFrame:
    """偏好设置面板"""

    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.frame = None
        self.preference_vars = {}
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        self.frame = ttk.Frame(self.parent)

        # 标题
        title = ttk.Label(self.frame, text="偏好设置",
                          font=('微软雅黑', 16, 'bold'))
        title.pack(pady=10)

        # 设置表单容器
        form_frame = ttk.Frame(self.frame)
        form_frame.pack(padx=50, pady=20, fill=tk.BOTH, expand=True)

        # 设置选项
        settings = [
            ("语音导航", "voice_navigation", tk.BooleanVar(value=True)),
            ("实时交通", "consider_traffic", tk.BooleanVar(value=True)),
            ("自动重新规划", "auto_reroute", tk.BooleanVar(value=True)),
            ("夜间模式", "dark_mode", tk.BooleanVar(value=False)),
            ("地图类型", "map_type", tk.StringVar(value="standard"))
        ]

        for i, (label_text, var_name, var) in enumerate(settings):
            self.preference_vars[var_name] = var

            if isinstance(var, tk.BooleanVar):
                check = ttk.Checkbutton(form_frame, text=label_text, variable=var)
                check.grid(row=i, column=0, padx=10, pady=10, sticky=tk.W)
            elif isinstance(var, tk.StringVar):
                ttk.Label(form_frame, text=label_text).grid(
                    row=i, column=0, padx=10, pady=10, sticky=tk.W
                )

                # 下拉选择
                if var_name == "map_type":
                    map_types = ["标准", "卫星", "地形", "混合"]
                    combo = ttk.Combobox(form_frame, textvariable=var,
                                         values=map_types, state="readonly",
                                         width=15)
                    combo.grid(row=i, column=1, padx=10, pady=10)

        # 按钮框架
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=len(settings), column=0, columnspan=2, pady=30)

        # 保存按钮
        save_btn = ttk.Button(button_frame, text="保存设置",
                              command=self.on_save,
                              style='Primary.TButton')
        save_btn.pack(side=tk.LEFT, padx=10)

        # 重置按钮
        reset_btn = ttk.Button(button_frame, text="重置",
                               command=self.on_reset)
        reset_btn.pack(side=tk.LEFT, padx=10)

    def on_save(self):
        """保存偏好设置"""
        preferences = {}
        for var_name, var in self.preference_vars.items():
            preferences[var_name] = var.get()

        self.controller.save_preferences(preferences)

    def on_reset(self):
        """重置偏好设置"""
        self.preference_vars['voice_navigation'].set(True)
        self.preference_vars['consider_traffic'].set(True)
        self.preference_vars['auto_reroute'].set(True)
        self.preference_vars['dark_mode'].set(False)
        self.preference_vars['map_type'].set("标准")

        self.controller.reset_preferences()

    def load_preferences(self, preferences):
        """加载偏好设置"""
        for var_name, value in preferences.items():
            if var_name in self.preference_vars:
                var = self.preference_vars[var_name]
                if isinstance(var, tk.BooleanVar):
                    var.set(bool(value))
                elif isinstance(var, tk.StringVar):
                    var.set(str(value))