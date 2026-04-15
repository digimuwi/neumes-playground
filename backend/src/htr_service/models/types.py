"""Pydantic models for API request/response."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class BBox(BaseModel):
    """Bounding box in pixel coordinates."""

    x: int = Field(..., description="X coordinate of top-left corner")
    y: int = Field(..., description="Y coordinate of top-left corner")
    width: int = Field(..., ge=1, description="Width in pixels")
    height: int = Field(..., ge=1, description="Height in pixels")


class Syllable(BaseModel):
    """A recognized syllable with its polygon boundary."""

    text: str = Field(..., description="The syllable text")
    boundary: list[list[int]] = Field(
        ..., description="Polygon boundary as list of [x, y] coordinate pairs"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Average confidence of constituent characters"
    )


class Line(BaseModel):
    """A recognized text line with polygon boundary and nested syllables."""

    text: str = Field(..., description="Full text of the line")
    boundary: list[list[int]] = Field(
        ..., description="Line boundary polygon as list of [x, y] coordinate pairs"
    )
    baseline: list[list[int]] = Field(
        default_factory=list,
        description="Line baseline as list of [x, y] coordinate pairs",
    )
    syllables: list[Syllable] = Field(
        default_factory=list, description="Syllables in this line"
    )


class RegionRequest(BaseModel):
    """Optional region to process within the image."""

    x: int = Field(..., ge=0, description="X coordinate of region top-left")
    y: int = Field(..., ge=0, description="Y coordinate of region top-left")
    width: int = Field(..., ge=1, description="Width of region in pixels")
    height: int = Field(..., ge=1, description="Height of region in pixels")


class RecognitionResponse(BaseModel):
    """Response from the recognition endpoint."""

    lines: list[Line] = Field(
        default_factory=list, description="Recognized text lines with nested syllables"
    )
    neumes: list["NeumeDetection"] = Field(
        default_factory=list, description="Detected neumes with bounding boxes and confidence"
    )


class ProgressEvent(BaseModel):
    """SSE progress event during OCR processing."""

    stage: Literal["loading", "segmenting", "recognizing", "syllabifying", "detecting", "complete", "error"] = Field(
        ..., description="Current processing stage"
    )
    current: Optional[int] = Field(None, description="Current line number (1-indexed) during recognition")
    total: Optional[int] = Field(None, description="Total number of lines during recognition")
    result: Optional[RecognitionResponse] = Field(None, description="Final result when stage is 'complete'")
    message: Optional[str] = Field(None, description="Error message when stage is 'error'")


def format_sse_event(event: ProgressEvent) -> str:
    """Format a ProgressEvent as an SSE data line."""
    return f"data: {event.model_dump_json(exclude_none=True)}\n\n"


# --- Contribution models ---


class SyllableInput(BaseModel):
    """A syllable annotation for contribution."""

    text: str = Field(..., description="The syllable text (may include trailing hyphen)")
    boundary: list[list[int]] = Field(
        ..., description="Polygon boundary as list of [x, y] coordinate pairs"
    )


class NeumeDetection(BaseModel):
    """A detected neume from YOLO object detection."""

    type: str = Field(..., description="Neume type (e.g., 'punctum', 'clivis')")
    bbox: BBox = Field(..., description="Bounding box in pixel coordinates")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Detection confidence score"
    )


class NeumeInput(BaseModel):
    """A neume annotation for contribution."""

    type: str = Field(..., description="Neume type (e.g., 'punctum', 'clivis')")
    bbox: BBox = Field(..., description="Bounding box in pixel coordinates")


class NeumeClass(BaseModel):
    """A neume class entry in the shared registry."""

    id: int = Field(..., ge=0, description="Stable integer class ID")
    key: str = Field(..., min_length=1, description="Canonical neume type string used in annotations")
    name: str = Field(..., min_length=1, description="Display label for UI")
    description: str = Field("", description="Optional UI help text")
    active: bool = Field(True, description="Whether the class is offered for new labeling")


class NeumeClassCreate(BaseModel):
    """Request to create a new neume class."""

    key: str = Field(..., min_length=1, description="Canonical neume type string used in annotations")
    name: str = Field(..., min_length=1, description="Display label for UI")
    description: str = Field("", description="Optional UI help text")


class NeumeClassUpdate(BaseModel):
    """Request to update a neume class."""

    name: Optional[str] = Field(None, min_length=1, description="Updated display label for UI")
    description: Optional[str] = Field(None, description="Updated UI help text")
    active: Optional[bool] = Field(None, description="Whether the class is offered for new labeling")


class NeumeRelabel(BaseModel):
    """Request to relabel a neume in a contribution."""

    bbox: BBox = Field(..., description="Bounding box identifying the neume to relabel")
    new_type: str = Field(..., description="New neume type to assign")


class NeumeCrop(BaseModel):
    """A cropped neume image from a contribution."""

    type: str = Field(..., description="Neume type (e.g., 'punctum', 'clivis')")
    contribution_id: str = Field(..., description="ID of the source contribution")
    bbox: BBox = Field(..., description="Bounding box in pixel coordinates")
    crop_data_url: str = Field(..., description="Base64-encoded data URL of the cropped neume region")


class LineInput(BaseModel):
    """A text line containing syllables for contribution."""

    boundary: list[list[int]] = Field(
        ..., description="Line boundary polygon as list of [x, y] coordinate pairs"
    )
    syllables: list[SyllableInput] = Field(
        default_factory=list, description="Syllables in this line"
    )


class ContributionAnnotations(BaseModel):
    """Annotation data for a training data contribution."""

    lines: list[LineInput] = Field(
        default_factory=list, description="Text lines with syllables"
    )
    neumes: list[NeumeInput] = Field(
        default_factory=list, description="Neume annotations"
    )


class ContributionResponse(BaseModel):
    """Response from the contribution endpoint."""

    id: str = Field(..., description="Unique identifier for the contribution")
    message: str = Field(..., description="Status message")


class ImageMetadata(BaseModel):
    """Image metadata from a stored contribution."""

    filename: str = Field(..., description="Image filename (e.g., 'image.jpg')")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")


class ContributionSummary(BaseModel):
    """Summary of a stored contribution for listing."""

    id: str = Field(..., description="Contribution UUID")
    image: ImageMetadata = Field(..., description="Image metadata")
    line_count: int = Field(..., description="Number of text lines")
    syllable_count: int = Field(..., description="Total number of syllables across all lines")
    neume_count: int = Field(..., description="Number of neume annotations")


class ImageDetail(BaseModel):
    """Image metadata with base64-encoded data URL."""

    filename: str = Field(..., description="Image filename (e.g., 'image.jpg')")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    data_url: str = Field(..., description="Base64-encoded data URL (e.g., 'data:image/jpeg;base64,...')")


class ContributionDetail(BaseModel):
    """Full contribution data including base64 image."""

    id: str = Field(..., description="Contribution UUID")
    image: ImageDetail = Field(..., description="Image with base64 data URL")
    lines: list[LineInput] = Field(default_factory=list, description="Line annotations")
    neumes: list[NeumeInput] = Field(default_factory=list, description="Neume annotations")


# --- Training models ---

TrainingState = Literal["idle", "exporting", "training", "deploying", "complete", "failed"]


TrainingMode = Literal["fresh", "incremental"]
TrainingType = Literal["neumes", "segmentation", "both"]


class TrainingStatus(BaseModel):
    """Current state of the YOLO training pipeline."""

    state: TrainingState = Field("idle", description="Current training state")
    mode: Optional[TrainingMode] = Field(None, description="Training mode: fresh (from yolov8n.pt) or incremental (from existing model)")
    current_epoch: Optional[int] = Field(None, description="Current epoch number (1-indexed)")
    total_epochs: Optional[int] = Field(None, description="Total number of epochs")
    metrics: Optional[dict] = Field(None, description="Latest training metrics (mAP, loss, etc.)")
    model_version: Optional[str] = Field(None, description="Timestamp of deployed model (YYYYMMDD_HHMMSS)")
    error: Optional[str] = Field(None, description="Error message when state is 'failed'")
    started_at: Optional[str] = Field(None, description="ISO timestamp when training started")
    completed_at: Optional[str] = Field(None, description="ISO timestamp when training finished")


class TrainingStartRequest(BaseModel):
    """Optional parameters for starting a training run."""

    epochs: Optional[int] = Field(None, ge=1, description="Number of YOLO training epochs (default: 100 fresh, 30 incremental)")
    imgsz: int = Field(640, ge=32, description="Training image size in pixels")
    from_scratch: bool = Field(False, description="Force training from yolov8n.pt instead of resuming from existing model")
    seg_epochs: int = Field(50, ge=1, description="Number of segmentation training epochs")
    parallel: bool = Field(False, description="Run YOLO and segmentation training concurrently instead of sequentially")
    training_type: TrainingType = Field("both", description="Which pipeline(s) to run: 'neumes', 'segmentation', or 'both'")
