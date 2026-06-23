# Windows 截图工具 MVP 架构设计

> 版本：v1.3
> 日期：2026-06-23
> 状态：T01-T07 已完成，T08-T18 待开发
> 变更：
> - T07 完成：overlay.py 骨架（全屏半透明遮罩窗口 + ESC 关闭）
> - 阶段 3（UI 层）开始：1/5 完成（T07）
> - §3.4 overlay.py 从 ⏳ 改为 ✅ T07，描述与实现对齐（只 1 个类、只 1 个 paintEvent、只处理 ESC）

---

## 1. 技术选型

| 类别 | 选型 | 原因 |
|------|------|------|
| GUI 框架 | **PySide6** | Qt 原生支持无边框全屏窗口、鼠标事件、半透明背景、跨屏坐标处理；LGPL 协议个人友好；带 QClipboard 可直接处理图片剪贴板，省一个依赖 |
| 截图库 | **mss** | Python 生态最快的纯 Python 屏幕捕获库；API 极简；天然支持多显示器；底层用 GDI/DX，比 PIL.ImageGrab 快 3-5 倍 |
| 图片处理 | **Pillow** | 行业标准；处理 crop、保存 PNG、格式转换；与 mss 返回数据兼容好 |
| 热键库 | **keyboard** | API 简单，单文件就能注册全局热键；纯 Python 包装 WinAPI，低层级更稳定；不依赖额外守护进程 |
| 剪贴板 | **QClipboard（PySide6 自带）** | 同一技术栈内统一，无需引入 pywin32；正确处理 CF_DIB 格式，粘贴到微信/钉钉/Paint 都能用 |
| 打包方案 | **PyInstaller** | PySide6 官方推荐；`--onefile` 模式方便分发；spec 文件可控 |
| 日志 | **logging（标准库）** | 不引入第三方 |
| 测试 | **pytest** | 唯一单测模块（selection）使用；其他模块靠手动验证 |
| 配置 | **无（写死常量）** | 个人自用，不需要配置系统；改一个值直接改源码 |

**技术栈一句话总结**：PySide6 + mss + Pillow + keyboard，PyInstaller 打包，pytest 单测；无配置文件，无 ORM/插件中心。

### 为什么不用别的

- **不用 PyQt6**：GPL 协议对闭源/分发不友好，PySide6 是官方替代
- **不用 tkinter**：做半透明全屏遮罩非常别扭，跨屏坐标处理更弱
- **不用 pynput 做热键**：能做但 API 复杂，keyboard 库更轻
- **不用 pyautogui 截图**：高层封装，截图性能不如 mss
- **不用 Nuitka**：打包复杂度高，MVP 阶段不值得
- **不用配置文件**：个人自用，写死常量更简单；要改快捷键或保存路径直接改源码
- **不用 PyYAML**：没有配置文件就不需要 YAML 解析
- **不用 pyproject.toml**：MVP 阶段用 requirements.txt + 直接源码运行已足够，不引入构建系统

---

## 2. 项目架构

### 当前目录结构

```
screenshot-tool/
├── README.md                       # 项目说明、用法、快捷键自定义
├── requirements.txt                # 依赖锁定（PySide6/mss/Pillow/keyboard/PyInstaller/pytest）
├── .gitignore
├── docs/
│   ├── architecture.md             # 本文档
│   └── capture_design.md           # capture.py 设计稿
├── src/
│   ├── __init__.py
│   ├── logger.py                   ✅ T02  日志初始化（文件 + 控制台）
│   ├── capture.py                  ✅ T03  屏幕捕获（mss 封装）
│   ├── selection.py                ✅ T04  矩形规范化（纯函数）
│   ├── clipboard.py                ✅ T05  剪贴板写入（QClipboard）
│   ├── main.py                     ⏳      应用入口 + DEFAULT_HOTKEY 常量
│   ├── hotkey.py                   ⏳      全局热键注册/注销
│   ├── overlay.py                  ✅ T07  全屏遮罩窗口（仅 ESC 退出）
│   └── saver.py                    ✅ T06  文件保存 + DEFAULT_SAVE_DIR 常量
├── tests/
│   ├── __init__.py
│   └── test_selection.py           ✅ T04  pytest 单测（10 个用例，0.22s）
└── scripts/
    ├── verify_capture.py           ✅ T03  手动验证脚本（mss 截全屏+区域）
    ├── verify_clipboard.py         ✅ T05  手动验证脚本（剪贴板写入）
    ├── verify_saver.py             ✅ T06  手动验证脚本（5 项断言）
    ├── verify_overlay.py           ✅ T07  手动验证脚本（人工按 ESC）
    └── build.spec                  ⏳ T16  PyInstaller 配置
```

