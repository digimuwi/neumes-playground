## MODIFIED Requirements

### Requirement: Accept contribution via POST endpoint

The system SHALL provide a `POST /contribute` endpoint that accepts:
- An image file (JPEG or PNG)
- A JSON string containing annotation data with lines (grouped syllables) and neumes

The endpoint SHALL return HTTP 201 with a JSON response containing the contribution ID on success.

Neumes in the annotations input SHALL be silently ignored — they are accepted for API compatibility but not stored. Only text lines are persisted as PAGE XML.

#### Scenario: Successful contribution with syllables and neumes
- **WHEN** client sends POST to `/contribute` with valid image and annotations JSON containing lines with syllables and neumes array
- **THEN** system returns HTTP 201 with `{"id": "<uuid>", "message": "Contribution saved successfully"}`
- **AND** generated PAGE XML contains only text-type TextLines (neumes are ignored)

#### Scenario: Contribution with only syllables
- **WHEN** client sends POST to `/contribute` with valid image and annotations containing lines but empty neumes array
- **THEN** system returns HTTP 201 and generates PAGE XML with single content region containing only text-type TextLines

#### Scenario: Contribution with only neumes
- **WHEN** client sends POST to `/contribute` with valid image and annotations containing empty lines array but populated neumes
- **THEN** system returns HTTP 201 with success response
- **AND** generated PAGE XML contains an empty Page element (no TextRegion) since neumes are silently ignored and no text lines exist

#### Scenario: Missing image
- **WHEN** client sends POST to `/contribute` without an image file
- **THEN** system returns HTTP 422 with validation error

#### Scenario: Invalid annotations JSON
- **WHEN** client sends POST to `/contribute` with malformed JSON in annotations field
- **THEN** system returns HTTP 422 with validation error

### Requirement: Generate PAGE XML compatible with Kraken

The system SHALL generate PAGE XML files conforming to the PAGE 2019-07-15 schema.

The generated XML SHALL include:
- `PcGts` root element with PAGE namespace
- `Metadata` with Creator and Created timestamp
- `Page` element with imageFilename, imageWidth, and imageHeight
- Single `TextRegion` element with Coords containing text content (when text lines exist)
- `TextLine` elements with Coords, Baseline, `custom` attribute with type `text`, and TextEquiv

All TextLines SHALL have `custom="structure {type:text;}"`. There are no neume-type TextLines.

#### Scenario: Syllables grouped into TextLines with type attribute
- **WHEN** contribution contains lines with multiple syllables each
- **THEN** PAGE XML contains one `TextLine` per line with `custom="structure {type:text;}"`, with `Word` elements for each syllable containing the syllable's Coords and TextEquiv

#### Scenario: Syllable text without trailing hyphens
- **WHEN** contribution contains syllables with trailing hyphens (e.g., `CI-`, `NE-`)
- **THEN** PAGE XML Word elements contain text with trailing hyphens stripped (e.g., `CI`, `NE`)

#### Scenario: Baseline generation
- **WHEN** a TextLine is generated from a bounding box
- **THEN** the Baseline points attribute contains a horizontal line at approximately 85% of the bbox height

#### Scenario: Coords as polygon points
- **WHEN** a bbox is converted to PAGE XML Coords
- **THEN** the points attribute contains four space-separated x,y pairs representing the rectangle corners (clockwise from top-left)

### Requirement: Store contributions persistently

The system SHALL store each contribution in a directory structure: `contributions/<uuid>/image.{ext}` and `contributions/<uuid>/page.xml`.

The PAGE XML's `Page@imageFilename` attribute SHALL reference the image filename (e.g., `image.jpg`).

Saving a contribution SHALL NOT trigger any training process.

#### Scenario: Directory creation
- **WHEN** a valid contribution is received
- **THEN** system creates `contributions/<uuid>/` directory with image file and page.xml

#### Scenario: Image format preservation
- **WHEN** contribution includes a JPEG image
- **THEN** system stores it as `image.jpg` and references `image.jpg` in PAGE XML

#### Scenario: PNG image handling
- **WHEN** contribution includes a PNG image
- **THEN** system stores it as `image.png` and references `image.png` in PAGE XML

#### Scenario: No training triggered on save
- **WHEN** a contribution is saved successfully
- **THEN** no background training process is spawned and no contribution counter is incremented

### Requirement: Annotation input structure

The annotations JSON SHALL have the following structure:
- `lines`: array of line objects, each containing `syllables` array
- Each syllable: `{ "text": string, "bbox": { "x": int, "y": int, "width": int, "height": int } }`
- `neumes`: array of neume objects (accepted but ignored)
- Each neume: `{ "type": string, "bbox": { "x": int, "y": int, "width": int, "height": int } }`

All coordinates SHALL be in pixels relative to the image dimensions.

#### Scenario: Valid annotation structure
- **WHEN** annotations JSON contains lines array with syllables having text and bbox, and neumes array with type and bbox
- **THEN** system accepts the contribution and processes only the text lines

#### Scenario: Empty text allowed
- **WHEN** a syllable has empty string for text
- **THEN** system accepts it and includes empty TextEquiv in PAGE XML

## REMOVED Requirements

### Requirement: Neumes grouped into TextLines with Word children
**Reason**: Neume detection is moving from Kraken OCR to YOLOv8 object detection. Neume-type TextLines in PAGE XML are no longer generated. Neume storage will be redesigned in Change 6.
**Migration**: Neumes in contribution input are silently accepted but not stored. Change 6 will introduce JSON-based neume storage.

### Requirement: Neume band grouping by vertical overlap
**Reason**: The neume band grouping logic existed to create neume-type TextLines for Kraken training. With Kraken neume training removed, this grouping has no purpose.
**Migration**: No migration needed — this was an internal implementation detail with no external consumers.

### Requirement: Single content region containing neume TextLines
**Reason**: Content region no longer contains neume-type TextLines. It contains only text-type TextLines when text lines exist, or is absent when no text lines exist.
**Migration**: Frontend does not depend on neume TextLines in PAGE XML.
