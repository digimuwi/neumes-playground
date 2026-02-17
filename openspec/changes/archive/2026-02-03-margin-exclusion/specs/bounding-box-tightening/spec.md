## ADDED Requirements

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

## MODIFIED Requirements

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
