## Context

The backend syllabification system uses pyphen with ecclesiastical Latin patterns to split words into syllables. Currently, `syllabify_word()` returns syllables as plain text (e.g., `["Be", "ne", "dic", "tus"]`). The frontend displays these in individual boxes, but users cannot visually distinguish word boundaries.

## Goals / Non-Goals

**Goals:**
- Add trailing hyphens to non-final syllables to indicate word continuity
- Maintain existing syllabification logic unchanged
- Single-syllable words and final syllables remain unhyphenated

**Non-Goals:**
- Changing the underlying syllabification algorithm
- Modifying bounding box calculations
- Adding configuration options for hyphen behavior

## Decisions

### Decision 1: Modify `syllabify_word()` return values

**Choice**: Add hyphen suffixes directly in `syllabify_word()` rather than in a separate formatting layer.

**Rationale**:
- The function already handles the word-level context needed to determine final vs. non-final syllables
- No downstream code depends on syllables being hyphen-free
- Keeps the change isolated to one function

**Alternatives considered**:
- Post-processing in `map_chars_to_syllables()` — rejected because it would require tracking word boundaries that `syllabify_word()` already knows
- Client-side formatting — rejected because the backend should return display-ready text

### Decision 2: Hyphen placement using list slicing

**Choice**: Use `[s + "-" for s in syllables[:-1]] + syllables[-1:]` pattern.

**Rationale**:
- Handles single-syllable words naturally (empty slice + final syllable)
- Clear, readable one-liner
- No special-casing needed

## Risks / Trade-offs

**[Breaking change for clients expecting raw syllables]** → Mitigated: User confirmed no downstream consumers will break. The hyphenated format is the desired display format.

**[Hyphen appears in exported/stored text]** → Accepted: If syllable text is ever exported or stored, it will include hyphens. This is the intended behavior for display purposes.
