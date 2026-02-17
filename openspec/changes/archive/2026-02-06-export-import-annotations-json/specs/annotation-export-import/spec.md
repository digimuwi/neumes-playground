## ADDED Requirements

### Requirement: Export annotations as JSON
The system SHALL allow the user to export all current annotations, the loaded image, and document metadata as a single downloadable JSON file.

The exported JSON SHALL contain:
- `imageDataUrl`: the full base64 data URL of the loaded image
- `annotations`: the complete `Annotation[]` array with all properties (id, type, rect, text, neumeType)
- `metadata`: the `DocumentMetadata` object (cantusId, genre) if present

The export SHALL preserve normalized coordinates (0-1) exactly as stored in application state.

#### Scenario: Export with annotations and image loaded
- **WHEN** the user has an image loaded and one or more annotations exist
- **THEN** the system downloads a `.json` file containing the image data URL, all annotations, and metadata

#### Scenario: Export with no annotations
- **WHEN** the user has an image loaded but no annotations exist
- **THEN** the system downloads a `.json` file containing the image data URL, an empty annotations array, and metadata

#### Scenario: Export button disabled when no image
- **WHEN** no image is loaded
- **THEN** the export JSON button SHALL be disabled

### Requirement: Import annotations from JSON
The system SHALL allow the user to select a previously exported JSON file and restore the annotations, image, and metadata into application state.

On successful import, the system SHALL:
- Set the image from the `imageDataUrl` field
- Replace all annotations with the `annotations` array
- Restore `metadata` if present in the file

#### Scenario: Import into empty state
- **WHEN** no image or annotations are loaded and the user selects a valid JSON file
- **THEN** the system loads the image, annotations, and metadata from the file

#### Scenario: Import with existing annotations triggers confirmation
- **WHEN** annotations already exist and the user selects a valid JSON file
- **THEN** the system SHALL prompt the user to confirm before replacing existing annotations

#### Scenario: User confirms import replacement
- **WHEN** the user confirms the replacement prompt
- **THEN** the system replaces the current image, annotations, and metadata with the imported data

#### Scenario: User cancels import replacement
- **WHEN** the user cancels the replacement prompt
- **THEN** the system makes no changes to the current state

#### Scenario: Invalid JSON file
- **WHEN** the user selects a file that is not valid JSON or does not contain the expected structure
- **THEN** the system SHALL display an error message and make no changes to state

### Requirement: Import and export controls in toolbar
The system SHALL provide toolbar controls for both JSON export and JSON import, grouped with existing import/export controls.

#### Scenario: Toolbar displays export and import buttons
- **WHEN** the toolbar is rendered
- **THEN** an export JSON button and an import JSON button SHALL be visible alongside the existing MEI export button
