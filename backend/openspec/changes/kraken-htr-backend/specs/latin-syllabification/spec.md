## ADDED Requirements

### Requirement: Latin text syllabification

The system SHALL syllabify Latin text using pyphen with ecclesiastical Latin hyphenation patterns (hyphen-la liturgical). Each word SHALL be split into syllables according to liturgical Latin rules.

#### Scenario: Syllabify single word

- **WHEN** the word "Benedictus" is syllabified
- **THEN** the result is ["Be", "ne", "dic", "tus"]

#### Scenario: Syllabify multi-word text

- **WHEN** the text "patrum nostrorum" is syllabified
- **THEN** the result preserves word boundaries: [["pa", "trum"], ["nos", "tro", "rum"]]

#### Scenario: Handle short words

- **WHEN** a word like "et" cannot be further divided
- **THEN** the result is ["et"] (single syllable)

### Requirement: Character-to-syllable grouping

The system SHALL map character indices to syllables, tracking which characters belong to each syllable. Spaces between words SHALL be excluded from syllable output.

#### Scenario: Map characters to syllables

- **WHEN** text "dis patrum" with character bboxes is processed
- **THEN** syllable "dis" maps to characters 0-2, syllable "pa" maps to characters 4-5, syllable "trum" maps to characters 6-9

#### Scenario: Skip space characters

- **WHEN** a space character is encountered
- **THEN** it is skipped and not included in any syllable bbox

### Requirement: Syllable bounding box merging

The system SHALL merge character bounding boxes to produce a single bounding box per syllable. The merged bbox SHALL be the minimum enclosing rectangle of all constituent character bboxes.

#### Scenario: Merge character bboxes into syllable bbox

- **WHEN** syllable "Be" consists of characters with bboxes {x:100, y:50, w:30, h:40} and {x:130, y:52, w:25, h:38}
- **THEN** the merged syllable bbox is {x:100, y:50, width:55, height:42}

#### Scenario: Single character syllable

- **WHEN** a syllable consists of only one character
- **THEN** the syllable bbox equals the character bbox
