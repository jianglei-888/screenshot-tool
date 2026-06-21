# capture.py 设计方案

> 版本：v1.0
> 日期：2026-06-20
> 状态：设计稿（未实施）
> 所属：T03

---

## 1. 模块职责

### 负责

- 通过 mss 调用系统 GDI/DX 截取屏幕像素
- 把 mss 返回的 BGRA 字节流转成 PIL.Image
- 提供全屏截图和区域截图两个能力
- 对外屏蔽 mss 的实现细节（返回类型、坐标系统、mss 实例生命周期）
- DPI 缩放换算（Qt 逻辑坐标 → mss 物理坐标）

### 不负责

- UI 渲染、鼠标/键盘事件处理（→ overlay.py）
- 选区坐标的规范化（→ selection.py）
- 把图片送到剪贴板（→ clipboard.py）
- 把图片存成文件（→ saver.py）
- 全局热键监听（→ hotkey.py）

**模块边界**：capture.py 是个纯"像素采样器"，输入是坐标参数，输出是 PIL.Image。无副作用（不写文件、不动剪贴板），不持有 UI 状态。

---

## 2. 对外 API 设计

### 主函数（外部调用）

**`capture_fullscreen() -> PIL.Image.Image`**
- 截取所有显示器合成的虚拟全屏
- 参数：无
- 返回：RGB 模式的 PIL.Image，尺寸 = 虚拟全屏逻辑尺寸
- 异常：见第 5 节

**`capture_region(x: int, y: int, width: int, height: int) -> PIL.Image.Image`**
- 截取指定矩形区域
- 参数：4 个 int，含义是 Qt 逻辑坐标（设备无关像素），与 overlay/selection 一致
- 返回：RGB 模式的 PIL.Image，物理尺寸 = (width × DPR, height × DPR)
- 异常：见第 5 节

### 辅助函数（可选，未来需要时再加）

**`get_virtual_screen_size() -> tuple[int, int]`**
- 返回虚拟全屏的逻辑尺寸 (width, height)
- 用途：overlay 启动时定位、selection 做边界检查
- 如果不实现这个，调用方也可以从 Qt 的 `QScreen.virtualGeometry()` 拿

### 不暴露

- mss 实例（模块内单例，外部不接触）
- mss 异常（包装成自定义异常再抛）
- DPI 换算逻辑（隐藏在内部）

**返回值类型钉死为 PIL.Image**（不用 numpy 数组、不传 mss 原生 ScreenShot 对象），让下游 clipboard.py 和 saver.py 只需依赖 Pillow，不依赖 mss。

---

## 3. 数据流设计

### 完整调用链

```
main.py (主控)
  │
  ├── 1. 启动 overlay（用户按热键）
  │     │
  │     ↓ overlay.py
  │     鼠标按下/移动/抬起 → 实时绘制矩形
  │     ↓ Enter 确认
  │     │
  │     ↓ selection.py
  │     normalize(start, end, virtual_bounds) → (x, y, w, h)  逻辑坐标
  │     │
  │     ↓ 隐藏 overlay
  │     ↓
  ├── 2. 调用 capture_region(x, y, w, h)
  │     │
  │     ↓ capture.py
  │     1. 校验 (x, y, w, h) > 0
  │     2. 读主屏 devicePixelRatio (DPR)
  │     3. (x, y, w, h) × DPR → 物理坐标
  │     4. mss.grab(...)
  │     5. BGRA → PIL.Image (RGB)
  │     ↓
  │     返回 image: PIL.Image
  │
  ├── 3. 自动调用 clipboard.copy(image)
  │
  └── 4. 用户按 S 触发 saver.save(image)
```

### 模块关系

