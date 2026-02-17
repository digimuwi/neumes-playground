## ADDED Requirements

### Requirement: System computes threshold on image load

The system SHALL compute an Otsu threshold from the full image when an image is loaded. This threshold MUST be cached and reused for all subsequent tightening operations on that image.

#### Scenario: Image loaded successfully
- **WHEN** user uploads or loads a manuscript image
- **THEN** the system computes a global Otsu threshold from the image pixel data

#### Scenario: New image replaces existing
- **WHEN** user loads a new image while one is already displayed
- **THEN** the system computes a new threshold for the new image

### Requirement: Drawn rectangles are automatically tightened

The system SHALL automatically tighten every user-drawn rectangle to fit the foreground (ink) content before creating the annotation. The tightened rectangle MUST never be larger than the original in any dimension.

#### Scenario: Rectangle contains ink content
- **WHEN** user draws a rectangle around manuscript content
- **THEN** the resulting annotation rectangle is shrunk to the bounding box of foreground pixels

#### Scenario: Rectangle tightens in all directions
- **WHEN** user draws a rectangle with excess space on all sides of the content
- **THEN** the rectangle shrinks from left, right, top, and bottom to fit the ink

### Requirement: Original rectangle preserved when no content detected

The system SHALL preserve the original user-drawn rectangle if binarization detects no foreground pixels within the selection.

#### Scenario: Empty region selected
- **WHEN** user draws a rectangle over an area with no ink (only parchment background)
- **THEN** the annotation is created with the original rectangle dimensions unchanged

### Requirement: Small content is preserved

The system SHALL NOT filter or ignore small foreground regions. All detected foreground pixels MUST be included in the tightened bounding box.

#### Scenario: Small punctum selected
- **WHEN** user draws a rectangle around a small punctum neume
- **THEN** the rectangle tightens to fit the punctum exactly, without discarding it as noise

### Requirement: Tightening uses normalized coordinates

The system SHALL perform tightening calculations and return results in normalized coordinates (0-1 relative to image dimensions), consistent with the existing annotation coordinate system.

#### Scenario: Coordinates remain normalized
- **WHEN** a rectangle is tightened
- **THEN** the resulting rectangle uses normalized coordinates matching the existing annotation format
