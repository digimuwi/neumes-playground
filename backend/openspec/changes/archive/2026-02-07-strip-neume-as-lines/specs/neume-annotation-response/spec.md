## MODIFIED Requirements

### Requirement: Return neume annotations separately from syllables
The `/recognize` endpoint SHALL return a `neumes` array in the recognition response. Until YOLO-based neume detection is integrated, the `neumes` array SHALL always be empty. The response shape (`syllables`, `lines`, `neumes`) SHALL remain unchanged.

#### Scenario: Recognition response always contains empty neumes array
- **WHEN** the recognition pipeline processes any image
- **THEN** the response `result` contains a `neumes` array that is always an empty list `[]`

#### Scenario: Response shape is preserved for frontend compatibility
- **WHEN** the recognition pipeline completes successfully
- **THEN** the response `result` contains all three fields: `syllables` (list), `lines` (list), and `neumes` (empty list)

### Requirement: Only syllabify text lines
All lines detected by Kraken segmentation SHALL be treated as text lines and SHALL be syllabified. There is no longer a distinction between text-typed and neume-typed lines.

#### Scenario: All segmented lines are syllabified
- **WHEN** the recognition pipeline processes an image and Kraken detects lines
- **THEN** every detected line is recognized with the Tridis text model and syllabified

## REMOVED Requirements

### Requirement: Extract per-neume bounding boxes from recognition output
**Reason**: Neume detection no longer uses Kraken OCR on typed lines. The word-splitting and character-bbox-merging logic is removed. YOLO-based detection (future change) will provide neume bounding boxes directly.
**Migration**: No migration needed — the neumes array becomes empty. YOLO integration will restore neume detections with a different internal mechanism but the same response shape.

### Requirement: Neume annotation structure
**Reason**: No neume annotations are produced until YOLO integration. The `NeumeInput` type definition is retained for use by the `/contribute` endpoint, but the recognition pipeline no longer produces neume annotations.
**Migration**: None — neumes array is empty. Structure will be re-specified when YOLO detection is added.

### Requirement: Apply region coordinate transformation to neumes
**Reason**: No neume annotations are produced, so there are no coordinates to transform. This requirement will be re-added when YOLO-based detection is integrated.
**Migration**: None — the capability is dormant, not removed. The response shape is unchanged.
