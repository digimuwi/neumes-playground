"""Export stored contributions to PageXML for Kraken segmentation training.

Converts contributions (image + annotations.json) into PageXML files with
computed baselines and typed regions (text / neume), suitable for fine-tuning
Kraken's default segmentation model.

Usage:
    python -m htr_service.training.seg_export [--output-dir DIR]
"""

import json
import logging
import shutil
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

from ..contribution.storage import list_contributions

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = BASE_DIR / "datasets" / "segmentation"

_PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"


def _points_str(points: list[list[int]]) -> str:
    """Convert [[x,y], ...] to PageXML coordinate string 'x1,y1 x2,y2 ...'."""
    return " ".join(f"{int(x)},{int(y)}" for x, y in points)


def _interp_x(p1: list[int], p2: list[int], y: int) -> int:
    """Interpolate X coordinate where the edge p1→p2 crosses horizontal line y."""
    if p1[1] == p2[1]:
        return p1[0]
    t = (y - p1[1]) / (p2[1] - p1[1])
    return int(p1[0] + t * (p2[0] - p1[0]))


def clip_polygon_below(polygon: list[list[int]], y_threshold: int) -> list[list[int]]:
    """Clip a polygon from below — keep only the portion at or above y_threshold.

    Walks polygon edges, keeps vertices with y <= y_threshold, and interpolates
    new vertices where edges cross the threshold.
    """
    if not polygon:
        return polygon
    result = []
    n = len(polygon)
    for i in range(n):
        curr = polygon[i]
        nxt = polygon[(i + 1) % n]
        curr_inside = curr[1] <= y_threshold
        nxt_inside = nxt[1] <= y_threshold
        if curr_inside:
            result.append(curr)
        if curr_inside != nxt_inside:
            x = _interp_x(curr, nxt, y_threshold)
            result.append([x, y_threshold])
    return result


def clip_polygon_above(polygon: list[list[int]], y_threshold: int) -> list[list[int]]:
    """Clip a polygon from above — keep only the portion at or below y_threshold.

    Walks polygon edges, keeps vertices with y >= y_threshold, and interpolates
    new vertices where edges cross the threshold.
    """
    if not polygon:
        return polygon
    result = []
    n = len(polygon)
    for i in range(n):
        curr = polygon[i]
        nxt = polygon[(i + 1) % n]
        curr_inside = curr[1] >= y_threshold
        nxt_inside = nxt[1] >= y_threshold
        if curr_inside:
            result.append(curr)
        if curr_inside != nxt_inside:
            x = _interp_x(curr, nxt, y_threshold)
            result.append([x, y_threshold])
    return result


def _syllable_bottom_center(boundary: list[list[int]]) -> tuple[int, int]:
    """Compute bottom-center of a syllable boundary polygon."""
    xs = [pt[0] for pt in boundary]
    ys = [pt[1] for pt in boundary]
    return (min(xs) + max(xs)) // 2, max(ys)


def compute_baseline(syllables: list[dict]) -> list[list[int]]:
    """Compute a baseline polyline from syllable boundary positions.

    Takes the bottom-center of each syllable boundary, sorted by X.
    Returns a list of [x, y] points forming the baseline.
    """
    points = []
    for syl in syllables:
        boundary = syl.get("boundary", [])
        if len(boundary) < 3:
            continue
        points.append(_syllable_bottom_center(boundary))

    if not points:
        return []

    # Sort by X coordinate (left to right)
    points.sort(key=lambda p: p[0])

    # For a single syllable, create a horizontal segment
    if len(points) == 1:
        x, y = points[0]
        boundary = syllables[0]["boundary"]
        x_min = min(pt[0] for pt in boundary)
        x_max = max(pt[0] for pt in boundary)
        return [[x_min, y], [x_max, y]]

    return [[x, y] for x, y in points]


def group_neumes_by_line(
    lines: list[dict],
    baselines: list[list[list[int]]],
    neumes: list[dict],
    image_height: int,
) -> list[list[dict]]:
    """Group neume bboxes by their associated text line.

    For each text line, collects neumes whose vertical center falls above
    that line — between the previous line's baseline Y and the current
    line's baseline Y.

    Returns a list of neume groups, one per line (may be empty).
    """
    # Compute baseline Y for each line (average Y of baseline points)
    baseline_ys = []
    for bl in baselines:
        if bl:
            avg_y = sum(pt[1] for pt in bl) / len(bl)
            baseline_ys.append(avg_y)
        else:
            baseline_ys.append(None)

    groups: list[list[dict]] = [[] for _ in lines]

    for neume in neumes:
        bbox = neume.get("bbox", {})
        neume_center_y = bbox.get("y", 0) + bbox.get("height", 0) / 2

        # Find which line this neume belongs to:
        # It's above the line whose baseline Y is just below the neume's center
        assigned = False
        for i, bl_y in enumerate(baseline_ys):
            if bl_y is None:
                continue
            if neume_center_y < bl_y:
                groups[i].append(neume)
                assigned = True
                break

        # If below all baselines, assign to the last line
        if not assigned and baseline_ys:
            for i in range(len(baseline_ys) - 1, -1, -1):
                if baseline_ys[i] is not None:
                    groups[i].append(neume)
                    break

    return groups


