# legacy / city_navigation —— 早期"城市路网导航"版本（仅归档）

## 这是什么

本目录保留了项目早期另一套实现：一个**面向城市路网**的导航系统，和当前主程序
（网格寻路可视化）不是同一套代码，也不参与主程序的构建、测试与发布。

保留它的原因只有一个：**留档**。里面有一些还挺有用的思路，可以当参考实现翻看。

## 与主程序的区别

| 维度 | 主程序 `smartnav/` | 本目录 legacy |
| --- | --- | --- |
| 地图 | 二维网格（可编辑障碍物） | 城市节点 + 道路边（邻接表） |
| 功能 | 八种算法、动画、性能对比 | 用户注册登录、路线历史、POI 收藏、偏好设置 |
| 存储 | JSON 地图文件 | SQLite（`data/navigation.db`，含字段级加密） |
| 算法 | A\*/Dijkstra/BFS/DFS/贪心/双向BFS/JPS/Theta\* | 改进 Dijkstra（含交通拥堵因子） |
| 依赖 | **无**（纯标准库） | pycryptodome、cryptography、sqlalchemy、python-dotenv |
| 状态 | 持续维护 | 归档，不再更新 |

## 目录结构

```
legacy/city_navigation/
├── main.py                 # 命令行入口（菜单式交互）
├── main_gui.py             # 早期 Tkinter 多窗口界面
├── config.py               # 配置（数据库路径、加密密钥、地图数据）
├── core/
│   ├── user_management.py  # 注册 / 登录 / 偏好
│   ├── path_planning.py    # 改进 Dijkstra + 多路线对比
│   └── real_time_navigation.py  # 实时导航、语音播报、动态改道
├── data/
│   ├── database.py         # SQLite 封装（用户、历史、收藏）
│   └── data_encryption.py  # AES 字段加密
└── gui/                    # 登录 / 注册 / 规划 / 导航 / 偏好 五个窗口
```

## 运行（不推荐，仅为了能跑起来）

```bash
cd legacy/city_navigation
pip install pycryptodome cryptography sqlalchemy python-dotenv
python main.py        # 命令行版
python main_gui.py    # 图形版
```

## 如需继续使用，建议这样改造

1. `core/path_planning.py` 里的交通拥堵模型其实可以反向移植到主程序——把
   `GridMap.get_movement_cost` 扩展成"按格子附加权重"，主程序就支持了加权地形；
2. SQLite 用户体系与主程序无关，若不需要多用户，可以整个丢掉；
3. AES 加密依赖 `Crypto`，要保留就得接受这条第三方依赖；纯标准库替代方案是
   `hashlib.scrypt` 做口令哈希（不落库明文即可）。

## 注意

- 该目录**不参与** CI、pytest 与 `ruff` 检查；
- `data/navigation.db` 未纳入版本库（含用户数据，已在 `.gitignore` 中排除）；
- 代码保留原样，未做任何重构，可能存在与主程序不一致的命名与风格。
