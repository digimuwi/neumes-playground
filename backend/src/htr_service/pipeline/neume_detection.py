"""Neume detection using YOLOv8 + SAHI tiled inference.

Detects and classifies individual neumes on text-masked manuscript images.
Uses SAHI to tile large images into overlapping patches for YOLOv8 inference.
Tile size is derived from the median interlinear spacing in the Kraken
segmentation result.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kraken.containers import Segmentation
from PIL import Image

from ..models.types import BBox, NeumeDetection
from .tiling import OVERLAP_RATIO, compute_tile_size

logger = logging.getLogger(__name__)

# Model path
BASE_DIR = Path(__file__).parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
YOLO_MODEL_PATH = MODELS_DIR / "neume_detector.pt"


@dataclass
class _CachedYoloModel:
    """A loaded YOLO model with its file modification time."""

    model: object  # ultralytics.YOLO
    mtime: float


# Module-level cache
_yolo_cache: Optional[_CachedYoloModel] = None


def _load_yolo_model() -> Optional[object]:
    """Load the YOLO neume detection model with mtime-based caching.

    Returns None if the model file does not exist.
    """
    global _yolo_cache

    if not YOLO_MODEL_PATH.exists():
        return None

    current_mtime = YOLO_MODEL_PATH.stat().st_mtime

    if _yolo_cache is not None and _yolo_cache.mtime == current_mtime:
        return _yolo_cache.model

    logger.info("Loading YOLO neume detection model from %s", YOLO_MODEL_PATH)
    try:
        from ultralytics import YOLO

        model = YOLO(str(YOLO_MODEL_PATH))
        _yolo_cache = _CachedYoloModel(model=model, mtime=current_mtime)
        return model
    except Exception:
        logger.exception("Failed to load YOLO model from %s", YOLO_MODEL_PATH)
        return None


def detect_neumes(
    masked_image: Image.Image,
    segmentation: Segmentation,
) -> list[NeumeDetection]:
    """Detect neumes on a text-masked manuscript image.

    Args:
        masked_image: PIL RGB image with text regions already masked out.
        segmentation: Kraken Segmentation result (used to compute tile size).

    Returns:
        List of NeumeDetection objects with type, bbox, and confidence.
        Returns an empty list if no YOLO model is available.
    """
    model = _load_yolo_model()
    if model is None:
        logger.warning(
            "No neume detection model found at %s — skipping detection. "
            "Train a model via POST /training/start.",
            YOLO_MODEL_PATH,
        )
        return []

    tile_size = compute_tile_size(segmentation)
    logger.debug("Using SAHI tile size: %dpx", tile_size)

    try:
        from sahi import AutoDetectionModel
        from sahi.predict import get_sliced_prediction

        detection_model = AutoDetectionModel.from_pretrained(
            model_type="yolov8",
            model=model,
            confidence_threshold=0.25,
        )

        result = get_sliced_prediction(
            image=masked_image,
            detection_model=detection_model,
            slice_height=tile_size,
            slice_width=tile_size,
            overlap_height_ratio=OVERLAP_RATIO,
            overlap_width_ratio=OVERLAP_RATIO,
            postprocess_class_agnostic=True,
        )

        detections = []
        for prediction in result.object_prediction_list:
            bbox = prediction.bbox
            detections.append(
                NeumeDetection(
                    type=prediction.category.name,
                    bbox=BBox(
                        x=int(bbox.minx),
                        y=int(bbox.miny),
                        width=int(bbox.maxx - bbox.minx),
                        height=int(bbox.maxy - bbox.miny),
                    ),
                    confidence=float(prediction.score.value),
                )
            )

        logger.info("Detected %d neumes", len(detections))
        return detections

    except Exception:
        logger.exception("Neume detection failed")
        return []


def detect_neumes_direct(image: Image.Image) -> list[NeumeDetection]:
    """Detect neumes by running YOLO directly on the image without SAHI tiling.

    Intended for small, user-selected regions where tiling is unnecessary.

    Args:
        image: PIL RGB image (typically a cropped region).

    Returns:
        List of NeumeDetection objects with type, bbox, and confidence.
        Returns an empty list if no YOLO model is available.
    """
    model = _load_yolo_model()
    if model is None:
        logger.warning(
            "No neume detection model found at %s — skipping detection. "
            "Train a model via POST /training/start.",
            YOLO_MODEL_PATH,
        )
        return []

    try:
        results = model.predict(source=image, conf=0.25, agnostic_nms=True, verbose=False)

        detections = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls_id = int(box.cls[0])
                detections.append(
                    NeumeDetection(
                        type=result.names[cls_id],
                        bbox=BBox(
                            x=int(x1),
                            y=int(y1),
                            width=int(x2 - x1),
                            height=int(y2 - y1),
                        ),
                        confidence=float(box.conf[0]),
                    )
                )

        logger.info("Detected %d neumes (direct)", len(detections))
        return detections

    except Exception:
        logger.exception("Direct neume detection failed")
        return []
