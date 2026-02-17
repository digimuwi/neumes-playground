"""Kraken segmentation model training with versioning and atomic deployment.

Fine-tunes Kraken's default segmentation model using PageXML ground truth
exported from user contributions. Teaches the model to distinguish text
regions (with baselines) from neume regions (no baselines).
"""

import csv
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
SEG_MODEL_PATH = MODELS_DIR / "seg_model.mlmodel"
SEG_VERSIONS_DIR = MODELS_DIR / "seg_versions"
SEG_LOG_DIR = BASE_DIR / "datasets" / "segmentation" / "logs"


def _write_training_summary(log_dir: str, total_epochs: int) -> None:
    """Write a human-readable summary from the CSV logger output."""
    metrics_path = Path(log_dir) / "metrics.csv"
    if not metrics_path.is_file():
        logger.debug("No metrics.csv found in %s", log_dir)
        return

    summary_path = Path(log_dir) / "summary.txt"
    with open(metrics_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return

    # Collect per-epoch validation rows (those with val_mean_iu)
    val_rows = [r for r in rows if r.get("val_mean_iu")]
    with open(summary_path, "w") as out:
        out.write(f"Segmentation training — {total_epochs} epochs\n")
        out.write(f"{'epoch':>6}  {'train_loss':>11}  {'val_acc':>8}  "
                  f"{'val_mean_iu':>11}  {'val_freq_iu':>11}\n")
        out.write("-" * 56 + "\n")
        for r in val_rows:
            out.write(
                f"{r.get('epoch', '?'):>6}  "
                f"{float(r.get('train_loss_epoch', 0)):>11.4f}  "
                f"{float(r.get('val_accuracy', 0)):>8.4f}  "
                f"{float(r.get('val_mean_iu', 0)):>11.4f}  "
                f"{float(r.get('val_freq_iu', 0)):>11.4f}\n"
            )

        if val_rows:
            best = max(val_rows, key=lambda r: float(r.get("val_mean_iu", 0)))
            out.write(f"\nBest val_mean_iu: {float(best.get('val_mean_iu', 0)):.4f} "
                      f"(epoch {best.get('epoch', '?')})\n")

    logger.info("Training summary written to %s", summary_path)


def _find_default_seg_model() -> Path:
    """Locate Kraken's built-in default segmentation model."""
    from kraken import blla
    return Path(blla.__file__).parent / "blla.mlmodel"


def run_segmentation_training(
    training_files: list[str],
    epochs: int = 50,
    device: str = "mps",
) -> Path | None:
    """Fine-tune Kraken's segmentation model on exported PageXML data.

    Args:
        training_files: List of paths to PageXML files.
        epochs: Number of training epochs.
        device: Accelerator device ('cpu', 'mps', 'gpu').

    Returns:
        Path to the deployed model, or None if training was skipped/failed.
    """
    if not training_files:
        logger.warning("No training files provided — skipping segmentation training")
        return None

    import torch
    torch.set_grad_enabled(True)

    from lightning.pytorch.callbacks import Callback
    from lightning.pytorch.loggers import CSVLogger

    from kraken.lib.train import KrakenTrainer, SegmentationModel
    from kraken.lib.default_specs import SEGMENTATION_HYPER_PARAMS

    base_model = _find_default_seg_model()
    logger.info("Fine-tuning from %s with %d files", base_model, len(training_files))

    hyper_params = SEGMENTATION_HYPER_PARAMS.copy()
    hyper_params["epochs"] = epochs
    hyper_params["lrate"] = 0.0001  # 5x lower than default — balances learning vs forgetting

    output_prefix = str(BASE_DIR / "datasets" / "segmentation" / "seg_model")

    model = SegmentationModel(
        hyper_params=hyper_params,
        output=output_prefix,
        model=str(base_model),
        training_data=training_files,
        evaluation_data=None,
        partition=0.95,
        format_type="xml",
        resize="union",
    )

    # Logging: CSV file + per-epoch Python log lines
    SEG_LOG_DIR.mkdir(parents=True, exist_ok=True)
    csv_logger = CSVLogger(
        save_dir=str(SEG_LOG_DIR),
        name="seg_training",
    )

    class _EpochLogger(Callback):
        """Log a summary line after each validation epoch."""

        def on_validation_epoch_end(self, trainer, pl_module):
            if trainer.sanity_checking:
                return
            epoch = trainer.current_epoch
            metrics = {k: v.item() if hasattr(v, "item") else v
                       for k, v in trainer.callback_metrics.items()}
            logger.info(
                "Seg epoch %d/%d  train_loss=%.4f  "
                "val_acc=%.4f  val_mean_iu=%.4f  val_freq_iu=%.4f",
                epoch + 1,
                epochs,
                metrics.get("train_loss_epoch", 0),
                metrics.get("val_accuracy", 0),
                metrics.get("val_mean_iu", 0),
                metrics.get("val_freq_iu", 0),
            )

    trainer = KrakenTrainer(
        accelerator=device if device != "mps" else "auto",
        devices=1,
        max_epochs=epochs,
        enable_progress_bar=False,
        logger=csv_logger,
        callbacks=[_EpochLogger()],
    )

    logger.info("Starting segmentation training (%d epochs)", epochs)
    trainer.fit(model)

    # Write a human-readable summary alongside the CSV
    _write_training_summary(csv_logger.log_dir, epochs)

    # Find best model
    best_model_path = model.best_model
    if not best_model_path or not Path(best_model_path).exists():
        # Fall back: find any output model
        output_dir = Path(output_prefix).parent
        candidates = sorted(output_dir.glob("seg_model_*.mlmodel"))
        if candidates:
            best_model_path = str(candidates[-1])
        else:
            logger.error("No trained model found after segmentation training")
            return None

    logger.info("Best segmentation model: %s", best_model_path)

    # Version the model
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    SEG_VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    versioned_path = SEG_VERSIONS_DIR / f"{timestamp}.mlmodel"
    shutil.copy2(best_model_path, versioned_path)
    logger.info("Saved model version: %s", versioned_path)

    # Atomic deploy
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = MODELS_DIR / f".seg_model_{timestamp}.mlmodel.tmp"
    shutil.copy2(best_model_path, tmp_path)
    os.replace(tmp_path, SEG_MODEL_PATH)
    logger.info("Deployed segmentation model to %s", SEG_MODEL_PATH)

    return SEG_MODEL_PATH
