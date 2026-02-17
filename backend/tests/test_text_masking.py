"""Tests for text masking module."""

from unittest.mock import MagicMock

import numpy as np
import pytest
from PIL import Image

from htr_service.pipeline.text_masking import mask_polygon_regions, mask_text_regions


def _make_segmentation(lines=None):
    """Create a mock Kraken Segmentation with given lines."""
    seg = MagicMock()
    seg.lines = lines or []
    return seg


def _make_line(boundary):
    """Create a mock Kraken line with a boundary polygon."""
    line = MagicMock()
    line.boundary = boundary
    return line


def _solid_image(width, height, color):
    """Create a solid-color RGB image."""
    return Image.new("RGB", (width, height), color=color)


class TestMaskTextRegions:
    """Tests for the mask_text_regions function."""

    def test_polygon_regions_filled_and_outside_unchanged(self):
        """Text polygon regions are filled; non-polygon pixels are unchanged."""
        # Create 100x100 image: beige background with black text inside polygon
        bg_color = (200, 180, 150)
        text_color = (20, 20, 20)
        img = _solid_image(100, 100, bg_color)
        arr = np.array(img)
        # Draw "text" (dark pixels) inside the polygon area
        arr[22:38, 22:58] = text_color
        img = Image.fromarray(arr)

        polygon = [(20, 20), (60, 20), (60, 40), (20, 40)]
        seg = _make_segmentation([_make_line(polygon)])

        result = mask_text_regions(img, seg)
        result_array = np.array(result)

        # Pixels inside the polygon should be filled with parchment color,
        # not the dark "text" color
        center_pixel = result_array[30, 40]
        assert center_pixel[0] > 100, (
            f"Polygon fill {center_pixel} should be bright (parchment), not dark (text)"
        )

        # Pixels far outside the polygon should be unchanged (original bg)
        corner_pixel = result_array[0, 0]
        np.testing.assert_array_equal(corner_pixel, bg_color)

        far_pixel = result_array[90, 90]
        np.testing.assert_array_equal(far_pixel, bg_color)

    def test_input_image_not_modified(self):
        """The original image pixel data is unchanged after the call."""
        img = _solid_image(100, 100, (128, 128, 128))
        original_data = np.array(img).copy()

        polygon = [(10, 10), (50, 10), (50, 50), (10, 50)]
        seg = _make_segmentation([_make_line(polygon)])

        mask_text_regions(img, seg)

        # Original image should be untouched
        np.testing.assert_array_equal(np.array(img), original_data)

    def test_local_color_sampling_two_regions(self):
        """Each polygon is filled with its own local parchment color."""
        # Create 200x200 image: top half red(200,50,50), bottom half green(50,200,50)
        img = Image.new("RGB", (200, 200))
        arr = np.array(img)
        arr[:100, :] = [200, 50, 50]   # Top half: red-ish
        arr[100:, :] = [50, 200, 50]   # Bottom half: green-ish
        img = Image.fromarray(arr)

        # Two polygons: one in the top half, one in the bottom half
        top_polygon = [(40, 30), (160, 30), (160, 60), (40, 60)]
        bottom_polygon = [(40, 130), (160, 130), (160, 160), (40, 160)]

        seg = _make_segmentation([
            _make_line(top_polygon),
            _make_line(bottom_polygon),
        ])

        result = mask_text_regions(img, seg)
        result_array = np.array(result)

        # Top polygon fill should be reddish (from surrounding red parchment)
        top_fill = result_array[45, 100]
        assert top_fill[0] > top_fill[1], (
            f"Top polygon fill {top_fill} should be reddish (R > G)"
        )

        # Bottom polygon fill should be greenish (from surrounding green parchment)
        bottom_fill = result_array[145, 100]
        assert bottom_fill[1] > bottom_fill[0], (
            f"Bottom polygon fill {bottom_fill} should be greenish (G > R)"
        )

    def test_zero_lines_returns_unchanged_copy(self):
        """Zero lines in segmentation returns image unchanged."""
        img = _solid_image(100, 100, (42, 42, 42))
        seg = _make_segmentation([])

        result = mask_text_regions(img, seg)

        np.testing.assert_array_equal(np.array(result), np.array(img))
        # Should be a copy, not the same object
        assert result is not img

    def test_empty_boundary_skipped(self):
        """Lines with empty boundary are skipped without error."""
        img = _solid_image(100, 100, (100, 100, 100))

        seg = _make_segmentation([
            _make_line([]),           # Empty boundary
            _make_line(None),         # None boundary
            _make_line([(20, 20), (80, 20), (80, 80), (20, 80)]),  # Valid
        ])

        result = mask_text_regions(img, seg)

        # Should not raise, and the valid polygon should be processed
        result_array = np.array(result)
        # Center of the valid polygon should be filled
        # (surrounding color is (100,100,100), so fill will also be ~(100,100,100),
        # but the function ran without error, which is the key assertion)
        assert result_array.shape == (100, 100, 3)

    def test_boundary_with_two_points_skipped(self):
        """Lines with fewer than 3 boundary points are skipped."""
        img = _solid_image(100, 100, (100, 100, 100))
        seg = _make_segmentation([
            _make_line([(10, 10), (50, 50)]),  # Only 2 points
        ])

        result = mask_text_regions(img, seg)

        # Image should be unchanged (polygon skipped)
        np.testing.assert_array_equal(np.array(result), np.array(img))

    def test_polygon_near_image_edge(self):
        """Polygon near image edge: sampling ring clipped to bounds."""
        img = _solid_image(100, 100, (180, 160, 140))

        # Polygon touching the top-left corner
        edge_polygon = [(0, 0), (40, 0), (40, 20), (0, 20)]
        seg = _make_segmentation([_make_line(edge_polygon)])

        result = mask_text_regions(img, seg)

        # Should not raise — ring is clipped to image bounds
        result_array = np.array(result)

        # Fill color should be close to (180, 160, 140) since the surrounding
        # parchment is uniform
        fill_pixel = result_array[10, 20]
        assert abs(int(fill_pixel[0]) - 180) <= 5
        assert abs(int(fill_pixel[1]) - 160) <= 5
        assert abs(int(fill_pixel[2]) - 140) <= 5

        # Pixels far from the polygon should be unchanged
        far_pixel = result_array[90, 90]
        np.testing.assert_array_equal(far_pixel, [180, 160, 140])