**未创建的目录/文件**（按当前决策）：
- ❌ `assets/`（图标等）— MVP 阶段无图标
- ❌ `pyproject.toml` — 不引入构建系统
- ❌ `config.yaml` / `config.py` — 无配置系统

**结构原则**：
- `src/` 平铺为主，按"职责"分文件而非"层"分目录（避免过度设计）
- `selection.py` 单独抽出，因为它是纯计算逻辑，最容易测试
- `capture/clipboard/saver` 三个 I/O 模块互相独立，方便替换实现
- 常量分散到对应模块：`DEFAULT_HOTKEY` 在 `main.py`，`DEFAULT_SAVE_DIR` 在 `saver.py`（贴近使用点）
- **测试文件分两类**：
  - pytest 单测放 `tests/`（仅 `test_selection.py`），命名 `test_*.py`
  - 手动验证脚本放 `scripts/`，命名 `verify_*.py`，用 `if __name__ == "__main__"` 入口

---

## 3. 核心模块设计

### 3.1 `main.py` — 应用入口 + 常量定义 ⏳

- **职责**：装配模块、初始化日志、注册热键、启动 Qt 事件循环
- **常量定义**：
  - `DEFAULT_HOTKEY = "ctrl+shift+a"`（模块顶部，要改直接改这里）
- **输入**：命令行参数（可选）
- **输出**：常驻进程，监听热键
- **依赖**：调用所有其他模块的初始化函数

### 3.2 `logger.py` — 日志 ✅ T02

- **职责**：初始化 logging，文件输出到 `%APPDATA%/screenshot-tool/log.txt`，同时输出到 stderr
- **关键行为**：
  - 模块级单例初始化（`_initialized` 标志）
  - 子 logger 命名规范：`screenshot_tool.<module>`
  - 日志级别可通过 `LOG_LEVEL` 环境变量覆盖（DEBUG/INFO/WARNING/ERROR）
- **输入**：日志级别
- **输出**：标准 logging logger
- **关系**：被 main 调用一次；所有模块通过 `get_logger(__name__)` 拿 logger

### 3.3 `hotkey.py` — 全局热键 ⏳

- **职责**：注册/注销全局热键，热键按下时调用回调
- **输入**：热键字符串 + 回调函数
- **输出**：回调被调用（无返回值）
- **关键行为**：注册失败（权限/冲突）要降级提示
- **关系**：被 main 注册；触发时调用 overlay.show()

### 3.4 `overlay.py` — 全屏遮罩窗口 ✅ T07

- **职责**：T07 阶段仅实现**全屏半透明遮罩窗口骨架**（鼠标事件、选区绘制、确认/取消均不在 T07 范围）
- **类设计**：`OverlayWindow(QWidget)` 单类，无 Manager/Service/Controller/状态机
- **窗口属性**（T07 完成）：
  - Flag 组合：`FramelessWindowHint | WindowStaysOnTopHint | Tool`（无边框 + 置顶 + 任务栏不显示）
  - `WA_TranslucentBackground = True`（允许半透明绘制）
  - 覆盖范围：`QScreen.virtualGeometry()`（多显示器合成虚拟屏，**不**只覆盖主屏）
- **绘制**（T07 完成）：
  - `paintEvent` 仅 `QPainter.fillRect(self.rect(), QColor(0, 0, 0, 128))`（黑色 alpha=128 约 50% 透明）
  - T07 **不画**选区矩形 / 十字线 / 文字
- **交互**（T07 完成）：
  - 仅 `keyPressEvent` 处理 ESC：`log.info("Overlay closed by ESC")` + `self.close()`
  - T07 **不实现**鼠标事件、Enter 确认、右键取消
