## ADDED Requirements

### Requirement: Export button in toolbar

The toolbar SHALL display an "Export MEI" button that triggers the MEI export when clicked.

#### Scenario: User clicks export button
- **WHEN** user clicks the "Export MEI" button in the toolbar
- **THEN** the browser downloads a file named "export.mei" containing valid MEI XML

#### Scenario: Export button disabled without image
- **WHEN** no image is loaded in the application
- **THEN** the export button SHALL be disabled

### Requirement: MEI document structure

The exported MEI document SHALL follow the standard MEI hierarchy with meiHead, facsimile, and musical content sections.

#### Scenario: Valid MEI structure
- **WHEN** user exports annotations
- **THEN** the output SHALL contain:
  - XML declaration with UTF-8 encoding
  - `<mei>` root element with MEI namespace
  - `<meiHead>` with basic metadata
  - `<music>` containing `<facsimile>` and `<body>`
  - `<body>` containing `<mdiv>/<score>/<section>/<staff>/<layer>` hierarchy

### Requirement: Syllable ordering

Syllables in the export SHALL be ordered in reading order: grouped by text line (top to bottom), then ordered left-to-right within each line.

#### Scenario: Multi-line document
- **WHEN** annotations span multiple text lines
- **THEN** syllables from the first (topmost) line appear before syllables from subsequent lines

#### Scenario: Left-to-right within line
- **WHEN** a text line contains multiple syllables
- **THEN** syllables are ordered by their horizontal position (leftmost first)

### Requirement: Syllable element structure

Each syllable annotation SHALL be exported as a `<syllable>` element containing a `<syl>` child with the text content.

#### Scenario: Syllable with text
- **WHEN** a syllable annotation has text "Ky"
- **THEN** the export contains `<syllable xml:id="..."><syl>Ky</syl>...</syllable>`

#### Scenario: Syllable without text
- **WHEN** a syllable annotation has no text
- **THEN** the export contains `<syllable xml:id="..."><syl/></syllable>`

### Requirement: Neume nesting within syllables

Each neume SHALL be exported as a `<neume>` element nested within its assigned syllable, ordered left-to-right.

#### Scenario: Multiple neumes per syllable
- **WHEN** two neumes are assigned to one syllable (left neume at x=0.1, right neume at x=0.2)
- **THEN** both neumes appear as children of that syllable, with the x=0.1 neume first

#### Scenario: Neume type attribute
- **WHEN** a neume has type "punctum"
- **THEN** the exported `<neume>` element has attribute `type="punctum"`

### Requirement: Facsimile zones

Each annotation (syllable and neume) SHALL have a corresponding `<zone>` element in the facsimile section with pixel coordinates.

#### Scenario: Zone coordinates
- **WHEN** an annotation has normalized rect {x: 0.1, y: 0.2, width: 0.05, height: 0.03} and image is 1000x800 pixels
- **THEN** the zone has `ulx="100" uly="160" lrx="150" lry="184"`

#### Scenario: Zone linking
- **WHEN** a syllable has id "syl-1"
- **THEN** the syllable element has `facs="#zone-syl-1"` and a zone exists with `xml:id="zone-syl-1"`

### Requirement: Surface element

The facsimile section SHALL contain a `<surface>` element defining the coordinate space and referencing the source image.

#### Scenario: Surface dimensions
- **WHEN** the source image is 1000x800 pixels
- **THEN** the surface has `ulx="0" uly="0" lrx="1000" lry="800"`

#### Scenario: Graphic reference
- **WHEN** exporting
- **THEN** the surface contains `<graphic target="source-image.jpg" width="1000px" height="800px"/>`

### Requirement: Unique identifiers

All exported elements (syllables, neumes, zones) SHALL have unique `xml:id` attributes.

#### Scenario: ID format
- **WHEN** exporting annotations
- **THEN** syllables have ids like "syl-{uuid}", neumes have "n-{uuid}", zones have "zone-{element-id}"
