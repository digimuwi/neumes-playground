## ADDED Requirements

### Requirement: Each neume is assigned to exactly one syllable

The system SHALL assign every neume annotation to exactly one syllable annotation. If no syllables exist, neumes SHALL have no assignment.

#### Scenario: Neume with available syllables gets assigned
- **WHEN** at least one syllable and one neume exist
- **THEN** each neume SHALL be assigned to exactly one syllable

#### Scenario: Neume with no syllables has no assignment
- **WHEN** neumes exist but no syllables exist
- **THEN** neumes SHALL have no syllable assignment

### Requirement: Neumes are assigned to the closest syllable to the left within the same text line

Within a neume's owning text line, the system SHALL assign the neume to the syllable whose polygon left edge (minimum X of polygon vertices) is closest to and less than or equal to the neume's anchor X coordinate. The neume's anchor point SHALL be derived from its polygon: X = minimum X of polygon vertices, Y = maximum Y of polygon vertices (lower-left corner equivalent).

#### Scenario: Neume directly above syllable is assigned to it
- **WHEN** a neume with polygon minX at 0.3 is in the same text line band as syllables with polygon minX at 0.1, 0.3, and 0.5
- **THEN** the neume SHALL be assigned to the syllable with polygon minX at 0.3

#### Scenario: Neume between two syllables is assigned to the left one
- **WHEN** a neume with polygon minX at 0.35 is in the same text line band as syllables with polygon minX at 0.2 and 0.5
- **THEN** the neume SHALL be assigned to the syllable with polygon minX at 0.2

#### Scenario: Neume left of all syllables gets leftmost
- **WHEN** a neume with polygon minX at 0.05 is in the same text line band as syllables with polygon minX at 0.15, 0.3, and 0.5
- **THEN** the neume SHALL be assigned to the syllable with polygon minX at 0.15

### Requirement: Assignment curve endpoints use closest point on polygon

The system SHALL compute assignment curve endpoints by finding the closest point on the syllable polygon's edges to the neume's anchor point, instead of clamping to a rectangular boundary.

#### Scenario: Curve endpoint on polygon edge
- **WHEN** drawing an assignment curve from a neume anchor to its assigned syllable
- **THEN** the syllable endpoint SHALL be the closest point on the syllable polygon's edge segments to the neume anchor point

### Requirement: Assignments are recomputed on every annotation change

The system SHALL recalculate all neume-to-syllable assignments whenever any annotation is added, updated, or deleted. Assignments are derived from geometry and not stored in state.

#### Scenario: Adding a syllable updates assignments
- **WHEN** a new syllable is added between existing neumes
- **THEN** neume assignments SHALL be recalculated to reflect the new syllable

#### Scenario: Moving a neume updates its assignment
- **WHEN** a neume's position is changed
- **THEN** that neume's assignment SHALL be recalculated based on its new position

#### Scenario: Deleting a syllable updates assignments
- **WHEN** a syllable is deleted
- **THEN** neumes previously assigned to it SHALL be reassigned to remaining syllables
