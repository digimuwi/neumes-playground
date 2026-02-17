"""Shared tiling constants and helpers for SAHI-compatible image slicing.

Provides tile-size computation from Kraken segmentation results and a grid
generator that replicates SAHI's ``get_slice_bboxes`` algorithm exactly, so
training tiles match inference tiles.
"""

import statistics
from dataclasses import dataclass

from kraken.containers import Segmentation

# Tile size limits
TILE_SIZE_MIN = 320
TILE_SIZE_MAX = 1280
TILE_SIZE_DEFAULT = 640
TILE_SIZE_MULTIPLIER = 4

# SAHI overlap ratio between adjacent tiles
OVERLAP_RATIO = 0.2


@dataclass
class TileSpec:
    """A single tile in the slicing grid."""

    row: int
    col: int
    x: int  # left edge (pixels)
    y: int  # top edge (pixels)
    width: int  # tile width (pixels)
    height: int  # tile height (pixels)


def compute_tile_size(segmentation: Segmentation) -> int:
    """Compute SAHI tile size from median interlinear spacing.

    Sorts text lines by baseline y-position, computes the vertical gap
    between consecutive line boundaries (bottom of line N to top of line
    N+1), takes the median, and multiplies by 4.  The result is clamped
    to [320, 1280].

    Falls back to 640 px if fewer than 2 lines are present.
    """
    if len(segmentation.lines) < 2:
        return TILE_SIZE_DEFAULT

    # Sort lines by median baseline y-position
    lines_with_y = []
    for line in segmentation.lines:
        if line.baseline:
            median_y = statistics.median(pt[1] for pt in line.baseline)
            lines_with_y.append((median_y, line))

    if len(lines_with_y) < 2:
        return TILE_SIZE_DEFAULT

    lines_with_y.sort(key=lambda pair: pair[0])

    # Compute gaps between consecutive lines
    gaps = []
    for i in range(len(lines_with_y) - 1):
        _, current_line = lines_with_y[i]
        _, next_line = lines_with_y[i + 1]

        if current_line.boundary and next_line.boundary:
            current_bottom = max(pt[1] for pt in current_line.boundary)
            next_top = min(pt[1] for pt in next_line.boundary)
            gap = next_top - current_bottom
            if gap > 0:
                gaps.append(gap)

    if not gaps:
        return TILE_SIZE_DEFAULT

    median_gap = statistics.median(gaps)
    tile_size = int(median_gap * TILE_SIZE_MULTIPLIER)
    return max(TILE_SIZE_MIN, min(TILE_SIZE_MAX, tile_size))


def generate_tile_grid(
    img_width: int,
    img_height: int,
    tile_size: int,
    overlap_ratio: float = OVERLAP_RATIO,
) -> list[TileSpec]:
    """Generate a SAHI-compatible tiling grid for an image.

    Replicates the exact algorithm from ``sahi.slicing.get_slice_bboxes``:
    tiles are placed with constant stride, and edge tiles are shifted back
    to maintain full ``tile_size`` dimensions (never truncated or padded).

    Args:
        img_width: Image width in pixels.
        img_height: Image height in pixels.
        tile_size: Tile width and height in pixels (square tiles).
        overlap_ratio: Fractional overlap between adjacent tiles.

    Returns:
        List of :class:`TileSpec` covering the entire image.
    """
    overlap_px = int(overlap_ratio * tile_size)
    tiles: list[TileSpec] = []

    y_max = y_min = 0
    row = 0

    while y_max < img_height:
        x_min = x_max = 0
        y_max = y_min + tile_size
        col = 0

        while x_max < img_width:
            x_max = x_min + tile_size

            if y_max > img_height or x_max > img_width:
                # Edge tile: shift back to maintain full tile size
                xmax = min(img_width, x_max)
                ymax = min(img_height, y_max)
                xmin = max(0, xmax - tile_size)
                ymin = max(0, ymax - tile_size)
                tiles.append(TileSpec(
                    row=row, col=col,
                    x=xmin, y=ymin,
                    width=xmax - xmin, height=ymax - ymin,
                ))
            else:
                tiles.append(TileSpec(
                    row=row, col=col,
                    x=x_min, y=y_min,
                    width=tile_size, height=tile_size,
                ))

            x_min = x_max - overlap_px
            col += 1

        y_min = y_max - overlap_px
        row += 1

    return tiles
