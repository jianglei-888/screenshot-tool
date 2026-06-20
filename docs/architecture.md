# Windows 截图工具 MVP 架构设计

> 版本：v1.1
> 日期：2026-06-20
> 状态：设计稿（未实施）
> 变更：移除 config.yaml/config.py，改为写死常量；测试仅保留 test_selection.py

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
| 配置 | **无（写死常量）** | 个人自用，不需要配置系统；改一个值直接改源码 |

**技术栈一句话总结**：PySide6 + mss + Pillow + keyboard，PyInstaller 打包；无配置文件。

### 为什么不用别的

- **不用 PyQt6**：GPL 协议对闭源/分发不友好，PySide6 是官方替代
- **不用 tkinter**：做半透明全屏遮罩非常别扭，跨屏坐标处理更弱
- **不用 pynput 做热键**：能做但 API 复杂，keyboard 库更轻
- **不用 pyautogui 截图**：高层封装，截图性能不如 mss
- **不用 Nuitka**：打包复杂度高，MVP 阶段不值得
- **不用配置文件**：个人自用，写死常量更简单；要改快捷键或保存路径直接改源码

---

## 2. 项目架构

```
screenshot-tool/
├── README.md                       # 项目说明、用法、快捷键自定义
├── requirements.txt                # 依赖锁定版本
├── .gitignore                      # 忽略 __pycache__、build/、dist/
├── src/
│   ├── __init__.py
│   ├── main.py                     # 入口：装配各模块、启动事件循环；定义 DEFAULT_HOTKEY
│   ├── logger.py                   # 日志初始化（文件 + 控制台）
│   ├── hotkey.py                   # 全局热键注册/注销、回调触发
│   ├── capture.py                  # 屏幕捕获（mss 封装）+ 区域裁剪
│   ├── overlay.py                  # 全屏遮罩窗口（PySide6）
│   ├── selection.py                # 选区绘制与坐标计算（纯逻辑，可独立测试）
│   ├── clipboard.py                # 图片写入剪贴板
│   └── saver.py                    # 保存 PNG；定义 DEFAULT_SAVE_DIR
├── tests/
│   ├── __init__.py
│   └── test_selection.py           # 选区坐标计算单测（纯函数好测）
└── scripts/
    └── build.spec                  # PyInstaller 打包配置

注：assets/ 目录（图标等）延后建立，MVP 阶段无图标。
```

**结构原则**：

- `src/` 平铺为主，按"职责"分文件而非"层"分目录（避免过度设计）
- `selection.py` 单独抽出，因为它是纯计算逻辑，最容易测试
- `capture/clipboard/saver` 三个 I/O 模块互相独立，方便替换实现
- 常量分散到对应模块：`DEFAULT_HOTKEY` 在 `main.py`，`DEFAULT_SAVE_DIR` 在 `saver.py`（贴近使用点）
- 测试只保留 `test_selection.py`（唯一一个纯函数、无外部依赖、值得单测的模块）

---

## 3. 核心模块设计

### 3.1 `main.py` — 应用入口 + 常量定义

- **职责**：装配模块、初始化日志、注册热键、启动 Qt 事件循环
- **常量定义**：
  - `DEFAULT_HOTKEY = "ctrl+shift+a"`（模块顶部，要改直接改这里）
- **输入**：命令行参数（可选）
- **输出**：常驻进程，监听热键
- **依赖**：调用所有其他模块的初始化函数

### 3.2 `logger.py` — 日志

- **职责**：初始化 logging，文件输出到 `%APPDATA%/screenshot-tool/log.txt`
- **输入**：日志级别
- **输出**：标准 logging logger
- **关系**：被 main 调用一次

### 3.3 `hotkey.py` — 全局热键

- **职责**：注册/注销全局热键，热键按下时调用回调
- **输入**：热键字符串 + 回调函数
- **输出**：回调被调用（无返回值）
- **关键行为**：注册失败（权限/冲突）要降级提示
- **关系**：被 main 注册；触发时调用 overlay.show()

