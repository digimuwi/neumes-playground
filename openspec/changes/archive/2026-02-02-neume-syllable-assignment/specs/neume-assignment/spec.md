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

Within a neume's owning text line, the system SHALL assign the neume to the syllable whose center X is closest to and less than or equal to the neume's center X.

#### Scenario: Neume directly above syllable is assigned to it
- **WHEN** a neume at centerX 0.3 is in the same text line band as syllables at centerX 0.1, 0.3, and 0.5
- **THEN** the neume SHALL be assigned to the syllable at centerX 0.3

#### Scenario: Neume between two syllables is assigned to the left one
- **WHEN** a neume at centerX 0.35 is in the same text line band as syllables at centerX 0.2 and 0.5
- **THEN** the neume SHALL be assigned to the syllable at centerX 0.2

### Requirement: Neume left of all syllables is assigned to the leftmost syllable

As an exception to the "closest left" rule, when a neume's center X is less than all syllables' center X positions in its text line, the system SHALL assign it to the leftmost syllable.

#### Scenario: Neume to the left of all syllables gets leftmost
- **WHEN** a neume at centerX 0.05 is in the same text line band as syllables at centerX 0.15, 0.3, and 0.5
- **THEN** the neume SHALL be assigned to the syllable at centerX 0.15

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