- **不做的事**（T08-T10 范围）：
  - ❌ 鼠标拖拽选区
  - ❌ 选区矩形绘制
  - ❌ Enter 确认 / 右键取消
  - ❌ 截图前隐藏自己
  - ❌ 任何 focus hack（`activateWindow` / `setFocus` 等）
- **关系**：T07 阶段完全独立，**不调用** capture / selection / clipboard / saver；T08+ 才集成
- **验证**：`scripts/verify_overlay.py` — 打印 8 项 setup 断言（屏幕数 / 几何 / 3 个 flag / 半透明属性 / 可见性）+ 人工按 ESC 关闭

### 3.5 `selection.py` — 矩形规范化 ✅ T04

- **职责**：纯函数，把拖拽起点和终点规范化为 TL-origin 矩形
- **输入**：`start: tuple[int, int]`, `end: tuple[int, int]`
- **输出**：`(x, y, width, height)`
- **不负责**：
  - ❌ 屏幕裁剪（不接收 `virtual_bounds`，由调用方负责）
  - ❌ 最小尺寸校验（宽高为 0 时原样返回，由调用方拒绝）
  - ❌ 类型校验（无 isinstance 检查，依赖调用方传 int）
- **支持**：
  - ✅ 反向拖拽（任意方向拖拽都返回 TL-origin 矩形）
  - ✅ 负坐标输入（多显示器场景下主屏左侧副屏的 x 为负）
  - ✅ 宽/高为 0（degenerate rectangle 是合法输出）
- **关系**：被 overlay 调用；纯逻辑，独立可测
- **测试**：`tests/test_selection.py` — 10 个 pytest 用例（四方向 4 + 零尺寸 3 + 负坐标 3），运行 0.22s

### 3.6 `capture.py` — 屏幕捕获 ✅ T03

- **职责**：用 mss 抓取屏幕像素，转为 PIL.Image
- **接口**：
  - `capture_fullscreen() -> Image.Image`：抓取所有显示器合成的虚拟全屏
  - `capture_region(x, y, width, height) -> Image.Image`：抓取指定矩形区域
- **实现要点**：
  - 模块级 mss 单例（`_sct = mss.mss()`），避免重复 init
  - BGRA 字节流 → RGB 模式 PIL.Image（`Image.frombytes("RGB", size, bgra, "raw", "BGRX")`）
  - mss 内部直接处理区域裁剪（不需要在 Python 端再裁一次）
- **不负责**：
  - ❌ DPI 缩放（输入输出都是物理像素，调用方负责）
  - ❌ 屏幕边界检查（调用方保证坐标合法）
  - ❌ 跨屏坐标处理（mss 原生支持多显示器合成）
- **异常**：
  - 坐标非法（非正整数）→ `ValueError`
  - mss grab 失败 → `RuntimeError`
- **关系**：被 overlay 调用；产出传给 clipboard 和 saver
- **验证**：`scripts/verify_capture.py` — 手动验证脚本，输出尺寸/耗时/保存路径

### 3.7 `clipboard.py` — 剪贴板 ✅ T05

- **职责**：把 PIL.Image 写入系统剪贴板
- **接口**：`copy_image(image: Image.Image) -> bool`
- **输入**：PIL.Image（RGB 或 RGBA 推荐）
- **输出**：`True` 成功 / `False` 失败（所有异常一律捕获，**不抛异常给调用方**）
- **实现要点**：
  - `from PIL.ImageQt import toqimage`（Pillow 12+ 的新 API；旧 API 的 `ImageQt` 类已删除）
  - `toqimage(image)` 返回的对象 `isinstance(QImage)` 为 `True`，可直接用于 `setImage()`
  - `QApplication.clipboard().setImage(qimage)`
- **前置条件**：调用时 QApplication 必须已存在（main.py 负责创建）
- **关系**：被 main 流程调用（在 overlay 确认后自动执行）
- **验证**：`scripts/verify_clipboard.py` — 手动验证脚本，跑通后人工在 Paint 粘贴确认

### 3.8 `saver.py` — 文件保存 + 常量定义 ✅ T06

- **职责**：自动保存 PIL.Image 到默认目录，无保存对话框
- **常量定义**（模块顶部）：
  - `DEFAULT_SAVE_DIR = Path.home() / "Pictures" / "Screenshots"`
  - `FILENAME_TEMPLATE = "screenshot_{timestamp}.png"`
