## MODIFIED Requirements

### Requirement: Include full result in completion event
The final `complete` event SHALL include the full recognition result in a `result` field, containing syllables, lines, and neumes arrays.

#### Scenario: Complete event contains recognition result
- **WHEN** OCR processing finishes successfully
- **THEN** client receives `{"stage": "complete", "result": {"syllables": [...], "lines": [...], "neumes": [...]}}`
