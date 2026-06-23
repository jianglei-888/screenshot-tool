"""T10 automated verification for src/overlay.py hide-before-close.

Single QApplication + single event loop; A/B/C subcases run serially
via QTimer. Uses QTest to simulate mouse + keyboard events.

Subcases:
  A: Drag + Enter       — window hides then closes; result == normalized rect
  B: Enter with no drag — window stays open, result stays None
  C: Drag + ESC         — window closes, result is None (T09 regression)

Run from project root:
    .venv/Scripts/python.exe -u scripts/verify_overlay_hide.py
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
    def __init__(self) -> None:
        self.window: OverlayWindow | None = None
        self.passed = 0
        self.failed = 0

    def _spawn(self) -> OverlayWindow:
        self.window = OverlayWindow()
        self.window.show()
        return self.window

    def _check(self, cond: bool, label: str, extra: str = "") -> None:
        if cond:
            self.passed += 1
            print(f"  [OK] {label}{(' — ' + extra) if extra else ''}")
        else:
            self.failed += 1
            print(f"  [FAIL] {label}{(' — ' + extra) if extra else ''}")


def run() -> int:
    app = QApplication(sys.argv)
    r = Runner()

    print("=" * 60)
    print("T10 Verification — Hide before close")
    print("=" * 60)
    print()

    geo = QGuiApplication.primaryScreen().virtualGeometry()
    p1 = QPoint(geo.x() + 100, geo.y() + 100)
    p2 = QPoint(geo.x() + 400, geo.y() + 300)
    expected_rect = (100, 100, 300, 200)

    state = {"phase": "spawn_A"}

    def tick():
        s = state
        w = r.window

        # ---- A: Drag + Enter → hide + close, result == rect ----
        if s["phase"] == "spawn_A":
            print("[A] Drag + Enter — window must hide then close, result == rect")
            r._spawn()
            s["phase"] = "act_A"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "act_A":
            _drag(w, p1, p2)
            QTest.keyClick(w, Qt.Key.Key_Return)
            s["phase"] = "check_A"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "check_A":
            r._check(not w.isVisible(), "A: window not visible after Enter",
                     f"isVisible={w.isVisible()}")
            r._check(w.result == expected_rect, "A: result equals normalized drag rect",
                     f"result={w.result}")
            s["phase"] = "spawn_B"
            QTimer.singleShot(STEP_MS, tick)
            return

        # ---- B: Enter with no drag → window stays open, result None ----
        if s["phase"] == "spawn_B":
            print("[B] Enter with no drag — window must stay open, result None")
            r._spawn()
            s["phase"] = "act_B"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "act_B":
            QTest.keyClick(w, Qt.Key.Key_Return)
            s["phase"] = "check_B"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "check_B":
            r._check(w.isVisible(), "B: window still visible after Enter on empty selection",
                     f"isVisible={w.isVisible()}")
            r._check(w.result is None, "B: result remains None",
                     f"result={w.result}")
            w.close()
            s["phase"] = "spawn_C"
            QTimer.singleShot(STEP_MS, tick)
            return

        # ---- C: Drag + ESC → window closes, result None (T09 regression) ----
        if s["phase"] == "spawn_C":
            print("[C] Drag + ESC — regression: window closes, result None")
            r._spawn()
            s["phase"] = "act_C"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "act_C":
            _drag(w, p1, p2)
            QTest.keyClick(w, Qt.Key.Key_Escape)
            s["phase"] = "check_C"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "check_C":
            r._check(not w.isVisible(), "C: window not visible after ESC",
                     f"isVisible={w.isVisible()}")
            r._check(w.result is None, "C: result is None after ESC",
                     f"result={w.result}")
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
