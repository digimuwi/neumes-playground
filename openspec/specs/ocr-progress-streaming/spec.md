## ADDED Requirements

### Requirement: Display OCR processing stage
The OcrDialog SHALL display stage-specific messages reflecting the current backend processing stage.

#### Scenario: Loading stage displayed
- **WHEN** the backend emits a `loading` stage event
- **THEN** the dialog displays "Loading model..."

#### Scenario: Segmenting stage displayed
- **WHEN** the backend emits a `segmenting` stage event
- **THEN** the dialog displays "Detecting text regions..."

#### Scenario: Recognizing stage displayed
- **WHEN** the backend emits a `recognizing` stage event
- **THEN** the dialog displays "Recognizing text..."

#### Scenario: Syllabifying stage displayed
- **WHEN** the backend emits a `syllabifying` stage event
- **THEN** the dialog displays "Processing syllables..."

### Requirement: Display per-line progress during recognition
During the recognition stage, the dialog SHALL display a determinate progress indicator showing line-by-line progress.

#### Scenario: Progress bar shows current line
- **WHEN** the backend emits `{ stage: "recognizing", current: 2, total: 5 }`
- **THEN** the dialog displays "Line 2 of 5" with a progress bar at 40%

#### Scenario: Progress updates as lines complete
- **WHEN** recognition progresses from line 1 to line 4 of 4 lines
- **THEN** the progress bar updates from 25% to 100%

### Requirement: Use indeterminate spinner for non-recognition stages
For stages without line-level progress (loading, segmenting, syllabifying), the dialog SHALL display an indeterminate spinner.

#### Scenario: Loading shows spinner
- **WHEN** the stage is `loading`
- **THEN** the dialog displays an indeterminate spinner (not a progress bar)

#### Scenario: Segmenting shows spinner
- **WHEN** the stage is `segmenting`
- **THEN** the dialog displays an indeterminate spinner

#### Scenario: Syllabifying shows spinner
- **WHEN** the stage is `syllabifying`
- **THEN** the dialog displays an indeterminate spinner

### Requirement: Consume SSE stream from backend
The htrService SHALL parse Server-Sent Events from the `/recognize` endpoint and invoke progress callbacks for each stage event.

#### Scenario: Progress callback invoked for each stage
- **WHEN** the backend streams events: loading → segmenting → recognizing (×N) → syllabifying → complete
- **THEN** the onProgress callback is invoked for each event in sequence

#### Scenario: Final result extracted from complete event
- **WHEN** the backend emits `{ stage: "complete", result: {...} }`
- **THEN** the recognize function returns the syllable annotations from the result

### Requirement: Handle stream errors gracefully
If the backend emits an error event, the system SHALL display the error message and allow the user to dismiss the dialog.

#### Scenario: Backend error displayed
- **WHEN** the backend emits `{ stage: "error", message: "Model failed to load" }`
- **THEN** the dialog displays the error message
- **THEN** the user can close the dialog

#### Scenario: Network error handled
- **WHEN** the SSE connection fails mid-stream
- **THEN** the system displays a generic error message
- **THEN** the application remains functional

### Requirement: Shared SSE logic for region and page recognition
Both `recognizeRegion` and `recognizePage` functions SHALL use a shared SSE parsing implementation.

#### Scenario: Region recognition uses SSE
- **WHEN** user Shift+draws a region to trigger OCR
- **THEN** the same SSE progress events are streamed and displayed

#### Scenario: Page recognition uses SSE
- **WHEN** user triggers full-page OCR
- **THEN** the same SSE progress events are streamed and displayed
