"""Export stored contributions to YOLOv8 training dataset format.

Converts contributions (image + annotations.json) into YOLO-format training
data: text-masked JPEG images + normalized label files, with a dataset.yaml
for direct use with `yolo train`.

Usage:
    python -m htr_service.training.yolo_export [--output-dir DIR] [--val-ratio F] [--seed N]
"""

import argparse
import json
import logging
import random
import shutil
from pathlib import Path

import yaml
from PIL import Image

from ..neume_registry import (
    DEFAULT_CLASSES_PATH,
    load_neume_class_map,
    load_neume_registry,
)
from ..contribution.storage import CONTRIBUTIONS_DIR, list_contributions, read_document
from ..pipeline.text_masking import mask_polygon_regions
from ..pipeline.tiling import TILE_SIZE_DEFAULT, TILE_SIZE_MAX, TILE_SIZE_MIN, TILE_SIZE_MULTIPLIER, generate_tile_grid

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "datasets" / "neumes"


def load_neume_classes(path: Path = DEFAULT_CLASSES_PATH) -> dict[str, int]:
    """Load neume class mapping from a YAML file.

    Args:
        path: Path to neume_classes.yaml.

    Returns:
        Dict mapping neume type string to integer class ID.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        ValueError: If the YAML file has invalid structure.
    """
    return load_neume_class_map(path)


def bbox_to_yolo(x: int, y: int, width: int, height: int, img_w: int, img_h: int) -> tuple[float, float, float, float]:
    """Convert pixel bbox to YOLO normalized format.

    Args:
        x, y: Top-left corner in pixels.
        width, height: Box dimensions in pixels.
        img_w, img_h: Image dimensions in pixels.

    Returns:
        Tuple of (x_center, y_center, width, height) normalized to [0, 1].
    """
    x_center = (x + width / 2) / img_w
    y_center = (y + height / 2) / img_h
    norm_w = width / img_w
    norm_h = height / img_h
    return x_center, y_center, norm_w, norm_h


def _compute_tile_size_from_boundaries(
    line_boundaries: list[list[list[int]]],
) -> int:
    """Compute SAHI tile size from contributed line boundary polygons.

    Uses the same algorithm as tiling.compute_tile_size but works with
    raw polygon coordinate lists instead of a Kraken Segmentation object.
    """
    import statistics

    if len(line_boundaries) < 2:
        return TILE_SIZE_DEFAULT

    # Sort lines by median y of their boundary polygon
    lines_with_y = []
    for boundary in line_boundaries:
        if boundary:
            median_y = statistics.median(pt[1] for pt in boundary)
            lines_with_y.append((median_y, boundary))

    if len(lines_with_y) < 2:
        return TILE_SIZE_DEFAULT

    lines_with_y.sort(key=lambda pair: pair[0])

    # Compute gaps between consecutive lines
    gaps = []
    for i in range(len(lines_with_y) - 1):
        _, current_boundary = lines_with_y[i]
        _, next_boundary = lines_with_y[i + 1]

        current_bottom = max(pt[1] for pt in current_boundary)
        next_top = min(pt[1] for pt in next_boundary)
        gap = next_top - current_bottom
        if gap > 0:
            gaps.append(gap)

    if not gaps:
        return TILE_SIZE_DEFAULT

    median_gap = statistics.median(gaps)
    tile_size = int(median_gap * TILE_SIZE_MULTIPLIER)
    return max(TILE_SIZE_MIN, min(TILE_SIZE_MAX, tile_size))


