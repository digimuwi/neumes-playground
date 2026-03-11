"""FastAPI application for HTR recognition service."""

import io
import json
from pathlib import Path
from typing import Generator, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image

from .models.types import (
    BBox,
    ContributionAnnotations,
    ContributionDetail,
    ContributionResponse,
    ContributionSummary,
    ImageMetadata,
    Line,
    NeumeDetection,
    ProgressEvent,
    RecognitionResponse,
    Syllable,
    TrainingStartRequest,
    TrainingStatus,
    format_sse_event,
)
from .contribution import get_contribution, save_contribution, update_contribution_annotations
from .contribution.storage import list_contributions
from .cors import build_cors_options
from .pipeline.geometry import extract_char_bboxes
from .pipeline.neume_detection import detect_neumes, detect_neumes_direct
from .pipeline.polygon_slicing import slice_line_polygon, syllable_x_ranges
from .pipeline.recognition import recognize_lines
from .pipeline.region import Region, crop_to_region, transform_bbox_to_full_image, validate_region
from .pipeline.segmentation import build_single_line_segmentation, segment_image
from .pipeline.text_masking import mask_text_regions
from .syllabification.latin import load_syllabifier, map_chars_to_syllables, merge_char_bboxes
from .training.yolo_trainer import (
    TrainingAlreadyRunningError,
    get_training_status,
    start_training,
)

# Paths to model and patterns (relative to package)
BASE_DIR = Path(__file__).parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "Tridis_Medieval_EarlyModern.mlmodel"
PATTERNS_PATH = BASE_DIR / "patterns" / "hyph_la_liturgical.dic"

app = FastAPI(
    title="HTR Service",
    description="Medieval manuscript syllable recognition using Kraken HTR",
    version="0.1.0",
)

app.add_middleware(CORSMiddleware, **build_cors_options())


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


class AnnotationsParseError(Exception):
    """Raised when annotations JSON is invalid."""

    pass


def _parse_annotations(annotations_json: str) -> ContributionAnnotations:
    """Parse annotations JSON string to ContributionAnnotations model."""
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
    annotations: str = Form(..., description="Annotations JSON with lines and neumes"),
):
    """Contribute training data for neume detection model training.

    Accepts an image and annotation data with polygon boundaries,
    and stores in the contributions directory for later training use.

    Args:
        image: The manuscript image file
        annotations: JSON string with structure:
            {
                "lines": [{"boundary": [[x,y],...], "syllables": [{"text": "...", "boundary": [[x,y],...]}]}],
                "neumes": [{"type": "...", "bbox": {...}}]
            }

    Returns:
        ContributionResponse with the contribution ID
    """
    # Parse and validate annotations
    try:
        parsed_annotations = _parse_annotations(annotations)
    except AnnotationsParseError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Load image to get dimensions
    try:
        image_bytes = await image.read()
        img = Image.open(io.BytesIO(image_bytes))
        image_width, image_height = img.size
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid image file: {e}")

    # Save contribution
    contribution_id, _ = save_contribution(
        image_bytes=image_bytes,
        annotations=parsed_annotations,
        image_width=image_width,
        image_height=image_height,
        content_type=image.content_type,
        original_filename=image.filename,
    )

    return ContributionResponse(
        id=contribution_id,
        message="Contribution saved successfully",
    )


@app.post("/training/start", status_code=202, response_model=TrainingStatus)
async def training_start(
    request: TrainingStartRequest = TrainingStartRequest(),
):
    """Start YOLO and segmentation model training.

    Exports training datasets from current contributions, then fine-tunes
    both models in independent background threads. Only one training run
    at a time is allowed.
    """
    try:
        status = start_training(
            epochs=request.epochs,
            imgsz=request.imgsz,
            seg_epochs=request.seg_epochs,
            from_scratch=request.from_scratch,
            parallel=request.parallel,
            training_type=request.training_type,
        )
    except TrainingAlreadyRunningError:
        raise HTTPException(status_code=409, detail="Training already in progress")
    return status


@app.get("/training/status", response_model=TrainingStatus)
async def training_status():
    """Get the current YOLO training status."""
    return get_training_status()


@app.get("/contributions", response_model=list[ContributionSummary])
async def list_contributions_endpoint():
    """List all stored contributions with summary info."""
    contributions = list_contributions()
    summaries = []
    for contribution_id, contribution_path in contributions:
        try:
            annotations_data = json.loads(
                (contribution_path / "annotations.json").read_text(encoding="utf-8")
            )
            image_meta = annotations_data.get("image", {})
            lines = annotations_data.get("lines", [])
            neumes = annotations_data.get("neumes", [])
            syllable_count = sum(
                len(line.get("syllables", [])) for line in lines
            )
            summaries.append(ContributionSummary(
                id=contribution_id,
                image=ImageMetadata(
                    filename=image_meta.get("filename", ""),
                    width=image_meta.get("width", 0),
                    height=image_meta.get("height", 0),
                ),
                line_count=len(lines),
                syllable_count=syllable_count,
                neume_count=len(neumes),
            ))
        except Exception:
            continue
    return summaries


@app.get("/contributions/{contribution_id}", response_model=ContributionDetail)
async def get_contribution_endpoint(contribution_id: str):
    """Retrieve a single contribution with full data including base64 image."""
    try:
        data = get_contribution(contribution_id)
    except (ValueError, FileNotFoundError):
        raise HTTPException(status_code=404, detail="Contribution not found")
    return data


@app.put("/contributions/{contribution_id}", response_model=ContributionResponse)
async def update_contribution_endpoint(
    contribution_id: str,
    annotations: ContributionAnnotations,
):
    """Update annotations for an existing contribution."""
    try:
        update_contribution_annotations(contribution_id, annotations)
    except ValueError:
        raise HTTPException(status_code=404, detail="Contribution not found")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Contribution not found")
    return ContributionResponse(
        id=contribution_id,
        message="Contribution updated successfully",
    )
