# Windows 截图工具

轻量级 Windows 截图工具，对标微信截图的核心体验。MVP 版本仅实现：快捷键启动、区域截图、自动复制到剪贴板、自动保存为 PNG。

## 状态

**当前进度**：T01-T11 已完成（11 / 18 = 61%），**阶段 3（UI 层）收尾**（5/5）。

| 已完成 | 模块 | 状态 |
|--------|------|------|
| T02 | `src/logger.py` | ✅ 日志初始化 |
| T03 | `src/capture.py` | ✅ 屏幕捕获（mss 封装） |
| T04 | `src/selection.py` | ✅ 矩形规范化（纯函数） |
| T05 | `src/clipboard.py` | ✅ 剪贴板写入 |
| T06 | `src/saver.py` | ✅ 自动保存到默认目录 |
| T07 | `src/overlay.py` | ✅ 全屏半透明遮罩（ESC 关闭） |
| T08 | `src/overlay.py` | ✅ 鼠标拖拽选区（cut-out 视觉效果） |
| T09 | `src/overlay.py` | ✅ Enter 确认 / ESC / 右键取消 + `@property result` |
| T10 | `src/overlay.py` | ✅ 确认后 `hide()` 再 `close()`（截图中不含遮罩） |
| T11 | `scripts/verify_integration.py` | ✅ 端到端集成测试（overlay → capture → clipboard → saver） |

**当前能力**：手动启动 overlay 后，可完成"拖拽选区 → Enter 确认 → 截图中不含遮罩 → 自动复制到剪贴板 → 自动保存到默认目录"全流程。**OverlayWindow 保持纯 UI 职责**——业务串联发生在调用方层。

**未实现**：
- ❌ 全局热键启动（main.py + hotkey.py 待 T12-T13）
- ❌ 错误处理包装（T15）
- ❌ 打包为 exe（T16-T17）

**已知未覆盖项**：T11 验证脚本未做截图视觉断言（仅验流程跑通）；T14 全流程联调时**人工事后打开 PNG**确认无残影。

完整架构与开发计划见 [docs/architecture.md](docs/architecture.md)。

## 功能范围（MVP）

- 全局快捷键启动截图模式（T12-T13 待实现）
- 鼠标拖拽选择截图区域（✅ T08 选区，✅ T09 确认/取消，✅ T10 隐藏遮罩）
- 全屏半透明遮罩 + ESC 关闭（✅ T07）
- 自动复制到系统剪贴板（✅ T05）
- **自动保存**为 PNG 到 `~/Pictures/Screenshots`（✅ T06，无保存对话框）

## 不实现的功能

OCR、长截图、AI 识图、标注、箭头、马赛克、历史记录、云同步、账号、自动上传、原生保存对话框（"Save As"）。

## 技术栈

| 类别   | 选型        |
|--------|-------------|
| Python | 3.11+       |
| GUI    | PySide6     |
| 截图   | mss         |
| 图片   | Pillow      |
| 热键   | keyboard    |
| 打包   | PyInstaller |
| 测试   | pytest      |

## 默认配置（写死在源码里）

| 配置项 | 默认值 | 修改位置 |
|--------|--------|----------|
| 快捷键 | `Ctrl+Shift+A` | `src/main.py` 的 `DEFAULT_HOTKEY` |
| 默认保存目录 | `~/Pictures/Screenshots` | `src/saver.py` 的 `DEFAULT_SAVE_DIR` |
| 文件名格式 | `screenshot_YYYYMMDD_HHMMSS.png` | `src/saver.py` 的 `FILENAME_TEMPLATE` |

同秒连续保存时自动加序号：`_1`、`_2`...（如 `screenshot_20260623_124502_1.png`）。

## 安装与运行

```bash
# 1. 创建虚拟环境（推荐）
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt

# 2. 跑已实现模块的验证脚本（按需）
.venv/Scripts/python.exe scripts/verify_capture.py          # 截全屏 + 区域
.venv/Scripts/python.exe scripts/verify_clipboard.py        # 写剪贴板（需手动开 Paint 粘贴确认）
.venv/Scripts/python.exe scripts/verify_saver.py            # 5 项断言
.venv/Scripts/python.exe scripts/verify_overlay.py          # 弹全屏遮罩，按 ESC 关闭
.venv/Scripts/python.exe scripts/verify_selection_drag.py   # 人工拖拽选区，按 ESC 关闭
.venv/Scripts/python.exe scripts/verify_overlay_confirm.py  # T09 QTest 自动化（4 子用例 / 8 断言）
.venv/Scripts/python.exe scripts/verify_overlay_hide.py     # T10 QTest 自动化（3 子用例 / 6 断言）
.venv/Scripts/python.exe scripts/verify_integration.py      # T11 端到端集成（4 子用例 / 13 断言）

# 3. 跑 pytest 单测
.venv/Scripts/python.exe -m pytest tests/ -v

# 4. 完整应用入口（T13 实现后可用，目前不存在）
# .venv/Scripts/python.exe -m src.main
```

## 项目结构

```
screenshot-tool/
├── README.md
├── requirements.txt                # 依赖锁定
├── .gitignore
├── docs/
│   ├── architecture.md             # 架构设计与开发计划
│   └── capture_design.md           # capture.py 设计稿
├── src/
│   ├── logger.py                   ✅ T02  日志初始化
│   ├── capture.py                  ✅ T03  屏幕捕获（mss）
│   ├── selection.py                ✅ T04  矩形规范化
│   ├── clipboard.py                ✅ T05  剪贴板写入
│   ├── saver.py                    ✅ T06  文件保存
│   ├── overlay.py                  ✅ T07+T08+T09+T10  全屏遮罩 + 拖拽选区 + 确认/取消 + hide
│   ├── main.py                     ⏳      应用入口（T13）
│   └── hotkey.py                   ⏳      全局热键（T12）
├── tests/
│   └── test_selection.py           ✅ T04  pytest 单测（10 个用例）
└── scripts/
    ├── verify_capture.py           ✅ T03  手动验证脚本
    ├── verify_clipboard.py         ✅ T05  手动验证脚本
    ├── verify_saver.py             ✅ T06  手动验证脚本（5 项断言）
    ├── verify_overlay.py           ✅ T07  手动验证脚本（人工按 ESC）
    ├── verify_selection_drag.py    ✅ T08  手动验证脚本（人工拖拽）
    ├── verify_overlay_confirm.py   ✅ T09  QTest 自动化（4 子用例 / 8 断言）
    ├── verify_overlay_hide.py      ✅ T10  QTest 自动化（3 子用例 / 6 断言）
    ├── verify_integration.py       ✅ T11  端到端集成（4 子用例 / 13 断言）
    └── build.spec                  ⏳ T16  PyInstaller 配置
```

**测试规范**：
- `tests/` 只放 pytest 单测（命名 `test_*.py`）
- `scripts/` 放手动验证脚本（命名 `verify_*.py`）和打包配置

## 许可证

个人使用项目。
