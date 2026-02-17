## 1. Dependencies and Types

- [x] 1.1 Add `ultralytics` and `sahi` to `pyproject.toml` dependencies
- [x] 1.2 Add `NeumeDetection` model to `models/types.py` with `type: str`, `bbox: BBox`, `confidence: float`

## 2. Core Detection Module

- [x] 2.1 Create `pipeline/neume_detection.py` with YOLO model loading and mtime-based caching (module-level cache, same pattern as `model_loader.py`)
- [x] 2.2 Implement `_compute_tile_size(segmentation)` — compute median interlinear gap from sorted line boundaries, multiply by 4, clamp to [320, 1280], fallback 640px for <2 lines
- [x] 2.3 Implement `detect_neumes(masked_image, segmentation)` — load model, compute tile size, run SAHI `get_sliced_prediction`, map results to `NeumeDetection` list. Return empty list with warning log when no model file exists.

## 3. Tests

- [x] 3.1 Test that `detect_neumes` returns empty list and logs warning when no model file exists
- [x] 3.2 Test `_compute_tile_size` with multiple lines returns correct value (median gap x4, clamped)
- [x] 3.3 Test `_compute_tile_size` fallback to 640 with fewer than 2 lines
- [x] 3.4 Test `detect_neumes` with mocked YOLO model returns `NeumeDetection` objects with correct fields
- [x] 3.5 Test model caching: second call reuses cached model (mock verifies single load)
