## ADDED Requirements

### Requirement: Return neume annotations separately from syllables
The `/recognize` endpoint SHALL return neume annotations in a dedicated `neumes` array in the recognition response, separate from the `syllables` array. Each neume annotation SHALL contain the recognized neume type as a string and a bounding box in pixel coordinates.

#### Scenario: Image with neume and text lines returns both syllables and neumes
- **WHEN** the recognition pipeline processes an image containing both neume-typed and text-typed lines
- **THEN** the response `result` contains a `syllables` array with syllable annotations from text lines AND a `neumes` array with neume annotations from neume lines

#### Scenario: Image with only text lines returns empty neumes array
- **WHEN** the recognition pipeline processes an image containing only text-typed lines (or untyped lines)
- **THEN** the response `result` contains syllables and an empty `neumes` array

### Requirement: Only syllabify text lines
The response assembly SHALL only apply Latin syllabification to recognition results from text-typed lines (where `line_type` is `"text"` or `None`). Recognition results from neume-typed lines SHALL NOT be syllabified.

#### Scenario: Neume line recognition output is not syllabified
- **WHEN** a recognition result has `line_type="neume"` with text `"pitus peus es cpitus"`
- **THEN** the output is NOT passed through the Latin syllabifier and does NOT appear in the `syllables` array

#### Scenario: Text line recognition output is syllabified as before
- **WHEN** a recognition result has `line_type="text"` with text `"Benedictus"`
- **THEN** the output is syllabified and appears in the `syllables` array as before

### Requirement: Extract per-neume bounding boxes from recognition output
For neume-typed lines, the system SHALL split the recognition text on whitespace to identify individual neumes. Each word SHALL be mapped to its corresponding character bounding boxes (from Kraken cuts), which SHALL be merged into a single bounding box per neume.

#### Scenario: Multi-word neume recognition produces one bbox per word
- **WHEN** a neume line recognition result contains text `"pitus clivis ceitus"` with character-level cuts
- **THEN** three neume annotations are produced, each with a merged bounding box covering its word's characters

#### Scenario: Single-word neume recognition produces one neume annotation
- **WHEN** a neume line recognition result contains text `"punctum"` with character-level cuts
- **THEN** one neume annotation is produced with type `"punctum"` and a bounding box covering all characters

### Requirement: Neume annotation structure
Each neume annotation in the `neumes` array SHALL contain a `type` field (string, the recognized neume text) and a `bbox` field (object with `x`, `y`, `width`, `height` in pixel coordinates). The structure SHALL match `NeumeInput`.

#### Scenario: Neume annotation has correct structure
- **WHEN** a neume annotation is included in the response
- **THEN** it contains `{"type": "<neume_text>", "bbox": {"x": <int>, "y": <int>, "width": <int>, "height": <int>}}`

### Requirement: Apply region coordinate transformation to neumes
When processing a region crop, neume bounding box coordinates SHALL be transformed back to full-image coordinates, the same as syllable bounding boxes.

#### Scenario: Neume bbox coordinates are offset by region origin
- **WHEN** recognition is performed on a cropped region at `(100, 200)` and a neume is detected at `(50, 30)` within the crop
- **THEN** the neume bbox in the response has `x=150, y=230`
