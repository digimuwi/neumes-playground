## Context

The MEI export currently generates `<syl>` elements with raw text content but no word position information. Users indicate word boundaries using a trailing hyphen convention (e.g., "Al-" means the syllable continues to the next). This information needs to be converted to MEI's `@wordpos` attribute during export.

Current export flow:
1. `getSyllablesInReadingOrder()` returns syllables sorted by text line, then left-to-right
2. `generateSyllableXML()` creates `<syllable>` elements with `<syl>` children
3. Text is output as-is (including any hyphens)

## Goals / Non-Goals

**Goals:**
- Compute `wordpos` attribute from hyphen convention during export
- Strip trailing hyphens from exported text content
- Handle empty syllables transparently (skip but don't break word chains)

**Non-Goals:**
- Modifying the internal data model (hyphens remain stored in `text`)
- Validating word boundaries during input
- UI changes to indicate word position

## Decisions

### Decision 1: Compute wordpos during export, not during input

**Choice**: Calculate `wordpos` at export time by scanning syllables in reading order.

**Rationale**: Keeps the data model simple—no new fields needed. The hyphen in `text` is the source of truth. Export-time computation also handles reordering gracefully if syllable positions change.

**Alternatives considered**:
- Store `wordpos` on each annotation → Adds complexity, requires sync when syllables reorder
- Store `continuesWord: boolean` flag → Extra field when hyphen already encodes this

### Decision 2: Empty syllables are transparent to word chaining

**Choice**: When computing wordpos, skip empty syllables but track the previous non-empty syllable's hyphen state.

**Rationale**: Empty syllables represent melismas with no text. They shouldn't participate in word structure but also shouldn't break a word chain. Example: `"Al-" "" "le-" "ia"` → `i, -, m, t`.

### Decision 3: Single-pass algorithm

**Choice**: Process syllables in a single pass, tracking `prevNonEmptyEndedWithHyphen`.

**Algorithm**:
```
prevHyphen = false
for syllable in readingOrder:
    if text is empty:
        wordpos = undefined
    else:
        endsWithHyphen = text.endsWith("-")
        if prevHyphen:
            wordpos = endsWithHyphen ? "m" : "t"
        else:
            wordpos = endsWithHyphen ? "i" : "s"
        prevHyphen = endsWithHyphen
```

**Rationale**: O(n), no lookahead needed, straightforward to implement and test.

## Risks / Trade-offs

**[Risk] Orphan initial syllable** (e.g., "Al-" with no following syllable) → The syllable gets `wordpos="i"` which is technically correct—it's the start of an incomplete word. No special handling needed.

**[Trade-off] Hyphens stripped silently** → Users see "Al-" in the UI but export produces "Al". This is correct MEI behavior but could surprise users. Acceptable since the wordpos attribute encodes the continuation semantically.
