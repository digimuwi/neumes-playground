## Context

The app has many keyboard shortcuts and features that researchers don't discover because there's no in-app documentation. Users unfamiliar with power-user conventions miss navigation shortcuts (zoom/pan), annotation cycling (Tab), and drawing modifiers (Shift+drag for OCR).

Current keyboard handling is split across:
- `AnnotationCanvas.tsx`: global shortcuts (undo/redo, select all, delete, tab navigation, space for pan)
- `useCanvasDrawing.ts`: mouse interactions (drawing, shift-detection)

## Goals / Non-Goals

**Goals:**
- Provide discoverable help via floating button
- Document all keyboard shortcuts organized by task
- Document non-obvious features (curves, auto-tightening, suggestions)
- Allow `?` key to trigger help for power users
- Keep the dialog compact and scannable

**Non-Goals:**
- Interactive tutorial or onboarding flow
- Context-sensitive help (different help in different modes)
- Searchable help or keyboard shortcut customization
- Help for the backend/OCR system configuration

## Decisions

### 1. Component placement: Overlay on canvas, not in toolbar

**Decision**: Position the Fab as a fixed overlay in the bottom-right of the canvas area, not as a toolbar button.

**Rationale**:
- Toolbar already has functional buttons (upload, export, OCR, undo/redo)
- A floating button is more discoverable for new users
- Follows common patterns (Figma, Google Docs help buttons)

**Alternative considered**: Toolbar icon - rejected because it would blend in with action buttons.

### 2. Single self-contained component

**Decision**: Create `HelpButton.tsx` containing both the Fab and Dialog.

**Rationale**:
- No state needs to be shared with parent components
- Dialog open/close is local state
- Keeps the feature isolated and easy to maintain

### 3. Keyboard shortcut: `?` key (Shift+/)

**Decision**: Add `?` key handler in `AnnotationCanvas.tsx` alongside other global shortcuts.

**Rationale**:
- Consistent with existing shortcut pattern
- `?` is a common help shortcut (GitHub, Gmail, etc.)
- Must be added to the existing keydown handler, not a separate listener

**Implementation note**: Check that no input is focused before triggering (same guard as other shortcuts).

### 4. Content organization

**Decision**: Group shortcuts by task, not by key.

```
Navigate the Image     → Zoom, Pan, Reset
Cycle Annotations      → Tab, Shift+Tab, Select All, Escape, Delete
Drawing & OCR          → Click+drag, Shift+drag
Undo / Redo           → Cmd+Z, Cmd+Shift+Z
Tips                  → Curves, auto-tightening, suggestions
```

**Rationale**: Users think "how do I zoom?" not "what does Ctrl do?"

### 5. Platform-aware modifier keys

**Decision**: Show `⌘` on Mac, `Ctrl` on Windows/Linux.

**Rationale**: Users expect to see their platform's conventions. Detect via `navigator.platform`.

## Risks / Trade-offs

**[Dialog obscures canvas]** → Position Fab in corner with small footprint; dialog is modal so user explicitly opened it.

**[`?` conflicts with text input]** → Guard with `document.activeElement` check, same as existing shortcuts. Only trigger when no input focused.

**[Content becomes stale]** → Shortcut list is static content in the component. If shortcuts change, help must be updated manually. Acceptable for this scope.
