"""Image clipboard support using QClipboard.

Requires a QApplication instance to exist when called (caller's responsibility).
"""
from PIL import Image
from PIL.ImageQt import toqimage
from PySide6.QtWidgets import QApplication

from src.logger import get_logger

log = get_logger(__name__)


def copy_image(image: Image.Image) -> bool:
    """Copy a PIL.Image to the system clipboard.

    Args:
        image: PIL.Image (RGB or RGBA mode recommended).

    Returns:
        True on success; False on any error (QApplication missing,
        conversion failure, clipboard failure, etc.).
    """
    try:
        qimage = toqimage(image)
        QApplication.clipboard().setImage(qimage)
        return True
    except Exception as e:
        log.exception("Failed to copy image to clipboard: %s", e)
        return False