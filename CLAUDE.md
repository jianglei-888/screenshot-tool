# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目性质

Windows 桌面截图工具 MVP，对标微信截图核心体验。当前进度：T01-T07 已完成（7/18），阶段 3（UI 层）进行中。完整路线图见 `docs/architecture.md` §6 §7。

## 环境

- **路径**：`E:\cc操作库\my_code\screenshot-tool`（Windows 路径有空格，命令行必须用双引号）
- **Python**：3.11.8（虚拟环境 `.venv/`，不要用全局 Python——全局没装 PySide6）
- **核心依赖**：`PySide6 6.11` / `mss 10.2` / `Pillow 10+` / `keyboard 0.13` / `PyInstaller 6+` / `pytest 7+`
- **平台**：Windows 10/11（mss 用 GDI/DX；不能跨平台）

## 常用命令

所有命令用 `.venv/Scripts/python.exe`（不是 `python`/`python3`）。

```bash
# 安装依赖
.venv/Scripts/python.exe -m pip install -r requirements.txt

# 跑单测
.venv/Scripts/python.exe -m pytest tests/ -v
.venv/Scripts/python.exe -m pytest tests/test_selection.py -v           # 单文件
.venv/Scripts/python.exe -m pytest tests/test_selection.py::test_four_directions -v  # 单用例

# 跑手动验证脚本（按模块）
.venv/Scripts/python.exe scripts/verify_capture.py
.venv/Scripts/python.exe scripts/verify_clipboard.py
.venv/Scripts/python.exe scripts/verify_saver.py
.venv/Scripts/python.exe scripts/verify_overlay.py      # 会阻塞——人工按 ESC 关闭

# 跑脚本时加 -u 避免 stdout 缓冲看不到即时输出
.venv/Scripts/python.exe -u scripts/verify_overlay.py
```

## 项目约定（重要，不在 README 里写明）

### 测试分两类，不可混淆

- **`tests/`** 只放 pytest 单测，命名 `test_*.py`。**目前只有 `test_selection.py`**——它是唯一纯逻辑模块。I/O 模块（capture/clipboard/saver/overlay）**不写** pytest。
- **`scripts/`** 放手动验证脚本，命名 `verify_*.py`。`if __name__ == "__main__"` 入口，输出"几项断言通过"给人看，**不**用 `QTimer + sendEvent` 模拟键盘。
- PyInstaller 配置 `scripts/build.spec` 也在这个目录。

### T-编号任务系统

- 18 个 Task（T01-T18）严格顺序依赖，路线图在 `architecture.md` §6
- 每次只做一个 Task：先输出设计（不写代码）→ 用户确认 → 实现 → 验证 → 同步 README + architecture → 提交推送
- 不允许"提前实现 T08+"，每次对话只讨论当前 Task
- "Phase"（阶段）是 T 任务的分组：阶段 1 = 基础装配（T01-T02），阶段 2 = 核心能力（T03-T06），阶段 3 = UI 层（T07-T11），阶段 4 = 集成（T12-T14），阶段 5 = 稳健性（T15），阶段 6 = 交付（T16-T18）

### 模块架构原则（"不做什么"列表）

从 `architecture.md` 关键决策记录提炼：

- **不创建 Manager / Service / Controller / 状态机**。`OverlayWindow` 单类承担所有职责，后续 Task 通过加方法（`mousePressEvent` / `paintEvent` / `keyPressEvent`）扩展，**不**通过新增协调类
- **不引入配置文件**。`DEFAULT_HOTKEY` 在 `main.py`、`DEFAULT_SAVE_DIR` 在 `saver.py`、`FILENAME_TEMPLATE` 在 `saver.py`，改直接改源码
- **不创建 `pyproject.toml` / `assets/`**。MVP 阶段用 `requirements.txt` + 源码运行
- **selection 模块只做矩形规范化**，不裁剪屏幕、不做类型校验
- **overlay 覆盖虚拟屏**（`QScreen.virtualGeometry()`）而非主屏——和 `capture.py` 用 `mss.monitors[0]` 对齐
- **overlay 不用 focus hack**（不调用 `activateWindow()` / `setFocus()` / `raise_()`）
- **错误处理不抛异常给调用方**：`copy_image` / `save_image` 失败一律返回 `False`/`None`，调用方只判断返回值

### 修改范围红线（来自用户全局 CLAUDE.md）

- **每次只改一个 Task 范围的文件**。例如 T07 不允许碰 `capture.py` / `selection.py` / `saver.py` / `clipboard.py` / `main.py`
- **不允许顺手"优化"旁边的代码**——自己的改动导致的死代码自己清，原有的死代码不动
- **每行改动必须能追溯到用户需求**；不写防御性代码、不做不可触发场景的异常处理
- **改完主动跑验证**——`pytest` + 对应模块的 `verify_*.py`
- **完成一个 Task 立即 git commit + push 到 `origin/main`**

## 关键文件速查

- `docs/architecture.md`（v1.3）—— 唯一架构真相；每次 Task 完成都要同步（§3.x 模块描述、§5 状态、§6 剩余、§7 阶段、关键决策、版本号）
- `docs/capture_design.md` —— capture.py 设计稿（已实现，仅参考）
- `src/logger.py` —— `get_logger(__name__)` 单例；日志输出到 `%APPDATA%/screenshot-tool/log.txt` + stderr
- `src/selection.py` —— 唯一纯函数模块，pytest 10 个用例
- `src/overlay.py` —— T07 阶段仅一个 `OverlayWindow(QWidget)` 类；T08+ 加鼠标/绘制方法

## Git

- 主分支：`main`，推到 `origin/main`
- 提交信息格式：`feat: 新增 X 模块 + 同步 README/架构文档`（参考最近 7 个 commit 风格）
- Co-author 行：`Co-Authored-By: Claude <noreply@anthropic.com>`
