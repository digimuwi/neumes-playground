## ADDED Requirements

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
