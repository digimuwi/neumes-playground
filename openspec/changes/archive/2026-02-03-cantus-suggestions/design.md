## Context

Users annotate medieval chant manuscripts by drawing rectangular zones and labeling them as syllables (with text) or neumes (with type). The syllable text uses a hyphen convention: trailing `-` indicates a non-final syllable within a word (e.g., "Al-", "le-", "lu-", "ia" for "Alleluia").

The Cantus Index (`cantusindex.org`) maintains a comprehensive database of chant texts. Their API endpoint `GET /json-text/{searchString}` returns chants matching a search string, with fields: `cid` (Cantus ID), `fulltext`, and `genre`. The API returns `Access-Control-Allow-Origin: *`, enabling direct client-side requests.

Existing infrastructure we can leverage:
- `computeTextLines()` clusters syllables into lines using linear regression (handles tilted text)
- `getSyllablesInReadingOrder()` returns syllables sorted by line then x-position
- `computeWordpos()` already tracks word boundaries using the hyphen convention

## Goals / Non-Goals

**Goals:**
- Predict the next syllable based on existing syllable annotations
- Show suggestions as ghost text (non-intrusive, easily dismissed)
- Minimize API calls through caching and smart query construction
- Use liturgical Latin syllabification patterns for accuracy

**Non-Goals:**
- Suggesting neume types (out of scope)
- Supporting languages other than Latin
- Offline suggestion capability
- User-configurable suggestion sources

## Decisions

### 1. Query construction: Full words only, progressive shortening

**Decision**: Reconstruct only complete words from syllables (skip incomplete final word if it ends with `-`). On zero results, progressively drop the first word and retry.

**Rationale**:
- Partial words create too many false matches due to orthographic variations (ae/e, u/v)
- Dropping from the front preserves the most recent context, which is more predictive
- Alternative considered: Fuzzy matching - rejected because the API doesn't support it

### 2. Syllabification: `hyphen` package with liturgical Latin patterns

**Decision**: Use `hyphen/la-x-liturgic` npm package to syllabify predicted words.

**Rationale**:
- Liturgical Latin patterns are specifically tuned for chant texts
- Package is well-maintained with built-in patterns (no vendoring)
- Alternative considered: `hypher` + gregorio-project patterns - would require manual pattern loading

### 3. Reading order: Reuse existing `computeTextLines`

**Decision**: When a new annotation is created, re-run `computeTextLines()` including the new annotation, then slice all syllables that appear before it in reading order.

**Rationale**:
- Reuses battle-tested logic for handling tilted text lines
- Cost is O(n log n) but only runs once per new annotation, not on every keystroke
- Alternative considered: Approximate position check - rejected as error-prone with tilted lines

### 4. Next word extraction: Most common across results

**Decision**: For each matching chant, extract the word immediately following the query string. Return the most frequently occurring next word.

**Rationale**:
- Acts as a "soft vote" across the corpus
- Handles cases where multiple chants start similarly but diverge
- On ties, use first occurrence (arbitrary but consistent)

### 5. Caching: In-memory with query string keys

**Decision**: Cache API responses in a simple Map keyed by query string. No TTL (session-only cache).

**Rationale**:
- Same queries repeat often within a session (similar chant openings)
- Session-only avoids stale data concerns
- Alternative considered: localStorage persistence - adds complexity without clear benefit

### 6. UI: Ghost text with Tab/Enter acceptance

**Decision**: Show suggestion as placeholder-style ghost text in empty syllable TextField. Tab or Enter accepts; any other input dismisses.

**Rationale**:
- Familiar pattern (GitHub Copilot, IDE autocomplete)
- Non-intrusive - doesn't block normal typing
- Alternative considered: Dropdown autocomplete - too heavy for single-syllable suggestions

## Risks / Trade-offs

**[API availability]** → If cantusindex.org is down, suggestions silently fail (graceful degradation). No user-facing error.

**[Orthographic mismatch]** → Medieval manuscripts may use variant spellings not in Cantus Index. Mitigation: Progressive shortening gives more chances to match.

**[Syllabification edge cases]** → Hyphenation patterns optimize for line-breaking, not always syllable boundaries. Mitigation: Liturgical patterns are close enough for practical use.

**[Performance]** → Re-running `computeTextLines` on every new annotation. Mitigation: Only on creation, not on every keystroke; typical document has <100 syllables.

## Module Structure

```
src/
├── services/
│   └── cantusIndex.ts       # API client + response cache
├── utils/
│   └── textReconstruction.ts # Annotations → query string
└── hooks/
    └── useSuggestion.ts      # Orchestrates flow, returns suggestion
```

**Data flow:**
```
New annotation created
       │
       ▼
useSuggestion hook triggers
       │
       ▼
textReconstruction.ts: annotations → "Alleluia Domine"
       │
       ▼
cantusIndex.ts: query API (cached) → chant results
       │
       ▼
Extract most common next word → "Deus"
       │
       ▼
Syllabify with hyphen → ["De", "us"] → "De-"
       │
       ▼
Return to InlineAnnotationEditor as ghost text
```
