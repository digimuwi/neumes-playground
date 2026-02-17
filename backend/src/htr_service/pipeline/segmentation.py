"""Line segmentation using Kraken baseline segmentation."""

import logging
from pathlib import Path

from PIL import Image
from kraken import blla
from kraken.containers import BaselineLine, Segmentation
from kraken.lib import vgsl

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
CUSTOM_MODEL_PATH = BASE_DIR / "models" / "seg_model.mlmodel"

# Module-level model cache
_seg_model = None
_seg_model_mtime = None


def _load_custom_model() -> vgsl.TorchVGSLModel | None:
    """Load the custom segmentation model if it exists, with caching.

    Returns the model or None if no custom model is available.
    Invalidates cache when the file's modification time changes.
    """
    global _seg_model, _seg_model_mtime

    if not CUSTOM_MODEL_PATH.is_file():
        _seg_model = None
        _seg_model_mtime = None
        return None

    mtime = CUSTOM_MODEL_PATH.stat().st_mtime
    if _seg_model is not None and _seg_model_mtime == mtime:
        return _seg_model

    logger.info("Loading custom segmentation model from %s", CUSTOM_MODEL_PATH)
    _seg_model = vgsl.TorchVGSLModel.load_model(CUSTOM_MODEL_PATH)
    _seg_model_mtime = mtime
    return _seg_model


def segment_image(image: Image.Image) -> Segmentation:
    """Segment an image into text lines using Kraken baseline segmentation.

    Uses a custom segmentation model from models/seg_model.mlmodel when
    available, otherwise falls back to Kraken's default model.

    Args:
        image: PIL Image to segment

    Returns:
        Kraken Segmentation object containing detected lines with
        baseline and boundary information.
    """
    model = _load_custom_model()
    if model is not None:
        logger.debug("Using custom segmentation model")
        result = blla.segment(image, model=model)
    else:
        logger.debug("Using default Kraken segmentation model")
        result = blla.segment(image)
    logger.debug(f"Segmentation: {len(result.lines)} lines")
    return result


def build_single_line_segmentation(width: int, height: int) -> Segmentation:
    """Build a synthetic single-line Segmentation for a cropped text region.

    Creates a Segmentation with one BaselineLine spanning the full image.
    The baseline is a horizontal line at the vertical center; the boundary
    is the full image rectangle.

    Args:
        width: Width of the cropped image in pixels.
        height: Height of the cropped image in pixels.

    Returns:
        Kraken Segmentation with a single line.
    """
    return Segmentation(
        type="baselines",
        imagename="",
        text_direction="horizontal-lr",
        script_detection=False,
        lines=[
            BaselineLine(
                id="line_0",
                baseline=[(0, height // 2), (width - 1, height // 2)],
                boundary=[(0, 0), (width - 1, 0), (width - 1, height - 1), (0, height - 1)],
            )
        ],
    )
