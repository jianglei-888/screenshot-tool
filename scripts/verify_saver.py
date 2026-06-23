"""T06 verification script for src/saver.py.

Uses a temporary directory to avoid polluting ~/Pictures/Screenshots.
Run from project root:

    .venv/Scripts/python.exe scripts/verify_saver.py
"""
import re
import shutil
import sys
import tempfile
from pathlib import Path

# Ensure src/ is importable when running this script directly
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from PIL import Image

from src.saver import (
    DEFAULT_SAVE_DIR,
    FILENAME_TEMPLATE,
    generate_filename,
    save_image,
)

FILENAME_RE = re.compile(r"^screenshot_\d{8}_\d{6}(_\d+)?\.png$")


def _report(label, path, size):
    print(f"  {label}: {path} ({size} bytes)")


def main():
    temp_dir = Path(tempfile.gettempdir()) / "screenshot-tool-tests" / "saver"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    print(f"Test directory: {temp_dir}")
    print(f"Default save dir: {DEFAULT_SAVE_DIR}")
    print(f"Filename template: {FILENAME_TEMPLATE}\n")

    print("[1] generate_filename format check")
    name = generate_filename(save_dir=temp_dir)
    match = FILENAME_RE.match(name)
    print(f"  generated: {name}")
    print(f"  matches pattern: {bool(match)}")
    assert match, f"Filename {name!r} does not match expected pattern"

    print("\n[2] same-second collision: save 3x in <1s")
    img = Image.new("RGB", (120, 80), color=(255, 128, 0))
    paths = []
    for i in range(3):
        p = save_image(img, save_dir=temp_dir)
        assert p is not None, f"save_image returned None on call {i + 1}"
        assert p.exists(), f"Saved file does not exist: {p}"
        assert p.parent == temp_dir, f"Wrong directory: {p.parent}"
        paths.append(p)
        _report(f"call {i + 1}", p, p.stat().st_size)
    assert len({p.name for p in paths}) == 3, "Expected 3 distinct filenames"
    assert paths[0].name == "screenshot_" + paths[0].stem.removeprefix("screenshot_") + ".png"
    # First has no suffix, second has _1, third has _2
    suffixes = [p.stem.rsplit("_", 1)[-1] for p in paths]
    print(f"  distinct filenames: {len({p.name for p in paths})}")
    print(f"  stem suffixes: {suffixes}")

    print("\n[3] auto-create directory when missing")
    fresh_dir = temp_dir / "auto-created-subdir"
    assert not fresh_dir.exists()
    p = save_image(img, save_dir=fresh_dir)
    assert p is not None and fresh_dir.exists() and p.exists()
    _report("auto-created", p, p.stat().st_size)
    shutil.rmtree(fresh_dir)

    print("\n[4] invalid input (string instead of Image) returns None")
    result = save_image("not an image", save_dir=temp_dir)
    print(f"  result: {result}")
    assert result is None, f"Expected None, got {result!r}"

    print("\n[5] file integrity check (open round-trip)")
    p = save_image(img, save_dir=temp_dir)
    assert p is not None
    reloaded = Image.open(p)
    reloaded.load()
    print(f"  reloaded: size={reloaded.size}, mode={reloaded.mode}")
    assert reloaded.size == (120, 80)
    assert reloaded.mode == "RGB"

    print("\n" + "=" * 50)
    print("All assertions passed.")
    print(f"Inspect files in: {temp_dir}")
    print("Check log: %APPDATA%/screenshot-tool/log.txt")
    print("=" * 50)

    # Cleanup
    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
