"""T08 manual verification script for src/overlay.py — mouse drag.

Starts OverlayWindow and waits for the user to manually drag and press
ESC. Prints a visual checklist to the terminal.

Run from project root:
    .venv/Scripts/python.exe scripts/verify_selection_drag.py
"""
import sys
from pathlib import Path

# Ensure src/ is importable when running this script directly
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from src.overlay import OverlayWindow


def main():
    app = QApplication(sys.argv)

    geo = QGuiApplication.primaryScreen().virtualGeometry()

    print("=" * 60)
    print("T08 Manual Verification — Mouse Drag Selection")
    print("=" * 60)
    print(f"Virtual screen: {geo.width()}x{geo.height()} at "
          f"({geo.x()}, {geo.y()})")
    print()
    print("Manual checklist:")
    print("  [1] Cursor is a cross over the overlay")
    print("  [2] Drag with mouse — selection rectangle follows cursor")
    print("      - White border on selection, transparent inside")
    print("      - Outside selection: 50% dark overlay")
    print("  [3] Drag in any direction (TL->BR, BR->TL, TR->BL, BL->TR)")
    print("      - Rectangle always normalizes to TL-origin")
    print("  [4] Click without dragging — no rectangle appears")
    print("  [5] Press ESC — overlay closes, script exits")
    print()
    print(">>> Drag with mouse, then press ESC to close <<<")
    print()

    window = OverlayWindow()
    window.show()

    app.exec()

    print()
    print("Overlay closed. Confirm all 5 items passed.")


if __name__ == "__main__":
    main()