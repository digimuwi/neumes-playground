## ADDED Requirements

### Requirement: Syllables are clustered into text lines by bottom Y position

The system SHALL group syllables into text line clusters based on their bottom Y coordinates (rect.y + rect.height). Syllables whose bottom Y positions differ by less than 3% of the normalized image height (0.03) SHALL be considered part of the same text line.

#### Scenario: Syllables on same horizontal line are clustered together
- **WHEN** three syllables have bottom Y positions of 0.25, 0.26, and 0.255
- **THEN** all three syllables SHALL be grouped into a single text line cluster

#### Scenario: Syllables on different lines are separated
- **WHEN** two syllables have bottom Y positions of 0.25 and 0.35
- **THEN** the syllables SHALL be grouped into two separate text line clusters

### Requirement: Each text line is modeled as a linear equation

The system SHALL fit a linear regression model (y = mx + b) to each text line cluster using syllable center X positions and bottom Y positions as data points. This models tilted/drifting handwritten text lines.

#### Scenario: Multi-syllable line gets fitted slope
- **WHEN** a text line cluster contains syllables at (centerX: 0.1, bottomY: 0.25) and (centerX: 0.5, bottomY: 0.27)
- **THEN** the system SHALL compute a linear model with positive slope representing the downward drift

#### Scenario: Single-syllable line inherits slope from nearest multi-syllable line
- **WHEN** a text line cluster contains only one syllable
- **THEN** the system SHALL inherit the slope (m) from the nearest text line that has multiple syllables
- **AND** compute the intercept (b) such that the line passes through that syllable's bottom position

### Requirement: Text lines define vertical bands for neume ownership

The system SHALL define vertical bands based on text line equations. A neume at position (nx, ny) belongs to the first text line (sorted top-to-bottom by intercept) where the line's Y value at nx is greater than or equal to ny.

#### Scenario: Neume above first text line belongs to first line
- **WHEN** a neume is positioned above all text lines
- **THEN** the neume SHALL belong to the topmost text line

#### Scenario: Neume below all text lines belongs to last line
- **WHEN** a neume is positioned below all text lines
- **THEN** the neume SHALL belong to the bottommost text line

#### Scenario: Neume between two lines belongs to the line below it
- **WHEN** a neume's Y position is between two text line equations evaluated at the neume's X
- **THEN** the neume SHALL belong to the lower of the two text lines
