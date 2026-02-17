"""Tests for neume detection module."""

import logging
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from PIL import Image

from htr_service.pipeline import neume_detection
from htr_service.pipeline.neume_detection import (
    detect_neumes,
    detect_neumes_direct,
    YOLO_MODEL_PATH,
)
from htr_service.pipeline.tiling import compute_tile_size


def _make_segmentation(lines=None):
    """Create a mock Kraken Segmentation with given lines."""
    seg = MagicMock()
    seg.lines = lines or []
    return seg


def _make_line(baseline_ys, boundary_top, boundary_bottom):
    """Create a mock line with baseline and boundary.

    Args:
        baseline_ys: List of y-values for baseline points (x doesn't matter here).
        boundary_top: Top y-value of the boundary polygon.
        boundary_bottom: Bottom y-value of the boundary polygon.
    """
    line = MagicMock()
    line.baseline = [(100, y) for y in baseline_ys]
    line.boundary = [
        (50, boundary_top),
        (200, boundary_top),
        (200, boundary_bottom),
        (50, boundary_bottom),
    ]
    return line


def _solid_image(width=200, height=200):
    """Create a solid RGB test image."""
    return Image.new("RGB", (width, height), color=(180, 160, 140))


class TestDetectNeumesNoModel:
    """Tests for detect_neumes when no YOLO model exists."""

    def test_returns_empty_list(self, tmp_path, monkeypatch):
        """Returns empty list when no model file exists."""
        monkeypatch.setattr(neume_detection, "YOLO_MODEL_PATH", tmp_path / "nonexistent.pt")
        # Clear cache
        monkeypatch.setattr(neume_detection, "_yolo_cache", None)

        result = detect_neumes(_solid_image(), _make_segmentation())
        assert result == []

    def test_logs_warning(self, tmp_path, monkeypatch, caplog):
        """Logs a warning when no model file exists."""
        monkeypatch.setattr(neume_detection, "YOLO_MODEL_PATH", tmp_path / "nonexistent.pt")
        monkeypatch.setattr(neume_detection, "_yolo_cache", None)

        with caplog.at_level(logging.WARNING, logger="htr_service.pipeline.neume_detection"):
            detect_neumes(_solid_image(), _make_segmentation())

        assert any("No neume detection model" in msg for msg in caplog.messages)


class TestComputeTileSize:
    """Tests for compute_tile_size."""

    def test_multiple_lines_computes_from_median_gap(self):
        """With multiple lines, tile size = median gap * 4, clamped."""
        # Three lines with gaps of 40px and 60px → median gap = 50 → tile = 200
        # But 200 < 320 minimum → clamped to 320
        lines = [
            _make_line([100], 80, 120),    # Line 1: boundary 80-120
            _make_line([200], 160, 200),   # Line 2: boundary 160-200, gap from 120 to 160 = 40
            _make_line([320], 260, 300),   # Line 3: boundary 260-300, gap from 200 to 260 = 60
        ]
        seg = _make_segmentation(lines)
        result = compute_tile_size(seg)
        # median([40, 60]) = 50, * 4 = 200, clamped to 320
        assert result == 320

    def test_large_gaps_clamped_to_max(self):
        """Large interlinear gaps produce tile size clamped to 1280."""
        lines = [
            _make_line([100], 80, 120),
            _make_line([600], 500, 540),   # Gap from 120 to 500 = 380
            _make_line([1100], 1000, 1040),  # Gap from 540 to 1000 = 460
        ]
        seg = _make_segmentation(lines)
        result = compute_tile_size(seg)
        # median([380, 460]) = 420, * 4 = 1680, clamped to 1280
        assert result == 1280

    def test_normal_gap_unclamped(self):
        """Normal interlinear gaps produce an unclamped tile size."""
        # Gaps of 100px each → median = 100 → tile = 400 (within [320, 1280])
        lines = [
            _make_line([100], 80, 120),
            _make_line([250], 220, 260),   # Gap from 120 to 220 = 100
            _make_line([400], 360, 400),   # Gap from 260 to 360 = 100
        ]
        seg = _make_segmentation(lines)
        result = compute_tile_size(seg)
        assert result == 400

    def test_fewer_than_two_lines_returns_default(self):
        """Fewer than 2 lines returns default 640."""
        assert compute_tile_size(_make_segmentation([])) == 640
        assert compute_tile_size(_make_segmentation([_make_line([100], 80, 120)])) == 640

    def test_lines_without_baselines_returns_default(self):
        """Lines without baselines are skipped; if <2 remain, returns default."""
        line_no_baseline = MagicMock()
        line_no_baseline.baseline = []
        line_no_baseline.boundary = [(50, 80), (200, 80), (200, 120), (50, 120)]

        seg = _make_segmentation([line_no_baseline])
        assert compute_tile_size(seg) == 640


