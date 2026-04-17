"""YOLOv8 training orchestration with model versioning and atomic deployment.

Fine-tunes a YOLO neume detector from current contributions and deploys the
result to the detection pipeline.
"""

import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .yolo_export import DEFAULT_OUTPUT_DIR, export_dataset

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
YOLO_MODEL_PATH = MODELS_DIR / "neume_detector.pt"
VERSIONS_DIR = MODELS_DIR / "neume_versions"


def run_yolo_training(
    epochs: int | None = None,
    imgsz: int = 640,
    from_scratch: bool = False,
) -> Path | None:
    """Export the YOLO dataset, fine-tune the detector, and deploy it.

    Args:
        epochs: Number of training epochs. If None, auto-selects based on
            mode (100 for fresh, 30 for incremental).
        imgsz: Training image size in pixels.
        from_scratch: Force fresh training from yolov8n.pt even if a
            previously trained model exists.

    Returns:
        Path to the deployed model, or None if training was skipped/failed.
    """
    incremental = not from_scratch and YOLO_MODEL_PATH.exists()
    mode = "incremental" if incremental else "fresh"
    effective_epochs = epochs if epochs is not None else (30 if incremental else 100)

    logger.info(
        "YOLO training mode: %s (epochs=%d, imgsz=%d)",
        mode, effective_epochs, imgsz,
    )

    logger.info("Exporting YOLO training dataset...")
    summary = export_dataset(output_dir=DEFAULT_OUTPUT_DIR)

    if summary["exported"] == 0:
        logger.warning("No training data available — export produced 0 images")
        return None

    dataset_yaml = DEFAULT_OUTPUT_DIR / "dataset.yaml"
    logger.info(
        "YOLO export complete: %d images (%d train, %d val)",
        summary["exported"], summary["train"], summary["val"],
    )

    # Re-enable gradient tracking — Kraken's blla.segment() (used during
    # export) calls torch.set_grad_enabled(False) and never restores it,
    # which would silently break YOLO backpropagation.
    import torch
    torch.set_grad_enabled(True)

    from ultralytics import YOLO

    if mode == "incremental":
        model = YOLO(str(YOLO_MODEL_PATH))
        logger.info("Incremental training: resuming from %s", YOLO_MODEL_PATH)
    else:
        model = YOLO("yolov8n.pt")
        logger.info("Fresh training: starting from yolov8n.pt")

    train_kwargs = dict(
        data=str(dataset_yaml),
        epochs=effective_epochs,
        imgsz=imgsz,
        project=str(DEFAULT_OUTPUT_DIR / "runs"),
        exist_ok=True,
        device="mps",
        amp=False,
        mosaic=0.5,
        erasing=0.15,
    )
    if mode == "incremental":
        train_kwargs["lr0"] = 0.001

    results = model.train(**train_kwargs)

    best_weights = Path(results.save_dir) / "weights" / "best.pt"
    if not best_weights.exists():
        best_weights = Path(results.save_dir) / "weights" / "last.pt"

    if not best_weights.exists():
        logger.error("No trained weights found in %s", results.save_dir)
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    versioned_path = VERSIONS_DIR / f"{timestamp}.pt"
    shutil.copy2(best_weights, versioned_path)
    logger.info("Saved YOLO model version: %s", versioned_path)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = MODELS_DIR / f".neume_detector_{timestamp}.pt.tmp"
    shutil.copy2(best_weights, tmp_path)
    os.replace(tmp_path, YOLO_MODEL_PATH)
    logger.info("Deployed YOLO model to %s", YOLO_MODEL_PATH)

    return YOLO_MODEL_PATH
