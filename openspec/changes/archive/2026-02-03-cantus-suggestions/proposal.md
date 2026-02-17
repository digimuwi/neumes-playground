## Why

When annotating chants, users must manually type each syllable even though most chant texts are well-documented in the Cantus Index database. This is tedious and error-prone, especially for common chants. By querying the Cantus Index API based on already-entered syllables, we can predict what the next syllable is likely to be and offer it as a ghost text suggestion.

## What Changes

- Add a background service that queries the Cantus Index API (`https://cantusindex.org/json-text/{searchString}`) based on the text reconstructed from existing syllable annotations
- Implement text reconstruction from syllables using the existing hyphen convention (trailing `-` marks non-final syllables)
- Use the `hyphen` npm package with liturgical Latin patterns to syllabify predicted next words
- Show ghost text suggestions in newly created empty syllable annotations
- Allow Tab/Enter to accept suggestions, any other typing dismisses them
- Cache API responses to minimize server load

## Capabilities

### New Capabilities
- `cantus-suggestions`: Background suggestion system that predicts the next syllable based on context from the Cantus Index database

### Modified Capabilities
<!-- No spec-level requirement changes to existing capabilities -->

## Impact

- **New dependencies**: `hyphen` npm package for Latin syllabification
- **Network**: External API calls to cantusindex.org (CORS-enabled, client-side)
- **Components affected**: `InlineAnnotationEditor` (ghost text display and acceptance)
- **New modules**:
  - `src/services/cantusIndex.ts` - API client with caching
  - `src/utils/textReconstruction.ts` - Syllables to query string
  - `src/hooks/useSuggestion.ts` - Orchestration hook
