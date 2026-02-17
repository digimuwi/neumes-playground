"""Tests for polygon slicing: splitting line polygons into syllable polygons."""

import pytest

from htr_service.pipeline.geometry import CharBBox
from htr_service.pipeline.polygon_slicing import (
    slice_line_polygon,
    syllable_x_ranges,
)


def _make_char_bbox(x: int, width: int = 20) -> CharBBox:
    """Helper to create a CharBBox at a given x position."""
    return CharBBox(x=x, y=100, width=width, height=40, char="a", confidence=0.9)


# --- syllable_x_ranges ---


def test_x_ranges_multi_syllable():
    """Three syllables should produce three x-ranges, edges extended to polygon."""
    line_boundary = [(0, 50), (200, 50), (200, 150), (0, 150)]
    syl_bboxes = [
        [_make_char_bbox(10), _make_char_bbox(30)],
        [_make_char_bbox(60), _make_char_bbox(80), _make_char_bbox(100)],
        [_make_char_bbox(130), _make_char_bbox(150)],
    ]

    ranges = syllable_x_ranges(syl_bboxes, line_boundary)

    assert len(ranges) == 3
    # First syllable extends to polygon left edge (0)
    assert ranges[0][0] == 0
    assert ranges[0][1] == 50  # 30 + 20
    # Middle syllable uses char extents
    assert ranges[1][0] == 60
    assert ranges[1][1] == 120  # 100 + 20
    # Last syllable extends to polygon right edge (200)
    assert ranges[2][0] == 130
    assert ranges[2][1] == 200


def test_x_ranges_single_syllable():
    """Single syllable should span the full line polygon."""
    line_boundary = [(0, 50), (300, 50), (300, 150), (0, 150)]
    syl_bboxes = [[_make_char_bbox(50), _make_char_bbox(70)]]

    ranges = syllable_x_ranges(syl_bboxes, line_boundary)

    assert len(ranges) == 1
    assert ranges[0][0] == 0  # extended to polygon left
    assert ranges[0][1] == 300  # extended to polygon right


def test_x_ranges_empty():
    """Empty input produces empty output."""
    assert syllable_x_ranges([], [(0, 0), (100, 0), (100, 100)]) == []


# --- slice_line_polygon ---


def test_slice_multi_syllable():
    """Slicing a rectangular line polygon into 3 vertical strips."""
    line_boundary = [(0, 50), (300, 50), (300, 150), (0, 150)]
    x_ranges = [(0, 100), (100, 200), (200, 300)]

    results = slice_line_polygon(line_boundary, x_ranges)

    assert len(results) == 3
    for poly in results:
        assert poly is not None
        assert len(poly) >= 3  # valid polygon

    # First syllable polygon should be within x 0-100
    xs = [pt[0] for pt in results[0]]
    assert min(xs) >= 0
    assert max(xs) <= 100

    # Last syllable polygon should be within x 200-300
    xs = [pt[0] for pt in results[2]]
    assert min(xs) >= 200
    assert max(xs) <= 300


def test_slice_single_syllable():
    """Single syllable covering the full line should return ~the full polygon."""
    line_boundary = [(0, 50), (300, 50), (300, 150), (0, 150)]
    x_ranges = [(0, 300)]

    results = slice_line_polygon(line_boundary, x_ranges)

    assert len(results) == 1
    assert results[0] is not None
    xs = [pt[0] for pt in results[0]]
    assert min(xs) == 0
    assert max(xs) == 300


def test_slice_non_rectangular_polygon():
    """Slicing a trapezoidal polygon should produce polygons following its contour."""
    # Trapezoid: wider at bottom
    line_boundary = [(50, 50), (250, 50), (300, 150), (0, 150)]
    x_ranges = [(0, 150), (150, 300)]

    results = slice_line_polygon(line_boundary, x_ranges)

    assert len(results) == 2
    for poly in results:
        assert poly is not None


def test_slice_empty_intersection():
    """X-range outside polygon should return None."""
    line_boundary = [(100, 50), (200, 50), (200, 150), (100, 150)]
    x_ranges = [(300, 400)]  # completely outside

    results = slice_line_polygon(line_boundary, x_ranges)

    assert len(results) == 1
    assert results[0] is None


def test_slice_degenerate_boundary():
    """Boundary with fewer than 3 points should return None for all ranges."""
    line_boundary = [(0, 0), (100, 0)]  # just a line segment
    x_ranges = [(0, 100)]

    results = slice_line_polygon(line_boundary, x_ranges)

    assert len(results) == 1
    assert results[0] is None


def test_slice_coordinates_are_integers():
    """All output polygon coordinates should be integers."""
    line_boundary = [(0, 50), (300, 50), (300, 150), (0, 150)]
    x_ranges = [(0, 150), (150, 300)]

    results = slice_line_polygon(line_boundary, x_ranges)

    for poly in results:
        assert poly is not None
        for x, y in poly:
            assert isinstance(x, int)
            assert isinstance(y, int)