- **接口**：
  - `save_image(image, save_dir=None) -> Path | None`：保存为 PNG，成功返回绝对路径，失败/异常返回 `None`
  - `generate_filename(save_dir=DEFAULT_SAVE_DIR, template=FILENAME_TEMPLATE) -> str`：生成时间戳文件名，自动处理同秒冲突
  - `_next_available_path(path) -> Path`：内部辅助，已存在时追加 `_1`、`_2`...
- **输入**：PIL.Image（不校验类型，依赖调用方）；可选 `save_dir`，None 则用 `DEFAULT_SAVE_DIR`
- **输出**：成功返回 `Path`；失败/异常一律返回 `None`（不抛异常给调用方）
- **关键行为**：
  - 时间戳格式 `YYYYMMDD_HHMMSS`（本地时间）
  - 同秒连续保存：`_1`、`_2`... 序号从 1 开始
  - 目录不存在自动 `mkdir(parents=True, exist_ok=True)`
  - 全部异常（mkdir 失败、image.save 失败）捕获并记 ERROR 日志
- **不负责**：
  - ❌ 弹原生保存对话框（"Save As" 不在 MVP 范围）
  - ❌ 跨会话去重
  - ❌ 输入类型校验（信任调用方传 PIL.Image）
- **关系**：被 main 调用（自动保存触发，**不需要用户按键**；截图确认后立即落盘）
- **验证**：`scripts/verify_saver.py` — 5 项断言（格式 / 同秒冲突 / 自动建目录 / 错误输入 / 往返打开）

### 模块关系图

```
main (DEFAULT_HOTKEY)
 ├── logger (init)
 ├── hotkey (register → 触发 overlay.show)
 └── overlay.show()
      ├── selection (计算规范坐标)
      ├── 隐藏自己
      ├── capture (mss 截图 + 裁剪)
      ├── clipboard (自动复制)
      └── saver (DEFAULT_SAVE_DIR，用户触发保存)
```

---

## 4. 风险分析

| # | 风险 | 影响 | 应对 |
|---|------|------|------|
| 1 | **DPI 缩放不一致**（100% vs 150% 混合屏） | 选区坐标与截图坐标错位 | 由调用方在 overlay 端统一为物理坐标；MVP 假设主屏 DPR 一致 |
| 2 | **多显示器坐标系统** | mss 默认返回单屏，跨屏截图拿不到 | mss 用 `monitors[0]` 拿全部屏幕合成图；selection 支持负坐标输入 |
| 3 | **遮罩窗口被自己截到** | 截出来一片黑 | 截图前 `overlay.hide()`，截图后恢复；用 `QTimer.singleShot` 延迟避免渲染未完成 |
| 4 | **热键被占用**（如已被其他截图工具抢注） | 按下没反应 | 启动时检测冲突，提示用户改 `main.py` 中的 `DEFAULT_HOTKEY`；监听失败要降级到 UI 按钮启动 |
| 5 | **剪贴板图片格式不兼容** | 粘贴到某些软件是空白 | 走 QClipboard 写 QImage，Qt 内部会转成 CF_DIB；测试时至少在微信/钉钉/Paint 三处验证 |
| 6 | **PyInstaller 打包 PySide6 漏 dll** | 打包后启动崩溃 | 用 PyInstaller 6.x + `collect_submodules('PySide6')`；首次打包后要在干净环境测一遍 |
| 7 | **杀软误报** | PyInstaller `--onefile` 经常被杀软拦 | 加证书签名（可选），或改 `--onedir` 模式；README 说明 |
| 8 | **管理员权限应用无法截取** | 截游戏/系统设置是黑屏 | 这是 Windows 限制，MVP 不解决，文档说明 |
| 9 | **截图时屏幕变化**（鼠标动、动画） | 抓到的图与选区瞬间不一致 | 接受现状（微信也这样）；可选：截图前 `time.sleep(0.05)` |
| 10 | **PySide6 安装包大** | 打包后 exe 100MB+ | 接受；可后续研究裁剪未使用的 Qt 模块 |
| 11 | **热键监听在某些游戏/全屏应用下失效** | 按下无响应 | Windows 已知行为；后续可考虑用低级钩子兜底 |
| 12 | ~~**保存对话框被遮罩挡住**~~ | — | T06 决定 MVP 不弹保存对话框，此风险已消除 |
| 13 | **写死常量改起来要改源码** | 改快捷键/保存路径需要改 .py 文件并重启 | 个人自用接受；将来要支持配置再加 config 模块 |