### 3.4 `overlay.py` — 全屏遮罩窗口

- **职责**：弹出全屏无边框窗口、半透明黑色背景、捕获鼠标拖拽、显示选区矩形
- **输入**：屏幕尺寸列表（多显示器）
- **输出**：用户确认后，返回区域坐标 `(x, y, w, h)`；取消返回 `None`
- **关键行为**：
  - 窗口置顶 + 任务栏图标隐藏
  - ESC 取消、Enter 确认、右键取消
  - 实时显示选区尺寸（"234 × 156"）
  - 确认后**先隐藏自己**再触发 capture，避免截到遮罩
- **关系**：调用 selection 模块的逻辑；确认后调用 capture 截图

### 3.5 `selection.py` — 选区逻辑

- **职责**：纯函数，处理选区规范化（处理反向拖拽、限制在屏幕内、跨屏情况）
- **输入**：起点坐标、终点坐标、屏幕矩形列表
- **输出**：规范化后的 `(x, y, w, h)`
- **关系**：被 overlay 调用；纯逻辑，独立可测
- **测试**：唯一保留单测的模块（`tests/test_selection.py`）

### 3.6 `capture.py` — 屏幕捕获

- **职责**：用 mss 抓全屏（包含所有显示器合成），按选区裁剪
- **输入**：选区 `(x, y, w, h)`
- **输出**：`PIL.Image` 对象
- **关系**：被 overlay 调用；产出传给 clipboard 和 saver

### 3.7 `clipboard.py` — 剪贴板

- **职责**：把 PIL.Image 写入系统剪贴板
- **输入**：PIL.Image
- **输出**：bool（成功/失败）
- **实现**：用 `QApplication.clipboard().setImage(QImage)` 转换 PIL → QImage
- **关系**：被 main 流程调用（在 overlay 确认后自动执行）

### 3.8 `saver.py` — 文件保存 + 常量定义

- **职责**：弹原生保存对话框（带默认文件名），保存为 PNG
- **常量定义**：
  - `DEFAULT_SAVE_DIR = "~/Pictures/Screenshots"`（模块顶部，要改直接改这里）
  - `FILENAME_TEMPLATE = "screenshot_{timestamp}.png"`
- **输入**：PIL.Image
- **输出**：保存的文件路径，用户取消时返回 None
- **关键行为**：时间戳格式 `YYYYMMDD_HHMMSS`；同名文件自动加序号
- **关系**：被 main 调用（保存动作是用户触发，MVP 用快捷键 S 触发）

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
| 1 | **DPI 缩放不一致**（100% vs 150% 混合屏） | 选区坐标与截图坐标错位 | 统一用 Qt 的逻辑坐标；mss 拿物理坐标时按 DPI 缩放比换算 |
| 2 | **多显示器坐标系统** | mss 默认返回单屏，跨屏截图拿不到 | mss 用 `monitors` 拿全部屏幕合成图，再用逻辑坐标裁剪 |
| 3 | **遮罩窗口被自己截到** | 截出来一片黑 | 截图前 `overlay.hide()`，截图后恢复；用 `QTimer.singleShot` 延迟避免渲染未完成 |
| 4 | **热键被占用**（如已被其他截图工具抢注） | 按下没反应 | 启动时检测冲突，提示用户改 `main.py` 中的 `DEFAULT_HOTKEY`；监听失败要降级到 UI 按钮启动 |
| 5 | **剪贴板图片格式不兼容** | 粘贴到某些软件是空白 | 走 QClipboard 写 QImage，Qt 内部会转成 CF_DIB；测试时至少在微信/钉钉/Paint 三处验证 |
| 6 | **PyInstaller 打包 PySide6 漏 dll** | 打包后启动崩溃 | 用 PyInstaller 6.x + `collect_submodules('PySide6')`；首次打包后要在干净环境测一遍 |
| 7 | **杀软误报** | PyInstaller `--onefile` 经常被杀软拦 | 加证书签名（可选），或改 `--onedir` 模式；README 说明 |
| 8 | **管理员权限应用无法截取** | 截游戏/系统设置是黑屏 | 这是 Windows 限制，MVP 不解决，文档说明 |
| 9 | **截图时屏幕变化**（鼠标动、动画） | 抓到的图与选区瞬间不一致 | 接受现状（微信也这样）；可选：截图前 `time.sleep(0.05)` |
| 10 | **PySide6 安装包大** | 打包后 exe 100MB+ | 接受；可后续研究裁剪未使用的 Qt 模块 |
| 11 | **热键监听在某些游戏/全屏应用下失效** | 按下无响应 | Windows 已知行为；后续可考虑用低级钩子兜底 |
| 12 | **保存对话框被遮罩挡住** | 用户看不到 | 遮罩关闭后再弹保存框（已经是这个流程） |
| 13 | **写死常量改起来要改源码** | 改快捷键/保存路径需要改 .py 文件并重启 | 个人自用接受；将来要支持配置再加 config 模块 |