def _assign_bboxes_to_tile(
    neumes: list[dict],
    tile_x: int,
    tile_y: int,
    tile_w: int,
    tile_h: int,
    class_map: dict[str, int],
) -> list[str]:
    """Assign and clip neume bboxes to a single tile.

    A neume is assigned to a tile if its center falls within the tile
    bounds.  The bbox is then clipped to the tile edges and converted to
    YOLO normalized format relative to the tile dimensions.

    Returns a list of YOLO-format label lines for this tile.
    """
    label_lines = []
    for neume in neumes:
        bbox = neume["bbox"]
        # Center-in-tile test
        cx = bbox["x"] + bbox["width"] / 2
        cy = bbox["y"] + bbox["height"] / 2
        if not (tile_x <= cx < tile_x + tile_w and tile_y <= cy < tile_y + tile_h):
            continue

        # Clip bbox to tile boundaries (in image-space pixels)
        clipped_left = max(bbox["x"], tile_x)
        clipped_top = max(bbox["y"], tile_y)
        clipped_right = min(bbox["x"] + bbox["width"], tile_x + tile_w)
        clipped_bottom = min(bbox["y"] + bbox["height"], tile_y + tile_h)
        clipped_w = clipped_right - clipped_left
        clipped_h = clipped_bottom - clipped_top
        if clipped_w <= 0 or clipped_h <= 0:
            continue

        # Convert to tile-local coords and YOLO format
        local_x = clipped_left - tile_x
        local_y = clipped_top - tile_y
        class_id = class_map[neume["type"]]
        xc, yc, nw, nh = bbox_to_yolo(local_x, local_y, clipped_w, clipped_h, tile_w, tile_h)
        label_lines.append(f"{class_id} {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}")

    return label_lines


def _export_single_contribution(
    contribution_id: str,
    contribution_path: Path,
    class_map: dict[str, int],
    output_images_dir: Path,
    output_labels_dir: Path,
) -> int:
    """Export a single contribution as tiled images in YOLO format.

    Returns the number of tiles exported (0 if the contribution was skipped).
    """
    doc = read_document(contribution_path)
    annotations = {
        "image": {
            "filename": doc.image.filename,
            "width": doc.image.width,
            "height": doc.image.height,
        },
        "lines": [line.model_dump() for line in doc.lines],
        "neumes": [neume.model_dump() for neume in doc.neumes],
    }

    neumes = annotations["neumes"]
    if not neumes:
        logger.info("Skipping %s: no neumes", contribution_id)
        return 0

    # Filter to known neume types
    known_neumes = []
    for neume in neumes:
        neume_type = neume["type"]
        if neume_type not in class_map:
            logger.warning(
                "Unknown neume type %r in contribution %s — skipping this neume",
                neume_type,
                contribution_id,
            )
            continue
        known_neumes.append(neume)

    if not known_neumes:
        logger.info("Skipping %s: all neume types unknown", contribution_id)
        return 0

    image_filename = annotations["image"]["filename"]
    image_path = contribution_path / image_filename
    image = Image.open(image_path).convert("RGB")

    lines = annotations["lines"]
    syllable_polygons = []
    line_boundaries = []
    for line in lines:
        line_boundary = line.get("boundary", [])
        if line_boundary:
            line_boundaries.append(line_boundary)
        for syllable in line.get("syllables", []):
            boundary = syllable.get("boundary", [])
            if boundary and len(boundary) >= 3:
                syllable_polygons.append(
                    [(int(pt[0]), int(pt[1])) for pt in boundary]
                )

    # Mask contributed syllable regions (only what the user confirmed as text)
    masked = mask_polygon_regions(image, syllable_polygons)

    # Tile the image using line boundaries for spacing computation
    img_w, img_h = masked.size
    tile_size = _compute_tile_size_from_boundaries(line_boundaries)
    tiles = generate_tile_grid(img_w, img_h, tile_size, overlap_ratio=0.0)

    tile_count = 0
    for tile in tiles:
        label_lines = _assign_bboxes_to_tile(
            known_neumes, tile.x, tile.y, tile.width, tile.height, class_map,
        )

        # Skip tiles with no neumes
        if not label_lines:
            continue

        tile_name = f"{contribution_id}_tile{tile.row}_{tile.col}"

        # Crop and save tile image
        tile_img = masked.crop((tile.x, tile.y, tile.x + tile.width, tile.y + tile.height))
        tile_img.save(output_images_dir / f"{tile_name}.jpg", format="JPEG", quality=95)

        # Save label file
        label_path = output_labels_dir / f"{tile_name}.txt"
        label_path.write_text("\n".join(label_lines) + "\n", encoding="utf-8")

        tile_count += 1

    logger.info("Exported %s: %d tiles", contribution_id, tile_count)
    return tile_count


