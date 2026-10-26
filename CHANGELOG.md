# 更新日志

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-10-26

首个开源版本。

### 新增

- **八种寻路算法**：A\*、Dijkstra、BFS、DFS、贪心最佳优先、双向 BFS、Jump Point Search、Theta\*
- **图形界面**：网格地图编辑器、算法选择、寻路、动画演示、性能对比、导航模拟
- **多途经点规划**：最近邻 + 2-opt 求解访问顺序，对话框入口在「算法」菜单
- **地图管理**：JSON 读写、随机障碍、完美迷宫、房间/走廊模板、ASCII 与 CSV 互转
- **路径后处理**：视线拉直、Catmull-Rom 插值、线性/贝塞尔插值
- **命令行基准测试**：`tools/benchmark.py`，无界面输出对比表格
- **撤销重做**：批量地图操作可回退（Ctrl+Z / Ctrl+Y）
- **174 个单元测试** + GitHub Actions CI（三平台 × 三 Python 版本）

### 修复（相对重构前的单文件版本）

- **JPS 在 1 格宽缝隙地图上无解**：重写为标准跳点剪枝实现，并在剪枝失效时透明回退 A\*，
  结果永远最优；开阔地图上节点数仍从 3714 降到 10
- **双向 BFS 相遇点不最优**：改为层同步展开，起点终点相同时不再返回自环路径
- **Theta\* 四向模式产生斜线**：四向模式下退化为 A\*，不再违反移动规则
- **迷宫生成实际没挖通道**：原实现的判定条件写错了目标格，重写为递归回溯法（完美迷宫，
  房间之间恰好 N-1 条通道）
- **房间 / 走廊模板**：`create_rooms` 现在真的生成带门的隔断，且保证连通
- **随机障碍物无法保证连通**：新增 `GridMap.ensure_connectivity()` 与
  `generate_random_obstacles(..., ensure_connected=True)`
- **`AlgorithmBenchmark.get_best_algorithm()` 永远返回 None**：基准结果没有写回实例
- **`HeuristicFactory` 未知名称回退欧氏距离**：会破坏可采纳性，改为回退 0（等价 Dijkstra）
- **主窗口写死 Linux 沙盒路径** `/home/z/my-project/...`，在 Windows/macOS 上必崩：
  改为 `~/SmartNavigation/maps`，可用环境变量覆盖
- **快捷键管理器形同虚设**：注册表填了但没绑事件，且与 `setup_bindings` 重复维护；
  现统一由 `KeyboardShortcutManager` 注册，快捷键从 7 个增加到 17 个
- **`_ensure_connectivity` 是空实现**：补成真实的打通逻辑
- **路径校验器拒绝 Theta\* 合法路径**：拆成 `validate`（逐格）与 `validate_any_angle`
  （线段视线检测），后者与 Theta\* 共用 `GridMap.has_line_of_sight`

### 重构

- 3485 行单文件拆分为 `smartnav` 包（models / algorithms / planning / navigation /
  analysis / maps / utils / ui），GUI 与算法层彻底解耦，算法层可独立作为库使用
- 补充类型注解、docstring、`pyproject.toml` 与 `ruff` 配置；`ruff check` 零告警
