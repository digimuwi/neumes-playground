# Syllable Formatting

## Requirements

### Requirement: Non-final syllables have trailing hyphens

The system SHALL append a trailing hyphen character (`-`) to syllables that are not the final syllable of their word. This indicates to users that the syllable continues within the same word.

#### Scenario: Multi-syllable word syllabification
- **WHEN** the word "Benedictus" is syllabified
- **THEN** the system returns `["Be-", "ne-", "dic-", "tus"]`

#### Scenario: Two-syllable word syllabification
- **WHEN** the word "Dominus" is syllabified
- **THEN** the system returns `["Do-", "mi-", "nus"]`

### Requirement: Final syllables have no trailing hyphen

The system SHALL NOT append a trailing hyphen to the final syllable of a word. The final syllable indicates word completion.

#### Scenario: Final syllable is unhyphenated
- **WHEN** the word "Benedictus" is syllabified
- **THEN** the last element "tus" has no trailing hyphen

### Requirement: Single-syllable words have no hyphen

The system SHALL NOT append a trailing hyphen to words that consist of only one syllable, as there is no continuation.

#### Scenario: Single-syllable word
- **WHEN** the word "et" is syllabified
- **THEN** the system returns `["et"]` with no hyphen

#### Scenario: Another single-syllable word
- **WHEN** the word "in" is syllabified
- **THEN** the system returns `["in"]` with no hyphen
