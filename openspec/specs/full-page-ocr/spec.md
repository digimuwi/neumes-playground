# full-page-ocr

## Requirements

### Requirement: Full-page OCR button in AppBar
The AppBar SHALL display a "Recognize Page" button with a DocumentScanner icon that triggers full-page text recognition. The button SHALL be disabled when no image is loaded.

#### Scenario: Button visible and enabled with image loaded
- **WHEN** user has loaded a manuscript image
- **THEN** the "Recognize Page" button is visible and enabled in the AppBar

#### Scenario: Button disabled without image
- **WHEN** no image is loaded
- **THEN** the "Recognize Page" button is visible but disabled

#### Scenario: Clicking button triggers OCR
- **WHEN** user clicks the "Recognize Page" button with an image loaded and no existing annotations
- **THEN** system shows loading dialog and runs full-page OCR

### Requirement: Upload OCR prompt
The system SHALL display a modal dialog after every image upload asking if the user wants to run text recognition. The dialog SHALL have "Yes, recognize" and "No" options.

#### Scenario: Prompt appears after upload
- **WHEN** user uploads a new manuscript image
- **THEN** a modal dialog appears asking "Would you like to run text recognition on this manuscript?"

#### Scenario: User accepts OCR prompt
- **WHEN** user clicks "Yes, recognize" in the upload prompt
- **THEN** system shows loading dialog and runs full-page OCR

#### Scenario: User declines OCR prompt
- **WHEN** user clicks "No" in the upload prompt
- **THEN** dialog closes and image is displayed without running OCR

### Requirement: Existing annotations handling
When triggering full-page OCR with existing annotations on the canvas, the system SHALL prompt the user to choose whether to keep existing annotations and add new ones, or replace all annotations.

#### Scenario: Prompt when annotations exist
- **WHEN** user clicks "Recognize Page" with existing annotations on canvas
- **THEN** a dialog appears with options "Keep & Add", "Replace", and "Cancel"

#### Scenario: Keep and add annotations
- **WHEN** user selects "Keep & Add" in the existing annotations prompt
- **THEN** system runs OCR and adds new syllable annotations alongside existing ones

#### Scenario: Replace annotations
- **WHEN** user selects "Replace" in the existing annotations prompt
- **THEN** system clears all existing annotations, then runs OCR and adds new syllable annotations

#### Scenario: Cancel OCR
- **WHEN** user selects "Cancel" in the existing annotations prompt
- **THEN** dialog closes and no OCR is performed

### Requirement: OCR loading dialog
The system SHALL display a blocking modal dialog during all OCR operations (both full-page and region-based). The dialog SHALL show a spinner, "Recognizing text..." message, and a note that this may take a minute for large manuscripts.

#### Scenario: Loading dialog during full-page OCR
- **WHEN** full-page OCR is in progress
- **THEN** a modal loading dialog is displayed with spinner and progress message
- **AND** user cannot interact with the canvas

#### Scenario: Loading dialog during region OCR
- **WHEN** user completes a shift+drag rectangle selection
- **THEN** a modal loading dialog is displayed during the OCR operation

#### Scenario: Loading dialog closes on completion
- **WHEN** OCR completes successfully
- **THEN** loading dialog closes and annotations appear on canvas

### Requirement: OCR error handling
The system SHALL display a snackbar notification when OCR fails due to backend errors or network issues. The loading dialog SHALL close on error.

#### Scenario: Backend error
- **WHEN** OCR request fails due to backend error
- **THEN** loading dialog closes
- **AND** snackbar notification displays error message

#### Scenario: Network error
- **WHEN** OCR request fails due to network connectivity
- **THEN** loading dialog closes
- **AND** snackbar notification displays error message
