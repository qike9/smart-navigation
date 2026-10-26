# 贡献指南

感谢你愿意改进这个项目。以下约定可以让评审和合并更顺畅。

## 环境准备

```bash
git clone https://github.com/qike9/smart-navigation.git
cd smart-navigation
pip install -r requirements-dev.txt
python -m pytest tests/ -q      # 应全部通过
```

运行界面：`python smart_navigation.py`
跑基准：`python tools/benchmark.py`

## 开发约定

- **零运行时依赖**是硬约束：主程序只能使用 Python 标准库。需要第三方库的功能请做成可选
  （参考 `ExportManager.export_map_as_image` 对 Pillow 的处理：缺失时静默降级）。
- **算法层不得依赖 Tkinter**：`smartnav/` 顶层模块（models / algorithms / planning /
  navigation / analysis / maps / utils）必须能在无图形环境下导入，否则 CI 与库调用都会挂。
- 新增算法请继承 `PathfindingAlgorithm`、实现 `find_path`，并在 `AlgorithmFactory` 注册；
  同时补一条 `tests/test_algorithms.py` 的用例（至少覆盖：能出路径、路径合法、封闭地图
  正确返回失败）。
- 注释与文档用中文，变量名用英文；API 文档从简，讲清"为什么"比讲"是什么"更值钱。
- 提交前请自检：

  ```bash
  python -m pytest tests/ -q
  ruff check .
  python tools/benchmark.py --size 31 --repeat 1
  ```

## 分支与提交

- 分支命名：`feat/xxx`、`fix/xxx`、`docs/xxx`；
- 提交信息用中文或英文都可以，但要能说清"改了什么、为什么"，例如
  `fix(jps): 跳点搜索在 1 格缝隙地图上漏解，改为回退 A*`；
- 一个 PR 只做一件事，附带必要的测试。

## 报告问题

请提供：

1. 操作系统 + Python 版本（`python --version`）；
2. 复现步骤（用了哪个算法、地图怎么造的；能附地图 JSON 最好）；
3. 期望结果与实际结果；
4. 控制台报错信息（如有）。

## 行为准则

保持友善、就事论事。技术分歧用数据和可复现的例子说话，不针对个人。
