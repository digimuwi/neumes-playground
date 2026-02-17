"""YOLOv8 training orchestration with model versioning and atomic deployment.

Provides background training triggered via API, with progress reporting
and automatic deployment of trained models to the detection pipeline.

Usage:
    from htr_service.training.yolo_trainer import start_training, get_training_status
"""

import logging
import os
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

from ..models.types import TrainingStatus
from .yolo_export import DEFAULT_OUTPUT_DIR, export_dataset

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
YOLO_MODEL_PATH = MODELS_DIR / "neume_detector.pt"
VERSIONS_DIR = MODELS_DIR / "neume_versions"

_training_status = TrainingStatus()
_training_lock = threading.Lock()

# Track independent training threads
_yolo_result: dict | None = None
_seg_result: dict | None = None


def get_training_status() -> TrainingStatus:
    """Return the current training status."""
    return _training_status.model_copy()


class TrainingAlreadyRunningError(Exception):
    """Raised when a training run is requested while one is already active."""


def start_training(
    epochs: int | None = None,
    imgsz: int = 640,
    seg_epochs: int = 50,
    from_scratch: bool = False,
    parallel: bool = False,
    training_type: str = "both",
) -> TrainingStatus:
    """Start YOLO and/or segmentation training in background threads.

    Args:
        epochs: Number of YOLO training epochs. If None, auto-selects based
            on mode (100 for fresh, 30 for incremental).
        imgsz: YOLO training image size in pixels.
        seg_epochs: Number of segmentation training epochs.
        from_scratch: Force fresh training from yolov8n.pt even if a
            previously trained model exists.
        parallel: Run YOLO and segmentation training concurrently. When False
            (default), they run sequentially in a single thread. Ignored when
            training_type is not "both".
        training_type: Which pipeline(s) to run: "neumes", "segmentation",
            or "both" (default).

    Returns:
        Current TrainingStatus after initiating the run.

    Raises:
        TrainingAlreadyRunningError: If training is already in progress.
    """
    global _training_status, _yolo_result, _seg_result

    run_neumes = training_type in ("neumes", "both")
    run_seg = training_type in ("segmentation", "both")

    # Determine training mode
    incremental = not from_scratch and YOLO_MODEL_PATH.exists()
    mode = "incremental" if incremental else "fresh"
    effective_epochs = epochs if epochs is not None else (30 if incremental else 100)

    with _training_lock:
        if _training_status.state in ("exporting", "training", "deploying"):
            raise TrainingAlreadyRunningError("Training already in progress")

        _training_status = TrainingStatus(
            state="exporting",
            mode=mode,
            total_epochs=effective_epochs if run_neumes else seg_epochs,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        # Pre-fill skipped pipeline results so _check_both_done() doesn't wait for them
        _yolo_result = None if run_neumes else {}
        _seg_result = None if run_seg else {}

    logger.info(
        "Training mode: %s (epochs=%d, parallel=%s, training_type=%s)",
        mode, effective_epochs, parallel, training_type,
    )

    if run_neumes and run_seg and parallel:
        yolo_thread = threading.Thread(
            target=_yolo_training_loop,
            args=(effective_epochs, imgsz, mode),
            daemon=True,
        )
        seg_thread = threading.Thread(
            target=_seg_training_loop,
            args=(seg_epochs,),
            daemon=True,
        )
        yolo_thread.start()
        seg_thread.start()
    elif run_neumes and run_seg:
        combined_thread = threading.Thread(
            target=_sequential_training_loop,
            args=(effective_epochs, imgsz, mode, seg_epochs),
            daemon=True,
        )
        combined_thread.start()
    elif run_neumes:
        threading.Thread(
            target=_yolo_training_loop,
            args=(effective_epochs, imgsz, mode),
            daemon=True,
        ).start()
    else:
        threading.Thread(
            target=_seg_training_loop,
            args=(seg_epochs,),
            daemon=True,
        ).start()

    return get_training_status()


def _check_both_done() -> None:
    """Check if both training threads are done and update overall status."""
    global _training_status, _yolo_result, _seg_result

    with _training_lock:
        if _yolo_result is None or _seg_result is None:
            return  # One thread still running

        errors = []
        if _yolo_result.get("error"):
            errors.append(f"YOLO: {_yolo_result['error']}")
        if _seg_result.get("error"):
            errors.append(f"Segmentation: {_seg_result['error']}")

        if errors:
            _training_status = TrainingStatus(
                state="failed",
                error="; ".join(errors),
                started_at=_training_status.started_at,
            )
        else:
            _training_status = TrainingStatus(
                state="complete",
                mode=_training_status.mode,
                current_epoch=_yolo_result.get("epochs", 0),
                total_epochs=_yolo_result.get("epochs", 0),
                metrics=_training_status.metrics,
                model_version=_yolo_result.get("model_version"),
                started_at=_training_status.started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )


def _sequential_training_loop(epochs: int, imgsz: int, mode: str, seg_epochs: int) -> None:
    """Run YOLO then segmentation training sequentially in one thread."""
    _yolo_training_loop(epochs, imgsz, mode)
    _seg_training_loop(seg_epochs)


def _seg_training_loop(epochs: int) -> None:
    """Run segmentation training: export PageXML → fine-tune Kraken model."""
    global _seg_result

    try:
        from .seg_export import export_segmentation_dataset
        from .seg_trainer import run_segmentation_training

        logger.info("Exporting segmentation dataset...")
        summary = export_segmentation_dataset()

        if summary["exported"] == 0:
            logger.warning("No segmentation training data — skipping")
            _seg_result = {"error": None}
            _check_both_done()
            return

        logger.info("Starting segmentation training...")
        run_segmentation_training(
            training_files=summary["files"],
            epochs=epochs,
        )
        _seg_result = {"error": None}

    except Exception:
        logger.exception("Segmentation training failed")
        _seg_result = {"error": str(_get_current_exception())}

    _check_both_done()


def _yolo_training_loop(epochs: int, imgsz: int, mode: str) -> None:
    """Run the YOLO training pipeline: export → train → version → deploy."""
    global _training_status, _yolo_result

    try:
        # Phase 1: Export dataset
        logger.info("Exporting YOLO training dataset...")
        summary = export_dataset(output_dir=DEFAULT_OUTPUT_DIR)

        if summary["exported"] == 0:
            _yolo_result = {
                "error": "No training data available — export produced 0 images.",
            }
            _check_both_done()
            return

        dataset_yaml = DEFAULT_OUTPUT_DIR / "dataset.yaml"
        logger.info(
            "YOLO export complete: %d images (%d train, %d val)",
            summary["exported"], summary["train"], summary["val"],
        )

        # Phase 2: Train
        _training_status = _training_status.model_copy(update={"state": "training", "current_epoch": 0})

        # Re-enable gradient tracking — Kraken's blla.segment() (used
        # during export) calls torch.set_grad_enabled(False) and never
        # restores it, which would silently break YOLO backpropagation.
        import torch
        torch.set_grad_enabled(True)

        from ultralytics import YOLO

        if mode == "incremental":
            model = YOLO(str(YOLO_MODEL_PATH))
            logger.info("Incremental training: resuming from %s", YOLO_MODEL_PATH)
        else:
            model = YOLO("yolov8n.pt")
            logger.info("Fresh training: starting from yolov8n.pt")

        def _on_epoch_end(trainer):
            global _training_status
            epoch = trainer.epoch + 1
            metrics_dict = None
            if hasattr(trainer, "metrics") and trainer.metrics:
                raw = trainer.metrics
                metrics_dict = {k: round(float(v), 4) for k, v in raw.items() if isinstance(v, (int, float))}
            _training_status = _training_status.model_copy(
                update={"current_epoch": epoch, "metrics": metrics_dict},
            )

        model.add_callback("on_train_epoch_end", _on_epoch_end)

        train_kwargs = dict(
            data=str(dataset_yaml),
            epochs=epochs,
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

        # Phase 3: Version and deploy
        _training_status = _training_status.model_copy(update={"state": "deploying"})

        best_weights = Path(results.save_dir) / "weights" / "best.pt"
        if not best_weights.exists():
            best_weights = Path(results.save_dir) / "weights" / "last.pt"

        if not best_weights.exists():
            _yolo_result = {
                "error": f"No trained weights found in {results.save_dir}",
            }
            _check_both_done()
            return

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Save versioned copy
        VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
        versioned_path = VERSIONS_DIR / f"{timestamp}.pt"
        shutil.copy2(best_weights, versioned_path)
        logger.info("Saved YOLO model version: %s", versioned_path)

        # Atomic deploy: write to temp, then os.replace
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = MODELS_DIR / f".neume_detector_{timestamp}.pt.tmp"
        shutil.copy2(best_weights, tmp_path)
        os.replace(tmp_path, YOLO_MODEL_PATH)
        logger.info("Deployed YOLO model to %s", YOLO_MODEL_PATH)

        _yolo_result = {"error": None, "epochs": epochs, "model_version": timestamp}

    except Exception:
        logger.exception("YOLO training failed")
        _yolo_result = {"error": str(_get_current_exception())}

    _check_both_done()


def _get_current_exception() -> BaseException:
    """Get the current exception from sys.exc_info. Avoids import at module level."""
    import sys
    return sys.exc_info()[1] or RuntimeError("Unknown error")
