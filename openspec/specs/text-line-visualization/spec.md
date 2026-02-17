# Text Line Visualization

Visual rendering of computed text line baselines on the canvas.

## Requirements

### Requirement: Text line baselines are rendered on canvas

The system SHALL render a visual baseline for each computed text line on the canvas, positioned after the image layer and before annotation rectangles.

#### Scenario: Baselines appear when syllables exist
- **WHEN** the canvas contains one or more syllable annotations
- **THEN** a dashed baseline is rendered for each computed text line

#### Scenario: No baselines when no syllables
- **WHEN** the canvas contains no syllable annotations (only neumes or empty)
- **THEN** no text line baselines are rendered

### Requirement: Baselines follow computed slope

The system SHALL render each baseline following the linear regression slope computed by `useTextLines`, showing the actual tilt of the text line.

#### Scenario: Tilted text produces tilted baseline
- **WHEN** syllables on a text line have varying Y positions (tilted handwriting)
- **THEN** the baseline is rendered at an angle matching the computed slope

#### Scenario: Horizontal text produces horizontal baseline
- **WHEN** syllables on a text line are horizontally aligned
- **THEN** the baseline is rendered horizontally (slope ≈ 0)

### Requirement: Baselines span syllable extent

The system SHALL render each baseline from the left edge of the leftmost syllable to the right edge of the rightmost syllable on that line, with small padding on the left for the line number.

#### Scenario: Baseline spans multiple syllables
- **WHEN** a text line contains multiple syllables
- **THEN** the baseline extends from before the leftmost syllable to after the rightmost syllable

#### Scenario: Single-syllable line baseline
- **WHEN** a text line contains only one syllable
- **THEN** the baseline extends across that syllable's width with padding

### Requirement: Line numbers are displayed

The system SHALL render a circled line number at the start of each baseline, corresponding to the line's position in top-to-bottom order (matching MEI `<lb n="X"/>` numbering).

#### Scenario: Line numbers match MEI export order
- **WHEN** text lines are rendered
- **THEN** the topmost line displays "①", the second "②", and so on

#### Scenario: Line number position
- **WHEN** a baseline is rendered
- **THEN** the line number appears at the left end of the baseline

### Requirement: Visual styling is distinct and subtle

The system SHALL render baselines with styling that is visually distinct from annotations (syllables, neumes, preview) and subtle enough not to distract from the manuscript image.

#### Scenario: Color distinction
- **WHEN** baselines are rendered alongside annotations
- **THEN** baselines use a purple color distinct from blue (syllables), red (neumes), green (preview), and yellow (selected)

#### Scenario: Dashed line style
- **WHEN** baselines are rendered
- **THEN** baselines use a dashed line pattern (indicating computed/derived nature)
