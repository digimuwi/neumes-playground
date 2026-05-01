"""FastAPI application for HTR recognition service."""

import io
import json
import logging
from pathlib import Path
from typing import Generator, Optional

logger = logging.getLogger(__name__)

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image
from starlette.middleware.sessions import SessionMiddleware

from . import auth as auth_module
from . import storage_git
from .auth import User, require_user
from .contribution.storage import ANNOTATIONS_FILENAME, CONTRIBUTIONS_DIR
from .neume_registry import DEFAULT_CLASSES_PATH
from .models.types import (
    BBox,
    ContributionAnnotations,
    ContributionDetail,
    ContributionResponse,
    ContributionSummary,
    ImageMetadata,
    Line,
    NeumeClass,
    NeumeClassCreate,
    NeumeClassUpdate,
    NeumeCrop,
    NeumeDetection,
    NeumeRelabel,
    ProgressEvent,
    RecognitionResponse,
    Syllable,
    format_sse_event,
)
from .contribution import (
    VersionConflictError,
    find_image_file,
    get_contribution,
    read_document,
    relabel_neume,
    save_contribution,
    save_contribution_from_mei,
    update_contribution_annotations,
    update_contribution_from_mei,
)
from .contribution.storage import list_contributions
from .cors import build_cors_options
from .neume_registry import create_neume_class, load_neume_registry, update_neume_class
from .pipeline.geometry import extract_char_bboxes
from .pipeline.neume_detection import detect_neumes, detect_neumes_direct
from .pipeline.polygon_slicing import slice_line_polygon, syllable_x_ranges
from .pipeline.recognition import recognize_lines
from .pipeline.region import Region, crop_to_region, transform_bbox_to_full_image, validate_region
from .pipeline.segmentation import build_single_line_segmentation, segment_image
from .pipeline.text_masking import mask_text_regions
from .syllabification.latin import load_syllabifier, map_chars_to_syllables, merge_char_bboxes

# Paths to model and patterns (relative to package)
BASE_DIR = Path(__file__).parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "Tridis_Medieval_EarlyModern.mlmodel"
PATTERNS_PATH = BASE_DIR / "patterns" / "hyph_la_liturgical.dic"

app = FastAPI(
    title="HTR Service",
    description="Medieval manuscript syllable recognition using Kraken HTR",
    version="0.1.0",
)

_auth_settings = auth_module.get_settings()
app.add_middleware(
    SessionMiddleware,
    secret_key=_auth_settings.session_secret,
    same_site="none" if _auth_settings.backend_url.startswith("https://") else "lax",
    https_only=_auth_settings.backend_url.startswith("https://"),
)
app.add_middleware(CORSMiddleware, **build_cors_options())
app.include_router(auth_module.router)


class RegionParseError(Exception):
    """Raised when region JSON is invalid."""
    pass


class ImageLoadError(Exception):
    """Raised when image file is invalid."""
    pass


