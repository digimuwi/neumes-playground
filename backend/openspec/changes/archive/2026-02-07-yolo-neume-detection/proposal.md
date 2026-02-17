## Why

The text masking module (Change 3) produces clean RGB images with text erased. We now need the detection module that runs YOLOv8 object detection on those masked images to find and classify individual neumes. This is the core ML inference component of the new neume detection pipeline.

## What Changes

- New `pipeline/neume_detection.py` module with `detect_neumes()` function
- YOLOv8 model loading with mtime-based caching (same pattern as Kraken model loader)
- SAHI tiled inference for large manuscript images, with tile size derived from median interlinear spacing
- Each detection returns neume type, bounding box, and confidence score
- Graceful degradation: returns empty list with a log warning when no trained model exists yet
- New dependencies: `ultralytics`, `sahi`

## Capabilities

### New Capabilities
- `neume-detection`: Object detection of neumes on text-masked manuscript images using YOLOv8 + SAHI tiled inference

### Modified Capabilities
- `neume-annotation-response`: Neume detections will include a confidence score alongside type and bbox

## Impact

- **New files**: `src/htr_service/pipeline/neume_detection.py`, tests
- **Modified**: `pyproject.toml` (new dependencies), `src/htr_service/models/types.py` (NeumeDetection type with confidence)
- **Dependencies**: `ultralytics` (YOLOv8), `sahi` (tiled inference)
- **Model path**: `models/neume_detector.pt` (will not exist until training in Change 8)
