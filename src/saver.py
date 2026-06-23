"""File saving for screenshots.

Auto-saves PIL.Image to a default directory with a timestamped filename.
Same-second collisions get an incrementing suffix (_1, _2, ...). All errors
are caught and returned as None — callers only need to check the return
value.

No save dialog in MVP: this module is fire-and-forget to DEFAULT_SAVE_DIR.
"""
import datetime
from pathlib import Path

from PIL import Image

from src.logger import get_logger

log = get_logger(__name__)

DEFAULT_SAVE_DIR = Path.home() / "Pictures" / "Screenshots"
FILENAME_TEMPLATE = "screenshot_{timestamp}.png"


def generate_filename(
    save_dir: Path = DEFAULT_SAVE_DIR,
    template: str = FILENAME_TEMPLATE,
) -> str:
    """Generate a timestamped filename, resolving same-second collisions.

    Args:
        save_dir: Directory to check for existing files. Default is
            DEFAULT_SAVE_DIR.
        template: Filename template with `{timestamp}` placeholder.

    Returns:
        A filename (not a full path) guaranteed not to collide with
        existing files in `save_dir`. Format:
        `screenshot_YYYYMMDD_HHMMSS.png` for the first call in a second,
        `screenshot_YYYYMMDD_HHMMSS_1.png` for the second, etc.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = template.format(timestamp=timestamp)
    base_path = save_dir / base_name
    return _next_available_path(base_path).name


def save_image(
    image: Image.Image,
    save_dir: Path | None = None,
) -> Path | None:
    """Save a PIL.Image to disk as PNG.

    The target directory is created if missing. On any failure
    (mkdir error, image.save error, etc.) the exception is logged and
    None is returned — the caller does not need a try/except.

    Args:
        image: PIL.Image to save. Caller is responsible for ensuring
            this is a valid PIL.Image (no isinstance check performed).
        save_dir: Destination directory. None means DEFAULT_SAVE_DIR.

    Returns:
        Absolute path of the saved file, or None on failure.
    """
    target_dir = save_dir if save_dir is not None else DEFAULT_SAVE_DIR

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        log.exception("Failed to create save directory %s: %s", target_dir, e)
        return None

    try:
        filename = generate_filename(save_dir=target_dir)
        path = target_dir / filename
        image.save(str(path), "PNG")
        log.info("Saved screenshot to %s", path)
        return path
    except Exception as e:
        log.exception("Failed to save image to %s: %s", target_dir, e)
        return None


def _next_available_path(path: Path) -> Path:
    """Return a path that does not yet exist on disk.

    If `path` is free, return it as-is. Otherwise, try
    `<stem>_1<suffix>`, `<stem>_2<suffix>`, ... until a free slot is
    found. Counter starts at 1, not 0, so the original name is always
    preferred when free.
    """
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