def neume_group_bbox(neumes: list[dict]) -> list[list[int]] | None:
    """Compute bounding rectangle polygon for a group of neumes.

    Returns [[x1,y1], [x2,y1], [x2,y2], [x1,y2]] or None if empty.
    """
    if not neumes:
        return None

    x_min = float("inf")
    y_min = float("inf")
    x_max = float("-inf")
    y_max = float("-inf")

    for neume in neumes:
        bbox = neume["bbox"]
        x_min = min(x_min, bbox["x"])
        y_min = min(y_min, bbox["y"])
        x_max = max(x_max, bbox["x"] + bbox["width"])
        y_max = max(y_max, bbox["y"] + bbox["height"])

    x1, y1, x2, y2 = int(x_min), int(y_min), int(x_max), int(y_max)
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]


def _clip_adjacent_regions(regions: list[dict]) -> None:
    """Clip overlapping adjacent regions at the vertical midpoint of the overlap.

    Modifies region boundaries in-place so no pixel belongs to more than one
    region.  For TextRegions the enclosed TextLine boundary is clipped
    identically.
    """
    for i in range(len(regions) - 1):
        a = regions[i]
        b = regions[i + 1]
        a_y_max = max(pt[1] for pt in a["boundary"])
        b_y_min = min(pt[1] for pt in b["boundary"])
        if a_y_max <= b_y_min:
            continue  # no overlap
        clip_y = (a_y_max + b_y_min) // 2
        a["boundary"] = clip_polygon_below(a["boundary"], clip_y)
        b["boundary"] = clip_polygon_above(b["boundary"], clip_y)
        if a.get("text_boundary") is not None:
            a["text_boundary"] = clip_polygon_below(a["text_boundary"], clip_y)
        if b.get("text_boundary") is not None:
            b["text_boundary"] = clip_polygon_above(b["text_boundary"], clip_y)


def build_pagexml(
    image_filename: str,
    image_width: int,
    image_height: int,
    lines: list[dict],
    baselines: list[list[list[int]]],
    neume_groups: list[list[dict]],
) -> ElementTree:
    """Build a PageXML ElementTree from contribution data.

    Each text line is wrapped in exactly one TextRegion, and each neume group
    in one MusicRegion.  Adjacent region boundaries are clipped at the vertical
    midpoint of any overlap so no pixel belongs to more than one region.

    Args:
        image_filename: Filename of the associated image.
        image_width: Image width in pixels.
        image_height: Image height in pixels.
        lines: Line annotations (boundary + syllables).
        baselines: Computed baselines, one per line.
        neume_groups: Grouped neume bboxes, one group per line.

    Returns:
        ElementTree ready to write to a file.
    """
    # -- Phase 1: collect regions ----------------------------------------
    regions: list[dict] = []
    for i, (line, baseline) in enumerate(zip(lines, baselines)):
        if not baseline:
            continue
        boundary = line.get("boundary", [])
        if len(boundary) < 3:
            continue
        neume_rect = neume_group_bbox(neume_groups[i])
        if neume_rect:
            regions.append({"tag": "MusicRegion", "boundary": neume_rect,
                            "type": "neume"})
        regions.append({"tag": "TextRegion", "boundary": list(boundary),
                        "text_boundary": list(boundary),
                        "baseline": baseline, "type": "text"})

    # -- Phase 2: sort by vertical position and clip overlaps -------------
    def _y_mid(reg):
        ys = [pt[1] for pt in reg["boundary"]]
        return (min(ys) + max(ys)) / 2

    regions.sort(key=_y_mid)
    # Iterate until no overlaps remain (clipping one pair can shift
    # boundaries enough to create a small overlap with the next pair).
    for _ in range(5):
        _clip_adjacent_regions(regions)
        regions = [r for r in regions if len(r["boundary"]) >= 3]
        regions.sort(key=_y_mid)

    # -- Phase 3: serialize to XML ---------------------------------------
    root = Element("PcGts", xmlns=_PAGE_NS)
    page = SubElement(
        root,
        "Page",
        imageFilename=image_filename,
        imageWidth=str(image_width),
        imageHeight=str(image_height),
    )
    region_id = 0
    for reg in regions:
        region_id += 1
        if reg["tag"] == "TextRegion":
            boundary = reg["text_boundary"]
            if len(boundary) < 3:
                boundary = reg["boundary"]
            tr = SubElement(page, "TextRegion",
                            id=f"r_{region_id}", type=reg["type"])
            SubElement(tr, "Coords", points=_points_str(reg["boundary"]))
            tl = SubElement(tr, "TextLine", id=f"l_{region_id}")
            SubElement(tl, "Coords", points=_points_str(boundary))
            SubElement(tl, "Baseline", points=_points_str(reg["baseline"]))
        else:
            mr = SubElement(page, "MusicRegion",
                            id=f"r_{region_id}", type=reg["type"])
            SubElement(mr, "Coords", points=_points_str(reg["boundary"]))

    return ElementTree(root)


