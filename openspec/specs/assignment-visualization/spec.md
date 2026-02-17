## ADDED Requirements

### Requirement: Assignment curves are always visible

The system SHALL render bezier curves connecting each neume to its assigned syllable whenever assignments exist. Curves are visible at all times, not only on selection.

#### Scenario: Curves render when assignments exist
- **WHEN** neumes are assigned to syllables
- **THEN** bezier curves SHALL be drawn from each neume to its assigned syllable

#### Scenario: No curves when no assignments
- **WHEN** no syllables exist (and thus no assignments)
- **THEN** no assignment curves SHALL be rendered

### Requirement: Curves connect neume lower-left to closest syllable edge

Each curve SHALL start at the lower-left corner of the neume's bounding box (`rect.x`, `rect.y + rect.height`) and end at the closest point on the syllable's bounding box edge.

#### Scenario: Neume above syllable connects from lower-left to top edge
- **WHEN** a neume's lower-left X is within the syllable's horizontal bounds
- **THEN** the curve SHALL start at the neume's lower-left corner and end on the syllable's top edge at the neume's lower-left X position

#### Scenario: Neume to upper-left connects from lower-left to top-left area
- **WHEN** a neume's lower-left X is left of the syllable's left edge
- **THEN** the curve SHALL start at the neume's lower-left corner and end at the top-left corner of the syllable box

### Requirement: Curves use bezier styling with control points

The system SHALL render curves as cubic bezier curves with control points that create a smooth downward arc:
- Control point 1: same X as neume, Y at 40% of vertical distance to endpoint
- Control point 2: same X as endpoint, Y at 60% of vertical distance from neume

#### Scenario: Curve has smooth arc shape
- **WHEN** a curve is drawn from neume to syllable
- **THEN** the curve SHALL have a smooth S-curve or arc shape, not a straight line

### Requirement: Normal curves use neutral semi-transparent styling

In normal state, assignment curves SHALL be rendered with color rgba(120, 120, 120, 0.4) and line width 1.5 pixels.

#### Scenario: Unselected curves appear subtle
- **WHEN** neither the neume nor its assigned syllable is selected or hovered
- **THEN** the curve SHALL be rendered in neutral gray with 40% opacity

### Requirement: Highlighted curves use emphasized styling

When a neume or its assigned syllable is selected or hovered, the connecting curve SHALL be rendered with color rgba(80, 80, 80, 0.8) and line width 2.5 pixels.

#### Scenario: Selecting a syllable highlights all its curves
- **WHEN** a syllable is selected
- **THEN** all curves connecting neumes to that syllable SHALL be rendered with emphasized styling

#### Scenario: Selecting a neume highlights its curve
- **WHEN** a neume is selected
- **THEN** the curve connecting it to its assigned syllable SHALL be rendered with emphasized styling

#### Scenario: Hovering highlights the curve
- **WHEN** the mouse hovers over a neume or syllable
- **THEN** the relevant curves SHALL be rendered with emphasized styling
