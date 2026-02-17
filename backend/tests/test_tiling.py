"""Tests for shared tiling module."""

from unittest.mock import MagicMock

import pytest

from htr_service.pipeline.tiling import (
    TILE_SIZE_DEFAULT,
    TILE_SIZE_MAX,
    TILE_SIZE_MIN,
    compute_tile_size,
    generate_tile_grid,
)


# --- Helpers ---


def _make_segmentation(lines=None):
    """Create a mock Kraken Segmentation with given lines."""
    seg = MagicMock()
    seg.lines = lines or []
    return seg


def _make_line(baseline_ys, boundary_top, boundary_bottom):
    """Create a mock line with baseline and boundary."""
    line = MagicMock()
    line.baseline = [(100, y) for y in baseline_ys]
    line.boundary = [
        (50, boundary_top),
        (200, boundary_top),
        (200, boundary_bottom),
        (50, boundary_bottom),
    ]
    return line


# --- compute_tile_size ---


class TestComputeTileSize:
    """Tests for compute_tile_size."""

    def test_multiple_lines_computes_from_median_gap(self):
        """With multiple lines, tile size = median gap * 4, clamped."""
        lines = [
            _make_line([100], 80, 120),
            _make_line([200], 160, 200),   # gap from 120 to 160 = 40
            _make_line([320], 260, 300),   # gap from 200 to 260 = 60
        ]
        seg = _make_segmentation(lines)
        result = compute_tile_size(seg)
        # median([40, 60]) = 50, * 4 = 200, clamped to 320
        assert result == TILE_SIZE_MIN

    def test_large_gaps_clamped_to_max(self):
        """Large interlinear gaps produce tile size clamped to 1280."""
        lines = [
            _make_line([100], 80, 120),
            _make_line([600], 500, 540),   # gap from 120 to 500 = 380
            _make_line([1100], 1000, 1040),  # gap from 540 to 1000 = 460
        ]
        seg = _make_segmentation(lines)
        result = compute_tile_size(seg)
        # median([380, 460]) = 420, * 4 = 1680, clamped to 1280
        assert result == TILE_SIZE_MAX

    def test_normal_gap_unclamped(self):
        """Normal interlinear gaps produce an unclamped tile size."""
        lines = [
            _make_line([100], 80, 120),
            _make_line([250], 220, 260),   # gap from 120 to 220 = 100
            _make_line([400], 360, 400),   # gap from 260 to 360 = 100
        ]
        seg = _make_segmentation(lines)
        result = compute_tile_size(seg)
        assert result == 400

    def test_fewer_than_two_lines_returns_default(self):
        """Fewer than 2 lines returns default 640."""
        assert compute_tile_size(_make_segmentation([])) == TILE_SIZE_DEFAULT
        assert compute_tile_size(_make_segmentation([_make_line([100], 80, 120)])) == TILE_SIZE_DEFAULT

    def test_lines_without_baselines_returns_default(self):
        """Lines without baselines are skipped; if <2 remain, returns default."""
        line_no_baseline = MagicMock()
        line_no_baseline.baseline = []
        line_no_baseline.boundary = [(50, 80), (200, 80), (200, 120), (50, 120)]

        seg = _make_segmentation([line_no_baseline])
        assert compute_tile_size(seg) == TILE_SIZE_DEFAULT


# --- generate_tile_grid ---


