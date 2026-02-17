## MODIFIED Requirements

### Requirement: Return neume annotations separately from syllables
The `/recognize` endpoint SHALL return a `neumes` array in the recognition response. Each neume entry SHALL include `type` (string neume class name), `bbox` (BBox in full-image pixel coordinates), and `confidence` (float between 0 and 1). When no YOLO model is available, the `neumes` array SHALL be empty. The response shape (`syllables`, `lines`, `neumes`) SHALL remain unchanged.

#### Scenario: Recognition response contains neume detections when model is available
- **WHEN** the recognition pipeline processes an image and a trained YOLO model exists
- **THEN** the response `result` contains a `neumes` array where each entry has `type` (str), `bbox` (BBox), and `confidence` (float)

#### Scenario: Recognition response contains empty neumes when no model exists
- **WHEN** the recognition pipeline processes any image and no YOLO model is available
- **THEN** the response `result` contains a `neumes` array that is an empty list `[]`

#### Scenario: Response shape is preserved for frontend compatibility
- **WHEN** the recognition pipeline completes successfully
- **THEN** the response `result` contains all three fields: `syllables` (list), `lines` (list), and `neumes` (list)

#### Scenario: Neume bboxes are in full-image coordinates when region crop is used
- **WHEN** a region crop is specified and neumes are detected
- **THEN** neume bboxes are offset by the region origin to produce full-image coordinates

### Requirement: Only syllabify text lines
All lines detected by Kraken segmentation SHALL be treated as text lines and SHALL be syllabified. There is no longer a distinction between text-typed and neume-typed lines.

#### Scenario: All segmented lines are syllabified
- **WHEN** the recognition pipeline processes an image and Kraken detects lines
- **THEN** every detected line is recognized with the Tridis text model and syllabified
