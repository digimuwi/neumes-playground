## MODIFIED Requirements

### Requirement: Stream progress events during OCR processing
The `/recognize` endpoint SHALL return a Server-Sent Events (SSE) stream instead of a single JSON response. Each event SHALL be a JSON object with a `stage` field indicating the current processing stage.

#### Scenario: Client receives progress events for each stage
- **WHEN** client POSTs an image to `/recognize`
- **THEN** client receives SSE events in sequence: `loading`, `segmenting`, `recognizing`, `syllabifying`, `detecting`, `complete`
