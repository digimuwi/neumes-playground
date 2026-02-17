## Why

Changes 3 and 4 built the text masking and YOLO neume detection modules as standalone pipeline components. They are not yet wired into the `/recognize` endpoint. After this change, `/recognize` returns both text and neume results — neumes come from YOLO detection on the text-masked image instead of the old Kraken OCR approach.

## What Changes

- Add a `"detecting"` stage to the SSE progress stream (emitted after syllabifying, before complete)
- Call `mask_text_regions()` then `detect_neumes()` during the recognition stream generator
- Populate the `neumes` array in `RecognitionResponse` with YOLO detections (type, bbox, confidence)
- Apply region coordinate offset to neume bounding boxes when a region crop is active
- Update `ProgressEvent.stage` to include the new `"detecting"` literal

## Capabilities

### New Capabilities

(none)

### Modified Capabilities
- `ocr-progress-streaming`: Add `"detecting"` stage to the SSE event sequence
- `neume-annotation-response`: Neumes now come from YOLO object detection with confidence scores; the array is populated when a model is available, empty otherwise

## Impact

- **Modified files**: `api.py` (stream generator, imports), `models/types.py` (ProgressEvent stage literal)
- **API change**: New `"detecting"` SSE stage — additive, not breaking (clients that don't handle it can ignore it)
- **Response change**: `neumes` array may now contain items (was always empty) — additive, not breaking
