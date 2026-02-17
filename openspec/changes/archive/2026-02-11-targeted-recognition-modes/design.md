## Context

The backend `/recognize` endpoint now accepts an optional `type` field (`"neume"` or `"text"`) that skips irrelevant pipeline stages for faster, focused results. The frontend currently only triggers region OCR via Shift+draw, which always runs the full pipeline. We need a mode-based UI that lets users toggle between neume recognition and text recognition before drawing regions.

Current drawing flow in `AnnotationCanvas.handleRectangleDrawn`:
- Shift held → `handleOCRRegion()` (full pipeline)
- No shift → create manual annotation with tightening

Current state sharing between `Toolbar` and `AnnotationCanvas` is via `AppContext` (useReducer + Immer history).

## Goals / Non-Goals

**Goals:**
- Let users toggle neume/text recognition modes via keyboard shortcuts
- Send the `type` parameter to `/recognize` when in a recognition mode
- Show a pulsing region on the canvas while the request is in-flight
- Display the active mode in the toolbar

**Non-Goals:**
- No changes to the full-page OCR flow (DocumentScanner button)
- No persisting recognition mode across sessions or in undo/redo history
- No changes to the backend API itself

## Decisions

### 1. Recognition mode state on AppContext (not in reducer)

`recognitionMode` needs to be read by both `Toolbar` (chip display) and `AnnotationCanvas` (drawing behavior, keyboard handling). Rather than threading props through `App.tsx`, we extend `AppContext` with a `useState` alongside the existing reducer.

This keeps mode out of the undo/redo history stack and out of localStorage persistence, while remaining accessible to both components via the existing `useAppContext()` hook.

**Alternative considered**: Lifting state to `App.tsx` and passing as props. Rejected because both consumers already use context, and prop-threading adds friction.

### 2. Keyboard toggle with Escape reset

- Press `n` → toggle between neume mode and manual mode
- Press `t` → toggle between text mode and manual mode
- Press `n` while in text mode → switch to neume mode (and vice versa)
- `Escape` → returns to manual mode (in addition to its existing deselect behavior)

Keyboard handlers go in the existing `handleKeyDown` in `AnnotationCanvas`, guarded by `isInInput`.

### 3. Blinking region via requestAnimationFrame

When a recognition request is in-flight, the drawn rectangle is stored as `loadingRegion: Rectangle | null` (local state in `AnnotationCanvas`). A separate `useEffect` runs a `requestAnimationFrame` loop that updates a `blinkPhase` counter, which the main canvas draw effect reads to compute a pulsing opacity:

```
opacity = 0.15 + 0.2 * Math.sin(blinkPhase * 0.005)
```

This piggybacks on the existing canvas redraw rather than creating a separate rendering layer.

**Alternative considered**: CSS overlay div with animation. Rejected because the region is in normalized image coordinates and the canvas already handles coordinate transforms; duplicating that logic in a DOM element would be fragile.

### 4. Remove Shift+draw, simplify useCanvasDrawing

The `isShiftHeld` tracking in `useCanvasDrawing` is removed entirely. The hook's `onRectangleDrawn` callback no longer receives a `isShiftHeld` parameter. Recognition behavior is now driven by `recognitionMode` in the parent component.

### 5. Extend htrService.recognizeRegion with type parameter

Add an optional `type?: 'neume' | 'text'` parameter. When provided, it's appended to the FormData. The SSE parser gains handling for the `detecting` stage (neume recognition).

### 6. Toolbar chip placement

The mode chip sits in the OCR group section of the toolbar (near the Recognize Page button), using MUI `Chip` with a distinct color. It shows `"Neume mode (n)"` or `"Text mode (t)"` and is hidden when in manual mode. Clicking the chip could also deactivate the mode.

## Risks / Trade-offs

- **requestAnimationFrame during recognition** → Continuous redraws while loading. Mitigated by: targeted requests are fast (fewer pipeline stages), so the animation window is brief. The RAF loop is cleaned up when `loadingRegion` becomes null.
- **Escape key overload** → Escape now deselects AND clears recognition mode. This is acceptable because both actions represent "reset to default state" semantics. Order: clear mode first, then deselect (or both at once).
- **Removing Shift+draw** → Users lose the "full pipeline on region" shortcut. Mitigated by: full-page OCR button still exists, and users rarely need full-pipeline on a sub-region when they can target neumes or text specifically.
