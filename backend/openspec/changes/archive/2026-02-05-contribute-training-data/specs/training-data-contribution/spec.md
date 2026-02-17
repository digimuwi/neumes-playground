## ADDED Requirements

### Requirement: Accept contribution via POST endpoint

The system SHALL provide a `POST /contribute` endpoint that accepts:
- An image file (JPEG or PNG)
- A JSON string containing annotation data with lines (grouped syllables) and neumes

The endpoint SHALL return HTTP 201 with a JSON response containing the contribution ID on success.

#### Scenario: Successful contribution with syllables and neumes
- **WHEN** client sends POST to `/contribute` with valid image and annotations JSON containing lines with syllables and neumes array
- **THEN** system returns HTTP 201 with `{"id": "<uuid>", "message": "Contribution saved successfully"}`

#### Scenario: Contribution with only syllables
- **WHEN** client sends POST to `/contribute` with valid image and annotations containing lines but empty neumes array
- **THEN** system returns HTTP 201 and generates PAGE XML with only text TextRegion

#### Scenario: Contribution with only neumes
- **WHEN** client sends POST to `/contribute` with valid image and annotations containing empty lines array but populated neumes
- **THEN** system returns HTTP 201 and generates PAGE XML with only neume TextRegion

#### Scenario: Missing image
- **WHEN** client sends POST to `/contribute` without an image file
- **THEN** system returns HTTP 422 with validation error

#### Scenario: Invalid annotations JSON
- **WHEN** client sends POST to `/contribute` with malformed JSON in annotations field
- **THEN** system returns HTTP 422 with validation error

### Requirement: Generate PAGE XML compatible with Kraken

The system SHALL generate PAGE XML files conforming to the PAGE 2019-07-15 schema that can be used with Kraken's `ketos train` and `ketos segtrain` commands.

The generated XML SHALL include:
- `PcGts` root element with PAGE namespace
- `Metadata` with Creator and Created timestamp
- `Page` element with imageFilename, imageWidth, and imageHeight
- `TextRegion` elements with Coords
- `TextLine` elements with Coords, Baseline, and TextEquiv

#### Scenario: Syllables grouped into TextLines
- **WHEN** contribution contains lines with multiple syllables each
- **THEN** PAGE XML contains one `TextLine` per line, with `Word` elements for each syllable containing the syllable's Coords and TextEquiv

#### Scenario: Neumes as individual TextLines
- **WHEN** contribution contains neumes
- **THEN** PAGE XML contains a `TextRegion type="music-notation"` with each neume as a separate `TextLine`, where the neume type name is the TextEquiv content

#### Scenario: Baseline generation
- **WHEN** a TextLine is generated from a bounding box
- **THEN** the Baseline points attribute contains a horizontal line at approximately 85% of the bbox height

#### Scenario: Coords as polygon points
- **WHEN** a bbox is converted to PAGE XML Coords
- **THEN** the points attribute contains four space-separated x,y pairs representing the rectangle corners (clockwise from top-left)

### Requirement: Store contributions persistently

The system SHALL store each contribution in a directory structure: `contributions/<uuid>/image.{ext}` and `contributions/<uuid>/page.xml`.

The PAGE XML's `Page@imageFilename` attribute SHALL reference the image filename (e.g., `image.jpg`).

#### Scenario: Directory creation
- **WHEN** a valid contribution is received
- **THEN** system creates `contributions/<uuid>/` directory with image file and page.xml

#### Scenario: Image format preservation
- **WHEN** contribution includes a JPEG image
- **THEN** system stores it as `image.jpg` and references `image.jpg` in PAGE XML

#### Scenario: PNG image handling
- **WHEN** contribution includes a PNG image
- **THEN** system stores it as `image.png` and references `image.png` in PAGE XML

### Requirement: Annotation input structure

The annotations JSON SHALL have the following structure:
- `lines`: array of line objects, each containing `syllables` array
- Each syllable: `{ "text": string, "bbox": { "x": int, "y": int, "width": int, "height": int } }`
- `neumes`: array of neume objects
- Each neume: `{ "type": string, "bbox": { "x": int, "y": int, "width": int, "height": int } }`

All coordinates SHALL be in pixels relative to the image dimensions.

#### Scenario: Valid annotation structure
- **WHEN** annotations JSON contains lines array with syllables having text and bbox, and neumes array with type and bbox
- **THEN** system accepts the contribution and processes it

#### Scenario: Empty text allowed
- **WHEN** a syllable has empty string for text
- **THEN** system accepts it and includes empty TextEquiv in PAGE XML