def _parse_region(region_json: Optional[str]) -> Optional[Region]:
    """Parse region JSON string to Region object."""
    if not region_json:
        return None

    try:
        import json
        data = json.loads(region_json)
        return Region(
            x=int(data["x"]),
            y=int(data["y"]),
            width=int(data["width"]),
            height=int(data["height"]),
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        raise RegionParseError(f"Invalid region format: {e}")


def _load_image(file: UploadFile) -> Image.Image:
    """Load and validate an uploaded image file."""
    try:
        contents = file.file.read()
        image = Image.open(io.BytesIO(contents))
        # Convert to RGB if necessary
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        return image
    except Exception as e:
        raise ImageLoadError(f"Invalid image file: {e}")


def _offset_polygon(
    polygon: list[list[int]], region: Region,
) -> list[list[int]]:
    """Translate polygon coordinates by a region offset."""
    return [[x + region.x, y + region.y] for x, y in polygon]


def _syllabify_results(
    recognition_results: list,
    region_obj: Optional[Region],
) -> list[Line]:
    """Syllabify recognition results and build Line models.

    Args:
        recognition_results: List of RecognitionResult from recognize_lines.
        region_obj: Optional region for coordinate offset.

    Returns:
        List of Line models with syllables.
    """
    syllabifier = load_syllabifier(PATTERNS_PATH)
    all_lines: list[Line] = []

    for rec_result in recognition_results:
        if not rec_result.text.strip():
            continue

        char_bboxes = extract_char_bboxes(
            rec_result.text, rec_result.cuts, rec_result.confidences
        )

        mapped = map_chars_to_syllables(
            rec_result.text, char_bboxes, syllabifier
        )

        syl_char_bboxes_list = [syl_bboxes for _, syl_bboxes in mapped]
        line_boundary = [(int(pt[0]), int(pt[1])) for pt in rec_result.boundary]

        x_ranges = syllable_x_ranges(syl_char_bboxes_list, line_boundary)
        syllable_polygons = slice_line_polygon(line_boundary, x_ranges)

        line_syllables: list[Syllable] = []
        for (syl_text, syl_bboxes), syl_polygon in zip(mapped, syllable_polygons):
            if syl_polygon is None or not syl_bboxes:
                continue

            _, _, _, _, avg_conf = merge_char_bboxes(syl_bboxes)

            boundary = [[x, y] for x, y in syl_polygon]
            if region_obj:
                boundary = _offset_polygon(boundary, region_obj)

            line_syllables.append(Syllable(
                text=syl_text,
                boundary=boundary,
                confidence=avg_conf,
            ))

        line_boundary_json = [[int(pt[0]), int(pt[1])] for pt in rec_result.boundary]
        line_baseline_json = [[int(pt[0]), int(pt[1])] for pt in rec_result.baseline]

        if region_obj:
            line_boundary_json = _offset_polygon(line_boundary_json, region_obj)
            line_baseline_json = _offset_polygon(line_baseline_json, region_obj)

        all_lines.append(Line(
            text=rec_result.text,
            boundary=line_boundary_json,
            baseline=line_baseline_json,
            syllables=line_syllables,
        ))

    return all_lines


def _generate_recognition_stream(
    file: UploadFile,
    region_json: Optional[str],
    recognition_type: Optional[str] = None,
) -> Generator[str, None, None]:
    """Generate SSE events for OCR recognition pipeline.

    Args:
        file: Uploaded image file.
        region_json: Optional region JSON string.
        recognition_type: Optional type ("neume" or "text") for targeted
            recognition. When set, only the relevant pipeline stages run.
    """
    progress_events: list[str] = []

    def on_line_progress(current: int, total: int) -> None:
        progress_events.append(
            format_sse_event(ProgressEvent(stage="recognizing", current=current, total=total))
        )

    try:
        # Validate type parameter
        if recognition_type is not None and recognition_type not in ("neume", "text"):
            yield format_sse_event(ProgressEvent(
                stage="error",
                message=f"Invalid type value: {recognition_type!r}. Must be 'neume' or 'text'.",
            ))
            return

        # Loading stage
        yield format_sse_event(ProgressEvent(stage="loading"))
        img = _load_image(file)

        # Parse and validate region
        region_obj = _parse_region(region_json)
        if region_obj:
            validate_region(img, region_obj)
            img = crop_to_region(img, region_obj)

        # --- Targeted neume recognition ---
        if recognition_type == "neume":
            yield format_sse_event(ProgressEvent(stage="detecting"))
            neume_detections = detect_neumes_direct(img)

            all_neumes: list[NeumeDetection] = []
            for det in neume_detections:
                if region_obj:
                    all_neumes.append(
                        NeumeDetection(
                            type=det.type,
                            bbox=BBox(
                                x=det.bbox.x + region_obj.x,
                                y=det.bbox.y + region_obj.y,
                                width=det.bbox.width,
                                height=det.bbox.height,
                            ),
                            confidence=det.confidence,
                        )
                    )
                else:
                    all_neumes.append(det)

            yield format_sse_event(ProgressEvent(
                stage="complete",
                result=RecognitionResponse(lines=[], neumes=all_neumes),
            ))
            return

        # --- Targeted text recognition ---
        if recognition_type == "text":
            if not MODEL_PATH.exists():
                raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
            if not PATTERNS_PATH.exists():
                raise FileNotFoundError(f"Patterns not found: {PATTERNS_PATH}")

            segmentation = build_single_line_segmentation(img.width, img.height)

            recognition_results = recognize_lines(
                img, segmentation, MODEL_PATH, on_line_progress=on_line_progress
            )
            for event in progress_events:
                yield event

            yield format_sse_event(ProgressEvent(stage="syllabifying"))
            all_lines = _syllabify_results(recognition_results, region_obj)

            yield format_sse_event(ProgressEvent(
                stage="complete",
                result=RecognitionResponse(lines=all_lines, neumes=[]),
            ))
            return

        # --- Full pipeline (type is None) ---

        # Check model and patterns exist
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
        if not PATTERNS_PATH.exists():
            raise FileNotFoundError(f"Patterns not found: {PATTERNS_PATH}")

        # Segment the original (non-binarized) image — segmentation works
        # much better on RGB than on binarized images.
        yield format_sse_event(ProgressEvent(stage="segmenting"))
        segmentation = segment_image(img)

        if not segmentation.lines:
            yield format_sse_event(ProgressEvent(
                stage="complete",
                result=RecognitionResponse(lines=[], neumes=[])
            ))
            return

        # Recognition stage (with per-line progress)
        recognition_results = recognize_lines(
            img, segmentation, MODEL_PATH, on_line_progress=on_line_progress
        )

        # Yield all collected recognition progress events
        for event in progress_events:
            yield event

        # Syllabifying stage
        yield format_sse_event(ProgressEvent(stage="syllabifying"))
        all_lines = _syllabify_results(recognition_results, region_obj)

        # Detecting stage
        yield format_sse_event(ProgressEvent(stage="detecting"))
        masked_image = mask_text_regions(img, segmentation)
        neume_detections = detect_neumes(masked_image, segmentation)

        # Map neume bboxes to full-image coordinates
        all_neumes_list: list[NeumeDetection] = []
        for det in neume_detections:
            if region_obj:
                all_neumes_list.append(
                    NeumeDetection(
                        type=det.type,
                        bbox=BBox(
                            x=det.bbox.x + region_obj.x,
                            y=det.bbox.y + region_obj.y,
                            width=det.bbox.width,
                            height=det.bbox.height,
                        ),
                        confidence=det.confidence,
                    )
                )
            else:
                all_neumes_list.append(det)

        # Complete stage with result
        yield format_sse_event(ProgressEvent(
            stage="complete",
            result=RecognitionResponse(
                lines=all_lines, neumes=all_neumes_list
            ),
        ))

    except ImageLoadError as e:
        yield format_sse_event(ProgressEvent(stage="error", message=str(e)))
    except RegionParseError as e:
        yield format_sse_event(ProgressEvent(stage="error", message=str(e)))
    except ValueError as e:
        yield format_sse_event(ProgressEvent(stage="error", message=str(e)))
    except Exception as e:
        yield format_sse_event(ProgressEvent(stage="error", message=f"Processing error: {e}"))


@app.post("/recognize")
async def recognize(
    image: UploadFile = File(..., description="Image file to process"),
    region: Optional[str] = Form(None, description="Optional region JSON: {x, y, width, height}"),
    type: Optional[str] = Form(None, description="Optional recognition type: 'neume' or 'text'"),
):
    """Recognize syllables in an uploaded manuscript image.

    Returns an SSE stream with progress events during processing.
    Events include: loading, segmenting, recognizing (with line progress),
    syllabifying, and complete (with final result).

    When type is set, only the relevant pipeline stages run:
    - type="neume": loading → detecting → complete
    - type="text": loading → recognizing → syllabifying → complete
    """
    return StreamingResponse(
        _generate_recognition_stream(image, region, recognition_type=type),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/neume-classes", response_model=list[NeumeClass])
async def list_neume_classes():
    """Return the shared neume class registry."""
    return load_neume_registry()


@app.post("/neume-classes", status_code=201, response_model=NeumeClass)
async def create_neume_class_endpoint(
    body: NeumeClassCreate,
    user: User = Depends(require_user),
):
    """Create a new neume class with a stable appended ID."""
    try:
        created = create_neume_class(body)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    storage_git.commit_paths(
        [DEFAULT_CLASSES_PATH],
        message=f"Add neume class {created.key} — {user.login}",
        author_name=user.login,
    )
    return created


@app.patch("/neume-classes/{class_id}", response_model=NeumeClass)
async def update_neume_class_endpoint(
    class_id: int,
    body: NeumeClassUpdate,
    user: User = Depends(require_user),
):
    """Update mutable neume class fields."""
    try:
        updated = update_neume_class(class_id, body)
    except KeyError:
        raise HTTPException(status_code=404, detail="Neume class not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    storage_git.commit_paths(
        [DEFAULT_CLASSES_PATH],
        message=f"Update neume class {updated.key} — {user.login}",
        author_name=user.login,
    )
    return updated


class AnnotationsParseError(Exception):
    """Raised when annotation payload is invalid."""

    pass


def _looks_like_xml(s: str) -> bool:
    return s.lstrip().startswith("<")


def _parse_annotations_legacy_json(annotations_json: str) -> ContributionAnnotations:
    """Parse legacy JSON annotation payload to ContributionAnnotations model."""
    try:
        data = json.loads(annotations_json)
        return ContributionAnnotations(**data)
    except json.JSONDecodeError as e:
        raise AnnotationsParseError(f"Invalid JSON: {e}")
    except Exception as e:
        raise AnnotationsParseError(f"Invalid annotations format: {e}")


@app.post("/contribute", status_code=201, response_model=ContributionResponse)
async def contribute(
    image: UploadFile = File(..., description="Image file (JPEG or PNG)"),
    mei: Optional[str] = Form(None, description="MEI 5.0 XML annotations"),
    annotations: Optional[str] = Form(
        None, description="(Legacy) JSON annotations with lines and neumes"
    ),
    user: User = Depends(require_user),
):
    """Contribute training data for neume detection model training.

    Accepts an image and annotation data. The preferred form field is
    `mei` (MEI 5.0 XML). The legacy `annotations` JSON field is still
    accepted during the migration window.
    """
    # Pick whichever form field is present
    if mei is None and annotations is None:
        raise HTTPException(
            status_code=422,
            detail="Either 'mei' or 'annotations' form field is required",
        )

    # If 'annotations' looks like XML, treat it as MEI (the FE may rename mid-deploy)
    raw_payload = mei if mei is not None else annotations
    if raw_payload is None:
        raise HTTPException(status_code=422, detail="Empty annotations payload")

    payload_is_mei = mei is not None or _looks_like_xml(raw_payload)

    # Load image to get dimensions
    try:
        image_bytes = await image.read()
        img = Image.open(io.BytesIO(image_bytes))
        image_width, image_height = img.size
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid image file: {e}")

    try:
        if payload_is_mei:
            contribution_id, contribution_dir = save_contribution_from_mei(
                image_bytes=image_bytes,
                mei_bytes=raw_payload.encode("utf-8"),
                image_width=image_width,
                image_height=image_height,
                content_type=image.content_type,
                original_filename=image.filename,
            )
        else:
            parsed = _parse_annotations_legacy_json(raw_payload)
            contribution_id, contribution_dir = save_contribution(
                image_bytes=image_bytes,
                annotations=parsed,
                image_width=image_width,
                image_height=image_height,
                content_type=image.content_type,
                original_filename=image.filename,
            )
    except AnnotationsParseError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid MEI: {e}")

    image_name = image.filename or "image"
    storage_git.commit_paths(
        [contribution_dir],
        message=f"Add contribution {contribution_id} for {image_name} — {user.login}",
        author_name=user.login,
    )

    return ContributionResponse(
        id=contribution_id,
        message="Contribution saved successfully",
    )


@app.get("/contributions", response_model=list[ContributionSummary])
async def list_contributions_endpoint():
    """List all stored contributions with summary info."""
    contributions = list_contributions()
    summaries = []
    for contribution_id, contribution_path in contributions:
        try:
            doc = read_document(contribution_path)
            syllable_count = sum(len(line.syllables) for line in doc.lines)
            summaries.append(ContributionSummary(
                id=contribution_id,
                image=ImageMetadata(
                    filename=doc.image.filename,
                    width=doc.image.width,
                    height=doc.image.height,
                ),
                line_count=len(doc.lines),
                syllable_count=syllable_count,
                neume_count=len(doc.neumes),
            ))
        except Exception:
            logger.exception("Failed to summarize contribution %s", contribution_id)
            continue
    return summaries


def _parse_if_match(if_match: str | None) -> str | None:
    """Strip surrounding quotes from an ETag-style If-Match header.

    Returns None when the header is absent or equals '*' (RFC 7232 wildcard
    that matches any current version — we just skip the check).
    """
    if if_match is None:
        return None
    value = if_match.strip()
    if value == "*" or value == "":
        return None
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    return value


@app.get("/contributions/{contribution_id}", response_model=ContributionDetail)
async def get_contribution_endpoint(contribution_id: str, response: Response):
    """Retrieve a single contribution with full data including base64 image."""
    try:
        data = get_contribution(contribution_id)
    except (ValueError, FileNotFoundError):
        raise HTTPException(status_code=404, detail="Contribution not found")
    response.headers["ETag"] = f'"{data["version"]}"'
    return data


@app.put("/contributions/{contribution_id}", response_model=ContributionResponse)
async def update_contribution_endpoint(
    contribution_id: str,
    request: Request,
    response: Response,
    user: User = Depends(require_user),
    if_match: str | None = Header(default=None, alias="If-Match"),
):
    """Update annotations for an existing contribution.

    Body may be:
      - Raw MEI XML (Content-Type: text/xml or application/xml)
      - JSON `{"mei": "<?xml..."}` (Content-Type: application/json)
      - Legacy JSON ContributionAnnotations (Content-Type: application/json)

    Send the ETag from the last GET as `If-Match` to prevent overwriting
    concurrent edits; returns 412 on mismatch.
    """
    # Validate UUID up-front so invalid IDs return 404, not 422
    import uuid as _uuid
    try:
        _uuid.UUID(contribution_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Contribution not found")

    expected_version = _parse_if_match(if_match)
    if expected_version is None:
        logger.warning(
            "PUT /contributions/%s from %s without If-Match — concurrent edits may be lost",
            contribution_id, user.login,
        )

    body = await request.body()
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()

    try:
        if content_type in ("text/xml", "application/xml") or _looks_like_xml(
            body.decode("utf-8", errors="replace")
        ):
            new_version = update_contribution_from_mei(
                contribution_id, body, expected_version=expected_version
            )
        else:
            # JSON body — sniff for {mei: ...} envelope vs legacy ContributionAnnotations
            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=422, detail=f"Invalid JSON: {e}")

            if isinstance(data, dict) and "mei" in data and isinstance(data["mei"], str):
                new_version = update_contribution_from_mei(
                    contribution_id,
                    data["mei"].encode("utf-8"),
                    expected_version=expected_version,
                )
            else:
                try:
                    parsed = ContributionAnnotations(**data)
                except Exception as e:
                    raise HTTPException(status_code=422, detail=f"Invalid annotations: {e}")
                new_version = update_contribution_annotations(
                    contribution_id, parsed, expected_version=expected_version
                )
    except VersionConflictError as e:
        raise HTTPException(
            status_code=412,
            detail=(
                "Contribution was modified by someone else since you loaded it. "
                "Reload to see the latest version before saving again."
            ),
            headers={"ETag": f'"{e.actual}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid MEI: {e}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Contribution not found")

    storage_git.commit_paths(
        [CONTRIBUTIONS_DIR / contribution_id / ANNOTATIONS_FILENAME],
        message=f"Update annotations on {contribution_id} — {user.login}",
        author_name=user.login,
    )
    response.headers["ETag"] = f'"{new_version}"'
    return ContributionResponse(
        id=contribution_id,
        message="Contribution updated successfully",
        version=new_version,
    )


@app.patch("/contributions/{contribution_id}/neumes", response_model=ContributionResponse)
async def relabel_neume_endpoint(
    contribution_id: str,
    body: NeumeRelabel,
    response: Response,
    user: User = Depends(require_user),
    if_match: str | None = Header(default=None, alias="If-Match"),
):
    """Relabel a single neume in a contribution by matching its bounding box."""
    expected_version = _parse_if_match(if_match)
    try:
        new_version = relabel_neume(
            contribution_id,
            bbox=body.bbox.model_dump(),
            new_type=body.new_type,
            expected_version=expected_version,
        )
    except VersionConflictError as e:
        raise HTTPException(
            status_code=412,
            detail=(
                "Contribution was modified by someone else since you loaded it. "
                "Reload to see the latest version before relabeling again."
            ),
            headers={"ETag": f'"{e.actual}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Contribution not found")
    storage_git.commit_paths(
        [CONTRIBUTIONS_DIR / contribution_id / ANNOTATIONS_FILENAME],
        message=f"Relabel neume in {contribution_id} to {body.new_type} — {user.login}",
        author_name=user.login,
    )
    response.headers["ETag"] = f'"{new_version}"'
    return ContributionResponse(
        id=contribution_id,
        message="Neume relabeled successfully",
        version=new_version,
    )


@app.get("/neumes", response_model=list[NeumeCrop])
async def list_neumes(
    type: Optional[str] = Query(None, description="Filter by neume type"),
):
    """List neume crops across all contributions.

    Returns cropped images of individual neumes from all stored contributions,
    optionally filtered by neume type.
    """
    import base64
    import mimetypes

    crops: list[NeumeCrop] = []

    for contribution_id, contribution_path in list_contributions():
        try:
            doc = read_document(contribution_path)
            if not doc.neumes:
                continue

            matching = [n for n in doc.neumes if type is None or n.type == type]
            if not matching:
                continue

            image_path = find_image_file(contribution_path)
            img = Image.open(image_path)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"

            for neume in matching:
                bbox = neume.bbox
                x = max(0, bbox.x)
                y = max(0, bbox.y)
                right = min(img.width, bbox.x + bbox.width)
                bottom = min(img.height, bbox.y + bbox.height)

                if right <= x or bottom <= y:
                    continue

                crop = img.crop((x, y, right, bottom))

                buf = io.BytesIO()
                fmt = "PNG" if "png" in mime else "JPEG"
                crop.save(buf, format=fmt)
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                crop_data_url = f"data:{mime};base64,{b64}"

                crops.append(NeumeCrop(
                    type=neume.type,
                    contribution_id=contribution_id,
                    bbox=BBox(x=x, y=y, width=right - x, height=bottom - y),
                    crop_data_url=crop_data_url,
                ))
        except Exception:
            logger.exception("Failed to crop neumes for %s", contribution_id)
            continue

    return crops
