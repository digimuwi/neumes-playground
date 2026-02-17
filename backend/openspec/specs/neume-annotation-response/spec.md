### Requirement: Return neume annotations separately from syllables

The `/recognize` endpoint SHALL return a `neumes` array in the recognition response. Each neume entry SHALL include `type` (string neume class name), `bbox` (BBox in full-image pixel coordinates), and `confidence` (float between 0 and 1). When no YOLO model is available, the `neumes` array SHALL be empty.

The response structure SHALL use a nested format where syllables are grouped under their parent lines. Each line SHALL include its `boundary` polygon (from Kraken segmentation), `baseline` (from Kraken segmentation), `text` (recognized text), and a `syllables` array. Each syllable SHALL include `text`, `boundary` polygon (sliced from the parent line polygon), and `confidence`.

The response shape SHALL be: `{ lines: [...], neumes: [...] }`.

#### Scenario: Recognition response with nested syllable polygons
- **WHEN** the recognition pipeline processes an image
- **THEN** the response `result` contains a `lines` array where each line has `text` (string), `boundary` (polygon coordinate array), `baseline` (coordinate array), and `syllables` array where each syllable has `text` (string), `boundary` (polygon coordinate array), and `confidence` (float)
- **AND** the response `result` contains a `neumes` array

#### Scenario: Syllable boundary polygons follow line contour
- **WHEN** a line has a curved or slanted boundary polygon and multiple syllables
- **THEN** each syllable's boundary polygon follows the line's contour within its horizontal extent

#### Scenario: Recognition response contains empty neumes when no model exists
- **WHEN** the recognition pipeline processes any image and no YOLO model is available
- **THEN** the response `result` contains a `neumes` array that is an empty list `[]`

#### Scenario: Neume bboxes are in full-image coordinates when region crop is used
- **WHEN** a region crop is specified and neumes are detected
- **THEN** neume bboxes are offset by the region origin to produce full-image coordinates

#### Scenario: Line and syllable polygons are in full-image coordinates when region crop is used
- **WHEN** a region crop is specified
- **THEN** line boundary polygons and syllable boundary polygons are offset by the region origin to produce full-image coordinates
