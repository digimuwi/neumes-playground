### Requirement: System computes threshold on image load

The system SHALL compute an Otsu threshold from the full image when an image is loaded. This threshold MUST be cached and reused for all subsequent tightening operations on that image.

#### Scenario: Image loaded successfully
- **WHEN** user uploads or loads a manuscript image
- **THEN** the system computes a global Otsu threshold from the image pixel data

#### Scenario: New image replaces existing
- **WHEN** user loads a new image while one is already displayed
- **THEN** the system computes a new threshold for the new image

### Requirement: System detects black margins on image load

The system SHALL detect the presence of black margins when an image is loaded by counting pixels with intensity below the margin cutoff (30). If more than 1% of pixels are below this cutoff, margins are considered present.

#### Scenario: Image with black margins
- **WHEN** user loads a manuscript image where more than 1% of pixels have intensity < 30
- **THEN** the system detects margins are present and sets marginThreshold to 30

#### Scenario: Image without margins
- **WHEN** user loads a manuscript image where 1% or fewer pixels have intensity < 30
- **THEN** the system detects no margins and sets marginThreshold to 0

### Requirement: Margin pixels excluded from Otsu computation

The system SHALL exclude pixels with intensity below the margin threshold when computing the Otsu threshold. This ensures the threshold is computed only on parchment and ink pixels.

#### Scenario: Otsu computed on non-margin pixels only
- **WHEN** margins are detected in an image
- **THEN** the Otsu threshold is computed using only pixels with intensity ≥ 30

#### Scenario: Otsu computed on all pixels when no margins
- **WHEN** no margins are detected in an image
- **THEN** the Otsu threshold is computed using all pixels (unchanged behavior)

### Requirement: Drawn rectangles are automatically tightened

The system SHALL automatically tighten every user-drawn rectangle to fit the foreground (ink) content before creating the annotation. The tightened rectangle MUST never be larger than the original in any dimension. Foreground pixels are defined as pixels with intensity in the range [marginThreshold, otsuThreshold).

#### Scenario: Rectangle contains ink content
- **WHEN** user draws a rectangle around manuscript content
- **THEN** the resulting annotation rectangle is shrunk to the bounding box of foreground pixels

#### Scenario: Rectangle tightens in all directions
- **WHEN** user draws a rectangle with excess space on all sides of the content
- **THEN** the rectangle shrinks from left, right, top, and bottom to fit the ink

#### Scenario: Rectangle overlapping margin excludes margin
- **WHEN** user draws a rectangle that includes both ink content and black margin area
- **THEN** the rectangle tightens to the ink only, excluding the margin pixels

### Requirement: Original rectangle preserved when no content detected

The system SHALL preserve the original user-drawn rectangle if binarization detects no foreground pixels within the selection, OR if the detected foreground is smaller than the minimum size threshold (4×4 pixels).

#### Scenario: Empty region selected
- **WHEN** user draws a rectangle over an area with no ink (only parchment background)
- **THEN** the annotation is created with the original rectangle dimensions unchanged

#### Scenario: Noise-only region selected
- **WHEN** user draws a rectangle and the only detected foreground is smaller than 4×4 pixels
- **THEN** the annotation is created with the original rectangle dimensions unchanged

### Requirement: Threshold biased towards ink detection

The system SHALL apply a positive offset to the computed Otsu threshold when determining foreground pixels for tightening. This bias ensures faint ink strokes are more likely to be classified as foreground.

#### Scenario: Faint ink detected with bias
- **WHEN** user draws a rectangle around content with faint ink strokes
- **THEN** the threshold used for tightening includes a positive offset (e.g., +5) from the raw Otsu value

#### Scenario: Bias does not affect stored threshold
- **WHEN** the system applies threshold bias for tightening
- **THEN** the original computed Otsu threshold remains unchanged for other uses

### Requirement: Minimum bounding box size enforced

The system SHALL enforce a minimum size for tightened bounding boxes. If the detected foreground produces a bounding box smaller than 4 pixels in width OR 4 pixels in height, the system MUST return the original user-drawn rectangle instead.

#### Scenario: Tiny detection returns original rect
- **WHEN** tightening detects foreground pixels that span less than 4×4 pixels
- **THEN** the original user-drawn rectangle is preserved unchanged

#### Scenario: Valid small neume is preserved
- **WHEN** tightening detects foreground pixels spanning at least 4×4 pixels
- **THEN** the tightened bounding box is used normally

### Requirement: Tightened boxes include padding

The system SHALL add 1-pixel padding on each side of the tightened bounding box. This padding MUST be clamped so the final rectangle never exceeds the original user-drawn rectangle in any dimension.

#### Scenario: Padding added within bounds
- **WHEN** tightening produces a bounding box with room for padding
- **THEN** the result includes 1 pixel of padding on all sides

#### Scenario: Padding clamped to original rect
- **WHEN** tightening produces a bounding box where padding would exceed the original selection
- **THEN** the padding is clamped to not exceed the original rectangle boundaries

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
