"""Text masking for neume detection preprocessing.

Erases text from manuscript images by filling Kraken segmentation boundary
polygons with locally-sampled parchment color. The result is an RGB image
with only neume ink remaining, suitable for YOLOv8 object detection.
"""

import logging

import numpy as np
from PIL import Image, ImageDraw
from kraken.containers import Segmentation
from shapely.geometry import Polygon as ShapelyPolygon

logger = logging.getLogger(__name__)

# Dilation amount in pixels for the sampling ring around each text polygon.
_DILATION_PX = 5

# Minimum number of pixels in the sampling ring to compute a reliable median.
# If fewer pixels are available, fall back to a broader sampling area.
_MIN_RING_PIXELS = 10


def mask_polygon_regions(
    image: Image.Image,
    polygons: list[list[tuple[int, int]]],
) -> Image.Image:
    """Erase regions from an RGB image using a list of boundary polygons.

    Each polygon is filled with locally-sampled parchment color, identical
    to `mask_text_regions` but driven by explicit polygon coordinates rather
    than a Kraken Segmentation object.

    Args:
        image: PIL RGB image of the manuscript.
        polygons: List of polygon boundaries. Each polygon is a list of
            (x, y) coordinate tuples.

    Returns:
        A new PIL RGB image with polygon regions filled. Input is not modified.
    """
    if not polygons:
        return image.copy()

    img_array = np.array(image)
    height, width = img_array.shape[:2]

    for boundary in polygons:
        if not boundary or len(boundary) < 3:
            continue
        fill_color = _sample_parchment_color(boundary, img_array, width, height)
        _fill_polygon(boundary, fill_color, img_array, width, height)

    return Image.fromarray(img_array)


def mask_text_regions(image: Image.Image, segmentation: Segmentation) -> Image.Image:
    """Erase text from an RGB image using Kraken segmentation boundary polygons.

    For each text line's boundary polygon, the region is filled with the
    median color of the surrounding parchment, sampled from a thin ring
    around the polygon.

    Args:
        image: PIL RGB image of the manuscript.
        segmentation: Kraken Segmentation result with line boundary polygons.

    Returns:
        A new PIL RGB image with text regions filled with parchment color.
        The input image is not modified.
    """
    if not segmentation.lines:
        return image.copy()

    img_array = np.array(image)
    height, width = img_array.shape[:2]

    for line in segmentation.lines:
        boundary = line.boundary
        if not boundary:
            continue

        # Ensure polygon has at least 3 points
        if len(boundary) < 3:
            logger.debug("Skipping line with fewer than 3 boundary points")
            continue

        fill_color = _sample_parchment_color(boundary, img_array, width, height)
        _fill_polygon(boundary, fill_color, img_array, width, height)

    return Image.fromarray(img_array)


def _sample_parchment_color(
    boundary: list[tuple[int, int]],
    img_array: np.ndarray,
    width: int,
    height: int,
) -> tuple[int, int, int]:
    """Sample the parchment color surrounding a text polygon.

    Dilates the polygon outward, then samples pixel colors in the ring
    between the original and dilated boundary. Returns the per-channel
    median as the fill color.

    Falls back to sampling the polygon's bounding box area (excluding
    the polygon interior) if the ring has too few pixels.
    """
    coords = [(float(x), float(y)) for x, y in boundary]
    try:
        poly = ShapelyPolygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)  # Fix self-intersections
        dilated = poly.buffer(_DILATION_PX)
    except Exception:
        logger.debug("Shapely polygon creation failed, using fallback color")
        return _fallback_color(boundary, img_array, width, height)

    # Rasterize the original and dilated polygons to masks
    original_mask = _rasterize_polygon(boundary, width, height)
    dilated_coords = list(dilated.exterior.coords)
    dilated_boundary = [(int(round(x)), int(round(y))) for x, y in dilated_coords]
    dilated_mask = _rasterize_polygon(dilated_boundary, width, height)

    # Sampling ring = dilated AND NOT original
    ring_mask = dilated_mask & ~original_mask

    ring_pixels = img_array[ring_mask]
    if len(ring_pixels) < _MIN_RING_PIXELS:
        return _fallback_color(boundary, img_array, width, height)

    median_color = np.median(ring_pixels, axis=0).astype(np.uint8)
    return int(median_color[0]), int(median_color[1]), int(median_color[2])


def _fallback_color(
    boundary: list[tuple[int, int]],
    img_array: np.ndarray,
    width: int,
    height: int,
) -> tuple[int, int, int]:
    """Fallback color sampling using the bounding box area around the polygon.

    Samples pixels in the polygon's bounding box but outside the polygon
    interior. If that also has too few pixels, returns the image-wide median.
    """
    xs = [pt[0] for pt in boundary]
    ys = [pt[1] for pt in boundary]

    # Expand bbox by the dilation amount, clipped to image bounds
    x_min = max(0, min(xs) - _DILATION_PX)
    x_max = min(width, max(xs) + _DILATION_PX)
    y_min = max(0, min(ys) - _DILATION_PX)
    y_max = min(height, max(ys) + _DILATION_PX)

    original_mask = _rasterize_polygon(boundary, width, height)

    # Bounding box mask
    bbox_mask = np.zeros((height, width), dtype=bool)
    bbox_mask[y_min:y_max, x_min:x_max] = True

    # Sample bbox pixels excluding the polygon interior
    sample_mask = bbox_mask & ~original_mask
    sample_pixels = img_array[sample_mask]

    if len(sample_pixels) >= _MIN_RING_PIXELS:
        median_color = np.median(sample_pixels, axis=0).astype(np.uint8)
        return int(median_color[0]), int(median_color[1]), int(median_color[2])

    # Last resort: image-wide median
    median_color = np.median(
        img_array.reshape(-1, img_array.shape[-1]), axis=0
    ).astype(np.uint8)
    return int(median_color[0]), int(median_color[1]), int(median_color[2])


def _rasterize_polygon(
    boundary: list[tuple[int, int]], width: int, height: int
) -> np.ndarray:
    """Rasterize a polygon to a boolean mask.

    Args:
        boundary: List of (x, y) vertex coordinates.
        width: Image width.
        height: Image height.

    Returns:
        Boolean numpy array of shape (height, width) with True inside the polygon.
    """
    mask_img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask_img)
    draw.polygon([(x, y) for x, y in boundary], fill=255)
    return np.array(mask_img, dtype=bool)


def _fill_polygon(
    boundary: list[tuple[int, int]],
    color: tuple[int, int, int],
    img_array: np.ndarray,
    width: int,
    height: int,
) -> None:
    """Fill a polygon region in the image array with a solid color.

    Modifies img_array in place.
    """
    mask = _rasterize_polygon(boundary, width, height)
    img_array[mask] = color
