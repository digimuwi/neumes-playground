"""Tests for SSE progress streaming in the /recognize endpoint."""

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from htr_service.api import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def valid_image_bytes():
    """Create a simple valid image for testing."""
    img = Image.new("RGB", (100, 100), color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def invalid_image_bytes():
    """Create invalid image data."""
    return b"not an image"


def parse_sse_events(content: str) -> list[dict]:
    """Parse SSE event stream into list of JSON objects."""
    events = []
    for line in content.split("\n"):
        if line.startswith("data: "):
            data = line[6:]  # Strip "data: " prefix
            events.append(json.loads(data))
    return events


def _mock_recognition_pipeline():
    """Return a context manager that mocks the full recognition pipeline."""
    return (
        patch("htr_service.api.segment_image"),
        patch("htr_service.api.recognize_lines"),
        patch("htr_service.api.load_syllabifier"),
        patch("htr_service.api.extract_char_bboxes"),
        patch("htr_service.api.map_chars_to_syllables"),
        patch("htr_service.api.merge_char_bboxes"),
        patch("htr_service.api.syllable_x_ranges"),
        patch("htr_service.api.slice_line_polygon"),
        patch("htr_service.api.mask_text_regions"),
        patch("htr_service.api.detect_neumes"),
    )


class TestSSEProgressStream:
    """Tests for SSE streaming progress events."""

    def test_response_content_type(self, client, valid_image_bytes):
        """Test that response has text/event-stream content type."""
        with patch("htr_service.api.segment_image") as mock_segment:
            mock_segment.return_value = MagicMock(lines=[])

            response = client.post(
                "/recognize",
                files={"image": ("test.png", valid_image_bytes, "image/png")},
            )

            assert response.headers["content-type"].startswith("text/event-stream")

    def test_loading_event_emitted(self, client, valid_image_bytes):
        """Test that loading event is emitted at start."""
        with patch("htr_service.api.segment_image") as mock_segment:
            mock_segment.return_value = MagicMock(lines=[])

            response = client.post(
                "/recognize",
                files={"image": ("test.png", valid_image_bytes, "image/png")},
            )

            events = parse_sse_events(response.text)
            assert len(events) >= 1
            assert events[0]["stage"] == "loading"

    def test_all_stages_emitted_for_empty_image(self, client, valid_image_bytes):
        """Test event sequence for image with no detected lines."""
        with patch("htr_service.api.segment_image") as mock_segment:
            mock_segment.return_value = MagicMock(lines=[])

            response = client.post(
                "/recognize",
                files={"image": ("test.png", valid_image_bytes, "image/png")},
            )

            events = parse_sse_events(response.text)
            stages = [e["stage"] for e in events]

            assert "loading" in stages
            assert "segmenting" in stages
            assert "complete" in stages

    def test_complete_event_contains_result(self, client, valid_image_bytes):
        """Test that complete event contains the recognition result."""
        with patch("htr_service.api.segment_image") as mock_segment:
            mock_segment.return_value = MagicMock(lines=[])

            response = client.post(
                "/recognize",
                files={"image": ("test.png", valid_image_bytes, "image/png")},
            )

            events = parse_sse_events(response.text)
            complete_event = next(e for e in events if e["stage"] == "complete")

            assert "result" in complete_event
            assert "lines" in complete_event["result"]
            assert "neumes" in complete_event["result"]

    def test_error_event_on_invalid_image(self, client, invalid_image_bytes):
        """Test that error event is emitted for invalid image file."""
        response = client.post(
            "/recognize",
            files={"image": ("test.png", invalid_image_bytes, "image/png")},
        )

        events = parse_sse_events(response.text)
        error_events = [e for e in events if e["stage"] == "error"]

        assert len(error_events) == 1
        assert "message" in error_events[0]
        assert "Invalid image file" in error_events[0]["message"]

    def test_recognition_progress_events(self, client, valid_image_bytes):
        """Test that per-line recognition progress events are emitted."""
        mock_lines = [MagicMock(), MagicMock(), MagicMock()]
        mock_segmentation = MagicMock(lines=mock_lines)

        mock_rec_result = MagicMock(
            text="test",
            cuts=[],
            confidences=[],
            baseline=[[0, 0], [10, 0]],
            boundary=[[0, 0], [10, 0], [10, 10], [0, 10]],
        )

        with patch("htr_service.api.segment_image") as mock_segment, \
             patch("htr_service.api.recognize_lines") as mock_recognize, \
             patch("htr_service.api.load_syllabifier") as mock_syllabifier, \
             patch("htr_service.api.extract_char_bboxes") as mock_extract, \
             patch("htr_service.api.map_chars_to_syllables") as mock_map, \
             patch("htr_service.api.merge_char_bboxes") as mock_merge, \
             patch("htr_service.api.syllable_x_ranges") as mock_xranges, \
             patch("htr_service.api.slice_line_polygon") as mock_slice, \
             patch("htr_service.api.mask_text_regions") as mock_mask, \
             patch("htr_service.api.detect_neumes") as mock_detect:

            mock_segment.return_value = mock_segmentation

            def recognize_with_callback(img, seg, path, on_line_progress=None):
                if on_line_progress:
                    for i in range(3):
                        on_line_progress(i + 1, 3)
                return [mock_rec_result, mock_rec_result, mock_rec_result]

            mock_recognize.side_effect = recognize_with_callback
            mock_syllabifier.return_value = MagicMock()
            mock_extract.return_value = []
            mock_map.return_value = []
            mock_xranges.return_value = []
            mock_slice.return_value = []
            mock_mask.return_value = MagicMock()
            mock_detect.return_value = []

            response = client.post(
                "/recognize",
                files={"image": ("test.png", valid_image_bytes, "image/png")},
            )

            events = parse_sse_events(response.text)
            recognizing_events = [e for e in events if e["stage"] == "recognizing"]

            assert len(recognizing_events) == 3
            assert recognizing_events[0] == {"stage": "recognizing", "current": 1, "total": 3}
            assert recognizing_events[1] == {"stage": "recognizing", "current": 2, "total": 3}
            assert recognizing_events[2] == {"stage": "recognizing", "current": 3, "total": 3}

    def test_syllabifying_event_emitted(self, client, valid_image_bytes):
        """Test that syllabifying event is emitted before syllabification."""
        mock_lines = [MagicMock()]
        mock_segmentation = MagicMock(lines=mock_lines)
        mock_rec_result = MagicMock(
            text="test",
            cuts=[],
            confidences=[],
            baseline=[[0, 0], [10, 0]],
            boundary=[[0, 0], [10, 0], [10, 10], [0, 10]],
        )

        with patch("htr_service.api.segment_image") as mock_segment, \
             patch("htr_service.api.recognize_lines") as mock_recognize, \
             patch("htr_service.api.load_syllabifier") as mock_syllabifier, \
             patch("htr_service.api.extract_char_bboxes") as mock_extract, \
             patch("htr_service.api.map_chars_to_syllables") as mock_map, \
             patch("htr_service.api.merge_char_bboxes") as mock_merge, \
             patch("htr_service.api.syllable_x_ranges") as mock_xranges, \
             patch("htr_service.api.slice_line_polygon") as mock_slice, \
             patch("htr_service.api.mask_text_regions") as mock_mask, \
             patch("htr_service.api.detect_neumes") as mock_detect:

            mock_segment.return_value = mock_segmentation
            mock_recognize.return_value = [mock_rec_result]
            mock_syllabifier.return_value = MagicMock()
            mock_extract.return_value = []
            mock_map.return_value = []
            mock_xranges.return_value = []
            mock_slice.return_value = []
            mock_mask.return_value = MagicMock()
            mock_detect.return_value = []

            response = client.post(
                "/recognize",
                files={"image": ("test.png", valid_image_bytes, "image/png")},
            )

            events = parse_sse_events(response.text)
            stages = [e["stage"] for e in events]

            assert "syllabifying" in stages

    def test_detecting_event_emitted(self, client, valid_image_bytes):
        """Test that detecting stage event is emitted in the SSE stream."""
        mock_lines = [MagicMock()]
        mock_segmentation = MagicMock(lines=mock_lines)
        mock_rec_result = MagicMock(
            text="test",
            cuts=[],
            confidences=[],
            baseline=[[0, 0], [10, 0]],
            boundary=[[0, 0], [10, 0], [10, 10], [0, 10]],
        )

        with patch("htr_service.api.segment_image") as mock_segment, \
             patch("htr_service.api.recognize_lines") as mock_recognize, \
             patch("htr_service.api.load_syllabifier") as mock_syllabifier, \
             patch("htr_service.api.extract_char_bboxes") as mock_extract, \
             patch("htr_service.api.map_chars_to_syllables") as mock_map, \
             patch("htr_service.api.merge_char_bboxes") as mock_merge, \
             patch("htr_service.api.syllable_x_ranges") as mock_xranges, \
             patch("htr_service.api.slice_line_polygon") as mock_slice, \
             patch("htr_service.api.mask_text_regions") as mock_mask, \
             patch("htr_service.api.detect_neumes") as mock_detect:

            mock_segment.return_value = mock_segmentation
            mock_recognize.return_value = [mock_rec_result]
            mock_syllabifier.return_value = MagicMock()
            mock_extract.return_value = []
            mock_map.return_value = []
            mock_xranges.return_value = []
            mock_slice.return_value = []
            mock_mask.return_value = MagicMock()
            mock_detect.return_value = []

            response = client.post(
                "/recognize",
                files={"image": ("test.png", valid_image_bytes, "image/png")},
            )

            events = parse_sse_events(response.text)
            stages = [e["stage"] for e in events]

            assert "detecting" in stages
            assert stages.index("syllabifying") < stages.index("detecting") < stages.index("complete")

    def test_neume_detections_in_complete_event(self, client, valid_image_bytes):
        """Test that neume detections appear in the complete event's result."""
        from htr_service.models.types import BBox, NeumeDetection

        mock_lines = [MagicMock()]
        mock_segmentation = MagicMock(lines=mock_lines)
        mock_rec_result = MagicMock(
            text="test",
            cuts=[],
            confidences=[],
            baseline=[[0, 0], [10, 0]],
            boundary=[[0, 0], [10, 0], [10, 10], [0, 10]],
        )

        mock_neumes = [
            NeumeDetection(
                type="punctum",
                bbox=BBox(x=10, y=20, width=30, height=40),
                confidence=0.95,
            ),
            NeumeDetection(
                type="clivis",
                bbox=BBox(x=50, y=60, width=25, height=35),
                confidence=0.87,
            ),
        ]

        with patch("htr_service.api.segment_image") as mock_segment, \
             patch("htr_service.api.recognize_lines") as mock_recognize, \
             patch("htr_service.api.load_syllabifier") as mock_syllabifier, \
             patch("htr_service.api.extract_char_bboxes") as mock_extract, \
             patch("htr_service.api.map_chars_to_syllables") as mock_map, \
             patch("htr_service.api.merge_char_bboxes") as mock_merge, \
             patch("htr_service.api.syllable_x_ranges") as mock_xranges, \
             patch("htr_service.api.slice_line_polygon") as mock_slice, \
             patch("htr_service.api.mask_text_regions") as mock_mask, \
             patch("htr_service.api.detect_neumes") as mock_detect:

            mock_segment.return_value = mock_segmentation
            mock_recognize.return_value = [mock_rec_result]
            mock_syllabifier.return_value = MagicMock()
            mock_extract.return_value = []
            mock_map.return_value = []
            mock_xranges.return_value = []
            mock_slice.return_value = []
            mock_mask.return_value = MagicMock()
            mock_detect.return_value = mock_neumes

            response = client.post(
                "/recognize",
                files={"image": ("test.png", valid_image_bytes, "image/png")},
            )

            events = parse_sse_events(response.text)
            complete_event = next(e for e in events if e["stage"] == "complete")

            neumes = complete_event["result"]["neumes"]
            assert len(neumes) == 2
            assert neumes[0]["type"] == "punctum"
            assert neumes[0]["bbox"] == {"x": 10, "y": 20, "width": 30, "height": 40}
            assert neumes[0]["confidence"] == 0.95
            assert neumes[1]["type"] == "clivis"
            assert neumes[1]["confidence"] == 0.87

    def test_neumes_empty_when_detect_returns_empty(self, client, valid_image_bytes):
        """Test that neumes array is empty when detect_neumes returns empty list."""
        mock_lines = [MagicMock()]
        mock_segmentation = MagicMock(lines=mock_lines)
        mock_rec_result = MagicMock(
            text="test",
            cuts=[],
            confidences=[],
            baseline=[[0, 0], [10, 0]],
            boundary=[[0, 0], [10, 0], [10, 10], [0, 10]],
        )

        with patch("htr_service.api.segment_image") as mock_segment, \
             patch("htr_service.api.recognize_lines") as mock_recognize, \
             patch("htr_service.api.load_syllabifier") as mock_syllabifier, \
             patch("htr_service.api.extract_char_bboxes") as mock_extract, \
             patch("htr_service.api.map_chars_to_syllables") as mock_map, \
             patch("htr_service.api.merge_char_bboxes") as mock_merge, \
             patch("htr_service.api.syllable_x_ranges") as mock_xranges, \
             patch("htr_service.api.slice_line_polygon") as mock_slice, \
             patch("htr_service.api.mask_text_regions") as mock_mask, \
             patch("htr_service.api.detect_neumes") as mock_detect:

            mock_segment.return_value = mock_segmentation
            mock_recognize.return_value = [mock_rec_result]
            mock_syllabifier.return_value = MagicMock()
            mock_extract.return_value = []
            mock_map.return_value = []
            mock_xranges.return_value = []
            mock_slice.return_value = []
            mock_mask.return_value = MagicMock()
            mock_detect.return_value = []

            response = client.post(
                "/recognize",
                files={"image": ("test.png", valid_image_bytes, "image/png")},
            )

            events = parse_sse_events(response.text)
            complete_event = next(e for e in events if e["stage"] == "complete")

            assert complete_event["result"]["neumes"] == []
