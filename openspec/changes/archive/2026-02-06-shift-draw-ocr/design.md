## Context

The app currently creates one annotation per drawn rectangle. Users manually type syllable text for each. The backend HTR service at `http://localhost:8000/recognize` can process an image region and return detected syllables with bounding boxes.

Current drawing flow:
1. User drags rectangle on canvas
2. `useCanvasDrawing` computes normalized coords
3. `handleRectangleDrawn` creates single annotation via `addAnnotation`

## Goals / Non-Goals

**Goals:**
- Enable batch syllable annotation via Shift+draw
- Call backend OCR and create annotations for each detected syllable
- Maintain current single-annotation behavior for normal draw

**Non-Goals:**
- Editing/refining OCR results in a modal before confirming
- Progress indicator or cancellation UI (keep it simple)
- Caching or offline OCR results

## Decisions

### 1. Trigger mechanism: Shift+draw
**Choice**: Use Shift key modifier during rectangle draw

**Rationale**:
- No UI changes required
- Consistent with modifier patterns (Cmd+click for multi-select)
- Doesn't disrupt default workflow

**Alternatives considered**:
- Toolbar toggle button: Adds UI clutter, requires click before each OCR region
- Right-click context menu: More discoverable but breaks flow

### 2. Service layer location
**Choice**: Create `src/services/htrService.ts` for backend communication

**Rationale**:
- Follows existing pattern (`src/services/cantusIndex.ts`)
- Separates HTTP concerns from component logic
- Easy to mock for testing

### 3. Coordinate transformation
**Choice**: Convert normalized coords → pixels for API, then pixels → normalized for annotations

**Rationale**:
- Backend expects pixel coordinates
- Frontend stores normalized coordinates (0-1)
- Transformation happens in service layer

### 4. Undo behavior
**Choice**: Each OCR operation creates one history entry containing all created annotations

**Rationale**:
- User can undo entire OCR result with single Ctrl+Z
- Matches user mental model ("undo that OCR")
- Requires batch action: `ADD_ANNOTATIONS` (plural)

## Risks / Trade-offs

- **[Backend unavailable]** → Show error toast, don't break app. User can retry or fall back to manual annotation.
- **[OCR returns no syllables]** → Show brief feedback ("No syllables detected"), don't create empty annotations.
- **[Slow recognition]** → Accept for now; cursor change to "wait" during call. Non-goal to add cancellation.