---

## 5. 开发任务拆解

每个 Task 控制在 30 分钟以内，可独立验证。Task ID 全局编号。

### 基础层

| ID | 任务 | 验证方式 |
|----|------|----------|
| **T01** | 创建项目目录结构、README、requirements.txt、.gitignore（15min） | `tree` 查看结构符合；`pip install -r requirements.txt` 成功 |
| **T02** | 实现 `logger.py`：文件 + 控制台双输出（15min） | 运行后日志文件存在，DEBUG/INFO/WARNING 分级正确 |

### 核心能力层

| ID | 任务 | 验证方式 |
|----|------|----------|
| **T03** | 实现 `capture.py` 全屏截图：mss 初始化 + 抓单帧（20min） | 脚本调用后生成一张全屏 PNG，目视确认 |
| **T04** | 扩展 `capture.py` 支持区域裁剪（15min） | 给定坐标，生成裁剪图，目视确认 |
| **T05** | 实现 `selection.py`：选区规范化（反向拖拽、超界、跨屏）（25min） | 单测覆盖：正常/反向/越界/跨屏四种 case |
| **T06** | 实现 `clipboard.py`：PIL → QImage → 剪贴板（20min） | 截图后粘贴到画图/Paint，能看到图 |
| **T07** | 实现 `saver.py`：文件名生成（时间戳模板）+ 默认目录（20min） | 单测：文件名格式正确；同秒多次保存自动加序号 |

### UI 层

| ID | 任务 | 验证方式 |
|----|------|----------|
| **T08** | 实现 `overlay.py` 框架：PySide6 全屏无边框窗口 + 半透明背景（30min） | 运行后全屏黑罩出现，ESC 关闭 |
| **T09** | overlay 鼠标事件：按下、移动、抬起，绘制选区矩形（30min） | 拖拽有矩形跟随，右下角显示尺寸 |
| **T10** | overlay 选区确认：Enter 确认、ESC 取消、右键取消（20min） | 三种退出方式都能正常返回坐标或 None |
| **T11** | overlay 截图前后隐藏自己：截图前 hide，截图后正常退出（20min） | 截出来的图里没有黑色遮罩 |
| **T12** | 集成测试：overlay → capture → clipboard 一条龙（30min） | 按 Enter 后图片已在剪贴板 |

### 集成层

| ID | 任务 | 验证方式 |
|----|------|----------|
| **T13** | 实现 `hotkey.py`：注册全局热键（25min） | 按下 `ctrl+shift+a` 触发回调 |
| **T14** | 实现 `main.py`：装配 + 启动事件循环（30min） | `python -m src.main` 启动后热键可用，退出干净 |
| **T15** | 全流程联调：热键 → 截图 → 剪贴板 → 保存（30min） | 实测一次完整流程，符合 PRD 6 步 |

