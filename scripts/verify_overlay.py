"""T07 verification script for src/overlay.py.

Manual test:
1. Run this script — virtual screen is covered by a semi-transparent
   dark overlay.
2. Visually confirm: fullscreen, no title bar, no taskbar icon,
   screen content visible through the translucent layer.
3. Press ESC — overlay closes, script prints confirmation.

Run from project root:
    .venv/Scripts/python.exe scripts/verify_overlay.py
"""
import sys
from pathlib import Path

# Ensure src/ is importable when running this script directly
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from src.overlay import OverlayWindow


def _yes_no(value: bool) -> str:
    return "yes" if value else "NO"


def main():
    app = QApplication(sys.argv)

    screens = QGuiApplication.screens()
    virtual_geo = QGuiApplication.primaryScreen().virtualGeometry()

    print(f"Number of screens: {len(screens)}")
    print(f"Virtual screen geometry: x={virtual_geo.x()}, "
          f"y={virtual_geo.y()}, w={virtual_geo.width()}, "
          f"h={virtual_geo.height()}\n")

    window = OverlayWindow()
    window.show()

    actual_geo = window.geometry()
    flags = window.windowFlags()

    print(f"Window geometry: x={actual_geo.x()}, "
          f"y={actual_geo.y()}, w={actual_geo.width()}, "
          f"h={actual_geo.height()}")
    print(f"  matches virtual screen: {_yes_no(actual_geo == virtual_geo)}")
    print(f"  FramelessWindowHint:    {_yes_no(bool(flags & Qt.WindowType.FramelessWindowHint))}")
    print(f"  WindowStaysOnTopHint:   {_yes_no(bool(flags & Qt.WindowType.WindowStaysOnTopHint))}")
    print(f"  Tool flag:              {_yes_no(bool(flags & Qt.WindowType.Tool))}")
    print(f"  WA_TranslucentBackground: "
          f"{_yes_no(window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))}")
    print(f"  Window visible:         {_yes_no(window.isVisible())}")

    print("\n>>> Press ESC on the overlay window to close it <<<\n")

    app.exec()

    print(f"Window visible after exec: {_yes_no(window.isVisible())}")
    if not window.isVisible():
        print("OK: overlay closed successfully.")
    else:
        print("FAIL: overlay still visible after exec (was ESC pressed?).")

    print(f"\nCheck log for 'Overlay closed by ESC': "
          f"%APPDATA%/screenshot-tool/log.txt")


if __name__ == "__main__":
    main()