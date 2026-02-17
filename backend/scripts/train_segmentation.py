"""Manually trigger segmentation model training.

Exports contributions to PageXML, then fine-tunes Kraken's default
segmentation model to distinguish text regions from neume regions.

Usage:
    python scripts/train_segmentation.py [--epochs 50] [--device mps]
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure the package is importable when run from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from htr_service.training.seg_export import export_segmentation_dataset
from htr_service.training.seg_trainer import run_segmentation_training

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train the Kraken segmentation model on contribution data"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs (default: 50)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="mps",
        help="Accelerator device: mps, cpu, gpu (default: mps)",
    )
    args = parser.parse_args()

    # Phase 1: Export
    logger.info("Exporting contributions to PageXML...")
    summary = export_segmentation_dataset()
    logger.info(
        "Export complete: %d exported, %d skipped",
        summary["exported"],
        summary["skipped"],
    )

    if summary["exported"] == 0:
        logger.error("No training data — nothing to train on")
        sys.exit(1)

    # Phase 2: Train
    logger.info("Starting segmentation training (%d epochs, device=%s)", args.epochs, args.device)
    deployed = run_segmentation_training(
        training_files=summary["files"],
        epochs=args.epochs,
        device=args.device,
    )

    if deployed:
        logger.info("Done — model deployed to %s", deployed)
    else:
        logger.error("Training did not produce a model")
        sys.exit(1)


if __name__ == "__main__":
    main()
