### Requirement: Export button in toolbar

The Export dropdown menu in the toolbar SHALL include a "MEI" item that triggers the MEI export when clicked.

#### Scenario: User clicks MEI export menu item
- **WHEN** user clicks "MEI" in the Export dropdown menu
- **THEN** the browser downloads a file named "export.mei" containing valid MEI XML

#### Scenario: MEI export menu item disabled without image
- **WHEN** no image is loaded in the application
- **THEN** the "MEI" item in the Export dropdown SHALL be disabled

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

#### Scenario: Cantus metadata included when present
- **WHEN** user exports annotations and document has Cantus metadata (cantusId, genre)
- **THEN** the `<meiHead>` SHALL contain a `<workList>` with the Cantus identifier and genre

#### Scenario: WorkList structure with Cantus metadata
- **WHEN** document has cantusId "006847" and genre "Antiphon"
- **THEN** the `<meiHead>` contains:
  ```xml
  <workList>
    <work>
      <identifier type="cantus">006847</identifier>
      <classification>
        <term type="genre">Antiphon</term>
      </classification>
    </work>
  </workList>
  ```

#### Scenario: No workList when no Cantus metadata
- **WHEN** user exports annotations and document has no Cantus metadata
- **THEN** the `<meiHead>` SHALL NOT contain a `<workList>` element

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

Each annotation (syllable and neume) SHALL have a corresponding `<zone>` element in the facsimile section with pixel coordinates derived from the bounding rectangle of the annotation's polygon.

#### Scenario: Zone coordinates
- **WHEN** an annotation has polygon `[[0.1,0.2],[0.15,0.2],[0.15,0.23],[0.1,0.23]]` and image is 1000x800 pixels
- **THEN** the zone has `ulx="100" uly="160" lrx="150" lry="184"`

#### Scenario: Zone coordinates from irregular polygon
- **WHEN** an annotation has polygon `[[0.1,0.22],[0.15,0.2],[0.15,0.25],[0.1,0.23]]` and image is 1000x800 pixels
- **THEN** the zone uses the bounding rect: `ulx="100" uly="160" lrx="150" lry="200"`

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

### Requirement: Wordpos attribute on syl elements

The exported `<syl>` elements SHALL include a `@wordpos` attribute indicating word position, computed from trailing hyphen convention in syllable text.

#### Scenario: Initial syllable of multi-syllable word
- **WHEN** a syllable has text "Al-" (ends with hyphen) and previous non-empty syllable did not end with hyphen
- **THEN** the exported `<syl>` has `wordpos="i"` and text content "Al" (hyphen stripped)

#### Scenario: Middle syllable of multi-syllable word
- **WHEN** a syllable has text "le-" (ends with hyphen) and previous non-empty syllable ended with hyphen
- **THEN** the exported `<syl>` has `wordpos="m"` and text content "le" (hyphen stripped)

#### Scenario: Terminal syllable of multi-syllable word
- **WHEN** a syllable has text "ia" (no hyphen) and previous non-empty syllable ended with hyphen
- **THEN** the exported `<syl>` has `wordpos="t"` and text content "ia"

#### Scenario: Single-syllable word
- **WHEN** a syllable has text "Et" (no hyphen) and previous non-empty syllable did not end with hyphen
- **THEN** the exported `<syl>` has `wordpos="s"` and text content "Et"

### Requirement: Empty syllables skip wordpos computation

Empty syllables (melismas with no text) SHALL NOT have a `@wordpos` attribute and SHALL NOT break word chains.

#### Scenario: Empty syllable has no wordpos
- **WHEN** a syllable has empty text
- **THEN** the exported `<syl/>` element has no `wordpos` attribute

#### Scenario: Empty syllable preserves word chain
- **WHEN** syllables in order are "Al-", "", "le-", "ia"
- **THEN** the wordpos values are "i", (none), "m", "t" respectively

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
