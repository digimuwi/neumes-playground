## Context

Currently, after drawing a rectangle on the canvas, the annotation is created and selected, but focus remains on the canvas. Users must manually click the text input field in the sidebar to enter syllable text. This creates friction in batch annotation workflows.

The annotation editor shows different inputs based on type:
- Syllable: TextField for text input
- Neume: Select dropdown for neume type

## Goals / Non-Goals

**Goals:**
- Eliminate manual click to focus input after creating annotation
- Reduce friction when annotating runs of same-type items (syllables or neumes)
- Maintain ability to switch types at any time

**Non-Goals:**
- Keyboard shortcuts for type switching (future enhancement)
- Auto-advance to next annotation after input (user controls this via drawing)
- Persisting "last type" preference across sessions

## Decisions

### 1. Derive default type from last annotation

**Decision**: When creating a new annotation, inherit the type from the most recently created annotation (by array position). If no annotations exist, default to 'syllable'.

**Rationale**: Simpler than tracking separate state. The annotations array already captures creation order. No new state to manage or persist.

**Alternatives considered**:
- Explicit `defaultAnnotationType` state: More complex, needs to be kept in sync
- Remember across sessions: Overkill for this use case

### 2. Track "newly created" via a transient flag

**Decision**: Add a `isNewlyCreated` flag to the context that gets set when ADD_ANNOTATION fires and cleared after focus is applied.

**Rationale**: Need to distinguish "just drew this" from "clicked on existing annotation". Only auto-focus on newly created annotations, not when clicking existing ones to edit.

**Implementation**:
- ADD_ANNOTATION action sets `isNewlyCreated: true` in state
- AnnotationEditor's useEffect checks this flag, focuses input, then dispatches CLEAR_NEW_FLAG
- CLEAR_NEW_FLAG sets `isNewlyCreated: false`

### 3. Focus management via refs

**Decision**: Use React refs to the TextField and Select components in AnnotationEditor. When `isNewlyCreated` is true and there's a selected annotation, call `.focus()` on the appropriate ref based on annotation type.

**Rationale**: Standard React pattern for imperative focus management. MUI TextField exposes inputRef for this purpose.

## Risks / Trade-offs

**[Focus stealing from user intent]** → Only auto-focus on newly created annotations (via isNewlyCreated flag), not when user clicks existing annotation to edit.

**[Race condition with render]** → Use useEffect with appropriate dependencies to ensure component is rendered before focusing. MUI components handle this well.