class TestMaskPolygonRegions:
    """Tests for the mask_polygon_regions function."""

    def test_multiple_polygons_masked(self):
        """Multiple polygons are all filled with parchment color."""
        bg_color = (200, 180, 150)
        img = _solid_image(200, 200, bg_color)
        arr = np.array(img)
        # Dark regions inside polygon areas
        arr[25:35, 25:55] = (20, 20, 20)
        arr[125:135, 125:155] = (20, 20, 20)
        img = Image.fromarray(arr)

        polygons = [
            [(20, 20), (60, 20), (60, 40), (20, 40)],
            [(120, 120), (160, 120), (160, 140), (120, 140)],
        ]

        result = mask_polygon_regions(img, polygons)
        result_array = np.array(result)

        # Both polygon centers should be bright (filled with parchment)
        assert result_array[30, 40][0] > 100
        assert result_array[130, 140][0] > 100

    def test_empty_polygon_list_returns_copy(self):
        """Empty polygon list returns an unchanged copy."""
        img = _solid_image(100, 100, (42, 42, 42))

        result = mask_polygon_regions(img, [])

        np.testing.assert_array_equal(np.array(result), np.array(img))
        assert result is not img

    def test_input_image_not_modified(self):
        """Original image is not modified."""
        img = _solid_image(100, 100, (128, 128, 128))
        original_data = np.array(img).copy()

        polygons = [[(10, 10), (50, 10), (50, 50), (10, 50)]]
        mask_polygon_regions(img, polygons)

        np.testing.assert_array_equal(np.array(img), original_data)

    def test_skips_degenerate_polygons(self):
        """Polygons with fewer than 3 points are skipped without error."""
        img = _solid_image(100, 100, (100, 100, 100))

        polygons = [
            [],                          # empty
            [(10, 10), (50, 50)],        # only 2 points
            [(20, 20), (80, 20), (80, 80), (20, 80)],  # valid
        ]

        result = mask_polygon_regions(img, polygons)

        # Should not raise
        assert np.array(result).shape == (100, 100, 3)