---

## 5. 当前开发进度

| ID | 任务 | 状态 | 验证方式 |
|----|------|------|----------|
| T01 | 项目结构（README、requirements.txt、.gitignore、目录） | ✅ 完成 | 目录树符合；`pip install -r requirements.txt` 成功 |
| T02 | logger.py（日志初始化） | ✅ 完成 | 运行后日志文件存在，DEBUG/INFO/WARNING 分级正确 |
| T03 | capture.py（mss 全屏 + 区域截图） | ✅ 完成 | `scripts/verify_capture.py` 跑通，输出尺寸/耗时正确 |
| T04 | selection.py（矩形规范化） | ✅ 完成 | 10 个 pytest 用例通过（0.22s） |
| T05 | clipboard.py（PIL → QImage → 剪贴板） | ✅ 完成 | `scripts/verify_clipboard.py` 跑通，Paint 粘贴确认 |
| T06 | saver.py（自动保存到默认目录） | ✅ 完成 | `scripts/verify_saver.py` 5 项断言通过；同秒冲突 `_1`/`_2` 序号正确 |
| T07 | overlay.py（全屏半透明遮罩 + ESC 关闭） | ✅ 完成 | `scripts/verify_overlay.py` 8 项 setup 断言通过；人工按 ESC 关闭 |

**进度**：7 / 18 Task 完成（39%），处于**阶段 3（UI 层）**进行中（1/5）。

---

## 6. 剩余任务列表

| ID | 任务 | 依赖 | 预计 | 验证方式 |
|----|------|------|------|----------|
| T08 | overlay 鼠标事件：按下/移动/抬起 + 选区矩形 | T07 | 30min | 拖拽有矩形跟随，右下角显示尺寸 |
| T09 | overlay 确认/取消：Enter/ESC/右键 | T08 | 20min | 三种退出方式都能正常返回坐标或 None |
| T10 | overlay 截图前隐藏自己 | T09 | 20min | 截出来的图里没有黑色遮罩 |
| T11 | UI 集成测试：overlay → capture → clipboard → saver 一条龙 | T10, T05, T06 | 30min | 按 Enter 后图片已在剪贴板 + 已落盘到默认目录 |
| T12 | hotkey.py：注册全局热键 | T11 | 25min | 按下 `ctrl+shift+a` 触发回调 |
| T13 | main.py：装配 + 启动事件循环 | T12, T11 | 30min | `python -m src.main` 启动后热键可用，退出干净 |
| T14 | 全流程联调：热键 → 截图 → 剪贴板 → 保存 | T13 | 30min | 实测一次完整流程，符合 PRD 6 步 |
| T15 | 错误处理：热键/截图/剪贴板失败的日志与降级 | T14 | 25min | 故意触发错误，进程不崩，有日志 |
| T16 | build.spec：PyInstaller 配置 | T14 | 25min | `pyinstaller scripts/build.spec` 成功生成 exe |
| T17 | 打包验证：干净环境运行 exe | T16 | 20min | 双击 exe 可启动，热键可用 |
| T18 | README 完善：使用说明、快捷键、打包方法 | T17 | 20min | 新人按 README 能跑通 |

**剩余**：11 / 18 Task 待开发，预计总耗时 ~5.0 小时。

---

## 7. 推荐开发顺序

按依赖关系分 6 个阶段，每阶段完成后可独立运行/测试：

### 阶段 1：基础装配 ✅ 完成
T01 → T02
**产出**：能写日志

### 阶段 2：核心能力 ✅ 完成
T03 ✅ → T04 ✅ → T05 ✅ → T06 ✅
**产出**：脚本化跑通 capture → clipboard → saver（无 UI）
**下一步**：T07（overlay 框架）

