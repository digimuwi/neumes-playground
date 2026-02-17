## Context

The application currently uses the Cantus Index API (`fetchChants()` in `cantusIndex.ts`) for real-time syllable suggestions during annotation. This feature is being deprecated since OCR is reliable, but the Cantus Index remains valuable for metadata enrichment.

Current state:
- `AppState` has no document-level metadata field
- `fetchChants()` implements progressive query shortening (drops first word if no match)
- MEI export has basic `<meiHead>` with just a title
- No UI for Cantus lookup exists

## Goals / Non-Goals

**Goals:**
- Add extensible `metadata` field to `AppState` for document-level data
- Provide on-demand Cantus ID lookup triggered by user action
- Handle multiple matches with a selection dialog
- Include Cantus metadata in MEI exports

**Non-Goals:**
- Automatic/background Cantus lookup (user must trigger explicitly)
- Support for multiple chants per image (assumes single chant)
- Manual Cantus ID entry (just show "not found" if no match)
- Removing the existing syllable suggestion code (separate cleanup task)

## Decisions

### 1. Metadata field structure

**Decision**: Use an optional `metadata` object with optional fields rather than flat properties.

```typescript
metadata?: {
  cantusId?: string;
  genre?: string;
}
```

**Rationale**: Extensible for future metadata fields without multiple optional top-level properties. Grouping related data makes intent clear.

**Alternative considered**: Flat fields (`cantusId?: string` directly on AppState) - rejected because it doesn't scale well as more metadata types are added.

### 2. Text collection for query

**Decision**: Collect text from all syllable annotations in reading order, strip hyphens, join with spaces.

**Rationale**: Reuses existing `computeTextLines()` for reading order. Stripping hyphens reconstructs words as Cantus Index expects them.

### 3. Query strategy

**Decision**: Reuse existing `fetchChants()` with its progressive shortening logic.

**Rationale**: Already handles edge cases (no results → drop first word, retry). In-memory caching reduces API calls. No need to duplicate logic.

### 4. Single match auto-selection

**Decision**: When exactly one chant matches, auto-select it and update metadata immediately.

**Rationale**: Reduces clicks for the common case. User can re-run lookup if wrong.

### 5. Selection dialog for multiple matches

**Decision**: Show a modal dialog with radio button list displaying cid, genre, and text preview for each match.

**Rationale**: Material-UI Dialog fits existing patterns. Radio buttons make single-selection clear. Text preview helps user distinguish similar chants.

### 6. MEI metadata location

**Decision**: Add `<workList>` with `<work>` containing `<identifier type="cantus">` and `<classification>` for genre.

```xml
<workList>
  <work>
    <identifier type="cantus">006847</identifier>
    <classification>
      <term type="genre">Antiphon</term>
    </classification>
  </work>
</workList>
```

**Rationale**: MEI standard practice for work-level identifiers. Keeps source image reference in `<graphic>`, scholarly identifiers in `<workList>`.

### 7. Action and undo behavior

**Decision**: `SET_METADATA` action creates a new history entry (undoable).

**Rationale**: Consistent with other state changes. User can undo if they selected wrong chant.

## Risks / Trade-offs

**[Risk] API rate limiting** → Existing cache in `fetchChants()` mitigates. Single lookup per user action is low volume.

**[Risk] No match for valid chant** → Progressive shortening helps. Accepted limitation: user sees "not found", no fallback to manual entry for now.

**[Risk] Wrong auto-selection with single match** → User can re-run lookup, or undo. Acceptable since single-match is usually correct.

**[Trade-off] Single chant assumption** → Simplifies implementation but limits use for multi-chant folios. Future enhancement can add selection-based lookup.
