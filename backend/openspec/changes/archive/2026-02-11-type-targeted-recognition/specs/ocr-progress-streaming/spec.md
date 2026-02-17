## MODIFIED Requirements

### Requirement: Stream progress events during OCR processing
The `/recognize` endpoint SHALL return a Server-Sent Events (SSE) stream instead of a single JSON response. Each event SHALL be a JSON object with a `stage` field indicating the current processing stage. When `type` is set, only the stages relevant to that type SHALL be emitted.

#### Scenario: Client receives progress events for each stage
- **WHEN** client POSTs an image to `/recognize` without a `type` parameter
- **THEN** client receives SSE events in sequence: `loading`, `segmenting`, `recognizing`, `syllabifying`, `detecting`, `complete`

#### Scenario: Client receives neume-only stages
- **WHEN** client POSTs an image to `/recognize` with `type="neume"`
- **THEN** client receives SSE events in sequence: `loading`, `detecting`, `complete`

#### Scenario: Client receives text-only stages
- **WHEN** client POSTs an image to `/recognize` with `type="text"`
- **THEN** client receives SSE events in sequence: `loading`, `recognizing`, `syllabifying`, `complete`
