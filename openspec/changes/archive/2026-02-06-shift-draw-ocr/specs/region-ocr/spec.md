## ADDED Requirements

### Requirement: Shift+draw triggers OCR recognition
When the user holds Shift while drawing a rectangle, the system SHALL send the marked region to the HTR backend for syllable recognition instead of creating a single annotation.

#### Scenario: Successful OCR with multiple syllables
- **WHEN** user holds Shift and draws a rectangle over text containing multiple syllables
- **THEN** system calls backend `/recognize` endpoint with the image and region
- **THEN** system creates one syllable annotation for each detected syllable
- **THEN** each annotation has pre-filled text from OCR result
- **THEN** all annotations are added to state in a single history entry

#### Scenario: Normal draw without Shift
- **WHEN** user draws a rectangle without holding Shift
- **THEN** system creates a single annotation as before (no OCR call)

### Requirement: OCR region uses pixel coordinates
The system SHALL convert normalized rectangle coordinates to pixel coordinates when calling the backend, and convert returned pixel bounding boxes back to normalized coordinates for storage.

#### Scenario: Coordinate transformation round-trip
- **WHEN** user draws a region at normalized coords (0.1, 0.2, 0.3, 0.4) on a 1000x800 image
- **THEN** backend receives pixel region {x: 100, y: 160, width: 300, height: 320}
- **THEN** returned syllable bboxes are converted back to normalized coords for annotation storage

### Requirement: OCR handles empty results gracefully
The system SHALL handle the case where OCR detects no syllables without creating any annotations.

#### Scenario: No syllables detected
- **WHEN** user Shift+draws over a region with no recognizable text
- **THEN** system does not create any annotations
- **THEN** system does not add an entry to undo history

### Requirement: OCR handles backend errors gracefully
The system SHALL handle backend communication errors without breaking the application.

#### Scenario: Backend unavailable
- **WHEN** user Shift+draws but backend is unreachable
- **THEN** system shows an error message to the user
- **THEN** application remains functional for manual annotation

### Requirement: Batch annotations support single undo
All annotations created from a single OCR operation SHALL be undoable with a single undo action.

#### Scenario: Undo OCR result
- **WHEN** OCR creates 5 syllable annotations
- **THEN** user presses Ctrl+Z once
- **THEN** all 5 annotations are removed together
