## MODIFIED Requirements

### Requirement: Annotation input structure

The annotations JSON SHALL have the following structure:
- `lines`: array of line objects, each containing:
  - `boundary`: array of `[x, y]` coordinate pairs defining the line's boundary polygon
  - `syllables`: array of syllable objects
- Each syllable: `{ "text": string, "boundary": [[x, y], [x, y], ...] }` where `boundary` is an array of `[x, y]` coordinate pairs defining the syllable's polygon boundary
- `neumes`: array of neume objects
- Each neume: `{ "type": string, "bbox": { "x": int, "y": int, "width": int, "height": int } }`

Neume type strings SHALL be accepted as-is with no validation against a fixed class list.

All coordinates SHALL be in pixels relative to the image dimensions.

#### Scenario: Valid annotation structure with polygon boundaries
- **WHEN** annotations JSON contains lines with boundary polygons and syllables with boundary polygons, and neumes with type and bbox
- **THEN** system accepts the contribution and stores both text lines and neumes

#### Scenario: Empty text allowed
- **WHEN** a syllable has empty string for text
- **THEN** system accepts it and stores the empty text in `annotations.json`

#### Scenario: Any neume type accepted
- **WHEN** annotations contain neumes with arbitrary type strings (e.g., `"punctum"`, `"custom-new-type"`)
- **THEN** system accepts and stores them without validation

### Requirement: Store contributions persistently

The system SHALL store each contribution in a directory structure:
- `contributions/<uuid>/image.{ext}` — the uploaded image
- `contributions/<uuid>/annotations.json` — annotation data with image metadata

The `annotations.json` file SHALL contain:
- `image` object with `filename` (string), `width` (int), and `height` (int)
- `lines` array where each line has a `boundary` polygon and `syllables` array with polygon-based syllables
- `neumes` array matching the submitted annotation neumes

Annotation data SHALL be stored exactly as submitted — no transformation.

Saving a contribution SHALL NOT trigger any training process.

#### Scenario: Directory creation
- **WHEN** a valid contribution is received
- **THEN** system creates `contributions/<uuid>/` directory with `image.{ext}` and `annotations.json`

#### Scenario: Annotations stored verbatim
- **WHEN** contribution contains syllables with trailing hyphens (e.g., `"Be-"`, `"NE-"`) and polygon boundaries
- **THEN** `annotations.json` stores the text and polygon coordinates exactly as submitted

#### Scenario: No training triggered on save
- **WHEN** a contribution is saved successfully
- **THEN** no background training process is spawned