### 阶段 3：UI 层（1/5 完成）
T07 ✅ → T08 → T09 → T10 → T11
**产出**：手动启动 overlay，能完整选区+截图+复制
**注意**：T11 会临时用按钮或快捷键调起，等 T12 再换热键
**下一步**：T08（鼠标事件 + 选区矩形）

### 阶段 4：集成
T12 → T13 → T14
**产出**：热键启动的完整 MVP

### 阶段 5：稳健性
T15
**产出**：错误不崩

### 阶段 6：交付
T16 → T17 → T18
**产出**：可分发 exe + 完整文档

### 关键里程碑

| 里程碑 | 状态 | 验证内容 |
|--------|------|----------|
| 阶段 1 结束 | ✅ | 基础能力（日志可写） |
| 阶段 2 结束 | ✅ | 核心能力全验证（脚本化截图 + 复制 + 保存） |
| 阶段 3 进行中 | 🔄 | 手动启动 overlay 部分验证（遮罩 + ESC 关闭） |
| 阶段 3 结束 | ⏳ | 用户体验可验证（手动按钮能完整流程） |
| 阶段 4 结束 | ⏳ | MVP 完成（热键可用） |
| 阶段 6 结束 | ⏳ | 可交付 |

### 风险任务（建议预留 buffer）

- **T08** overlay 鼠标事件（PySide6 事件系统需要熟悉）
- **T10** 截图时序（隐藏/恢复窗口 + 延迟）
- **T16** 打包 PySide6（首次打包几乎肯定有 dll 缺失问题）

---

## 关键决策记录

1. **PySide6 不用 PyQt6**：LGPL 协议友好
2. **mss 不用 PIL.ImageGrab**：性能 + 多显示器支持
3. **keyboard 不用 pynput**：API 简单
4. **QClipboard 不用 win32clipboard**：减少依赖
5. **PyInstaller 不用 Nuitka**：MVP 阶段复杂度太高
6. **不引入 ORM/配置中心/插件系统**：避免过度设计
7. **selection 模块独立且纯函数**：UI 不混业务逻辑，单测成本低
8. **selection 不做屏幕裁剪**：调用方负责边界处理；模块接口最简（2 个参数）
9. **不引入配置文件**：`DEFAULT_HOTKEY`（`main.py`）和 `DEFAULT_SAVE_DIR`（`saver.py`）作为模块常量；要改直接改源码
10. **不创建 pyproject.toml / assets/**：MVP 阶段不引入构建系统和图标
11. **测试文件分两类**：
    - pytest 单测放 `tests/`（仅 `test_selection.py`，唯一纯逻辑模块）
    - 手动验证脚本放 `scripts/`，命名 `verify_*.py`，用 `if __name__ == "__main__"` 入口
12. **scripts/ 目录用途**：手动验证脚本（`verify_*.py`）+ PyInstaller 配置（`build.spec`）
13. **overlay 单一类 + 单一入口（无 Manager/Service/Controller/状态机）**：
    - T07 阶段 `OverlayWindow(QWidget)` 单类承担所有职责
    - 不创建任何协调层（Manager/Service/Controller 都不引入）
    - 不引入状态机；T08+ 通过方法扩展（mousePressEvent / paintEvent / keyPressEvent）而不是新增类
    - 模块不暴露 `show_overlay()` 包装函数，调用方直接 `OverlayWindow().show()`
14. **overlay 覆盖虚拟屏而非主屏**：
    - 用 `QScreen.virtualGeometry()` 拿到多显示器合成边界，与 `capture.py` 的 `mss.monitors[0]` 对齐
    - 选区坐标可以是负数（多屏布局：左侧副屏 x 为负），`selection.normalize()` 已支持
15. **overlay 不用 focus hack**：
    - 不调用 `activateWindow()` / `setFocus()` / `raise_()` 等
    - 依赖 `show()` 后的 Qt 默认行为拿到焦点
    - ESC 触发 `self.close()`，无任何全局键盘钩子（T07 阶段不引入 `keyboard` 库）

---

## 待确认事项

- T06+ 按 §7 推荐顺序推进
- T18 README 完善时补充"如何改快捷键"小节（编辑 `main.py` 的 `DEFAULT_HOTKEY`）

---

当前项目版本架构 v1.1