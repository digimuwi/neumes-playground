## ADDED Requirements

### Requirement: Text reconstruction from syllables
The system SHALL reconstruct query text from existing syllable annotations by:
1. Collecting all syllables that precede the current annotation in reading order
2. Stripping trailing hyphens and concatenating syllables within words
3. Using only complete words (if the final syllable ends with `-`, that incomplete word is excluded)

#### Scenario: Complete words reconstructed
- **WHEN** syllables ["Al-", "le-", "lu-", "ia", "Do-", "mi-", "ne"] exist before current position
- **THEN** system reconstructs "Alleluia Domine" as the query string

#### Scenario: Incomplete final word excluded
- **WHEN** syllables ["Al-", "le-", "lu-", "ia", "De-"] exist before current position
- **THEN** system reconstructs "Alleluia" as the query string (incomplete "De-" excluded)

#### Scenario: No complete words
- **WHEN** only ["Al-"] exists before current position
- **THEN** system returns empty string (no query possible)

### Requirement: Reading order determination
The system SHALL determine reading order by:
1. Computing text lines using the existing `computeTextLines()` function (which handles tilted handwriting)
2. Ordering syllables by line (top to bottom), then by x-position within each line (left to right)
3. Including the newly created annotation in the computation to determine its position

#### Scenario: New annotation placed mid-document
- **WHEN** a new syllable annotation is created between existing syllables
- **THEN** system correctly identifies which syllables precede it based on line and x-position

### Requirement: Cantus Index API querying
The system SHALL query the Cantus Index API at `https://cantusindex.org/json-text/{searchString}` with the reconstructed text.

#### Scenario: Successful API query
- **WHEN** query string is "Alleluia Domine"
- **THEN** system fetches from `https://cantusindex.org/json-text/Alleluia%20Domine`

#### Scenario: Empty query string
- **WHEN** query string is empty
- **THEN** system SHALL NOT make an API request

### Requirement: Progressive query shortening
The system SHALL progressively shorten the query on zero results by removing words from the beginning.

#### Scenario: Full query returns no results
- **WHEN** "Alleluia Domine Deus" returns zero results
- **THEN** system retries with "Domine Deus"

#### Scenario: Shortened query returns no results
- **WHEN** "Domine Deus" also returns zero results
- **THEN** system retries with "Deus"

#### Scenario: Single word returns no results
- **WHEN** "Deus" returns zero results
- **THEN** system gives up and returns no suggestion

### Requirement: API response caching
The system SHALL cache API responses in memory, keyed by query string, for the duration of the session.

#### Scenario: Repeated query uses cache
- **WHEN** "Alleluia" has been queried previously in this session
- **THEN** system returns cached response without making a new API request

#### Scenario: Different query not cached
- **WHEN** "Alleluia Domine" is queried after "Alleluia" was cached
- **THEN** system makes a new API request (different cache key)

### Requirement: Next word extraction
The system SHALL extract the next word from API results by:
1. For each matching chant fulltext, finding the word immediately after the query string
2. Counting occurrences of each next word across all results
3. Returning the most frequently occurring next word

#### Scenario: Common next word found
- **WHEN** results contain "Alleluia Domine Deus meus" (2x) and "Alleluia Domine exaudi" (1x)
- **THEN** system returns "Deus" as the next word

#### Scenario: Tie in next word frequency
- **WHEN** results contain equal occurrences of different next words
- **THEN** system returns the first encountered next word

#### Scenario: No continuation found
- **WHEN** no result contains text beyond the query string
- **THEN** system returns no suggestion

### Requirement: Latin syllabification
The system SHALL syllabify predicted words using liturgical Latin hyphenation patterns from the `hyphen` package.

#### Scenario: Multi-syllable word
- **WHEN** next word is "Deus"
- **THEN** system syllabifies to ["De", "us"]

#### Scenario: Single-syllable word
- **WHEN** next word is "et"
- **THEN** system syllabifies to ["et"]

### Requirement: Suggestion formatting
The system SHALL format the suggestion as a syllable with appropriate hyphen:
- First syllable of multi-syllable word: append `-` (e.g., "De-")
- Only syllable of single-syllable word: no hyphen (e.g., "et")

#### Scenario: First syllable of multi-syllable word
- **WHEN** syllabification produces ["De", "us"]
- **THEN** suggestion is "De-"

#### Scenario: Single-syllable word
- **WHEN** syllabification produces ["et"]
- **THEN** suggestion is "et"

### Requirement: Ghost text display
The system SHALL display the suggestion as ghost text in newly created empty syllable annotations.

#### Scenario: New syllable with suggestion available
- **WHEN** user creates a new syllable annotation AND a suggestion is available
- **THEN** the text input shows the suggestion as ghost/placeholder text

#### Scenario: New syllable with no suggestion
- **WHEN** user creates a new syllable annotation AND no suggestion is available
- **THEN** the text input shows no ghost text

#### Scenario: Existing syllable with text
- **WHEN** user selects an existing syllable that already has text
- **THEN** no ghost text is shown (only for empty new annotations)

### Requirement: Suggestion acceptance
The system SHALL accept the suggestion when the user presses Tab or Enter on an empty text field with a ghost suggestion.

#### Scenario: Tab accepts suggestion
- **WHEN** ghost text shows "De-" AND user presses Tab
- **THEN** the syllable text is set to "De-"

#### Scenario: Enter accepts suggestion
- **WHEN** ghost text shows "De-" AND user presses Enter
- **THEN** the syllable text is set to "De-"

### Requirement: Suggestion dismissal
The system SHALL dismiss the ghost suggestion when the user types any character.

#### Scenario: Typing dismisses suggestion
- **WHEN** ghost text shows "De-" AND user types "A"
- **THEN** ghost text disappears AND text field contains "A"

#### Scenario: Backspace on empty field
- **WHEN** ghost text shows "De-" AND user presses Backspace
- **THEN** ghost text remains (field is already empty)

### Requirement: Graceful degradation
The system SHALL fail silently when the Cantus Index API is unavailable, showing no suggestion rather than an error.

#### Scenario: API request fails
- **WHEN** the API request fails (network error, timeout, non-200 response)
- **THEN** system shows no suggestion (no error message to user)

#### Scenario: API returns invalid JSON
- **WHEN** the API returns malformed response
- **THEN** system shows no suggestion (no error message to user)
