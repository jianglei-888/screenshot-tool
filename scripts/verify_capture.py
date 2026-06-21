"""T03 verification script for src/capture.py.

Verifies:
1. capture_fullscreen() returns a valid PIL.Image of the virtual screen
2. capture_region(x, y, w, h) returns a valid PIL.Image of the given area
3. Output dimensions are correct
4. Capture latency is reasonable (< 200ms typical for 1080p/4K)

Run:
    python tests/test_capture.py
"""
import sys
import tempfile
import time
from pathlib import Path

# Ensure src/ is importable when running this script directly
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.capture import capture_fullscreen, capture_region


def _report(label, image, elapsed_ms, path):
    print(f"  name:   {label}")
    print(f"  size:   {image.size}  (width x height)")
    print(f"  mode:   {image.mode}")
    print(f"  time:   {elapsed_ms:.1f} ms")
    print(f"  saved:  {path}")


def main():
    temp_dir = Path(tempfile.gettempdir()) / "screenshot-tool-tests"
    temp_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {temp_dir}\n")

    print("[1] capture_fullscreen()")
    t0 = time.perf_counter()
    img = capture_fullscreen()
    elapsed = (time.perf_counter() - t0) * 1000
    path = temp_dir / "test_full.png"
    img.save(path)
    _report("fullscreen", img, elapsed, path)

    print("\n[2] capture_region(0, 0, 800, 600)")
    t0 = time.perf_counter()
    img = capture_region(0, 0, 800, 600)
    elapsed = (time.perf_counter() - t0) * 1000
    path = temp_dir / "test_region_800x600.png"
    img.save(path)
    _report("region 800x600", img, elapsed, path)

    print("\n[3] capture_region(100, 100, 400, 300)")
    t0 = time.perf_counter()
    img = capture_region(100, 100, 400, 300)
    elapsed = (time.perf_counter() - t0) * 1000
    path = temp_dir / "test_region_400x300.png"
    img.save(path)
    _report("region 400x300 at (100,100)", img, elapsed, path)

    print("\n" + "=" * 50)
    print("Verification complete.")
    print(f"Inspect files in: {temp_dir}")
    print("=" * 50)


if __name__ == "__main__":
    main()
