## MODIFIED Requirements

### Requirement: Generate PAGE XML compatible with Kraken

The system SHALL generate PAGE XML files conforming to the PAGE 2019-07-15 schema that can be used with Kraken's `ketos train` and `ketos segtrain` commands.

The generated XML SHALL include:
- `PcGts` root element with PAGE namespace
- `Metadata` with Creator and Created timestamp
- `Page` element with imageFilename, imageWidth, and imageHeight
- Single `TextRegion` element with Coords containing all content
- `TextLine` elements with Coords, Baseline, `custom` attribute with type, and TextEquiv

Each `TextLine` SHALL have a `custom` attribute in the format `structure {type:<type>;}` where `<type>` is either `neume` or `text`.

#### Scenario: Syllables grouped into TextLines with type attribute
- **WHEN** contribution contains lines with multiple syllables each
- **THEN** PAGE XML contains one `TextLine` per line with `custom="structure {type:text;}"`, with `Word` elements for each syllable containing the syllable's Coords and TextEquiv

#### Scenario: Syllable text without trailing hyphens
- **WHEN** contribution contains syllables with trailing hyphens (e.g., `CI-`, `NE-`)
- **THEN** PAGE XML Word elements contain text with trailing hyphens stripped (e.g., `CI`, `NE`)

#### Scenario: Neumes grouped into TextLines with Word children
- **WHEN** contribution contains neumes
- **THEN** PAGE XML contains `TextLine` elements with `custom="structure {type:neume;}"`, where each TextLine groups neumes by vertical proximity into bands, and each neume is a `Word` child with Coords and the neume type as TextEquiv content

#### Scenario: Neume band grouping by vertical overlap
- **WHEN** contribution contains neumes at different vertical positions
- **THEN** neumes whose bounding boxes overlap vertically (or are within close proximity) are grouped into the same TextLine, ordered left-to-right by x-coordinate within each band

#### Scenario: Single content region
- **WHEN** contribution contains both syllables and neumes
- **THEN** PAGE XML contains a single `TextRegion id="content" type="music-notation"` containing all TextLines (both text and neume types)

#### Scenario: Contribution with only syllables
- **WHEN** contribution contains lines but empty neumes array
- **THEN** PAGE XML contains single TextRegion with only text-type TextLines

#### Scenario: Contribution with only neumes
- **WHEN** contribution contains neumes but empty lines array
- **THEN** PAGE XML contains single TextRegion with only neume-type TextLines

#### Scenario: Baseline generation
- **WHEN** a TextLine is generated from a bounding box
- **THEN** the Baseline points attribute contains a horizontal line at approximately 85% of the bbox height

#### Scenario: Coords as polygon points
- **WHEN** a bbox is converted to PAGE XML Coords
- **THEN** the points attribute contains four space-separated x,y pairs representing the rectangle corners (clockwise from top-left)