| 调用方 | 被调方 | 传递内容 |
|--------|--------|----------|
| main.py | `capture_region()` | (x, y, w, h) 逻辑坐标 |
| `capture_region()` | `mss.grab()` | 物理坐标 dict |
| `capture_region()` | `PIL.Image.frombytes()` | BGRA 字节流 |
| main.py | `clipboard.copy()` | PIL.Image |
| main.py | `saver.save()` | PIL.Image |

**调用次数**：一次截图流程中 `capture_region` 只被调用 1 次（用户确认后），不重复截图。

---

## 4. mss 实现方案

### 为什么选 mss

| 候选 | 速度 | 多显示器 | 依赖 | API 复杂度 |
|------|------|----------|------|------------|
| **mss** | 最快（GDI BitBlt） | 原生支持（`monitors[0]` 虚拟全屏） | 单一 wheel | 极简 |
| PIL.ImageGrab | 慢 3-5 倍 | 单屏 | PIL 自带 | 简单 |
| pyautogui.screenshot | 中等 | 单屏 | 多依赖 | 中等 |
| Qt QScreen.grabWindow | 中等 | Qt 自带 | PySide6 | 中等 |

mss 在速度上明显领先（底层 GDI 比 Qt 路径短），多显示器原生支持，依赖最小。MVP 阶段用它最合适。Qt 的 QScreen 留作备选——万一 mss 在某些 Windows 版本上有兼容问题，迁移成本不高（接口都收在 capture.py 内部）。

### mss 工作机制

**mss 实例**：
- 模块级单例（在 capture.py 顶部创建一次）
- 重复 init 有开销，且 Windows 上频繁创建/销毁可能句柄泄漏
- 单例 + 线程局部（如果将来需要并发）

**monitors 列表**：
- `mss.monitors` 返回显示器列表
- `monitors[0]`：所有显示器合成的虚拟全屏（可能含负坐标，表示主屏左侧/上方的副屏）
- `monitors[1..n]`：每块物理显示器
- 截图时用 `monitors[0]` 作为参考系

**grab 调用**：
- `sct.grab({"left": x, "top": y, "width": w, "height": h})` 返回 ScreenShot
- 内部包含 BGRA 字节流和尺寸
- 转 PIL.Image 用 `Image.frombytes("RGB", size, bgr_bytes)`（丢 alpha 通道，截图不需要透明）

### 区域截图实现思路

```
输入 (x, y, w, h) 逻辑坐标
    ↓
读取主屏 DPR
    ↓
(x_phys, y_phys, w_phys, h_phys) = (x, y, w, h) × DPR
    ↓
mss.grab({"left": x_phys, "top": y_phys, "width": w_phys, "height": h_phys})
    ↓
得到 ScreenShot (BGRA bytes, size)
    ↓
Image.frombytes("RGB", size, bgr_bytes)  # BGR→RGB 转换 + 丢 alpha
    ↓
返回 PIL.Image
```

### DPI 缩放处理（关键）

mss 用物理像素，Qt 用逻辑像素。如果不处理，HiDPI 屏上选区形状会跟截到的图对不上。

**处理流程**：
1. 从 Qt 拿主屏：`primary = QApplication.primaryScreen()`（capture.py 需要 QApplication 已启动，或在第一次调用时缓存）
2. 读 devicePixelRatio：`dpr = primary.devicePixelRatio()`（HiDPI 常见 1.5 / 2.0）
3. 选区坐标（来自 overlay/selection，逻辑）乘以 dpr 得到物理坐标
4. 喂给 mss.grab()

**示例**（HiDPI 200% 屏）：
- 用户在 100×100 逻辑像素区域框选
- 物理像素 = 200×200
- mss 截 200×200 物理像素
- 转 PIL 后 size = (200, 200)，正好对应视觉上的 100×100 逻辑像素

**混合 DPI 屏**（少见）：按主屏 dpr 处理，跨屏部分有轻微比例差。MVP 不处理。

### 多显示器

