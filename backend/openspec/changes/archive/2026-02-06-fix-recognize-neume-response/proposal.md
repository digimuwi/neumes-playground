## Why

The `/recognize` endpoint treats all recognition results identically — neume lines and text lines both get Latin-syllabified and returned as `syllables`. This means neume recognition output (e.g., "pitus peus es cpitus") is nonsensically syllabified, and the frontend has no way to render neume annotations (red boxes) separately from syllable annotations (blue boxes). The `line_type` field from recognition is completely discarded during response assembly.

## What Changes

- **BREAKING**: Add a `neumes` field to `RecognitionResponse` containing neume annotations with type and bbox
- Check `rec_result.line_type` in the response assembly loop (`api.py:239-281`) to separate neume lines from text lines
- Only syllabify text lines; skip Latin syllabification for neume lines
- Parse neume recognition output into individual neume annotations, mapping each recognized word to a neume type with its character bounding box

## Capabilities

### New Capabilities
- `neume-annotation-response`: The `/recognize` endpoint returns neume annotations separately from syllables, with neume type and bounding box for each detected neume

### Modified Capabilities
- `ocr-progress-streaming`: The `complete` event result now includes a `neumes` array alongside `syllables` and `lines`

## Impact

- `src/htr_service/models/types.py` — Add `neumes` field to `RecognitionResponse`
- `src/htr_service/api.py` — Modify response assembly loop to branch on `line_type`
- `src/htr_service/pipeline/geometry.py` — May need a function to extract per-word bounding boxes for neume tokens
- Frontend will need to handle the new `neumes` field in the SSE complete event (out of scope for this backend change)