def export_contribution(
    contribution_id: str,
    contribution_path: Path,
    output_dir: Path,
) -> bool:
    """Export a single contribution to PageXML.

    Returns True if export succeeded, False if skipped.
    """
    annotations_path = contribution_path / "annotations.json"
    data = json.loads(annotations_path.read_text(encoding="utf-8"))

    lines = data.get("lines", [])
    neumes = data.get("neumes", [])
    image_meta = data.get("image", {})
    image_width = image_meta.get("width", 0)
    image_height = image_meta.get("height", 0)

    if not lines:
        logger.info("Skipping %s: no lines", contribution_id)
        return False

    # Compute baselines from syllable positions
    baselines = []
    has_any_baseline = False
    for line in lines:
        syllables = line.get("syllables", [])
        bl = compute_baseline(syllables)
        baselines.append(bl)
        if bl:
            has_any_baseline = True

    if not has_any_baseline:
        logger.info("Skipping %s: no syllables for baseline computation", contribution_id)
        return False

    # Group neumes by line
    neume_groups = group_neumes_by_line(lines, baselines, neumes, image_height)

    # Find image file
    image_filename = image_meta.get("filename", "image.jpg")
    image_source = contribution_path / image_filename
    if not image_source.is_file():
        # Try other extensions
        for ext in ("jpg", "png"):
            candidate = contribution_path / f"image.{ext}"
            if candidate.is_file():
                image_source = candidate
                image_filename = candidate.name
                break

    # Build PageXML
    tree = build_pagexml(
        image_filename=image_filename,
        image_width=image_width,
        image_height=image_height,
        lines=lines,
        baselines=baselines,
        neume_groups=neume_groups,
    )

    # Symlink image (avoid copying large files)
    image_ext = image_source.suffix
    image_dest = output_dir / f"{contribution_id}{image_ext}"
    if image_dest.exists():
        image_dest.unlink()
    image_dest.symlink_to(image_source.resolve())

    # Update Page element to reference the symlinked image name
    page_elem = tree.getroot()[0]  # First child of PcGts is Page
    page_elem.set("imageFilename", image_dest.name)

    # Write PageXML
    xml_path = output_dir / f"{contribution_id}.xml"
    indent(tree, space="  ")
    tree.write(xml_path, encoding="unicode", xml_declaration=True)

    return True


def export_segmentation_dataset(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict:
    """Export all contributions to PageXML for segmentation training.

    Args:
        output_dir: Directory to write PageXML files and image symlinks.

    Returns:
        Summary dict with 'exported' and 'skipped' counts and 'files' list.
    """
    # Clear and recreate output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contributions = list_contributions()
    exported = 0
    skipped = 0
    files: list[str] = []

    for contribution_id, contribution_path in contributions:
        if export_contribution(contribution_id, contribution_path, output_dir):
            exported += 1
            files.append(str(output_dir / f"{contribution_id}.xml"))
            logger.info("Exported %s", contribution_id)
        else:
            skipped += 1

    logger.info(
        "Segmentation export complete: %d exported, %d skipped",
        exported,
        skipped,
    )
    return {"exported": exported, "skipped": skipped, "files": files}


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Export contributions to PageXML")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory (default: datasets/segmentation)",
    )
    args = parser.parse_args()

    summary = export_segmentation_dataset(output_dir=args.output_dir)
    print(f"Exported: {summary['exported']}, Skipped: {summary['skipped']}")
