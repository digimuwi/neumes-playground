"""Storage for training data contributions."""

import base64
import json
import logging
import mimetypes
import uuid
from pathlib import Path

from ..models.types import ContributionAnnotations

logger = logging.getLogger(__name__)

# Contributions directory relative to package root
BASE_DIR = Path(__file__).parent.parent.parent.parent
CONTRIBUTIONS_DIR = BASE_DIR / "contributions"


def _detect_image_extension(content_type: str | None, filename: str | None) -> str:
    """Detect image file extension from content type or filename.

    Returns 'jpg' or 'png' based on content type or filename.
    Defaults to 'jpg' if unknown.
    """
    if content_type:
        if "png" in content_type.lower():
            return "png"
        if "jpeg" in content_type.lower() or "jpg" in content_type.lower():
            return "jpg"

    if filename:
        lower_name = filename.lower()
        if lower_name.endswith(".png"):
            return "png"
        if lower_name.endswith(".jpg") or lower_name.endswith(".jpeg"):
            return "jpg"

    return "jpg"


def save_contribution(
    image_bytes: bytes,
    annotations: ContributionAnnotations,
    image_width: int,
    image_height: int,
    content_type: str | None = None,
    original_filename: str | None = None,
) -> tuple[str, Path]:
    """Save a contribution (image + annotations JSON) to the contributions directory.

    Args:
        image_bytes: Raw image file bytes
        annotations: Validated annotation data (lines + neumes)
        image_width: Image width in pixels
        image_height: Image height in pixels
        content_type: MIME type of the image (e.g., 'image/jpeg')
        original_filename: Original filename of the uploaded image

    Returns:
        Tuple of (contribution_id, contribution_directory_path)
    """
    contribution_id = str(uuid.uuid4())
    contribution_dir = CONTRIBUTIONS_DIR / contribution_id

    # Create contribution directory
    contribution_dir.mkdir(parents=True, exist_ok=True)

    # Determine image extension
    ext = _detect_image_extension(content_type, original_filename)
    image_filename = f"image.{ext}"

    # Save image
    image_path = contribution_dir / image_filename
    image_path.write_bytes(image_bytes)

    # Build annotations JSON with image metadata
    annotations_data = {
        "image": {
            "filename": image_filename,
            "width": image_width,
            "height": image_height,
        },
        "lines": [line.model_dump() for line in annotations.lines],
        "neumes": [neume.model_dump() for neume in annotations.neumes],
    }

    # Save annotations JSON
    annotations_path = contribution_dir / "annotations.json"
    annotations_path.write_text(
        json.dumps(annotations_data, indent=2), encoding="utf-8"
    )

    return contribution_id, contribution_dir


def _validate_contribution_id(contribution_id: str) -> None:
    """Validate that a contribution ID is a valid UUID.

    Raises:
        ValueError: If the ID is not a valid UUID.
    """
    try:
        uuid.UUID(contribution_id)
    except ValueError:
        raise ValueError(f"Invalid contribution ID: {contribution_id}")


def find_image_file(contribution_dir: Path) -> Path:
    """Find the image file in a contribution directory.

    Returns:
        Path to the image file.

    Raises:
        FileNotFoundError: If no image file is found.
    """
    for ext in ("jpg", "png"):
        image_path = contribution_dir / f"image.{ext}"
        if image_path.is_file():
            return image_path
    raise FileNotFoundError(f"No image file in {contribution_dir}")


def get_contribution(contribution_id: str) -> dict:
    """Load a contribution with its base64-encoded image.

    Args:
        contribution_id: UUID of the contribution.

    Returns:
        Dict with id, image (filename, width, height, data_url), lines, neumes.

    Raises:
        ValueError: If the contribution ID is not a valid UUID.
        FileNotFoundError: If the contribution does not exist.
    """
    _validate_contribution_id(contribution_id)

    contribution_dir = CONTRIBUTIONS_DIR / contribution_id
    annotations_path = contribution_dir / "annotations.json"

    if not annotations_path.is_file():
        raise FileNotFoundError(f"Contribution not found: {contribution_id}")

    annotations_data = json.loads(annotations_path.read_text(encoding="utf-8"))
    image_path = find_image_file(contribution_dir)

    # Build base64 data URL
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    image_bytes = image_path.read_bytes()
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"

    image_meta = annotations_data["image"]
    return {
        "id": contribution_id,
        "image": {
            "filename": image_meta["filename"],
            "width": image_meta["width"],
            "height": image_meta["height"],
            "data_url": data_url,
        },
        "lines": annotations_data.get("lines", []),
        "neumes": annotations_data.get("neumes", []),
    }


def update_contribution_annotations(
    contribution_id: str, annotations: ContributionAnnotations
) -> None:
    """Update annotations for an existing contribution, preserving image metadata.

    Args:
        contribution_id: UUID of the contribution.
        annotations: New annotation data (lines + neumes).

    Raises:
        ValueError: If the contribution ID is not a valid UUID.
        FileNotFoundError: If the contribution does not exist.
    """
    _validate_contribution_id(contribution_id)

    contribution_dir = CONTRIBUTIONS_DIR / contribution_id
    annotations_path = contribution_dir / "annotations.json"

    if not annotations_path.is_file():
        raise FileNotFoundError(f"Contribution not found: {contribution_id}")

    # Load existing to preserve image metadata
    existing = json.loads(annotations_path.read_text(encoding="utf-8"))

    updated = {
        "image": existing["image"],
        "lines": [line.model_dump() for line in annotations.lines],
        "neumes": [neume.model_dump() for neume in annotations.neumes],
    }

    annotations_path.write_text(json.dumps(updated, indent=2), encoding="utf-8")


def list_contributions() -> list[tuple[str, Path]]:
    """List all valid contributions in the contributions directory.

    A valid contribution directory contains at least one image file
    (image.jpg or image.png) and an annotations.json file.

    Returns:
        List of (contribution_id, contribution_path) tuples, sorted by ID.
    """
    if not CONTRIBUTIONS_DIR.is_dir():
        return []

    results = []
    for entry in sorted(CONTRIBUTIONS_DIR.iterdir()):
        if not entry.is_dir():
            continue

        annotations_path = entry / "annotations.json"
        has_image = (entry / "image.jpg").is_file() or (entry / "image.png").is_file()

        if not annotations_path.is_file() or not has_image:
            logger.warning(
                "Skipping malformed contribution %s: missing %s",
                entry.name,
                "annotations.json" if not annotations_path.is_file() else "image file",
            )
            continue

        results.append((entry.name, entry))

    return results
