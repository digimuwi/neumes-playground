## ADDED Requirements

### Requirement: Stream progress events during OCR processing
The `/recognize` endpoint SHALL return a Server-Sent Events (SSE) stream instead of a single JSON response. Each event SHALL be a JSON object with a `stage` field indicating the current processing stage.

#### Scenario: Client receives progress events for each stage
- **WHEN** client POSTs an image to `/recognize`
- **THEN** client receives SSE events in sequence: `loading`, `segmenting`, `recognizing`, `syllabifying`, `complete`

### Requirement: Report per-line progress during recognition
During the recognition stage, the system SHALL emit a progress event for each line being processed. Each event SHALL include `current` (1-indexed line number) and `total` (total number of lines).

#### Scenario: Multi-line image shows per-line progress
- **WHEN** client submits an image with 4 detected lines
- **THEN** client receives 4 recognition events with `{"stage": "recognizing", "current": 1, "total": 4}` through `{"stage": "recognizing", "current": 4, "total": 4}`

### Requirement: Include full result in completion event
The final `complete` event SHALL include the full recognition result in a `result` field, containing the same structure as the previous JSON response (syllables and lines arrays).

#### Scenario: Complete event contains recognition result
- **WHEN** OCR processing finishes successfully
- **THEN** client receives `{"stage": "complete", "result": {"syllables": [...], "lines": [...]}}`

### Requirement: Stream errors as events
If an error occurs during processing, the system SHALL emit an error event with `stage: "error"` and a `message` field describing the error, then close the stream.

#### Scenario: Invalid image format error
- **WHEN** client submits an invalid image file
- **THEN** client receives `{"stage": "error", "message": "Invalid image file"}` and stream closes

#### Scenario: Processing error mid-stream
- **WHEN** an error occurs during recognition
- **THEN** client receives `{"stage": "error", "message": "<error description>"}` and stream closes

### Requirement: SSE response format
The response SHALL use content-type `text/event-stream`. Each event SHALL follow SSE format: `data: <json>\n\n`.

#### Scenario: Response has correct content type
- **WHEN** client POSTs to `/recognize`
- **THEN** response content-type is `text/event-stream`
