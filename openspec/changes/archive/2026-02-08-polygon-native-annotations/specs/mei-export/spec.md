## MODIFIED Requirements

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
