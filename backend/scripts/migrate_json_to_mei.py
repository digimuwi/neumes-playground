"""One-shot migration: convert legacy annotations.json files to annotations.mei.

Reads each contributions/<id>/annotations.json, parses it as
ContributionDocument, and writes annotations.mei alongside (does NOT
delete the .json — that's a separate cleanup step).

After this script, the backend will read .mei in preference to .json
(see storage._annotations_path), so the system flips to MEI immediately
while preserving the JSON files as a safety net.

Usage:
    python scripts/migrate_json_to_mei.py [--delete-json]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRIBUTIONS_DIR = REPO_ROOT / "contributions"

# Add backend src to path so we can import htr_service when run as a script
sys.path.insert(0, str(REPO_ROOT / "src"))

from htr_service.contribution import mei_io  # noqa: E402
from htr_service.contribution.mei_io import ContributionDocument  # noqa: E402
from htr_service.models.types import ImageMetadata, LineInput, NeumeInput  # noqa: E402


def migrate_one(contribution_dir: Path, delete_json: bool = False) -> str:
    """Convert one contribution. Returns 'migrated', 'skipped', or 'already'.

    'already' = annotations.mei already exists
    'skipped' = no annotations.json found
    'migrated' = JSON converted to MEI
    """
    json_path = contribution_dir / "annotations.json"
    mei_path = contribution_dir / "annotations.mei"

    if mei_path.is_file():
        return "already"

    if not json_path.is_file():
        return "skipped"

    data = json.loads(json_path.read_text(encoding="utf-8"))
    image_meta = data.get("image", {})

    doc = ContributionDocument(
        image=ImageMetadata(
            filename=image_meta.get("filename", "image.jpg"),
            width=image_meta.get("width", 0),
            height=image_meta.get("height", 0),
        ),
        lines=[LineInput(**line) for line in data.get("lines", [])],
        neumes=[NeumeInput(**neume) for neume in data.get("neumes", [])],
    )

    canonical = mei_io.write_contribution(doc)
    mei_path.write_bytes(canonical)

    # Sanity check: parse what we just wrote and confirm content equivalence.
    # Neume ORDER changes (writer sorts by spatial assignment), so compare as
    # multisets of (type, bbox tuples). Lines + image must match exactly.
    reparsed = mei_io.read_contribution(canonical)
    if reparsed.image.model_dump() != doc.image.model_dump():
        mei_path.unlink()
        raise RuntimeError(
            f"Image metadata mismatch for {contribution_dir.name}; kept JSON"
        )
    if [l.model_dump() for l in reparsed.lines] != [l.model_dump() for l in doc.lines]:
        mei_path.unlink()
        raise RuntimeError(
            f"Line content mismatch for {contribution_dir.name}; kept JSON"
        )
    orig_neumes = sorted(
        (n.type, n.bbox.x, n.bbox.y, n.bbox.width, n.bbox.height) for n in doc.neumes
    )
    new_neumes = sorted(
        (n.type, n.bbox.x, n.bbox.y, n.bbox.width, n.bbox.height) for n in reparsed.neumes
    )
    if orig_neumes != new_neumes:
        mei_path.unlink()
        raise RuntimeError(
            f"Neume content mismatch for {contribution_dir.name}; kept JSON"
        )

    if delete_json:
        json_path.unlink()

    return "migrated"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delete-json",
        action="store_true",
        help="Delete annotations.json after successful migration (default: keep both)",
    )
    parser.add_argument(
        "--contributions-dir",
        type=Path,
        default=CONTRIBUTIONS_DIR,
        help=f"Contributions directory (default: {CONTRIBUTIONS_DIR})",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not args.contributions_dir.is_dir():
        logger.error("Not a directory: %s", args.contributions_dir)
        sys.exit(1)

    counts = {"migrated": 0, "already": 0, "skipped": 0, "failed": 0}
    for entry in sorted(args.contributions_dir.iterdir()):
        if not entry.is_dir():
            continue
        try:
            result = migrate_one(entry, delete_json=args.delete_json)
            counts[result] += 1
            if result == "migrated":
                logger.info("Migrated %s", entry.name)
            elif result == "already":
                logger.info("Skipped %s (already has annotations.mei)", entry.name)
            else:
                logger.warning("Skipped %s (no annotations.json)", entry.name)
        except Exception as e:
            counts["failed"] += 1
            logger.error("Failed %s: %s", entry.name, e)

    print(
        f"\nMigration complete: "
        f"{counts['migrated']} migrated, "
        f"{counts['already']} already MEI, "
        f"{counts['skipped']} skipped (no JSON), "
        f"{counts['failed']} failed"
    )

    if counts["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
