## MODIFIED Requirements

### Requirement: Return neume annotations separately from syllables
The `/recognize` endpoint SHALL return a `neumes` array in the recognition response. Each neume detection SHALL include a `type` (string), `bbox` (BBox), and `confidence` (float between 0 and 1). Until a trained YOLO model is available, the `neumes` array SHALL be empty. The response shape (`syllables`, `lines`, `neumes`) SHALL remain unchanged.

#### Scenario: Recognition response contains neumes with confidence scores
- **WHEN** the recognition pipeline processes an image and a trained YOLO model is available
- **THEN** the response `result` contains a `neumes` array where each entry has `type` (str), `bbox` (BBox), and `confidence` (float)

#### Scenario: Recognition response contains empty neumes when no model exists
- **WHEN** the recognition pipeline processes any image and no YOLO model is available
- **THEN** the response `result` contains a `neumes` array that is an empty list `[]`

#### Scenario: Response shape is preserved for frontend compatibility
- **WHEN** the recognition pipeline completes successfully
- **THEN** the response `result` contains all three fields: `syllables` (list), `lines` (list), and `neumes` (list)
