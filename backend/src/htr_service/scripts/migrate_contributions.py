"""One-time migration: backfill syllable polygon boundaries for existing contributions.

Re-runs Kraken segmentation + OCR on each contribution image, matches the
existing syllable annotations to OCR results, and replaces rectangular bboxes
with precise polygon boundaries sliced from line boundary polygons.

Usage:
    python -m htr_service.scripts.migrate_contributions [--dry-run]
"""

import argparse
import json
import logging
import shutil
from pathlib import Path

from PIL import Image
from shapely.geometry import Polygon as ShapelyPolygon, box as shapely_box

from ..contribution.storage import CONTRIBUTIONS_DIR, list_contributions
from ..pipeline.geometry import extract_char_bboxes
from ..pipeline.polygon_slicing import slice_line_polygon, syllable_x_ranges
from ..pipeline.recognition import recognize_lines
from ..pipeline.segmentation import segment_image
from ..syllabification.latin import load_syllabifier, map_chars_to_syllables, merge_char_bboxes

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "Tridis_Medieval_EarlyModern.mlmodel"
PATTERNS_PATH = BASE_DIR / "patterns" / "hyph_la_liturgical.dic"


def _bbox_to_rect_polygon(bbox: dict) -> list[list[int]]:
    """Convert a bbox dict to a rectangular polygon (fallback)."""
    x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


def _get_boundary(syl: dict) -> list[list[int]]:
    """Get boundary polygon from a syllable, handling both old bbox and new boundary format."""
    if "boundary" in syl:
        return syl["boundary"]
    return _bbox_to_rect_polygon(syl["bbox"])


def _get_bbox_from_syl(syl: dict) -> dict | None:
    """Extract a bbox dict from a syllable in either format."""
    if "bbox" in syl:
        return syl["bbox"]
    if "boundary" in syl and len(syl["boundary"]) >= 3:
        pts = syl["boundary"]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return {"x": min(xs), "y": min(ys), "width": max(xs) - min(xs), "height": max(ys) - min(ys)}
    return None


