## Why

The current `/recognize` endpoint always runs the full pipeline (segmentation → text recognition → syllabification → text masking → neume detection) for every request. When users already know whether a region contains neumes or text, this is wasteful — segmentation and masking can be skipped entirely. Adding an optional `type` parameter lets the frontend send targeted recognition requests for user-selected single-line regions, making the pipeline faster and more direct.

## What Changes

- Add an optional `type` form field to `POST /recognize` accepting `"neume"` or `"text"` (null/absent preserves existing behavior)
- When `type="neume"`: crop to region, run YOLO directly on the cropped image (skip segmentation, text masking, and SAHI tiling), return only neumes
- When `type="text"`: crop to region, synthesize a single-line `Segmentation` from crop dimensions, run rpred/Tridis + syllabification, return only text lines
- When `type` is absent: existing full pipeline runs unchanged

## Capabilities

### New Capabilities
- `targeted-recognition`: Pipeline branching logic when a `type` parameter is provided — direct YOLO for neumes, synthetic segmentation + rpred for text

### Modified Capabilities
- `ocr-progress-streaming`: The SSE event sequence changes when `type` is set — only the relevant stages are emitted (e.g., no `segmenting` or `detecting` stage for `type="text"`)

## Impact

- **API**: New optional form field `type` on `POST /recognize` — non-breaking, existing clients unaffected
- **Code**: `api.py` pipeline orchestration (`_generate_recognition_stream`), new helper for synthetic segmentation, new direct-YOLO code path in neume detection
- **Dependencies**: No new dependencies
