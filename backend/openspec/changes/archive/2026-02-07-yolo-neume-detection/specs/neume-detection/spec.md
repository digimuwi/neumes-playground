## ADDED Requirements

### Requirement: Detect neumes on text-masked manuscript images
The `detect_neumes` function SHALL accept a PIL RGB image (with text already masked) and a Kraken `Segmentation` object, and SHALL return a list of `NeumeDetection` objects each containing a neume type, bounding box, and confidence score.

#### Scenario: Neumes detected on masked image
- **WHEN** `detect_neumes` is called with a text-masked image and segmentation, and a trained YOLO model exists
- **THEN** it returns a list of `NeumeDetection` objects with `type` (str), `bbox` (BBox), and `confidence` (float between 0 and 1)

#### Scenario: No detections on clean image
- **WHEN** `detect_neumes` is called with a masked image that contains no neume ink
- **THEN** it returns an empty list

### Requirement: Return empty list when no YOLO model exists
When no trained YOLO model file is found at the expected path, `detect_neumes` SHALL return an empty list and log a warning message indicating that no neume detection model is available yet.

#### Scenario: No model file present
- **WHEN** `detect_neumes` is called and no YOLO model file exists at the configured path
- **THEN** it returns an empty list
- **AND** a warning is logged indicating the model is not yet available

### Requirement: Use SAHI tiled inference for large images
The detection module SHALL use SAHI to tile the manuscript image into overlapping patches, run YOLOv8 inference on each tile, and merge results with NMS. This handles the large image dimensions (e.g., 3328x4992) that exceed typical YOLO input sizes.

#### Scenario: Large image is tiled for inference
- **WHEN** `detect_neumes` is called with a large manuscript image
- **THEN** SAHI splits the image into overlapping tiles, runs detection on each, and merges results

### Requirement: Derive tile size from median interlinear spacing
The SAHI tile size SHALL be computed from the Kraken segmentation by measuring the median vertical gap between consecutive text line boundaries. The tile size SHALL be approximately 4x the median interlinear height, clamped to the range [320, 1280] pixels.

#### Scenario: Tile size computed from segmentation with multiple lines
- **WHEN** the segmentation contains 3 or more text lines
- **THEN** the tile size is derived from the median gap between consecutive line boundaries, multiplied by 4, clamped to [320, 1280]

#### Scenario: Tile size fallback with fewer than 2 lines
- **WHEN** the segmentation contains fewer than 2 text lines
- **THEN** a default tile size of 640 pixels is used

### Requirement: Cache YOLO model with mtime-based validation
The YOLO model SHALL be loaded once and cached at module level. On subsequent calls, if the model file's mtime has not changed, the cached model SHALL be reused. If the mtime has changed (model was retrained), the model SHALL be reloaded.

#### Scenario: Model is cached across calls
- **WHEN** `detect_neumes` is called multiple times and the model file has not changed
- **THEN** the YOLO model is loaded only once and reused from cache

#### Scenario: Model is reloaded when file changes
- **WHEN** the model file's mtime changes between calls (e.g., after retraining)
- **THEN** the model is reloaded from disk on the next call
