"""Storage for training data contributions.

On-disk format is MEI 5.0 (annotations.mei). The mei_io module owns
all XML-level concerns; this module deals with file IO, versioning,
and concurrency.
"""

import base64
import hashlib
import logging
import mimetypes
import threading
import uuid
from pathlib import Path

from ..models.types import ContributionAnnotations, ImageMetadata
from . import mei_io
from .mei_io import ContributionDocument

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent
CONTRIBUTIONS_DIR = BASE_DIR / "contributions"

ANNOTATIONS_FILENAME = "annotations.mei"

# Serializes read-check-write sequences across threads so If-Match enforcement
# doesn't race. Low-QPS service, so a single lock is fine.
_WRITE_LOCK = threading.Lock()


class VersionConflictError(Exception):
    """Raised when If-Match does not match the current on-disk version."""

    def __init__(self, *, expected: str, actual: str) -> None:
        super().__init__(
            f"Version mismatch: client had {expected!r}, server has {actual!r}"
        )
        self.expected = expected
        self.actual = actual


def _compute_version(mei_bytes: bytes) -> str:
    return hashlib.sha256(mei_bytes).hexdigest()


def _detect_image_extension(content_type: str | None, filename: str | None) -> str:
    """Detect image file extension from content type or filename.

    Returns 'jpg' or 'png'. Defaults to 'jpg' if unknown.
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


def _annotations_path(contribution_dir: Path) -> Path:
    """Return the path to the annotations file, preferring .mei but
    falling back to .json during the migration window."""
    mei_path = contribution_dir / ANNOTATIONS_FILENAME
    if mei_path.is_file():
        return mei_path
    legacy = contribution_dir / "annotations.json"
    if legacy.is_file():
        return legacy
    return mei_path


def save_contribution(
    image_bytes: bytes,
    annotations: ContributionAnnotations,
    image_width: int,
    image_height: int,
    content_type: str | None = None,
    original_filename: str | None = None,
) -> tuple[str, Path]:
    """Save a contribution (image + MEI annotations) to the contributions directory.

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

    contribution_dir.mkdir(parents=True, exist_ok=True)

    ext = _detect_image_extension(content_type, original_filename)
    image_filename = f"image.{ext}"

    image_path = contribution_dir / image_filename
    image_path.write_bytes(image_bytes)

    doc = ContributionDocument(
        image=ImageMetadata(
            filename=image_filename, width=image_width, height=image_height
        ),
        lines=list(annotations.lines),
        neumes=list(annotations.neumes),
    )
    mei_bytes = mei_io.write_contribution(doc)
    (contribution_dir / ANNOTATIONS_FILENAME).write_bytes(mei_bytes)

    return contribution_id, contribution_dir


def save_contribution_from_mei(
    image_bytes: bytes,
    mei_bytes: bytes,
    image_width: int,
    image_height: int,
    content_type: str | None = None,
    original_filename: str | None = None,
) -> tuple[str, Path]:
    """Save a contribution where annotations arrived as MEI bytes.

    The MEI is canonicalized before writing so the on-disk bytes (and
    thus the ETag) are stable regardless of how the client formatted
    its upload.
    """
    contribution_id = str(uuid.uuid4())
    contribution_dir = CONTRIBUTIONS_DIR / contribution_id
    contribution_dir.mkdir(parents=True, exist_ok=True)

    ext = _detect_image_extension(content_type, original_filename)
    image_filename = f"image.{ext}"
    (contribution_dir / image_filename).write_bytes(image_bytes)

    # Inject the actual image filename + dimensions in case the uploaded MEI's
    # <surface>/<graphic> have stale or generic values.
    doc = mei_io.read_contribution(mei_bytes)
    doc.image = ImageMetadata(
        filename=image_filename, width=image_width, height=image_height
    )
    canonical = mei_io.write_contribution(doc)
    (contribution_dir / ANNOTATIONS_FILENAME).write_bytes(canonical)

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


def read_document(contribution_dir: Path) -> ContributionDocument:
    """Load and parse a contribution's annotations into a ContributionDocument.

    Reads .mei if present, falls back to legacy .json files (the migration
    window). Used by training pipelines and API listing endpoints.
    """
    path = _annotations_path(contribution_dir)
    if path.suffix == ".mei":
        return mei_io.read_contribution(path.read_bytes())
    # Legacy JSON path
    return _read_legacy_json(path)


