## 1. Direct YOLO Detection

- [x] 1.1 Add `detect_neumes_direct(image)` function to `neume_detection.py` that runs `model.predict()` directly on the input image (no SAHI, no masking), reusing `_load_yolo_model()` cache and 0.25 confidence threshold
- [x] 1.2 Add tests for `detect_neumes_direct` — detection on a small image, empty list when no model exists

## 2. Synthetic Segmentation

- [x] 2.1 Add a helper function (e.g., `build_single_line_segmentation(width, height)`) that constructs a Kraken `Segmentation` with one `BaselineLine` — baseline at vertical center, boundary as full image rectangle
- [x] 2.2 Add tests for the synthetic segmentation helper — verify baseline coordinates, boundary shape, and segmentation type

## 3. API & Pipeline Branching

- [x] 3.1 Add optional `type` form field (`"neume"` | `"text"` | `None`) to the `/recognize` endpoint
- [x] 3.2 Add `type` parameter to `_generate_recognition_stream()` and implement branching: validate the type value, then dispatch to the appropriate sub-pipeline
- [x] 3.3 Implement `type="neume"` branch: crop → `detect_neumes_direct` → offset bboxes → return `RecognitionResponse(lines=[], neumes=[...])`; emit only `loading`, `detecting`, `complete` SSE stages
- [x] 3.4 Implement `type="text"` branch: crop → synthetic segmentation → `recognize_lines` → syllabification → return `RecognitionResponse(lines=[...], neumes=[])`; emit only `loading`, `recognizing`, `syllabifying`, `complete` SSE stages
- [x] 3.5 Skip `MODEL_PATH`/`PATTERNS_PATH` existence checks when they're not needed for the chosen type
