## 1. Type Updates

- [x] 1.1 Add `"detecting"` to the `ProgressEvent.stage` literal type in `models/types.py`

## 2. Wire Detection into Stream Generator

- [x] 2.1 Import `mask_text_regions` and `detect_neumes` in `api.py`
- [x] 2.2 Add detecting stage to `_generate_recognition_stream`: after syllabifying, emit `"detecting"` event, call `mask_text_regions(img, segmentation)` then `detect_neumes(masked_image, segmentation)`
- [x] 2.3 Map `NeumeDetection` results into the response, applying region coordinate offset to neume bboxes when `region_obj` is set
- [x] 2.4 Pass the neumes list to `RecognitionResponse(neumes=...)` in the complete event

## 3. Tests

- [x] 3.1 Test that `"detecting"` stage event is emitted in the SSE stream
- [x] 3.2 Test that neume detections appear in the complete event's result when detection returns results (mock `detect_neumes`)
- [x] 3.3 Test that neumes array is empty when `detect_neumes` returns empty list (no model)
