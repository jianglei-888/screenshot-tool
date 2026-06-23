# Windows 截图工具

轻量级 Windows 截图工具，对标微信截图的核心体验。MVP 版本仅实现：快捷键启动、区域截图、自动复制到剪贴板、自动保存为 PNG。

## 状态

**当前进度**：T01-T06 已完成（6 / 18 = 33%），阶段 2（核心能力）全部完成，正在进入阶段 3（UI 层）。

| 已完成 | 模块 | 状态 |
|--------|------|------|
| T02 | `src/logger.py` | ✅ 日志初始化 |
| T03 | `src/capture.py` | ✅ 屏幕捕获（mss 封装） |
| T04 | `src/selection.py` | ✅ 矩形规范化（纯函数） |
| T05 | `src/clipboard.py` | ✅ 剪贴板写入 |
| T06 | `src/saver.py` | ✅ 自动保存到默认目录 |

**注意**：目前 `python -m src.main` 还不能跑（main / overlay / hotkey 待开发，T07-T13）。已完成的模块各自有手动验证脚本可单独跑通。

完整架构与开发计划见 [docs/architecture.md](docs/architecture.md)。

## 功能范围（MVP）

- 全局快捷键启动截图模式（T07-T13 待实现）
- 鼠标拖拽选择截图区域（T07-T10 待实现）
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
.venv/Scripts/python.exe scripts/verify_capture.py      # 截全屏 + 区域
.venv/Scripts/python.exe scripts/verify_clipboard.py    # 写剪贴板（需手动开 Paint 粘贴确认）
.venv/Scripts/python.exe scripts/verify_saver.py        # 5 项断言

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
│   ├── main.py                     ⏳      应用入口（T13）
│   ├── hotkey.py                   ⏳      全局热键（T12）
│   └── overlay.py                  ⏳      全屏遮罩窗口（T07-T11）
├── tests/
│   └── test_selection.py           ✅ T04  pytest 单测（10 个用例）
└── scripts/
    ├── verify_capture.py           ✅ T03  手动验证脚本
    ├── verify_clipboard.py         ✅ T05  手动验证脚本
    ├── verify_saver.py             ✅ T06  手动验证脚本（5 项断言）
    └── build.spec                  ⏳ T16  PyInstaller 配置
```

**测试规范**：
- `tests/` 只放 pytest 单测（命名 `test_*.py`）
- `scripts/` 放手动验证脚本（命名 `verify_*.py`）和打包配置

## 许可证

个人使用项目。
