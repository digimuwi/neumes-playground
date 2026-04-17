"""CLI for training the neume detector and segmentation model.

Usage:
    python -m htr_service.training [--type {neumes,segmentation,both}] \
        [--epochs N] [--imgsz N] [--seg-epochs N] [--from-scratch]

Runs synchronously and logs progress to stderr. Exits non-zero on failure.
"""

from __future__ import annotations

import argparse
import logging
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m htr_service.training",
        description="Train neume detection and/or line segmentation models from current contributions.",
    )
    parser.add_argument(
        "--type",
        choices=("neumes", "segmentation", "both"),
        default="both",
        help="Which pipeline(s) to run (default: both)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="YOLO training epochs (default: 100 fresh / 30 incremental)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="YOLO training image size in pixels (default: 640)",
    )
    parser.add_argument(
        "--seg-epochs",
        type=int,
        default=50,
        help="Segmentation training epochs (default: 50)",
    )
    parser.add_argument(
        "--from-scratch",
        action="store_true",
        help="Force fresh YOLO training from yolov8n.pt even if a previously trained model exists",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )

    args = _build_parser().parse_args(argv)
    errors: list[str] = []

    if args.type in ("neumes", "both"):
        from .yolo_trainer import run_yolo_training
        try:
            run_yolo_training(
                epochs=args.epochs,
                imgsz=args.imgsz,
                from_scratch=args.from_scratch,
            )
        except Exception as exc:
            logging.exception("YOLO training failed")
            errors.append(f"YOLO: {exc}")

    if args.type in ("segmentation", "both"):
        from .seg_export import export_segmentation_dataset
        from .seg_trainer import run_segmentation_training
        try:
            summary = export_segmentation_dataset()
            if summary["exported"] == 0:
                logging.warning("No segmentation training data — skipping")
            else:
                run_segmentation_training(
                    training_files=summary["files"],
                    epochs=args.seg_epochs,
                )
        except Exception as exc:
            logging.exception("Segmentation training failed")
            errors.append(f"Segmentation: {exc}")

    if errors:
        for err in errors:
            logging.error(err)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