class TestDetectNeumesWithModel:
    """Tests for detect_neumes with a mocked YOLO model."""

    def _mock_sahi_prediction(self, name, minx, miny, maxx, maxy, score):
        """Create a mock SAHI object prediction."""
        pred = MagicMock()
        pred.category.name = name
        pred.bbox.minx = minx
        pred.bbox.miny = miny
        pred.bbox.maxx = maxx
        pred.bbox.maxy = maxy
        pred.score.value = score
        return pred

    def test_returns_neume_detections(self, tmp_path, monkeypatch):
        """With a model, returns NeumeDetection objects with correct fields."""
        mock_yolo_instance = MagicMock()

        mock_result = MagicMock()
        mock_result.object_prediction_list = [
            self._mock_sahi_prediction("punctum", 10, 20, 30, 40, 0.92),
            self._mock_sahi_prediction("clivis", 50, 60, 80, 90, 0.78),
        ]

        mock_auto_cls = MagicMock()
        mock_auto_cls.from_pretrained.return_value = MagicMock()

        # Bypass model loading entirely; mock SAHI via sys.modules for lazy imports
        monkeypatch.setattr(neume_detection, "_load_yolo_model", lambda: mock_yolo_instance)

        mock_sahi = MagicMock()
        mock_sahi.AutoDetectionModel = mock_auto_cls
        mock_sahi_predict = MagicMock()
        mock_sahi_predict.get_sliced_prediction = MagicMock(return_value=mock_result)

        with patch.dict("sys.modules", {"sahi": mock_sahi, "sahi.predict": mock_sahi_predict}):
            seg = _make_segmentation([
                _make_line([100], 80, 120),
                _make_line([250], 220, 260),
            ])
            detections = detect_neumes(_solid_image(), seg)

        assert len(detections) == 2

        assert detections[0].type == "punctum"
        assert detections[0].bbox.x == 10
        assert detections[0].bbox.y == 20
        assert detections[0].bbox.width == 20
        assert detections[0].bbox.height == 20
        assert detections[0].confidence == pytest.approx(0.92)

        assert detections[1].type == "clivis"
        assert detections[1].confidence == pytest.approx(0.78)

class TestDetectNeumesDirect:
    """Tests for detect_neumes_direct (no SAHI, no masking)."""

    def test_returns_empty_list_when_no_model(self, tmp_path, monkeypatch):
        """Returns empty list when no YOLO model file exists."""
        monkeypatch.setattr(neume_detection, "YOLO_MODEL_PATH", tmp_path / "nonexistent.pt")
        monkeypatch.setattr(neume_detection, "_yolo_cache", None)

        result = detect_neumes_direct(_solid_image())
        assert result == []

    def test_returns_detections(self, monkeypatch):
        """Returns NeumeDetection objects from direct YOLO prediction."""
        import torch

        mock_box = MagicMock()
        mock_box.xyxy = [torch.tensor([10.0, 20.0, 30.0, 40.0])]
        mock_box.cls = [torch.tensor(0)]
        mock_box.conf = [torch.tensor(0.85)]

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.names = {0: "punctum"}

        mock_model = MagicMock()
        mock_model.predict.return_value = [mock_result]

        monkeypatch.setattr(neume_detection, "_load_yolo_model", lambda: mock_model)

        detections = detect_neumes_direct(_solid_image(100, 100))

        assert len(detections) == 1
        assert detections[0].type == "punctum"
        assert detections[0].bbox.x == 10
        assert detections[0].bbox.y == 20
        assert detections[0].bbox.width == 20
        assert detections[0].bbox.height == 20
        assert detections[0].confidence == pytest.approx(0.85)
        mock_model.predict.assert_called_once()

    def test_logs_warning_when_no_model(self, tmp_path, monkeypatch, caplog):
        """Logs a warning when no YOLO model file exists."""
        monkeypatch.setattr(neume_detection, "YOLO_MODEL_PATH", tmp_path / "nonexistent.pt")
        monkeypatch.setattr(neume_detection, "_yolo_cache", None)

        with caplog.at_level(logging.WARNING, logger="htr_service.pipeline.neume_detection"):
            detect_neumes_direct(_solid_image())

        assert any("No neume detection model" in msg for msg in caplog.messages)


class TestModelCaching:
    """Tests for YOLO model caching behavior."""

    def test_model_cached_across_calls(self, tmp_path, monkeypatch):
        """Model is loaded once and reused on second call."""
        model_path = tmp_path / "neume_detector.pt"
        model_path.write_text("fake")
        monkeypatch.setattr(neume_detection, "YOLO_MODEL_PATH", model_path)
        monkeypatch.setattr(neume_detection, "_yolo_cache", None)

        mock_yolo_instance = MagicMock()
        mock_yolo_cls = MagicMock(return_value=mock_yolo_instance)
        mock_ultralytics = MagicMock(YOLO=mock_yolo_cls)

        with patch.dict("sys.modules", {"ultralytics": mock_ultralytics}):
            from htr_service.pipeline.neume_detection import _load_yolo_model

            model1 = _load_yolo_model()
            model2 = _load_yolo_model()

        assert model1 is mock_yolo_instance
        assert model2 is mock_yolo_instance
        # YOLO constructor called exactly once
        mock_yolo_cls.assert_called_once()
