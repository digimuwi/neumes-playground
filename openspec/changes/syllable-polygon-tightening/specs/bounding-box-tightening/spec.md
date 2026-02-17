## MODIFIED Requirements

### Requirement: Drawn rectangles are automatically tightened

The system SHALL automatically tighten every user-drawn rectangle to fit the foreground (ink) content before creating the annotation. For **syllable** annotations, the system SHALL produce a contour polygon via column-scan tightening. For **neume** annotations, the system SHALL produce a tight axis-aligned rectangle converted to a 4-point polygon. Foreground pixels are defined as pixels with intensity in the range [marginThreshold, otsuThreshold).

#### Scenario: Syllable rectangle produces contour polygon
- **WHEN** user draws a rectangle around syllable content
- **THEN** the resulting annotation stores a multi-point contour polygon that hugs the ink

#### Scenario: Neume rectangle produces tight rectangular polygon
- **WHEN** user draws a rectangle around neume content
- **THEN** the resulting annotation stores a 4-point rectangular polygon from axis-aligned tightening

#### Scenario: Rectangle contains ink content
- **WHEN** user draws a rectangle around manuscript content
- **THEN** the resulting annotation polygon is tightened to fit the foreground pixels

#### Scenario: Rectangle overlapping margin excludes margin
- **WHEN** user draws a rectangle that includes both ink content and black margin area
- **THEN** the annotation tightens to the ink only, excluding the margin pixels
