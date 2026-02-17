## MODIFIED Requirements

### Requirement: Neumes are assigned to the closest syllable to the left within the same text line

Within a neume's owning text line, the system SHALL assign the neume to the syllable whose left edge (`rect.x`) is closest to and less than or equal to the neume's lower-left X coordinate (`rect.x`). The neume's lower-left coordinate SHALL be used as the anchor point for assignment: X = `rect.x`, Y = `rect.y + rect.height`.

#### Scenario: Neume directly above syllable is assigned to it
- **WHEN** a neume with lower-left X at 0.3 is in the same text line band as syllables with left edges at 0.1, 0.3, and 0.5
- **THEN** the neume SHALL be assigned to the syllable with left edge at 0.3

#### Scenario: Neume between two syllables is assigned to the left one
- **WHEN** a neume with lower-left X at 0.35 is in the same text line band as syllables with left edges at 0.2 and 0.5
- **THEN** the neume SHALL be assigned to the syllable with left edge at 0.2

#### Scenario: Wide neume whose center would overlap next syllable
- **WHEN** a neume has rect.x = 0.25 and rect.width = 0.15 (center at 0.325) and syllables have left edges at 0.25 and 0.3
- **THEN** the neume SHALL be assigned to the syllable with left edge at 0.25 (based on lower-left X = 0.25, not center X = 0.325)

### Requirement: Neume left of all syllables is assigned to the leftmost syllable

As an exception to the "closest left" rule, when a neume's lower-left X is less than all syllables' left edge positions in its text line, the system SHALL assign it to the leftmost syllable.

#### Scenario: Neume to the left of all syllables gets leftmost
- **WHEN** a neume with lower-left X at 0.05 is in the same text line band as syllables with left edges at 0.15, 0.3, and 0.5
- **THEN** the neume SHALL be assigned to the syllable with left edge at 0.15