### 收尾层

| ID | 任务 | 验证方式 |
|----|------|----------|
| **T16** | 错误处理：热键冲突、截图失败、剪贴板失败的日志与降级（25min） | 故意触发错误，进程不崩，有日志 |
| **T17** | 写 `build.spec`：PyInstaller 配置（25min） | `pyinstaller scripts/build.spec` 成功生成 exe |
| **T18** | 打包后验证：exe 在干净环境运行（20min） | 双击 exe 可启动，热键可用 |
| **T19** | 写 README：使用说明、快捷键、打包方法（20min） | 新人按 README 能跑通 |

**总预估**：约 7-8 小时实际开发（按每 Task 实测时间含调试）。拆成 19 个 Task，单 Task 最长 30 分钟。

---

## 6. 开发顺序

按依赖关系分 6 个阶段，每阶段完成后可独立运行/测试：

```
阶段 1：基础装配（30min）
   T01 → T02
   产出：能写日志

阶段 2：核心能力（100min）
   T03 → T04 → T05 → T06 → T07
   产出：能用脚本截全屏、裁剪区域、写剪贴板、保存文件（无 UI）
   验证：写个临时脚本串起来，跑通

阶段 3：UI 层（130min）
   T08 → T09 → T10 → T11 → T12
   产出：手动启动 overlay，能完整选区+截图+复制
   注意：T12 会临时用按钮或快捷键调起，等 T13 再换热键

阶段 4：集成（85min）
   T13 → T14 → T15
   产出：热键启动的完整 MVP

阶段 5：稳健性（25min）
   T16
   产出：错误不崩

阶段 6：交付（65min）
   T17 → T18 → T19
   产出：可分发 exe + 完整文档
```

**关键里程碑**：

- **阶段 2 结束** → 核心能力可验证（手动传坐标能截图）
- **阶段 3 结束** → 用户体验可验证（手动按钮能完整流程）
- **阶段 4 结束** → MVP 完成（热键可用）
- **阶段 6 结束** → 可交付

**风险任务标记**（建议预留 buffer 时间）：

- T05 选区规范化（边界 case 多）
- T09 overlay 鼠标事件（PySide6 事件系统需要熟悉）
- T11 截图时序（隐藏/恢复窗口 + 延迟）
- T17 打包 PySide6（首次打包几乎肯定有 dll 缺失问题）

---

## 关键决策记录

1. **PySide6 不用 PyQt6**：协议友好
2. **mss 不用 PIL.ImageGrab**：性能 + 多显示器支持
3. **keyboard 不用 pynput**：API 简单
4. **QClipboard 不用 win32clipboard**：减少依赖
5. **PyInstaller 不用 Nuitka**：MVP 阶段复杂度太高
6. **不引入 ORM/配置中心/插件系统**：避免过度设计
7. **selection 模块独立**：纯函数最好测，UI 不该混业务逻辑
8. **不引入配置文件**：个人自用，`DEFAULT_HOTKEY`（`main.py`）和 `DEFAULT_SAVE_DIR`（`saver.py`）作为模块常量；要改直接改源码
9. **测试只保留 `test_selection.py`**：唯一值得单测的纯逻辑模块；其他模块（capture/clipboard/saver/overlay）依赖系统环境，单测成本高于价值，靠手动 + 集成测试覆盖

---

## 待确认事项

- [x] 移除 config.yaml/config.py，改为写死常量
- [x] 测试只保留 test_selection.py
- [ ] T01-T02 实施计划细化
- [ ] assets/ 目录延后建立：MVP 不打包图标，后续需要时再补 icon.ico
- [ ] README 中是否要给出"如何改快捷键"的小节（要改就编辑 main.py 的 DEFAULT_HOTKEY）
