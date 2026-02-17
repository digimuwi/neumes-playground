## ADDED Requirements

### Requirement: Minimum query length for API requests

The system SHALL only make API requests when the query contains at least two complete words, to avoid overly broad result sets.

#### Scenario: Single word query
- **WHEN** query is "Domine" (one word)
- **THEN** system returns no suggestion (does not make API request)

#### Scenario: Two word query
- **WHEN** query is "Domine non" (two words)
- **THEN** system makes API request and provides suggestion

#### Scenario: Incomplete word only
- **WHEN** user has only entered partial syllables like "Do-" "mi-"
- **THEN** system returns no suggestion (incomplete word doesn't count)

### Requirement: Chant prediction caching

The system SHALL cache the entire syllabified chant text after the first successful API query and use it to serve subsequent suggestions without additional API calls.

#### Scenario: First query establishes prediction cache
- **WHEN** user creates a new syllable and API returns chants
- **THEN** system picks the top chant, syllabifies its entire fulltext, and caches the syllable array with position 0

#### Scenario: Subsequent suggestion served from cache
- **WHEN** user accepts a suggestion and creates next syllable AND prediction cache exists
- **THEN** system returns the next syllable from cache without making an API call

#### Scenario: Position advances on accept
- **WHEN** user accepts suggestion "Do-" at position 0 in cache ["Do-", "mi-", "ne", ...]
- **THEN** position advances to 1 and next suggestion is "mi-"

### Requirement: Prediction cache invalidation on divergence

The system SHALL invalidate the prediction cache when the user types text that differs from the current suggestion.

#### Scenario: User types different text
- **WHEN** cache suggests "Do-" AND user types "Al" instead
- **THEN** prediction cache is invalidated AND next annotation triggers fresh API query

#### Scenario: User accepts suggestion
- **WHEN** cache suggests "Do-" AND user accepts with Tab/Enter
- **THEN** prediction cache remains valid AND position advances

### Requirement: Prediction exhaustion handling

The system SHALL return no suggestion when the prediction cache is exhausted (position exceeds syllable array length).

#### Scenario: End of chant reached
- **WHEN** position is 5 AND syllable array has 5 elements
- **THEN** system returns null (no suggestion)

#### Scenario: User continues past chant end
- **WHEN** user creates annotation after prediction exhausted
- **THEN** system attempts fresh API query with current context

## MODIFIED Requirements

### Requirement: API response caching

The system SHALL cache API responses in memory, keyed by query string, for the duration of the session. This cache operates independently of the prediction cache.

#### Scenario: Repeated query uses cache
- **WHEN** "Alleluia" has been queried previously in this session
- **THEN** system returns cached response without making a new API request

#### Scenario: Different query not cached
- **WHEN** "Alleluia Domine" is queried after "Alleluia" was cached
- **THEN** system makes a new API request (different cache key)

#### Scenario: Divergence triggers query with existing cache
- **WHEN** user diverges from prediction AND new query matches a previously cached query
- **THEN** system uses cached API response (no new request)
