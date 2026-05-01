"""Restore contributions from frontend annotation backup files.

Reads backup JSON files (containing base64 image + flat annotation list with
normalized coordinates), replicates the frontend's line-clustering algorithm,
converts to the backend contribution storage format, and creates contribution
directories.

Usage:
    python scripts/restore_contributions.py ~/Downloads/annotated-neumes
"""

import base64
import json
import math
import sys
import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image

CONTRIBUTIONS_DIR = Path(__file__).parent.parent / "contributions"

# --- Line clustering (replicates frontend useTextLines.ts) ---

PERP_THRESHOLD = 0.02
Y_THRESHOLD = 0.03


def _perpendicular_distance(
    x: float, y: float, slope: float, intercept: float
) -> float:
    numerator = abs(y - (slope * x + intercept))
    denominator = math.sqrt(slope * slope + 1)
    return numerator / denominator


def _fit_linear_regression(
    points: list[dict],
) -> tuple[float, float]:
    n = len(points)
    sum_x = sum(p["center_x"] for p in points)
    sum_y = sum(p["bottom_y"] for p in points)
    sum_xy = sum(p["center_x"] * p["bottom_y"] for p in points)
    sum_x2 = sum(p["center_x"] ** 2 for p in points)

    denominator = n * sum_x2 - sum_x * sum_x
    if abs(denominator) < 1e-10:
        return 0.0, sum_y / n

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def _cluster_syllables_into_lines(syllables: list[dict]) -> list[dict]:
    """Cluster syllable annotations into text lines.

    Replicates the frontend computeTextLines() algorithm.
    Input syllables have normalized (0-1) rect coordinates.
    """
    if not syllables:
        return []

    metrics = []
    for s in syllables:
        r = s["rect"]
        metrics.append({
            "annotation": s,
            "center_x": r["x"] + r["width"] / 2,
            "bottom_y": r["y"] + r["height"],
        })

    metrics.sort(key=lambda m: m["bottom_y"])

    clusters: list[dict] = []

    for syllable in metrics:
        best_idx = -1
        best_distance = float("inf")

        for i, cluster in enumerate(clusters):
            if len(cluster["points"]) >= 2:
                distance = _perpendicular_distance(
                    syllable["center_x"],
                    syllable["bottom_y"],
                    cluster["slope"],
                    cluster["intercept"],
                )
                if distance < best_distance and distance <= PERP_THRESHOLD:
                    best_distance = distance
                    best_idx = i
            else:
                distance = abs(syllable["bottom_y"] - cluster["intercept"])
                if distance < best_distance and distance <= Y_THRESHOLD:
                    best_distance = distance
                    best_idx = i

        if best_idx >= 0:
            cluster = clusters[best_idx]
            cluster["points"].append(syllable)
            if len(cluster["points"]) >= 2:
                slope, intercept = _fit_linear_regression(cluster["points"])
                cluster["slope"] = slope
                cluster["intercept"] = intercept
        else:
            clusters.append({
                "points": [syllable],
                "slope": 0.0,
                "intercept": syllable["bottom_y"],
            })

    # Build lines
    lines = []
    for cluster in clusters:
        lines.append({
            "slope": cluster["slope"],
            "intercept": cluster["intercept"],
            "syllables": [p["annotation"] for p in cluster["points"]],
        })

    # Inherit slopes for single-syllable lines
    multi = [l for l in lines if len(l["syllables"]) >= 2]
    if multi:
        for line in lines:
            if len(line["syllables"]) == 1:
                s = line["syllables"][0]
                r = s["rect"]
                cx = r["x"] + r["width"] / 2
                by = r["y"] + r["height"]

                nearest = min(multi, key=lambda m: abs(line["intercept"] - m["intercept"]))
                line["slope"] = nearest["slope"]
                line["intercept"] = by - nearest["slope"] * cx

    lines.sort(key=lambda l: l["intercept"])
    return lines


def _rect_to_pixel_bbox(rect: dict, width: int, height: int) -> dict:
    return {
        "x": round(rect["x"] * width),
        "y": round(rect["y"] * height),
        "width": max(1, round(rect["width"] * width)),
        "height": max(1, round(rect["height"] * height)),
    }


def _bbox_to_boundary(bbox: dict) -> list[list[int]]:
    x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


