"""Tests for segmentation module."""

from htr_service.pipeline.segmentation import build_single_line_segmentation


class TestBuildSingleLineSegmentation:
    """Tests for build_single_line_segmentation."""

    def test_baseline_at_vertical_center(self):
        seg = build_single_line_segmentation(400, 80)
        line = seg.lines[0]
        assert line.baseline == [(0, 40), (400, 40)]

    def test_boundary_is_full_rectangle(self):
        seg = build_single_line_segmentation(400, 80)
        line = seg.lines[0]
        assert line.boundary == [(0, 0), (400, 0), (400, 80), (0, 80)]

    def test_segmentation_type_is_baselines(self):
        seg = build_single_line_segmentation(200, 50)
        assert seg.type == "baselines"

    def test_single_line(self):
        seg = build_single_line_segmentation(200, 50)
        assert len(seg.lines) == 1

    def test_text_direction(self):
        seg = build_single_line_segmentation(200, 50)
        assert seg.text_direction == "horizontal-lr"

    def test_odd_height_floors_baseline(self):
        seg = build_single_line_segmentation(300, 77)
        line = seg.lines[0]
        assert line.baseline == [(0, 38), (300, 38)]
