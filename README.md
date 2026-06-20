# Windows 截图工具

轻量级 Windows 截图工具，对标微信截图的核心体验。MVP 版本仅实现：快捷键启动、区域截图、自动复制到剪贴板、保存为 PNG。

## 状态

设计阶段，代码尚未实现。完整架构设计见 [docs/architecture.md](docs/architecture.md)。

## 功能范围（MVP）

- 全局快捷键启动截图模式
- 鼠标拖拽选择截图区域
- 自动复制到系统剪贴板
- 手动保存为 PNG 文件

## 不实现的功能

OCR、长截图、AI 识图、标注、箭头、马赛克、历史记录、云同步、账号、自动上传。

## 技术栈

| 类别   | 选型        |
|--------|-------------|
| Python | 3.12        |
| GUI    | PySide6     |
| 截图   | mss         |
| 图片   | Pillow      |
| 热键   | keyboard    |
| 打包   | PyInstaller |

## 默认配置（写死在源码里）

- 快捷键：`Ctrl+Shift+A`
- 默认保存目录：`~/Pictures/Screenshots`

修改方式：
- 快捷键 → 编辑 `src/main.py` 的 `DEFAULT_HOTKEY`
- 保存目录 → 编辑 `src/saver.py` 的 `DEFAULT_SAVE_DIR`

## 安装与运行

```bash
pip install -r requirements.txt
python -m src.main
```

## 项目结构

```
screenshot-tool/
├── README.md
├── requirements.txt
├── .gitignore
├── src/         源代码
├── tests/       测试（仅 test_selection.py）
├── scripts/     PyInstaller 打包配置
└── docs/        设计文档
```

## 许可证

个人使用项目。
