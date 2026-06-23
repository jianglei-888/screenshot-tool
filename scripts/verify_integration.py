"""T11 automated verification — overlay → capture → clipboard → saver.

Drives OverlayWindow via QTest, then in this script (NOT inside overlay.py)
chains capture.capture_region → clipboard.copy_image → saver.save_image.

Asserts the three side-effects: image non-empty, clipboard has image,
exactly one new file in saver.DEFAULT_SAVE_DIR.

Subcases:
  A: Drag + Enter       — full pipeline, 4 assertions
  B: Drag + ESC         — no side effect, 2 assertions
  C: No drag + Enter    — no side effect, 1 assertion
  D: Drag + right-click — no side effect, 1 assertion

Run from project root:
    .venv/Scripts/python.exe -u scripts/verify_integration.py
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
from src import capture, clipboard, saver


STEP_MS = 150
CHECK_MS = 250
RECT = (100, 100, 300, 200)


def _drag(window, p1: QPoint, p2: QPoint) -> None:
    QTest.mousePress(window, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, p1)
    QTest.mouseMove(window, p2)
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton,
                       Qt.KeyboardModifier.NoModifier, p2)


def _snapshot_files():
    save_dir = saver.DEFAULT_SAVE_DIR
    if not save_dir.exists():
        return set()
    return set(save_dir.glob("screenshot_*.png"))


class Runner:
    def __init__(self):
        self.window: OverlayWindow | None = None
        self.passed = 0
        self.failed = 0
        self.files_before = set()
        self.phase = ""
        self.app = None

    def _check(self, cond: bool, label: str, extra: str = "") -> None:
        if cond:
            self.passed += 1
            print(f"  [OK] {label}{(' — ' + extra) if extra else ''}")
        else:
            self.failed += 1
            print(f"  [FAIL] {label}{(' — ' + extra) if extra else ''}")


def _spawn(r: Runner) -> OverlayWindow:
    r.files_before = _snapshot_files()
    r.window = OverlayWindow()
    r.window.show()
    return r.window


def _check_no_new_files(r: Runner, label_prefix: str) -> None:
    files_after = _snapshot_files()
    new_files = files_after - r.files_before
    r._check(len(new_files) == 0, f"{label_prefix}: no new screenshot file",
             f"new={new_files}")


def run() -> int:
    app = QApplication(sys.argv)
    r = Runner()
    r.app = app

    print("=" * 60)
    print("T11 Verification — End-to-end Integration")
    print("=" * 60)
    print()

    geo = QGuiApplication.primaryScreen().virtualGeometry()
    p1 = QPoint(geo.x() + RECT[0], geo.y() + RECT[1])
    p2 = QPoint(geo.x() + RECT[0] + RECT[2], geo.y() + RECT[1] + RECT[3])

    state = {"phase": "spawn_A"}

    def tick():
        s = state
        w = r.window

        # ---- A: Drag + Enter → full pipeline ----
        if s["phase"] == "spawn_A":
            print("[A] Drag + Enter → full pipeline")
            _spawn(r)
            s["phase"] = "act_A"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "act_A":
            _drag(w, p1, p2)
            QTest.keyClick(w, Qt.Key.Key_Return)
            s["phase"] = "check_A"
            QTimer.singleShot(CHECK_MS, tick)
            return

        if s["phase"] == "check_A":
            r._check(w.result == RECT, "A1: result == (100, 100, 300, 200)",
                     f"result={w.result}")

            x, y, wd, ht = w.result
            image = capture.capture_region(x, y, wd, ht)
            r._check(image.size == (RECT[2], RECT[3]),
                     "A2: captured image is 300x200",
                     f"size={image.size}")

            ok = clipboard.copy_image(image)
            r._check(ok is True, "A2b: clipboard.copy_image returned True",
                     f"ok={ok}")

            cb_img = QApplication.clipboard().image()
            r._check(not cb_img.isNull(),
                     "A3: clipboard has image",
                     f"isNull={cb_img.isNull()}")

            path = saver.save_image(image)
            r._check(path is not None and path.exists(),
                     "A3b: saver.save_image returned existing path",
                     f"path={path}")

            files_after = _snapshot_files()
            new_files = files_after - r.files_before
            r._check(len(new_files) == 1,
                     "A4: exactly one new screenshot file in save dir",
                     f"new_count={len(new_files)}, new={new_files}")
            if len(new_files) == 1:
                r._check(new_files.pop() == path,
                         "A4b: new file matches saver return path",
                         f"new={path}")

            s["phase"] = "spawn_B"
            QTimer.singleShot(STEP_MS, tick)
            return

        # ---- B: Drag + ESC → no side effect ----
        if s["phase"] == "spawn_B":
            print("[B] Drag + ESC → no side effect")
            _spawn(r)
            s["phase"] = "act_B"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "act_B":
            _drag(w, p1, p2)
            QTest.keyClick(w, Qt.Key.Key_Escape)
            s["phase"] = "check_B"
            QTimer.singleShot(CHECK_MS, tick)
            return

        if s["phase"] == "check_B":
            r._check(w.result is None, "B1: result is None after ESC",
                     f"result={w.result}")
            _check_no_new_files(r, "B2")
            s["phase"] = "spawn_C"
            QTimer.singleShot(STEP_MS, tick)
            return

        # ---- C: No drag + Enter → no side effect ----
        if s["phase"] == "spawn_C":
            print("[C] No drag + Enter → no side effect")
            _spawn(r)
            s["phase"] = "act_C"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "act_C":
            QTest.keyClick(w, Qt.Key.Key_Return)
            s["phase"] = "check_C"
            QTimer.singleShot(CHECK_MS, tick)
            return

        if s["phase"] == "check_C":
            r._check(w.result is None, "C1: result is None on empty selection",
                     f"result={w.result}")
            _check_no_new_files(r, "C2")
            s["phase"] = "spawn_D"
            QTimer.singleShot(STEP_MS, tick)
            return

        # ---- D: Drag + right-click → no side effect ----
        if s["phase"] == "spawn_D":
            print("[D] Drag + right-click → no side effect")
            _spawn(r)
            s["phase"] = "act_D"
            QTimer.singleShot(STEP_MS, tick)
            return

        if s["phase"] == "act_D":
            _drag(w, p1, p2)
            QTest.mouseClick(w, Qt.MouseButton.RightButton,
                             Qt.KeyboardModifier.NoModifier, p2)
            s["phase"] = "check_D"
            QTimer.singleShot(CHECK_MS, tick)
            return

        if s["phase"] == "check_D":
            r._check(w.result is None, "D1: result is None after right click",
                     f"result={w.result}")
            _check_no_new_files(r, "D2")
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
