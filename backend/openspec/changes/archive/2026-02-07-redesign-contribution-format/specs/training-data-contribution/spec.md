## MODIFIED Requirements

### Requirement: Accept contribution via POST endpoint

The system SHALL provide a `POST /contribute` endpoint that accepts:
- An image file (JPEG or PNG)
- A JSON string containing annotation data with lines (grouped syllables) and neumes

The endpoint SHALL return HTTP 201 with a JSON response containing the contribution ID on success.

The system SHALL store both text line annotations and neume annotations. Neumes are no longer discarded.

#### Scenario: Successful contribution with syllables and neumes
- **WHEN** client sends POST to `/contribute` with valid image and annotations JSON containing lines with syllables and neumes array
- **THEN** system returns HTTP 201 with `{"id": "<uuid>", "message": "Contribution saved successfully"}`
- **AND** stored `annotations.json` contains both the lines and the neumes exactly as submitted

#### Scenario: Contribution with only syllables
- **WHEN** client sends POST to `/contribute` with valid image and annotations containing lines but empty neumes array
- **THEN** system returns HTTP 201 and stores `annotations.json` with the lines and an empty neumes array

#### Scenario: Contribution with only neumes
- **WHEN** client sends POST to `/contribute` with valid image and annotations containing empty lines array but populated neumes
- **THEN** system returns HTTP 201 with success response
- **AND** stored `annotations.json` contains the neumes and an empty lines array

#### Scenario: Missing image
- **WHEN** client sends POST to `/contribute` without an image file
- **THEN** system returns HTTP 422 with validation error

#### Scenario: Invalid annotations JSON
- **WHEN** client sends POST to `/contribute` with malformed JSON in annotations field
- **THEN** system returns HTTP 422 with validation error

### Requirement: Store contributions persistently

The system SHALL store each contribution in a directory structure:
- `contributions/<uuid>/image.{ext}` — the uploaded image
- `contributions/<uuid>/annotations.json` — annotation data with image metadata

The `annotations.json` file SHALL contain:
- `image` object with `filename` (string), `width` (int), and `height` (int)
- `lines` array matching the submitted annotation lines
- `neumes` array matching the submitted annotation neumes

Annotation data SHALL be stored exactly as submitted — no transformation (e.g., no hyphen stripping, no coordinate normalization).

Saving a contribution SHALL NOT trigger any training process.

#### Scenario: Directory creation
- **WHEN** a valid contribution is received
- **THEN** system creates `contributions/<uuid>/` directory with `image.{ext}` and `annotations.json`

#### Scenario: Image format preservation
- **WHEN** contribution includes a JPEG image
- **THEN** system stores it as `image.jpg` and `annotations.json` contains `{"image": {"filename": "image.jpg", ...}}`

#### Scenario: PNG image handling
- **WHEN** contribution includes a PNG image
- **THEN** system stores it as `image.png` and `annotations.json` contains `{"image": {"filename": "image.png", ...}}`

#### Scenario: Image metadata in annotations
- **WHEN** a contribution is stored
- **THEN** `annotations.json` contains an `image` object with the correct `filename`, `width`, and `height` of the uploaded image

#### Scenario: No training triggered on save
- **WHEN** a contribution is saved successfully
- **THEN** no background training process is spawned and no contribution counter is incremented

#### Scenario: Annotations stored verbatim
- **WHEN** contribution contains syllables with trailing hyphens (e.g., `"Be-"`, `"NE-"`)
- **THEN** `annotations.json` stores the text exactly as submitted including hyphens

### Requirement: Annotation input structure

The annotations JSON SHALL have the following structure:
- `lines`: array of line objects, each containing `syllables` array
- Each syllable: `{ "text": string, "bbox": { "x": int, "y": int, "width": int, "height": int } }`
- `neumes`: array of neume objects
- Each neume: `{ "type": string, "bbox": { "x": int, "y": int, "width": int, "height": int } }`

Neume type strings SHALL be accepted as-is with no validation against a fixed class list.

All coordinates SHALL be in pixels relative to the image dimensions.

#### Scenario: Valid annotation structure
- **WHEN** annotations JSON contains lines array with syllables having text and bbox, and neumes array with type and bbox
- **THEN** system accepts the contribution and stores both text lines and neumes

#### Scenario: Empty text allowed
- **WHEN** a syllable has empty string for text
- **THEN** system accepts it and stores the empty text in `annotations.json`

#### Scenario: Any neume type accepted
- **WHEN** annotations contain neumes with arbitrary type strings (e.g., `"punctum"`, `"custom-new-type"`)
- **THEN** system accepts and stores them without validation

## REMOVED Requirements

### Requirement: Generate PAGE XML compatible with Kraken

**Reason**: PAGE XML has no downstream consumer. Kraken training infrastructure was removed in Changes 1-2. Neume detection moved to YOLO (Changes 3-5). The YOLO training export (Change 7) reads directly from `annotations.json`.

**Migration**: Contributions are now stored as `annotations.json`. If PAGE XML is ever needed, it can be regenerated from the JSON.
