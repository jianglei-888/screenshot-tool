"""T09 automated verification for src/overlay.py confirm/cancel.

Single QApplication + single event loop; A/B/C/D subcases run serially
via QTimer. Uses QTest to simulate mouse + keyboard events.

Subcases:
  A: Enter with no drag — window stays open, result stays None
  B: Drag + Enter       — window closes, result == normalized rect
  C: Drag + ESC         — window closes, result is None
  D: Drag + right-click — window closes, result is None

Run from project root:
    .venv/Scripts/python.exe -u scripts/verify_overlay_confirm.py
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from src.overlay import OverlayWindow


STEP_MS = 120


def _drag(window, p1: QPoint, p2: QPoint) -> None:
    QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p1)
    QTest.mouseMove(window, p2)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, p2)


class Runner:
    def __init__(self, app: QApplication) -> None:
        self.app = app
        self.window: OverlayWindow | None = None
        self.passed = 0
        self.failed = 0

    def _spawn(self) -> OverlayWindow:
        self.window = OverlayWindow()
        self.window.show()
        return self.window

    def _expect_visible(self, label: str) -> None:
        assert self.window is not None
        if self.window.isVisible():
            self.passed += 1
            print(f"  [OK] {label}")
        else:
            self.failed += 1
            print(f"  [FAIL] {label}")

    def _expect_closed(self, label: str) -> None:
        assert self.window is not None
        if not self.window.isVisible():
            self.passed += 1
            print(f"  [OK] {label}")
        else:
            self.failed += 1
            print(f"  [FAIL] {label}")

    def _expect_result(self, expected, label: str) -> None:
        assert self.window is not None
        actual = self.window.result
        if actual == expected:
            self.passed += 1
            print(f"  [OK] {label} (result={actual})")
        else:
            self.failed += 1
            print(f"  [FAIL] {label} (expected={expected}, got={actual})")


def run() -> int:
    app = QApplication(sys.argv)
    r = Runner(app)

    print("=" * 60)
    print("T09 Verification — Confirm/Cancel (Enter/ESC/RightClick)")
    print("=" * 60)
    print()

    geo = QGuiApplication.primaryScreen().virtualGeometry()
    p1 = QPoint(geo.x() + 100, geo.y() + 100)
    p2 = QPoint(geo.x() + 400, geo.y() + 300)
    expected_rect = (100, 100, 300, 200)

    state = {"i": 0, "phase": "spawn_A"}

    def tick():
        s = state

        # ---- A: Enter with no drag ----
        if s["phase"] == "spawn_A":
            print("[A] Enter with no drag — window must stay open")
            r._spawn()
            s["phase"] = "press_enter_A"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "press_enter_A":
            QTest.keyClick(r.window, Qt.Key.Key_Return)
            s["phase"] = "check_A"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "check_A":
            r._expect_visible("A: window still visible after Enter on empty selection")
            assert r.window is not None
            r._expect_result(None, "A: result remains None")
            r.window.close()
            s["phase"] = "spawn_B"
            QTimer.singleShot(STEP_MS, tick)
            return

        # ---- B: Drag + Enter ----
        if s["phase"] == "spawn_B":
            print("[B] Drag + Enter — window closes, result = normalized rect")
            r._spawn()
            s["phase"] = "drag_B"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "drag_B":
            _drag(r.window, p1, p2)
            QTest.keyClick(r.window, Qt.Key.Key_Return)
            s["phase"] = "check_B"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "check_B":
            r._expect_closed("B: window closed after Enter on valid selection")
            r._expect_result(expected_rect, "B: result equals normalized drag rect")
            s["phase"] = "spawn_C"
            QTimer.singleShot(STEP_MS, tick)
            return

        # ---- C: Drag + ESC ----
        if s["phase"] == "spawn_C":
            print("[C] Drag + ESC — window closes, result is None")
            r._spawn()
            s["phase"] = "drag_C"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "drag_C":
            _drag(r.window, p1, p2)
            QTest.keyClick(r.window, Qt.Key.Key_Escape)
            s["phase"] = "check_C"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "check_C":
            r._expect_closed("C: window closed after ESC")
            r._expect_result(None, "C: result is None after ESC")
            s["phase"] = "spawn_D"
            QTimer.singleShot(STEP_MS, tick)
            return

        # ---- D: Drag + right-click ----
        if s["phase"] == "spawn_D":
            print("[D] Drag + right-click — window closes, result is None")
            r._spawn()
            s["phase"] = "drag_D"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "drag_D":
            _drag(r.window, p1, p2)
            QTest.mouseClick(r.window, Qt.MouseButton.RightButton,
                             Qt.KeyboardModifier.NoModifier, p2)
            s["phase"] = "check_D"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "check_D":
            r._expect_closed("D: window closed after right click")
            r._expect_result(None, "D: result is None after right click")
            print()
            print("=" * 60)
            print(f"Result: {r.passed} passed, {r.failed} failed")
            print("=" * 60)
            QTimer.singleShot(0, app.quit)
            return

    QTimer.singleShot(STEP_MS, tick)
    app.exec()
    return 0 if r.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