def _read_legacy_json(path: Path) -> ContributionDocument:
    """Read a legacy annotations.json file and convert to ContributionDocument."""
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    image_meta = data.get("image", {})
    return ContributionDocument(
        image=ImageMetadata(
            filename=image_meta.get("filename", "image.jpg"),
            width=image_meta.get("width", 0),
            height=image_meta.get("height", 0),
        ),
        lines=data.get("lines", []),
        neumes=data.get("neumes", []),
    )


def get_contribution(contribution_id: str) -> dict:
    """Load a contribution with its base64-encoded image and MEI body.

    Returns:
        Dict with id, image (filename, width, height, data_url), mei (XML
        string), lines, neumes (flat — for backwards-compat with any caller
        that wants the parsed model), version.
    """
    _validate_contribution_id(contribution_id)

    contribution_dir = CONTRIBUTIONS_DIR / contribution_id
    annotations_path = _annotations_path(contribution_dir)

    if not annotations_path.is_file():
        raise FileNotFoundError(f"Contribution not found: {contribution_id}")

    if annotations_path.suffix == ".mei":
        mei_bytes = annotations_path.read_bytes()
    else:
        # Legacy JSON: convert on-the-fly to MEI for the response
        doc = _read_legacy_json(annotations_path)
        mei_bytes = mei_io.write_contribution(doc)

    version = _compute_version(mei_bytes)
    doc = mei_io.read_contribution(mei_bytes)

    image_path = find_image_file(contribution_dir)
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    image_bytes = image_path.read_bytes()
    b64 = base64.b64encode(image_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{b64}"

    return {
        "id": contribution_id,
        "image": {
            "filename": doc.image.filename,
            "width": doc.image.width,
            "height": doc.image.height,
            "data_url": data_url,
        },
        "mei": mei_bytes.decode("utf-8"),
        "lines": [line.model_dump() for line in doc.lines],
        "neumes": [neume.model_dump() for neume in doc.neumes],
        "version": version,
    }


def get_contribution_version(contribution_id: str) -> str:
    """Return the sha256 version of a contribution's annotations.

    Raises:
        ValueError: If the ID is invalid.
        FileNotFoundError: If the contribution does not exist.
    """
    _validate_contribution_id(contribution_id)
    contribution_dir = CONTRIBUTIONS_DIR / contribution_id
    annotations_path = _annotations_path(contribution_dir)
    if not annotations_path.is_file():
        raise FileNotFoundError(f"Contribution not found: {contribution_id}")
    if annotations_path.suffix == ".mei":
        return _compute_version(annotations_path.read_bytes())
    # Legacy: compute version from the canonicalized MEI we'd produce
    doc = _read_legacy_json(annotations_path)
    return _compute_version(mei_io.write_contribution(doc))


def update_contribution_annotations(
    contribution_id: str,
    annotations: ContributionAnnotations,
    *,
    expected_version: str | None = None,
) -> str:
    """Update annotations for an existing contribution, preserving image metadata.

    Args:
        contribution_id: UUID of the contribution.
        annotations: New annotation data (lines + neumes).
        expected_version: If provided, the sha256 of the MEI the client based
            its edits on. Raises VersionConflictError if the current on-disk
            version differs.

    Returns:
        The sha256 version of the file after the write.
    """
    _validate_contribution_id(contribution_id)

    contribution_dir = CONTRIBUTIONS_DIR / contribution_id

    with _WRITE_LOCK:
        existing_path = _annotations_path(contribution_dir)
        if not existing_path.is_file():
            raise FileNotFoundError(f"Contribution not found: {contribution_id}")

        existing_doc = read_document(contribution_dir)
        if expected_version is not None:
            current_version = get_contribution_version(contribution_id)
            if current_version != expected_version:
                raise VersionConflictError(
                    expected=expected_version, actual=current_version
                )

        new_doc = ContributionDocument(
            image=existing_doc.image,
            lines=list(annotations.lines),
            neumes=list(annotations.neumes),
        )
        canonical = mei_io.write_contribution(new_doc)
        target_path = contribution_dir / ANNOTATIONS_FILENAME
        target_path.write_bytes(canonical)

        # Migration cleanup: if a legacy .json existed alongside, remove it
        legacy = contribution_dir / "annotations.json"
        if legacy.is_file() and legacy != target_path:
            legacy.unlink()

        return _compute_version(canonical)


def update_contribution_from_mei(
    contribution_id: str,
    mei_bytes: bytes,
    *,
    expected_version: str | None = None,
) -> str:
    """Update annotations from raw MEI bytes (the FE's preferred path).

    Image metadata in the incoming MEI is overwritten with the existing
    on-disk values so the client can't mutate filename/dimensions.
    """
    _validate_contribution_id(contribution_id)

    contribution_dir = CONTRIBUTIONS_DIR / contribution_id

    with _WRITE_LOCK:
        existing_path = _annotations_path(contribution_dir)
        if not existing_path.is_file():
            raise FileNotFoundError(f"Contribution not found: {contribution_id}")

        existing_doc = read_document(contribution_dir)
        if expected_version is not None:
            current_version = get_contribution_version(contribution_id)
            if current_version != expected_version:
                raise VersionConflictError(
                    expected=expected_version, actual=current_version
                )

        incoming = mei_io.read_contribution(mei_bytes)
        incoming.image = existing_doc.image
        canonical = mei_io.write_contribution(incoming)

        target_path = contribution_dir / ANNOTATIONS_FILENAME
        target_path.write_bytes(canonical)
        legacy = contribution_dir / "annotations.json"
        if legacy.is_file() and legacy != target_path:
            legacy.unlink()

        return _compute_version(canonical)


def relabel_neume(
    contribution_id: str,
    bbox: dict,
    new_type: str,
    *,
    expected_version: str | None = None,
) -> str:
    """Relabel a single neume in a contribution by matching its bounding box.

    Args:
        contribution_id: UUID of the contribution.
        bbox: Dict with x, y, width, height identifying the neume.
        new_type: New neume type string.
        expected_version: If provided, the sha256 of the MEI the client based
            its edits on.

    Returns:
        The sha256 version of the file after the write.
    """
    _validate_contribution_id(contribution_id)

    contribution_dir = CONTRIBUTIONS_DIR / contribution_id

    with _WRITE_LOCK:
        existing_path = _annotations_path(contribution_dir)
        if not existing_path.is_file():
            raise FileNotFoundError(f"Contribution not found: {contribution_id}")

        existing_doc = read_document(contribution_dir)
        if expected_version is not None:
            current_version = get_contribution_version(contribution_id)
            if current_version != expected_version:
                raise VersionConflictError(
                    expected=expected_version, actual=current_version
                )

        # Mutate via the model — find the neume by exact bbox match
        target = (
            int(bbox["x"]),
            int(bbox["y"]),
            int(bbox["width"]),
            int(bbox["height"]),
        )
        found = False
        for neume in existing_doc.neumes:
            b = neume.bbox
            if (b.x, b.y, b.width, b.height) == target:
                neume.type = new_type
                found = True
                break
        if not found:
            raise ValueError("No neume found with the given bounding box")

        canonical = mei_io.write_contribution(existing_doc)
        target_path = contribution_dir / ANNOTATIONS_FILENAME
        target_path.write_bytes(canonical)
        legacy = contribution_dir / "annotations.json"
        if legacy.is_file() and legacy != target_path:
            legacy.unlink()

        return _compute_version(canonical)


def list_contributions() -> list[tuple[str, Path]]:
    """List all valid contributions in the contributions directory.

    A valid contribution directory contains at least one image file and
    an annotations file (either .mei or legacy .json).
    """
    if not CONTRIBUTIONS_DIR.is_dir():
        return []

    results = []
    for entry in sorted(CONTRIBUTIONS_DIR.iterdir()):
        if not entry.is_dir():
            continue

        has_annotations = (entry / ANNOTATIONS_FILENAME).is_file() or (
            entry / "annotations.json"
        ).is_file()
        has_image = (entry / "image.jpg").is_file() or (entry / "image.png").is_file()

        if not has_annotations or not has_image:
            logger.warning(
                "Skipping malformed contribution %s: missing %s",
                entry.name,
                "annotations.mei/json" if not has_annotations else "image file",
            )
            continue

        results.append((entry.name, entry))

    return results
