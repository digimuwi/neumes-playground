## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Original rectangle preserved when no content detected

The system SHALL preserve the original user-drawn rectangle if binarization detects no foreground pixels within the selection, OR if the detected foreground is smaller than the minimum size threshold (4×4 pixels).

#### Scenario: Empty region selected
- **WHEN** user draws a rectangle over an area with no ink (only parchment background)
- **THEN** the annotation is created with the original rectangle dimensions unchanged

#### Scenario: Noise-only region selected
- **WHEN** user draws a rectangle and the only detected foreground is smaller than 4×4 pixels
- **THEN** the annotation is created with the original rectangle dimensions unchanged