class TestGenerateTileGrid:
    """Tests for generate_tile_grid."""

    def test_single_tile_small_image(self):
        """Image smaller than tile_size produces exactly 1 tile."""
        tiles = generate_tile_grid(200, 300, tile_size=640)
        assert len(tiles) == 1
        t = tiles[0]
        assert t.row == 0 and t.col == 0
        assert t.x == 0 and t.y == 0
        assert t.width == 200 and t.height == 300

    def test_image_equals_tile_size(self):
        """Image exactly equal to tile_size produces exactly 1 tile."""
        tiles = generate_tile_grid(640, 640, tile_size=640)
        assert len(tiles) == 1
        t = tiles[0]
        assert t.x == 0 and t.y == 0
        assert t.width == 640 and t.height == 640

    def test_known_grid(self):
        """Known grid: 1000x1000 image with tile_size=640, overlap=0.2."""
        # overlap = int(0.2 * 640) = 128, stride = 640 - 128 = 512
        # x_starts: 0, then 0+640-128=512, then 512+640=1152>1000 → stop
        # y_starts: same
        # So 2x2 = 4 tiles
        tiles = generate_tile_grid(1000, 1000, tile_size=640, overlap_ratio=0.2)
        assert len(tiles) == 4

        # Tile (0,0): regular, fully inside
        t00 = tiles[0]
        assert t00.row == 0 and t00.col == 0
        assert t00.x == 0 and t00.y == 0
        assert t00.width == 640 and t00.height == 640

        # Tile (0,1): right edge, shifted back
        t01 = tiles[1]
        assert t01.row == 0 and t01.col == 1
        assert t01.x == 1000 - 640  # 360
        assert t01.width == 640

        # Tile (1,0): bottom edge
        t10 = tiles[2]
        assert t10.row == 1 and t10.col == 0
        assert t10.y == 1000 - 640  # 360
        assert t10.height == 640

        # Tile (1,1): corner
        t11 = tiles[3]
        assert t11.row == 1 and t11.col == 1
        assert t11.x == 360 and t11.y == 360
        assert t11.width == 640 and t11.height == 640

    def test_tiles_cover_entire_image(self):
        """Union of all tiles covers every pixel of the image."""
        img_w, img_h = 1500, 900
        tiles = generate_tile_grid(img_w, img_h, tile_size=640, overlap_ratio=0.2)

        # Check corners are covered
        for px, py in [(0, 0), (img_w - 1, 0), (0, img_h - 1), (img_w - 1, img_h - 1)]:
            covered = any(
                t.x <= px < t.x + t.width and t.y <= py < t.y + t.height
                for t in tiles
            )
            assert covered, f"Pixel ({px}, {py}) not covered by any tile"

    def test_no_overlap_partitions_exactly(self):
        """With overlap_ratio=0 on a divisible image, tiles partition without overlap."""
        tiles = generate_tile_grid(640, 640, tile_size=320, overlap_ratio=0.0)
        assert len(tiles) == 4

        xs = sorted(set(t.x for t in tiles))
        ys = sorted(set(t.y for t in tiles))
        assert xs == [0, 320]
        assert ys == [0, 320]

    def test_overlap_produces_more_tiles(self):
        """20% overlap produces more tiles than 0% overlap."""
        tiles_no_overlap = generate_tile_grid(1280, 1280, tile_size=640, overlap_ratio=0.0)
        tiles_with_overlap = generate_tile_grid(1280, 1280, tile_size=640, overlap_ratio=0.2)
        assert len(tiles_with_overlap) > len(tiles_no_overlap)

    def test_edge_tiles_have_full_size_when_possible(self):
        """Edge tiles are shifted back to maintain full tile_size when image is larger."""
        tiles = generate_tile_grid(800, 800, tile_size=640, overlap_ratio=0.2)
        for t in tiles:
            # All tiles should be 640x640 since image (800) > tile_size (640)
            assert t.width == 640
            assert t.height == 640

    def test_matches_sahi_algorithm(self):
        """Output matches SAHI's get_slice_bboxes for a known configuration."""
        from sahi.slicing import get_slice_bboxes

        img_w, img_h = 1200, 900
        tile_size = 500
        overlap = 0.2

        sahi_bboxes = get_slice_bboxes(
            image_height=img_h, image_width=img_w,
            slice_height=tile_size, slice_width=tile_size,
            overlap_height_ratio=overlap, overlap_width_ratio=overlap,
        )

        our_tiles = generate_tile_grid(img_w, img_h, tile_size, overlap)

        assert len(our_tiles) == len(sahi_bboxes)
        for tile, sahi_bbox in zip(our_tiles, sahi_bboxes):
            x_min, y_min, x_max, y_max = sahi_bbox
            assert tile.x == x_min
            assert tile.y == y_min
            assert tile.x + tile.width == x_max
            assert tile.y + tile.height == y_max
