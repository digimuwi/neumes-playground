## Why

The OCR processing endpoint takes ~20 seconds to complete, and currently returns only after full processing. Users have no feedback during this time, creating a frustrating experience where they don't know if the system is working or stuck.

## What Changes

- Add Server-Sent Events (SSE) streaming to the `/recognize` endpoint
- Emit progress events at each processing stage: loading, segmenting, recognizing (with per-line granularity), syllabifying
- Final event includes the complete recognition result
- Client can display real-time status updates during processing

## Capabilities

### New Capabilities
- `ocr-progress-streaming`: SSE-based progress reporting for OCR processing stages

### Modified Capabilities
<!-- No existing spec-level requirements are changing, only implementation -->

## Impact

- **API**: `/recognize` endpoint response format changes from JSON to SSE stream
- **Backend code**: `api.py` endpoint refactored to use `StreamingResponse`, `recognition.py` modified to support per-line progress callbacks
- **Client**: Will need to consume SSE events instead of waiting for JSON response (separate change)