def _line_boundary_from_syllables(syllable_boundaries: list[list[list[int]]]) -> list[list[int]]:
    """Compute a bounding rectangle for all syllable boundaries in a line."""
    all_x = [pt[0] for boundary in syllable_boundaries for pt in boundary]
    all_y = [pt[1] for boundary in syllable_boundaries for pt in boundary]
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    return [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]


def restore_file(backup_path: Path) -> str:
    """Restore a single backup file as a contribution. Returns the contribution ID."""
    data = json.loads(backup_path.read_text(encoding="utf-8"))

    # Decode image
    data_url = data["imageDataUrl"]
    header, b64_data = data_url.split(",", 1)
    img_bytes = base64.b64decode(b64_data)
    img = Image.open(BytesIO(img_bytes))
    img_width, img_height = img.size

    # Determine format
    if "png" in header:
        ext = "png"
        img_format = "PNG"
    else:
        ext = "jpg"
        img_format = "JPEG"

    # Separate syllables and neumes
    annotations = data["annotations"]
    syllables = [a for a in annotations if a["type"] == "syllable"]
    neumes = [a for a in annotations if a["type"] == "neume"]

    # Cluster syllables into lines
    text_lines = _cluster_syllables_into_lines(syllables)

    # Build contribution format
    contrib_lines = []
    for line in text_lines:
        syl_boundaries = []
        contrib_syllables = []
        for syl in line["syllables"]:
            bbox = _rect_to_pixel_bbox(syl["rect"], img_width, img_height)
            boundary = _bbox_to_boundary(bbox)
            syl_boundaries.append(boundary)
            contrib_syllables.append({
                "text": syl.get("text", ""),
                "boundary": boundary,
            })

        line_boundary = _line_boundary_from_syllables(syl_boundaries)
        contrib_lines.append({
            "boundary": line_boundary,
            "syllables": contrib_syllables,
        })

    contrib_neumes = []
    for neume in neumes:
        bbox = _rect_to_pixel_bbox(neume["rect"], img_width, img_height)
        contrib_neumes.append({
            "type": neume.get("neumeType", "unknown"),
            "bbox": bbox,
        })

    # Create contribution directory
    contribution_id = str(uuid.uuid4())
    contribution_dir = CONTRIBUTIONS_DIR / contribution_id
    contribution_dir.mkdir(parents=True, exist_ok=True)

    # Save image
    image_filename = f"image.{ext}"
    img.save(contribution_dir / image_filename, format=img_format)

    # Save annotations as canonical MEI
    from htr_service.contribution import mei_io
    from htr_service.contribution.mei_io import ContributionDocument
    from htr_service.models.types import (
        ImageMetadata,
        LineInput,
        NeumeInput,
        SyllableInput,
        BBox,
    )

    doc = ContributionDocument(
        image=ImageMetadata(
            filename=image_filename, width=img_width, height=img_height
        ),
        lines=[
            LineInput(
                boundary=line["boundary"],
                syllables=[
                    SyllableInput(text=s["text"], boundary=s["boundary"])
                    for s in line["syllables"]
                ],
            )
            for line in contrib_lines
        ],
        neumes=[
            NeumeInput(type=n["type"], bbox=BBox(**n["bbox"]))
            for n in contrib_neumes
        ],
    )
    (contribution_dir / "annotations.mei").write_bytes(mei_io.write_contribution(doc))

    return contribution_id


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/restore_contributions.py <backup_directory>")
        sys.exit(1)

    backup_dir = Path(sys.argv[1])
    if not backup_dir.is_dir():
        print(f"Error: {backup_dir} is not a directory")
        sys.exit(1)

    backup_files = sorted(backup_dir.glob("*.json"))
    if not backup_files:
        print(f"No JSON files found in {backup_dir}")
        sys.exit(1)

    print(f"Found {len(backup_files)} backup file(s)")
    CONTRIBUTIONS_DIR.mkdir(parents=True, exist_ok=True)

    for path in backup_files:
        contribution_id = restore_file(path)
        print(f"  {path.name} -> {contribution_id}")

    print(f"\nRestored {len(backup_files)} contribution(s) to {CONTRIBUTIONS_DIR}")


if __name__ == "__main__":
    main()