直接用 `mss.monitors[0]`（虚拟全屏）作为 mss.grab 的目标区域，mss 自己处理跨屏捕获。selection 提供的坐标来自 Qt 的逻辑坐标系统，已经处理了多屏合并（Qt 的多屏坐标也是连续的，可能含负值），与 mss 兼容。

---

## 5. 异常处理方案

### 异常类型设计

模块内定义：

- `CaptureError(Exception)`：基类
- `InvalidRegionError(CaptureError)`：坐标非法（宽高 ≤ 0、类型错）
- `ScreenAccessError(CaptureError)`：mss 抓屏失败（权限、驱动、句柄错误等）

所有截图失败都包装成这两种之一抛给调用方。调用方（main.py）统一处理：记日志 + 弹错误提示。

### 各场景处理

| 场景 | 行为 |
|------|------|
| **坐标非法**（width ≤ 0、height ≤ 0） | raise `InvalidRegionError("width and height must be positive")`，调用方应保证不传这种参数（由 selection.py 守门） |
| **坐标超出屏幕** | mss 越界部分会裁剪或返回异常。**策略**：不在 capture.py 内做边界检查，让 selection.py 全权负责 clip；这样职责单一、避免重复校验 |
| **权限问题** | 普通 Windows 应用无需管理员即可截屏。若 mss 抛 OSError/AccessDenied，捕获后包装为 `ScreenAccessError`，日志用 `logger.exception()` 记录原始异常 |
| **截图返回全黑** | mss 成功但内容是黑屏（受保护窗口/DRM/某些游戏反截屏）。**MVP 不处理**，按成功返回；未来如需要可加"全黑检测"告警 |
| **mss.grab 抛任意异常** | 任何 mss 内部异常 → 包成 `ScreenAccessError` 并 re-raise，message 附上调用参数（坐标 + DPR）方便排错 |
| **DPR 拿不到** | QApplication 未启动或主屏不可用（理论上不会发生）。fallback 假设 DPR = 1，正常运行；或抛 `ScreenAccessError("Qt screen unavailable")` |
| **DPI 缩放后尺寸为 0** | 逻辑尺寸 < 1/DPR 时物理尺寸为 0，mss 会失败。selection.py 已保证最小尺寸（如 ≥ 5 像素），此处兜底抛 `InvalidRegionError` |
| **mss 导入失败** | 模块顶部 ImportError。requirements.txt 应保证；不运行时处理 |
| **PIL.Image 转换失败** | 字节流长度不匹配等。包成 `ScreenAccessError("Image conversion failed: ...")` |

### 错误处理原则

1. **不静默吞错**：截图失败必须让调用方知道
2. **错误信息可定位**：异常 message 包含坐标、DPR、原因
3. **日志记录原始异常**：用 `logger.exception()` 而不是 `logger.error(str(e))`，保留堆栈
4. **不自动重试**：mss 失败通常不是临时性的，重试没意义
5. **失败时不返回半成品**：要么完整 PIL.Image，要么抛异常，不返回 None 或部分图

### 调用方的责任

- main.py 拿到 `CaptureError` 时：日志记 ERROR 级 + 给用户提示（如"截图失败，请重试"）
- main.py 拿到 `InvalidRegionError` 时：这是 bug（说明 selection.py 没守好门），日志记 ERROR + 不弹用户提示
- overlay.py 确认选区时调用 `get_virtual_screen_size()`（如果实现）做边界检查，clip 后的坐标保证合法性

---

## 6. 测试方案

### 测试策略

按架构要求，capture.py 不写单测（依赖系统环境，单测成本高于价值）。验证靠**手动验证脚本 + 集成测试**。

### 手动验证脚本（开发期用，T03 完成后跑一次）

**测试 1：全屏截图**
- 调用 `capture_fullscreen()`，保存到 `test_full.png`
- 验证：PNG 文件正常生成、非 0 字节、非异常大；打开后能看到屏幕内容（不是全黑）；尺寸 = 虚拟全屏尺寸
- 打印耗时，确认 < 200ms（4K 屏）

