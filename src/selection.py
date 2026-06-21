"""Rectangle normalization for screen capture.

Pure function: converts two drag points into a standard TL-origin
rectangle. No screen bounds, no input validation — caller is
responsible for those concerns.
"""


def normalize(
    start: tuple[int, int],
    end: tuple[int, int],
) -> tuple[int, int, int, int]:
    """Normalize two points into a TL-origin rectangle.

    Args:
        start: First point (x1, y1).
        end: Second point (x2, y2).

    Returns:
        (x, y, width, height) where x = min(x1, x2), y = min(y1, y2),
        width = |x2 - x1|, height = |y2 - y1|. width and height are
        non-negative; zero is allowed. Coordinates are not clipped.
    """
    x1, y1 = start
    x2, y2 = end
    return (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
