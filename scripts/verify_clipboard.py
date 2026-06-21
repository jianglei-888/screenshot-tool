"""T05 verification script for src/clipboard.py."""
import sys
import tempfile
from pathlib import Path

# Ensure src/ is importable when running this script directly
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PIL import Image
from PySide6.QtWidgets import QApplication

from src.clipboard import copy_image


def _report(label, image, path, success):
    print(f"  name:   {label}")
    print(f"  size:   {image.size}")
    print(f"  mode:   {image.mode}")
    print(f"  saved:  {path}")
    print(f"  result: {success}")


def main():
    QApplication.instance() or QApplication(sys.argv)
    temp_dir = Path(tempfile.gettempdir()) / "screenshot-tool-tests"
    temp_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {temp_dir}\n")

    print("[1] RGB rectangle (200x100 red)")
    img1 = Image.new("RGB", (200, 100), color=(255, 0, 0))
    path1 = temp_dir / "test_clipboard_red.png"
    img1.save(path1)
    _report("red rectangle", img1, path1, copy_image(img1))

    print("\n[2] RGB rectangle (400x300 blue)")
    img2 = Image.new("RGB", (400, 300), color=(0, 0, 255))
    path2 = temp_dir / "test_clipboard_blue.png"
    img2.save(path2)
    _report("blue rectangle", img2, path2, copy_image(img2))

    print("\n" + "=" * 50)
    print("Verification complete.")
    print(f"Inspect files in: {temp_dir}")
    print("Verify clipboard: open Paint, Ctrl+V, expect 400x300 blue rectangle")
    print("Check log: %APPDATA%/screenshot-tool/log.txt")
    print("=" * 50)


if __name__ == "__main__":
    main()