## Context

The app already has full delete infrastructure in place:
- `deleteAnnotation(id)` action creator in `src/state/actions.ts`
- `DELETE_ANNOTATION` case in the reducer that removes the annotation and clears selection
- History tracking that makes deletion undoable via Ctrl+Z

What's missing is user-facing controls to trigger deletion.

## Goals / Non-Goals

**Goals:**
- Allow users to delete the selected annotation via Delete or Backspace keys
- Provide a visible delete button in the annotation editor popover
- Deletion is undoable (already works via existing history system)

**Non-Goals:**
- Confirmation dialogs (undo is sufficient)
- Multi-select deletion (no multi-select exists yet)
- Bulk delete operations

## Decisions

### 1. Keyboard handling location

**Decision**: Add Delete/Backspace handling to the existing `handleKeyDown` in `AnnotationCanvas.tsx`

**Rationale**: This is where Tab (navigation) and Space (pan mode) are already handled. Keeps keyboard logic centralized. Same pattern of skipping when target is INPUT/TEXTAREA.

**Alternative considered**: Global handler in App.tsx - rejected because canvas-specific keys belong with canvas logic.

### 2. Delete button placement

**Decision**: Add trash IconButton inside InlineAnnotationEditor, top-right area

**Rationale**:
- Keeps all annotation actions in one place
- Visible when annotation is selected
- Standard trash icon is universally understood

**Alternative considered**: Floating delete button on the canvas near the annotation - rejected as more complex and less discoverable.

### 3. Both Delete and Backspace keys

**Decision**: Support both keys

**Rationale**: Keyboard layouts vary. Mac keyboards label it "delete" but it's actually backspace. Some keyboards have both. Supporting both ensures it works everywhere.

## Risks / Trade-offs

**Accidental deletion** → Mitigated by undo (Ctrl+Z). No confirmation needed.

**Delete while typing** → Mitigated by checking if focus is in INPUT/TEXTAREA before handling.
