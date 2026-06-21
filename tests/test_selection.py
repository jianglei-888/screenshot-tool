"""Tests for src/selection.py."""
import sys
from pathlib import Path

import pytest

# Ensure src/ is importable when running this file directly
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.selection import normalize  # noqa: E402


@pytest.mark.parametrize(
    "start,end,expected",
    [
        ((100, 100), (300, 400), (100, 100, 200, 300)),  # TL -> BR
        ((300, 400), (100, 100), (100, 100, 200, 300)),  # BR -> TL
        ((100, 400), (300, 100), (100, 100, 200, 300)),  # BL -> TR
        ((300, 100), (100, 400), (100, 100, 200, 300)),  # TR -> BL
    ],
)
def test_four_directions(start, end, expected):
    assert normalize(start, end) == expected


@pytest.mark.parametrize(
    "start,end,expected",
    [
        ((100, 100), (100, 400), (100, 100, 0, 300)),   # width = 0
        ((100, 100), (300, 100), (100, 100, 200, 0)),   # height = 0
        ((100, 100), (100, 100), (100, 100, 0, 0)),     # single point
    ],
)
def test_zero_dimensions(start, end, expected):
    assert normalize(start, end) == expected


@pytest.mark.parametrize(
    "start,end,expected",
    [
        ((-100, 0), (-50, 100), (-100, 0, 50, 100)),         # left monitor only
        ((-1920, 0), (0, 1080), (-1920, 0, 1920, 1080)),     # spans two monitors
        ((100, -50), (-100, 200), (-100, -50, 200, 250)),    # mixed signs
    ],
)
def test_negative_coordinates(start, end, expected):
    assert normalize(start, end) == expected
