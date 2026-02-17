## MODIFIED Requirements

### Requirement: Curves connect neume lower-left to closest syllable edge

Each curve SHALL start at the lower-left corner of the neume's bounding box (`rect.x`, `rect.y + rect.height`) and end at the closest point on the syllable's bounding box edge.

#### Scenario: Neume above syllable connects from lower-left to top edge
- **WHEN** a neume's lower-left X is within the syllable's horizontal bounds
- **THEN** the curve SHALL start at the neume's lower-left corner and end on the syllable's top edge at the neume's lower-left X position

#### Scenario: Neume to upper-left connects from lower-left to top-left area
- **WHEN** a neume's lower-left X is left of the syllable's left edge
- **THEN** the curve SHALL start at the neume's lower-left corner and end at the top-left corner of the syllable box
