"""Text recognition using Kraken OCR."""

import logging
from pathlib import Path
from typing import Callable, NamedTuple, Optional

from PIL import Image
from kraken import rpred
from kraken.lib import models
from kraken.containers import Segmentation

logger = logging.getLogger(__name__)


class RecognitionResult(NamedTuple):
    """Result of OCR recognition for a single line."""

    text: str
    cuts: list[tuple]  # List of character boundary polygons
    confidences: list[float]
    baseline: list[list[int]]
    boundary: list[list[int]]


# Module-level model cache
_model = None
_model_path = None


def load_model(model_path: Path) -> models.TorchSeqRecognizer:
    """Load Kraken recognition model, with caching."""
    global _model, _model_path

    if _model is None or _model_path != model_path:
        _model = models.load_any(str(model_path))
        _model_path = model_path

    return _model


def recognize_lines(
    image: Image.Image,
    segmentation: Segmentation,
    model_path: Path,
    on_line_progress: Optional[Callable[[int, int], None]] = None,
) -> list[RecognitionResult]:
    """Recognize text in segmented lines using single-model rpred.

    Args:
        image: PIL Image to process
        segmentation: Kraken Segmentation with detected lines
        model_path: Path to the Kraken recognition model
        on_line_progress: Optional callback called with (current, total) for each line

    Returns:
        List of RecognitionResult, one per line, containing text,
        character cuts, and confidences
    """
    total_lines = len(segmentation.lines)
    logger.debug(f"recognize_lines: {total_lines} lines in segmentation")

    model = load_model(model_path)

    results = []
    for idx, record in enumerate(rpred.rpred(model, image, segmentation, pad=16)):
        if on_line_progress:
            on_line_progress(idx + 1, total_lines)

        results.append(
            RecognitionResult(
                text=record.prediction,
                cuts=list(record.cuts),
                confidences=[float(c) for c in record.confidences],
                baseline=record.baseline,
                boundary=record.boundary,
            )
        )

    logger.debug(f"recognize_lines: {len(results)} results")
    return results
