## Context

Change 3 introduced `pipeline/text_masking.py` which erases text from manuscript images by filling Kraken boundary polygons with parchment color. The next step is a detection module that runs YOLOv8 on those masked images to find and classify neumes.

The existing model loading pattern (`pipeline/model_loader.py`) uses mtime-based caching with module-level state. The manuscript images are large (3328x4992) and require tiled inference.

No trained YOLO model exists yet — training comes in Changes 7-8. This module must work gracefully without a model.

## Goals / Non-Goals

**Goals:**
- Detect and classify neumes on text-masked manuscript images
- Use SAHI for tiled inference on large images, with tile size informed by interlinear spacing
- Cache the YOLO model with mtime validation (hot-swap when retrained)
- Return structured detections: type, bbox, confidence
- Gracefully return empty list when no model file exists

**Non-Goals:**
- Training the YOLO model (Change 8)
- Integrating into the `/recognize` SSE stream (Change 5)
- Neume-to-syllable or neume-to-line association (frontend concern)
- Configurable confidence thresholds (can add later if needed)

## Decisions

### Use `ultralytics` YOLO class directly for model loading
**Choice**: Load via `ultralytics.YOLO(path)` and cache the instance.
**Rationale**: The `ultralytics` library provides a simple, high-level API. The `YOLO` class handles device placement, input preprocessing, and NMS internally. No need for a custom wrapper.
**Alternative**: Using raw PyTorch model loading — rejected because ultralytics handles all the YOLO-specific pre/post-processing.

### Use SAHI `AutoDetectionModel` + `get_sliced_prediction` for tiled inference
**Choice**: SAHI wraps the ultralytics model and handles tiling, overlap, and NMS across tiles.
**Rationale**: Manuscript images (3328x4992) are too large for a single YOLO pass. SAHI provides battle-tested tile management with configurable overlap and post-processing.
**Alternative**: Manual tiling with custom NMS — rejected because SAHI does this well and is maintained.

### Derive tile size from median interlinear spacing
**Choice**: Compute median gap between consecutive text line boundaries (sorted by baseline y). Use ~4x this value as tile height and width (square tiles). Fallback to 640px if fewer than 2 lines.
**Rationale**: The interlinear space is where neumes live. Tile size should be large enough to contain one or more full interlinear bands. Using the segmentation data we already have avoids hardcoded values that won't generalize across manuscripts with different line spacings.
**Computation**: Sort lines by median baseline y → for consecutive pairs, compute (top of line N+1's boundary) - (bottom of line N's boundary) → take median → multiply by 4, clamp to [320, 1280].

### Cache YOLO model with mtime validation at module level
**Choice**: Same pattern as `model_loader.py` — a module-level `_yolo_cache` variable holding the model instance and file mtime. Reload when mtime changes.
**Rationale**: Consistency with existing codebase pattern. Enables hot-swap when a new model is trained.

### Return `NeumeDetection` with confidence score
**Choice**: Introduce a `NeumeDetection` Pydantic model with `type: str`, `bbox: BBox`, `confidence: float`.
**Rationale**: Confidence is free from YOLO and useful for the frontend (highlight uncertain detections, filter by threshold). Separate from `NeumeInput` which is the contribution model (what users submit).

### Model path convention
**Choice**: `models/neume_detector.pt` alongside the existing `models/Tridis_Medieval_EarlyModern.mlmodel`.
**Rationale**: Simple, discoverable, consistent with existing model directory usage.

## Risks / Trade-offs

- **No model exists yet** → Module returns empty list with a warning log. The pipeline remains fully functional for text-only recognition. Mitigated by clean graceful degradation.
- **SAHI tile overlap tuning** → Default overlap ratio (0.2) may not be optimal for neume-sized objects. Mitigation: use sensible defaults now, tune when real model exists.
- **`ultralytics` and `sahi` are heavy dependencies** → They pull in torch, opencv, etc. Mitigation: these are necessary for the YOLO inference path and will already be needed at training time.
- **Class name mapping** → YOLO models use integer class IDs internally. The mapping from ID to neume type name comes from the model's `names` dict (set during training). If no model exists, no mapping is needed. Risk of name mismatch is low since we control both training and inference.
