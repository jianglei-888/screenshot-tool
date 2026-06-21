"""Screen capture module using mss.

Provides:
- capture_fullscreen(): capture all monitors combined
- capture_region(x, y, width, height): capture a specific region

Coordinates are in physical pixels (mss native). Caller is responsible
for any DPI conversion.
"""
import mss
from PIL import Image

# Module-level mss singleton. Reusing the instance avoids repeated
# handle creation/teardown on Windows.
_sct = mss.mss()


def capture_fullscreen() -> Image.Image:
    """Capture all monitors combined as a single virtual-screen image.

    Returns:
        PIL.Image.Image: RGB mode image sized to the virtual screen.

    Raises:
        RuntimeError: if the mss grab call fails for any reason.
    """
    try:
        screenshot = _sct.grab(_sct.monitors[0])
    except Exception as e:
        raise RuntimeError(f"Full screen capture failed: {e}") from e
    return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")


def capture_region(x: int, y: int, width: int, height: int) -> Image.Image:
    """Capture a specific rectangular region of the screen.

    Args:
        x: Left coordinate in physical pixels.
        y: Top coordinate in physical pixels.
        width: Region width in physical pixels (must be a positive integer).
        height: Region height in physical pixels (must be a positive integer).

    Returns:
        PIL.Image.Image: RGB mode image of the region.

    Raises:
        ValueError: if any parameter is not a positive integer.
        RuntimeError: if the mss grab call fails for any reason.
    """
    if not isinstance(x, int) or not isinstance(y, int):
        raise ValueError(f"x and y must be integers, got x={x!r}, y={y!r}")
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValueError(
            f"width and height must be integers, got width={width!r}, height={height!r}"
        )
    if width <= 0 or height <= 0:
        raise ValueError(
            f"width and height must be positive, got width={width}, height={height}"
        )

    region = {"left": x, "top": y, "width": width, "height": height}
    try:
        screenshot = _sct.grab(region)
    except Exception as e:
        raise RuntimeError(f"Region capture failed (region={region}): {e}") from e
    return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