def _bbox_overlaps_polygon(bbox: dict, boundary: list) -> float:
    """Compute overlap ratio between a bbox and a boundary polygon.

    Returns the fraction of the bbox area that overlaps with the polygon.
    """
    if not boundary or len(boundary) < 3:
        return 0.0

    b = bbox
    bbox_poly = shapely_box(b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"])
    try:
        line_poly = ShapelyPolygon([(pt[0], pt[1]) for pt in boundary])
        if not line_poly.is_valid:
            line_poly = line_poly.buffer(0)
        intersection = bbox_poly.intersection(line_poly)
        if bbox_poly.area == 0:
            return 0.0
        return intersection.area / bbox_poly.area
    except Exception:
        return 0.0


def _match_syllables_to_line(
    stored_syllables: list[dict],
    ocr_mapped: list[tuple[str, list]],
    syllable_polygons: list,
) -> list[dict]:
    """Match stored syllables to OCR-derived polygons for a single line.

    For each stored syllable, find the best matching OCR syllable by text
    content and assign its polygon. Unmatched syllables get a rectangular
    polygon derived from their existing bbox as fallback.
    """
    result = []
    used_ocr_indices = set()

    for stored_syl in stored_syllables:
        stored_text = stored_syl["text"]
        best_idx = None
        best_score = -1

        for i, (ocr_text, _) in enumerate(ocr_mapped):
            if i in used_ocr_indices:
                continue
            # Exact text match gets highest priority
            if ocr_text == stored_text:
                best_idx = i
                best_score = 2
                break
            # Partial match (stripping hyphens)
            if ocr_text.rstrip("-") == stored_text.rstrip("-"):
                if best_score < 1:
                    best_idx = i
                    best_score = 1

        if best_idx is not None and syllable_polygons[best_idx] is not None:
            used_ocr_indices.add(best_idx)
            polygon = [[int(x), int(y)] for x, y in syllable_polygons[best_idx]]
            result.append({"text": stored_text, "boundary": polygon})
        else:
            # Fallback: convert bbox to rectangular polygon
            logger.warning(
                "Unmatched syllable %r — using bbox as fallback polygon",
                stored_text,
            )
            polygon = _get_boundary(stored_syl)
            result.append({"text": stored_text, "boundary": polygon})

    return result


def migrate_contribution(
    contribution_id: str,
    contribution_path: Path,
    dry_run: bool = False,
    force: bool = False,
) -> str:
    """Migrate a single contribution to the polygon-based format.

    Returns one of: "migrated", "skipped" (already new format), "warning" (had issues).
    """
    annotations_path = contribution_path / "annotations.json"
    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))

    lines = annotations.get("lines", [])

    # Idempotency: check if already migrated
    if not force and lines and "boundary" in lines[0]:
        logger.info("Skipping %s: already in new format", contribution_id)
        return "skipped"

    if not lines:
        logger.info("Skipping %s: no lines to migrate", contribution_id)
        return "skipped"

    # Load image
    image_filename = annotations["image"]["filename"]
    image_path = contribution_path / image_filename
    image = Image.open(image_path).convert("RGB")

    # Re-run segmentation + OCR
    logger.info("Segmenting %s...", contribution_id)
    segmentation = segment_image(image)

    if not segmentation.lines:
        logger.warning("%s: segmentation found no lines", contribution_id)
        # Keep existing boundaries as fallback
        new_lines = []
        for old_line in lines:
            new_syls = []
            for syl in old_line.get("syllables", []):
                new_syls.append({
                    "text": syl["text"],
                    "boundary": _get_boundary(syl),
                })
            # Use a bounding rect of all syllable boundaries as line boundary
            all_bboxes = [_get_bbox_from_syl(s) for s in old_line.get("syllables", [])]
            all_bboxes = [b for b in all_bboxes if b is not None]
            if all_bboxes:
                x_min = min(b["x"] for b in all_bboxes)
                y_min = min(b["y"] for b in all_bboxes)
                x_max = max(b["x"] + b["width"] for b in all_bboxes)
                y_max = max(b["y"] + b["height"] for b in all_bboxes)
                line_boundary = [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]
            else:
                line_boundary = old_line.get("boundary", [])
            new_lines.append({"boundary": line_boundary, "syllables": new_syls})

        annotations["lines"] = new_lines
        if not dry_run:
            _write_migrated(annotations_path, annotations)
        return "warning"

    logger.info("Recognizing %s (%d lines)...", contribution_id, len(segmentation.lines))
    recognition_results = recognize_lines(image, segmentation, MODEL_PATH)

    syllabifier = load_syllabifier(PATTERNS_PATH)

    # Build OCR data per line: line boundary + syllable polygons
    ocr_lines = []
    for rec_result in recognition_results:
        if not rec_result.text.strip():
            continue

        line_boundary = [(int(pt[0]), int(pt[1])) for pt in rec_result.boundary]

        char_bboxes = extract_char_bboxes(
            rec_result.text, rec_result.cuts, rec_result.confidences
        )
        mapped = map_chars_to_syllables(rec_result.text, char_bboxes, syllabifier)
        syl_char_bboxes_list = [syl_bboxes for _, syl_bboxes in mapped]

        x_ranges = syllable_x_ranges(syl_char_bboxes_list, line_boundary)
        syllable_polygons = slice_line_polygon(line_boundary, x_ranges)

        ocr_lines.append({
            "boundary": line_boundary,
            "mapped": mapped,
            "polygons": syllable_polygons,
        })

    # Match stored lines to OCR lines by spatial overlap
    had_warnings = False
    new_lines = []

    for old_line in lines:
        old_syllables = old_line.get("syllables", [])
        if not old_syllables:
            continue

        # Find the OCR line with highest overlap
        best_ocr_idx = None
        best_overlap = 0.0

        for i, ocr_line in enumerate(ocr_lines):
            # Average overlap of stored syllable bboxes with OCR line boundary
            overlaps = []
            for syl in old_syllables:
                bbox = _get_bbox_from_syl(syl)
                if bbox:
                    overlaps.append(_bbox_overlaps_polygon(bbox, ocr_line["boundary"]))
            if overlaps:
                avg_overlap = sum(overlaps) / len(overlaps)
                if avg_overlap > best_overlap:
                    best_overlap = avg_overlap
                    best_ocr_idx = i

        if best_ocr_idx is not None and best_overlap > 0.3:
            ocr_line = ocr_lines[best_ocr_idx]
            line_boundary = [[int(x), int(y)] for x, y in ocr_line["boundary"]]

            new_syllables = _match_syllables_to_line(
                old_syllables,
                ocr_line["mapped"],
                ocr_line["polygons"],
            )
            new_lines.append({
                "boundary": line_boundary,
                "syllables": new_syllables,
            })
        else:
            # No matching OCR line found — use bbox fallback
            logger.warning(
                "%s: line with %d syllables had no OCR match (best overlap=%.2f)",
                contribution_id,
                len(old_syllables),
                best_overlap,
            )
            had_warnings = True
            new_syls = []
            for syl in old_syllables:
                new_syls.append({
                    "text": syl["text"],
                    "boundary": _get_boundary(syl),
                })
            # Derive line boundary from syllable boundaries
            all_bboxes = [_get_bbox_from_syl(s) for s in old_syllables]
            all_bboxes = [b for b in all_bboxes if b is not None]
            if all_bboxes:
                x_min = min(b["x"] for b in all_bboxes)
                y_min = min(b["y"] for b in all_bboxes)
                x_max = max(b["x"] + b["width"] for b in all_bboxes)
                y_max = max(b["y"] + b["height"] for b in all_bboxes)
                line_boundary = [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]
            else:
                line_boundary = old_line.get("boundary", [])
            new_lines.append({"boundary": line_boundary, "syllables": new_syls})

    annotations["lines"] = new_lines

    if not dry_run:
        _write_migrated(annotations_path, annotations)

    return "warning" if had_warnings else "migrated"


def _write_migrated(annotations_path: Path, annotations: dict) -> None:
    """Write migrated annotations, creating a backup first."""
    backup_path = annotations_path.with_suffix(".json.bak")
    shutil.copy2(annotations_path, backup_path)

    annotations_path.write_text(
        json.dumps(annotations, indent=2), encoding="utf-8"
    )


def main() -> None:
    """CLI entry point for contribution migration."""
    parser = argparse.ArgumentParser(
        description="Migrate contribution annotations from bbox to polygon format.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run migration even if contributions already have boundary fields.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    contributions = list_contributions()
    if not contributions:
        print("No contributions found.")
        return

    migrated = 0
    skipped = 0
    warnings = 0

    for contribution_id, contribution_path in contributions:
        result = migrate_contribution(contribution_id, contribution_path, dry_run=args.dry_run, force=args.force)
        if result == "migrated":
            migrated += 1
        elif result == "skipped":
            skipped += 1
        elif result == "warning":
            warnings += 1

    action = "Would migrate" if args.dry_run else "Migrated"
    print(f"\nMigration complete:")
    print(f"  {action}: {migrated}")
    print(f"  Skipped (already new format): {skipped}")
    print(f"  With warnings: {warnings}")


if __name__ == "__main__":
    main()
