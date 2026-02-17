"""Slice line boundary polygons into per-syllable polygons.

Uses Shapely to intersect a Kraken line boundary polygon with vertical strips
at character cut positions, producing one polygon per syllable that follows
the line's actual contour.
"""

import logging
from typing import Optional

from shapely.geometry import MultiPolygon, Polygon, box
from shapely.geometry.base import BaseGeometry

from .geometry import CharBBox

logger = logging.getLogger(__name__)

Boundary = list[tuple[int, int]]


def syllable_x_ranges(
    syllable_char_bboxes: list[list[CharBBox]],
    line_boundary: Boundary,
) -> list[tuple[int, int]]:
    """Derive the x-range for each syllable from its character bounding boxes.

    The first syllable extends to the leftmost x of the line polygon.
    The last syllable extends to the rightmost x of the line polygon.

    Args:
        syllable_char_bboxes: List of CharBBox lists, one list per syllable.
        line_boundary: The line boundary polygon coordinates.

    Returns:
        List of (x_left, x_right) tuples, one per syllable.
    """
    if not syllable_char_bboxes:
        return []

    poly_xs = [pt[0] for pt in line_boundary]
    poly_x_min = min(poly_xs)
    poly_x_max = max(poly_xs)

    ranges = []
    for i, char_bboxes in enumerate(syllable_char_bboxes):
        if not char_bboxes:
            continue

        x_left = min(b.x for b in char_bboxes)
        x_right = max(b.x + b.width for b in char_bboxes)

        # First syllable extends to line polygon left edge
        if i == 0:
            x_left = min(x_left, poly_x_min)
        # Last syllable extends to line polygon right edge
        if i == len(syllable_char_bboxes) - 1:
            x_right = max(x_right, poly_x_max)

        ranges.append((x_left, x_right))

    return ranges


def _largest_polygon(geom: BaseGeometry) -> Optional[Polygon]:
    """Extract the largest polygon by area from a Shapely geometry."""
    if geom.is_empty:
        return None
    if isinstance(geom, Polygon):
        return geom
    if isinstance(geom, MultiPolygon):
        return max(geom.geoms, key=lambda p: p.area)
    # GeometryCollection or other types: find polygons inside
    polygons = [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]
    if polygons:
        return max(polygons, key=lambda p: p.area)
    return None


def slice_line_polygon(
    line_boundary: Boundary,
    x_ranges: list[tuple[int, int]],
) -> list[Optional[Boundary]]:
    """Slice a line boundary polygon into per-syllable polygons.

    For each syllable x-range, intersects the line polygon with a vertical
    strip and returns the resulting polygon coordinates.

    Args:
        line_boundary: Line boundary as a list of (x, y) tuples.
        x_ranges: List of (x_left, x_right) tuples, one per syllable.

    Returns:
        List of polygon boundaries (one per x-range). Each entry is a list
        of (x, y) integer tuples, or None if the intersection was empty.
    """
    if len(line_boundary) < 3:
        logger.warning("Line boundary has fewer than 3 points, cannot slice")
        return [None] * len(x_ranges)

    coords = [(float(x), float(y)) for x, y in line_boundary]
    line_poly = Polygon(coords)
    if not line_poly.is_valid:
        line_poly = line_poly.buffer(0)

    # Use the polygon's y-extent (with padding) for the vertical strips
    min_y = line_poly.bounds[1] - 10
    max_y = line_poly.bounds[3] + 10

    results: list[Optional[Boundary]] = []
    for x_left, x_right in x_ranges:
        strip = box(x_left, min_y, x_right, max_y)
        intersection = line_poly.intersection(strip)

        poly = _largest_polygon(intersection)
        if poly is None:
            logger.warning(
                "Empty intersection for x-range (%d, %d)", x_left, x_right
            )
            results.append(None)
            continue

        # Convert to integer coordinate tuples (drop closing duplicate)
        exterior_coords = list(poly.exterior.coords)
        if exterior_coords and exterior_coords[-1] == exterior_coords[0]:
            exterior_coords = exterior_coords[:-1]
        boundary = [(int(round(x)), int(round(y))) for x, y in exterior_coords]
        results.append(boundary)

    return results