def _generate_dataset_yaml(
    output_dir: Path,
    class_map: dict[str, int],
    classes_path: Path = DEFAULT_CLASSES_PATH,
) -> None:
    """Generate dataset.yaml for YOLOv8 training."""
    names = {
        neume_class.id: neume_class.key
        for neume_class in load_neume_registry(classes_path)
    }

    dataset_config = {
        "path": str(output_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": names,
    }

    yaml_path = output_dir / "dataset.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(dataset_config, f, default_flow_style=False, sort_keys=False)


def _prepare_output_dir(output_dir: Path) -> tuple[Path, Path, Path, Path]:
    """Clear and recreate the output directory structure.

    Returns (train_images, val_images, train_labels, val_labels) paths.
    """
    if output_dir.exists():
        shutil.rmtree(output_dir)

    train_images = output_dir / "images" / "train"
    val_images = output_dir / "images" / "val"
    train_labels = output_dir / "labels" / "train"
    val_labels = output_dir / "labels" / "val"

    for d in (train_images, val_images, train_labels, val_labels):
        d.mkdir(parents=True)

    return train_images, val_images, train_labels, val_labels


def export_dataset(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    classes_path: Path = DEFAULT_CLASSES_PATH,
    val_ratio: float = 0.2,
    seed: int = 42,
) -> dict:
    """Export all stored contributions to a YOLOv8 training dataset.

    Args:
        output_dir: Directory to write the dataset to.
        classes_path: Path to neume_classes.yaml.
        val_ratio: Fraction of contributions for validation (0.0 to 1.0).
        seed: Random seed for reproducible train/val split.

    Returns:
        Summary dict with exported/skipped counts and train/val breakdown.
    """
    class_map = load_neume_classes(classes_path)
    contributions = list_contributions()

    if not contributions:
        logger.warning("No contributions found in %s", CONTRIBUTIONS_DIR)
        return {"exported": 0, "skipped": 0, "train": 0, "val": 0}

    # Prepare output directory
    train_images, val_images, train_labels, val_labels = _prepare_output_dir(output_dir)

    # Split contributions into train/val
    rng = random.Random(seed)
    shuffled = list(contributions)
    rng.shuffle(shuffled)

    if val_ratio <= 0 or len(shuffled) <= 1:
        val_count = 0
    else:
        val_count = max(1, round(len(shuffled) * val_ratio))
    val_set = set(cid for cid, _ in shuffled[:val_count])

    exported = 0
    skipped = 0
    train_exported = 0
    val_exported = 0

    for contribution_id, contribution_path in contributions:
        is_val = contribution_id in val_set
        images_dir = val_images if is_val else train_images
        labels_dir = val_labels if is_val else train_labels

        tile_count = _export_single_contribution(
            contribution_id, contribution_path, class_map, images_dir, labels_dir,
        )

        if tile_count > 0:
            exported += tile_count
            if is_val:
                val_exported += tile_count
            else:
                train_exported += tile_count
        else:
            skipped += 1

    # Generate dataset.yaml
    _generate_dataset_yaml(output_dir, class_map, classes_path)

    return {
        "exported": exported,
        "skipped": skipped,
        "train": train_exported,
        "val": val_exported,
    }


def main() -> None:
    """CLI entry point for YOLO dataset export."""
    parser = argparse.ArgumentParser(
        description="Export contributions to YOLOv8 training dataset format.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.2,
        help="Fraction of contributions for validation (default: 0.2)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for train/val split (default: 42)",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    summary = export_dataset(
        output_dir=args.output_dir,
        val_ratio=args.val_ratio,
        seed=args.seed,
    )

    print(f"\nExport complete:")
    print(f"  Exported: {summary['exported']}")
    print(f"  Skipped:  {summary['skipped']}")
    print(f"  Train:    {summary['train']}")
    print(f"  Val:      {summary['val']}")
    print(f"  Output:   {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
