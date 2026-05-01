"""Evaluate segmentation models against contribution ground truth.

Compares the default Kraken segmentation model against the custom-trained
model (models/seg_model.mlmodel) using contribution annotations as ground
truth.

Metrics:
  - Line detection: precision, recall, F1 at configurable IoU threshold
  - Neume contamination: fraction of ground-truth neume area covered by
    predicted text-line boundaries (lower is better — the refined model
    should avoid segmenting neume regions as text)

Usage:
    python scripts/evaluate_segmentation.py [--iou-threshold 0.5]
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import Polygon as ShapelyPolygon, box as shapely_box
from shapely.ops import unary_union

# ---------------------------------------------------------------------------
# Kraken imports – blla.segment() disables torch gradients as a side-effect,
# but that does not matter for pure inference evaluation.
# ---------------------------------------------------------------------------
from kraken import blla
from kraken.lib import vgsl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CONTRIBUTIONS_DIR = BASE_DIR / "contributions"
CUSTOM_MODEL_PATH = BASE_DIR / "models" / "seg_model.mlmodel"


# ── helpers ────────────────────────────────────────────────────────────────


def _make_polygon(boundary: list[list[int]]) -> ShapelyPolygon | None:
    """Create a valid Shapely polygon from a boundary, or None."""
    if len(boundary) < 3:
        return None
    coords = [(pt[0], pt[1]) for pt in boundary]
    poly = ShapelyPolygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        return None
    return poly


def _bbox_to_polygon(bbox: dict) -> ShapelyPolygon:
    """Convert a {x, y, width, height} dict to a Shapely box."""
    return shapely_box(
        bbox["x"],
        bbox["y"],
        bbox["x"] + bbox["width"],
        bbox["y"] + bbox["height"],
    )


def _polygon_iou(a: ShapelyPolygon, b: ShapelyPolygon) -> float:
    """Compute Intersection-over-Union between two Shapely polygons."""
    if a.is_empty or b.is_empty:
        return 0.0
    inter = a.intersection(b).area
    union = a.union(b).area
    return inter / union if union > 0 else 0.0


# ── per-image evaluation ──────────────────────────────────────────────────


def evaluate_image(
    image: Image.Image,
    gt_lines: list[dict],
    gt_neumes: list[dict],
    model,  # None → default Kraken model
    iou_threshold: float,
) -> dict:
    """Run segmentation on *image* and compare against ground truth.

    Returns a dict with per-image metrics.
    """
    # Run segmentation
    if model is not None:
        seg = blla.segment(image, model=model)
    else:
        seg = blla.segment(image)

    # Build ground-truth polygons
    gt_polys = []
    for line in gt_lines:
        poly = _make_polygon(line.get("boundary", []))
        if poly is not None:
            gt_polys.append(poly)

    # Build predicted polygons from Kraken segmentation result
    pred_polys = []
    for line in seg.lines:
        boundary = line.boundary
        if not boundary or len(boundary) < 3:
            continue
        coords = [(pt[0], pt[1]) for pt in boundary]
        poly = ShapelyPolygon(coords)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if not poly.is_empty:
            pred_polys.append(poly)

    # ── Line-level precision / recall ─────────────────────────────────
    # Greedy matching: for each GT polygon find the best-matching pred
    matched_pred = set()
    true_positives = 0

    for gt_poly in gt_polys:
        best_iou = 0.0
        best_idx = -1
        for j, pred_poly in enumerate(pred_polys):
            if j in matched_pred:
                continue
            iou = _polygon_iou(gt_poly, pred_poly)
            if iou > best_iou:
                best_iou = iou
                best_idx = j
        if best_iou >= iou_threshold and best_idx >= 0:
            true_positives += 1
            matched_pred.add(best_idx)

    n_gt = len(gt_polys)
    n_pred = len(pred_polys)
    precision = true_positives / n_pred if n_pred else 1.0
    recall = true_positives / n_gt if n_gt else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    # ── Average IoU of matched pairs ──────────────────────────────────
    ious: list[float] = []
    matched_pred2 = set()
    for gt_poly in gt_polys:
        best_iou = 0.0
        best_idx = -1
        for j, pred_poly in enumerate(pred_polys):
            if j in matched_pred2:
                continue
            iou = _polygon_iou(gt_poly, pred_poly)
            if iou > best_iou:
                best_iou = iou
                best_idx = j
        if best_idx >= 0:
            ious.append(best_iou)
            matched_pred2.add(best_idx)
    mean_iou = float(np.mean(ious)) if ious else 0.0

    # ── Neume contamination ───────────────────────────────────────────
    # What fraction of ground-truth neume area is covered by predicted
    # text-line boundaries?  Lower = better.
    neume_contamination = 0.0
    if gt_neumes:
        neume_polys = [_bbox_to_polygon(n["bbox"]) for n in gt_neumes]
        neume_union = unary_union(neume_polys)
        total_neume_area = neume_union.area

        if total_neume_area > 0 and pred_polys:
            pred_union = unary_union(pred_polys)
            contaminated_area = neume_union.intersection(pred_union).area
            neume_contamination = contaminated_area / total_neume_area

    return {
        "gt_lines": n_gt,
        "pred_lines": n_pred,
        "true_positives": true_positives,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mean_iou": mean_iou,
        "neume_contamination": neume_contamination,
        "n_neumes": len(gt_neumes),
    }


# ── main ──────────────────────────────────────────────────────────────────


def load_contributions() -> list[tuple[str, Path]]:
    """Return list of (id, path) for valid contributions."""
    if not CONTRIBUTIONS_DIR.is_dir():
        return []
    results = []
    for entry in sorted(CONTRIBUTIONS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        has_ann = (entry / "annotations.mei").is_file() or (
            entry / "annotations.json"
        ).is_file()
        has_img = (entry / "image.jpg").is_file() or (entry / "image.png").is_file()
        if has_ann and has_img:
            results.append((entry.name, entry))
    return results


def find_image(contribution_dir: Path) -> Path:
    """Find the image file in a contribution directory."""
    for ext in ("jpg", "png"):
        p = contribution_dir / f"image.{ext}"
        if p.is_file():
            return p
    raise FileNotFoundError(f"No image in {contribution_dir}")


def run_evaluation(iou_threshold: float = 0.5) -> None:
    contributions = load_contributions()
    if not contributions:
        logger.error("No contributions found in %s", CONTRIBUTIONS_DIR)
        sys.exit(1)

    logger.info("Found %d contributions", len(contributions))

    # ── Load models ───────────────────────────────────────────────────
    custom_model = None
    if CUSTOM_MODEL_PATH.is_file():
        logger.info("Loading custom model from %s", CUSTOM_MODEL_PATH)
        custom_model = vgsl.TorchVGSLModel.load_model(CUSTOM_MODEL_PATH)
    else:
        logger.warning(
            "Custom model not found at %s — only evaluating default model",
            CUSTOM_MODEL_PATH,
        )

    models: dict[str, object] = {"default": None}
    if custom_model is not None:
        models["custom"] = custom_model

    # ── Evaluate each contribution with each model ────────────────────
    all_results: dict[str, list[dict]] = {name: [] for name in models}

    for cid, cpath in contributions:
        logger.info("Evaluating contribution %s", cid)
        image_path = find_image(cpath)
        image = Image.open(image_path).convert("RGB")

        from htr_service.contribution.storage import read_document
        doc = read_document(cpath)
        gt_lines = [line.model_dump() for line in doc.lines]
        gt_neumes = [neume.model_dump() for neume in doc.neumes]

        if not gt_lines:
            logger.info("  skipping (no ground-truth lines)")
            continue

        for model_name, model in models.items():
            t0 = time.perf_counter()
            result = evaluate_image(
                image, gt_lines, gt_neumes, model, iou_threshold
            )
            elapsed = time.perf_counter() - t0
            result["contribution_id"] = cid
            result["time_s"] = round(elapsed, 2)
            all_results[model_name].append(result)

            logger.info(
                "  %-8s  lines: %d→%d  P=%.2f R=%.2f F1=%.2f  "
                "mean_IoU=%.3f  neume_contam=%.1f%%  (%.1fs)",
                model_name,
                result["gt_lines"],
                result["pred_lines"],
                result["precision"],
                result["recall"],
                result["f1"],
                result["mean_iou"],
                result["neume_contamination"] * 100,
                elapsed,
            )

    # ── Aggregate results ─────────────────────────────────────────────
    print("\n" + "=" * 72)
    print(f"SEGMENTATION EVALUATION  (IoU threshold = {iou_threshold})")
    print("=" * 72)

    for model_name, results in all_results.items():
        if not results:
            continue

        n = len(results)
        avg = lambda key: sum(r[key] for r in results) / n

        print(f"\n{'Model':>18}: {model_name}")
        print(f"{'Images evaluated':>18}: {n}")
        print(f"{'Avg GT lines':>18}: {avg('gt_lines'):.1f}")
        print(f"{'Avg pred lines':>18}: {avg('pred_lines'):.1f}")
        print(f"{'Avg precision':>18}: {avg('precision'):.3f}")
        print(f"{'Avg recall':>18}: {avg('recall'):.3f}")
        print(f"{'Avg F1':>18}: {avg('f1'):.3f}")
        print(f"{'Avg mean IoU':>18}: {avg('mean_iou'):.3f}")

        imgs_with_neumes = [r for r in results if r["n_neumes"] > 0]
        if imgs_with_neumes:
            avg_contam = sum(r["neume_contamination"] for r in imgs_with_neumes) / len(imgs_with_neumes)
            print(f"{'Neume contamination':>18}: {avg_contam:.1%}  "
                  f"(over {len(imgs_with_neumes)} images with neumes)")
        else:
            print(f"{'Neume contamination':>18}: N/A (no neume annotations)")

        print(f"{'Avg time/image':>18}: {avg('time_s'):.2f}s")

    # ── Side-by-side comparison ───────────────────────────────────────
    if len(all_results) == 2 and all(all_results.values()):
        names = list(all_results.keys())
        r0 = all_results[names[0]]
        r1 = all_results[names[1]]
        n = min(len(r0), len(r1))

        print(f"\n{'─' * 72}")
        print("COMPARISON (custom vs default)")
        print(f"{'─' * 72}")

        for key, label, fmt, better in [
            ("f1", "F1", ".3f", "higher"),
            ("mean_iou", "Mean IoU", ".3f", "higher"),
            ("neume_contamination", "Neume contam.", ".1%", "lower"),
        ]:
            v0 = sum(r[key] for r in r0[:n]) / n
            v1 = sum(r[key] for r in r1[:n]) / n
            diff = v1 - v0
            arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "=")
            sign = "+" if diff > 0 else ""
            # For neume contamination, lower is better
            if key == "neume_contamination":
                quality = "better" if diff < 0 else ("worse" if diff > 0 else "same")
            else:
                quality = "better" if diff > 0 else ("worse" if diff < 0 else "same")

            print(
                f"  {label:>18}:  {names[0]}={v0:{fmt}}  "
                f"{names[1]}={v1:{fmt}}  "
                f"{arrow} {sign}{diff:{fmt}}  ({quality})"
            )

    # ── Per-image detail table ────────────────────────────────────────
    print(f"\n{'─' * 72}")
    print("PER-IMAGE DETAILS")
    print(f"{'─' * 72}")

    header = f"{'contribution':>12}  {'model':>8}  {'GT':>3}  {'pred':>4}  {'P':>5}  {'R':>5}  {'F1':>5}  {'mIoU':>5}  {'contam':>6}"
    print(header)
    print("-" * len(header))

    for model_name, results in all_results.items():
        for r in results:
            cid_short = r["contribution_id"][:8] + "…"
            print(
                f"{cid_short:>12}  {model_name:>8}  "
                f"{r['gt_lines']:>3}  {r['pred_lines']:>4}  "
                f"{r['precision']:>5.2f}  {r['recall']:>5.2f}  "
                f"{r['f1']:>5.2f}  {r['mean_iou']:>5.3f}  "
                f"{r['neume_contamination']:>5.1%}"
            )

    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate segmentation models against contribution ground truth"
    )
    parser.add_argument(
        "--iou-threshold",
        type=float,
        default=0.5,
        help="IoU threshold for matching predicted to GT lines (default: 0.5)",
    )
    args = parser.parse_args()
    run_evaluation(iou_threshold=args.iou_threshold)
