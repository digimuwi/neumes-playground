## ADDED Requirements

### Requirement: Line beginning markers in export

The exported MEI document SHALL include `<lb/>` (line beginning) elements to mark the start of each text line, preserving manuscript layout structure.

#### Scenario: First line has lb element
- **WHEN** exporting annotations that span one or more text lines
- **THEN** an `<lb n="1"/>` element appears before the first syllable in the layer

#### Scenario: Subsequent lines have lb elements
- **WHEN** annotations span three text lines with syllables
- **THEN** the output contains `<lb n="1"/>`, `<lb n="2"/>`, and `<lb n="3"/>` elements, each appearing before the syllables of that line

#### Scenario: lb element placement
- **WHEN** line 2 contains syllables "Do" and "mi"
- **THEN** the output contains `<lb n="2"/>` followed by `<syllable>` for "Do", then `<syllable>` for "mi"

#### Scenario: Empty lines are skipped
- **WHEN** text line detection finds a line with zero syllables
- **THEN** no `<lb/>` element is emitted for that line

#### Scenario: lb numbering skips empty lines
- **WHEN** line detection finds lines [line1 with syllables, line2 empty, line3 with syllables]
- **THEN** the output contains `<lb n="1"/>` and `<lb n="2"/>` (not n="3"), with n values reflecting only non-empty lines

### Requirement: lb element attributes

Each `<lb/>` element SHALL have an `n` attribute indicating the line number, but SHALL NOT have a `facs` attribute.

#### Scenario: n attribute present
- **WHEN** exporting the second non-empty text line
- **THEN** the `<lb/>` element has attribute `n="2"`

#### Scenario: No facs attribute
- **WHEN** exporting any `<lb/>` element
- **THEN** the element has no `facs` attribute
