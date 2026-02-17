## Context

The annotation tool currently uses a single-selection model (`selectedAnnotationId: string | null`). Users can select one annotation at a time, which triggers an inline editor popover. Deletion happens via Delete key or a button in the editor.

The state is managed through a React Context with a history-aware reducer (Immer-based). The canvas component handles mouse/keyboard events and delegates to the `useCanvasDrawing` hook for interaction logic.

## Goals / Non-Goals

**Goals:**
- Enable multi-annotation selection using standard platform conventions
- Support batch deletion of selected annotations
- Maintain backward compatibility with single-selection editing workflow
- Ensure batch delete is atomic for undo/redo

**Non-Goals:**
- Drag-to-select (marquee selection) - out of scope
- Batch editing of annotation properties (type, text) - deletion only
- Shift+Click range selection - using toggle-based selection instead

## Decisions

### 1. State representation: `Set<string>` vs `string[]`

**Decision**: Use `Set<string>` for `selectedAnnotationIds`

**Rationale**:
- O(1) lookup for "is this annotation selected?" (frequent during rendering)
- O(1) add/remove for toggle operations
- Naturally prevents duplicates

**Alternative considered**: Array would require `includes()` checks and manual dedup.

**Serialization note**: Sets don't serialize to JSON directly. For localStorage persistence, convert to/from array: `Array.from(set)` / `new Set(array)`.

### 2. Event detection: Modifier key handling

**Decision**: Check `event.metaKey` (Mac) or `event.ctrlKey` (Windows/Linux) for multi-select modifier.

**Rationale**: Standard platform convention. Use `event.metaKey || event.ctrlKey` to cover both.

### 3. Batch delete action structure

**Decision**: Single `DELETE_ANNOTATIONS` action taking `string[]` of IDs, creating one history entry.

**Rationale**:
- Dispatching multiple `DELETE_ANNOTATION` actions would create multiple history entries
- A single action ensures Ctrl+Z restores all deleted annotations atomically

**Alternative considered**: Wrapping multiple deletes in a transaction - adds complexity without benefit.

### 4. Editor visibility logic

**Decision**: Show editor when `selectedAnnotationIds.size === 1`, hide otherwise.

**Rationale**:
- Multi-select is for batch operations (deletion), not editing
- Showing editor for one of many selected would be confusing
- Clean separation: single-select = edit mode, multi-select = batch mode

## Risks / Trade-offs

**Risk**: Set serialization could break localStorage persistence
→ **Mitigation**: Convert Set↔Array at persistence boundaries in `loadState`/`saveState`

**Risk**: Cmd+A conflicts with browser/OS "select all text"
→ **Mitigation**: Only capture when canvas is focused, use `preventDefault()`

**Trade-off**: No visual distinction for "primary" selection in multi-select
→ **Accepted**: Batch delete treats all equally; no need for primary