**测试 2：区域截图**
- 调用 `capture_region(0, 0, 800, 600)`，保存到 `test_region.png`
- 验证：尺寸 = (800×DPR, 600×DPR) 或视觉上对应 800×600 逻辑像素；内容是屏幕左上角 800×600 区域

**测试 3：DPI 准确性**（HiDPI 屏才有意义）
- 用画图在屏幕 (0, 0) 位置画一个 100×100 的红色方块
- 调用 `capture_region(0, 0, 100, 100)`，保存
- 打开图：整个图应该是红色（不是左上角 1/4 是红色、其余黑/其他色）
- 失败案例：如果整个图被缩放了 1/2 或 2 倍，说明 DPR 没处理好

**测试 4：多显示器**（有双屏才测）
- 记下主屏和副屏在 Windows 设置中的位置
- 在副屏画个独特内容（比如大字"副屏"）
- 调用 `capture_region(副屏left, 副屏top, 200, 200)`，保存
- 打开图：应该是副屏内容

**测试 5：异常路径**
- 调用 `capture_region(0, 0, 0, 100)` → 应抛 `InvalidRegionError`，进程不崩
- 调用 `capture_region(0, 0, -1, 100)` → 应抛 `InvalidRegionError`
- 调用 `capture_region(0, 0, "abc", 100)` → 应抛 `TypeError`（类型注解保护）或 `InvalidRegionError`
- 调用 `capture_region(0, 0, 999999, 999999)` → 行为取决于 selection.py 是否 clip；不应崩，不应无限阻塞

**测试 6：日志**
- 跑完上面所有调用后打开 `log.txt`
- 验证：每次截图都记录了坐标、耗时、结果（成功/失败 + 原因）

**测试 7：清理**
- 验证完删除 `test_full.png` 和 `test_region.png`（不留仓库）

### 集成测试（阶段 4 联调时）

完整流程：热键 → overlay → capture → clipboard
- 启动主程序
- 按热键，全屏出黑罩
- 框选一个区域
- 打开画图，Ctrl+V
- 验证：粘贴出来的就是刚才框选的图

### 性能验证（粗略）

- 任务管理器看 mss 进程（其实是当前 Python 进程）的 CPU 和内存
- 连续截图 20 次后内存应稳定（无明显泄漏）
- 每次截图耗时应在 50-200ms（1080p 屏 ~50ms，4K 屏 ~150ms）

### T03 完成判定清单

- [ ] 全屏截图：返回非黑 PIL.Image，尺寸正确，耗时 < 200ms
- [ ] 区域截图：返回指定区域图，尺寸 = 逻辑尺寸 × DPR
- [ ] HiDPI 屏：选区形状与图一致（视觉验证）
- [ ] 多显示器：跨屏截图内容正确
- [ ] 异常坐标不崩，抛清晰异常
- [ ] 日志记录每次截图的坐标、DPR、耗时
- [ ] 验证脚本测完删除，仓库不留临时文件

---

## 关键决策记录（capture.py 专属）

1. **mss 不用 PIL.ImageGrab**：性能 + 多显示器
2. **mss 实例模块级单例**：避免重复 init 开销和句柄泄漏
3. **DPI 在 capture.py 内处理**：调用方传逻辑坐标，模块内换算物理坐标，对调用方屏蔽 DPI 细节
4. **不返回 numpy 数组**：统一返回 PIL.Image，下游只依赖 Pillow
5. **不写单测**：依赖系统环境，手动验证 + 集成测试覆盖
6. **不在 capture.py 做边界 clip**：职责给 selection.py，capture.py 只做纯采样
7. **失败抛异常不返回 None**：调用方写起来更简单，避免"忘了判空"的 bug

---

## 关联文档

- [architecture.md](./architecture.md) — 总架构设计
- T03 任务定义见 architecture.md 第 5 节
