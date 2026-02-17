## Context

The annotation canvas currently renders the manuscript image at a fixed scale that fits the container. Users cannot zoom in for detail work or pan around when working on large manuscripts. The existing coordinate system uses normalized values (0-1), which simplifies zoom implementation since annotation data doesn't need to change.

Current rendering pipeline:
```
Image → scaled to fit container → Canvas
Mouse events → canvas coords → normalized coords (stored)
```

## Goals / Non-Goals

**Goals:**
- Smooth zoom in/out centered on mouse cursor position
- Pan navigation when zoomed in via Space+drag
- Clear visual feedback for current interaction mode
- Maintain accuracy of annotation placement at all zoom levels
- Quick reset to default view

**Non-Goals:**
- Persisting zoom/pan state across sessions
- Adding zoom/pan to undo history
- Touch/pinch gestures (future enhancement)
- Minimap or overview panel

## Decisions

### 1. Zoom State Location: Local Component State

**Decision**: Store zoom level and pan offset in AnnotationCanvas local state, not in AppState.

**Rationale**: Zoom/pan is pure view state. Including it in AppState would:
- Pollute undo history with view changes
- Persist view state to localStorage unnecessarily
- Couple view concerns with data concerns

**Alternatives considered**:
- Global AppState: Rejected due to undo/redo pollution
- Separate ViewContext: Overkill for single-component state

### 2. Zoom Trigger: Ctrl+Wheel (Cmd+Wheel on Mac)

**Decision**: Use Ctrl+wheel for zoom, leaving unmodified wheel for potential future vertical scroll.

**Rationale**: Standard pattern in image editors and design tools. Prevents accidental zoom while scrolling.

**Alternatives considered**:
- Unmodified wheel: Conflicts with page/container scroll
- Buttons only: Less fluid for detailed annotation work

### 3. Zoom Anchor: Mouse Cursor Position

**Decision**: Zoom toward/away from the current mouse position.

**Rationale**: Most intuitive for detail work - users zoom into what they're looking at.

**Formula**:
```
newPan.x = mouseX - (mouseX - pan.x) * (newZoom / oldZoom)
newPan.y = mouseY - (mouseY - pan.y) * (newZoom / oldZoom)
```

### 4. Pan Interaction: Space+Drag

**Decision**: Hold Space to enter pan mode, then drag to pan.

**Rationale**:
- Photoshop/Figma convention, widely known
- Clear mode separation from rectangle drawing
- No conflict with existing mouse interactions

**Implementation**:
- Track `isSpaceHeld` via keydown/keyup on window
- When Space held: cursor changes to `grab`, mouse drag pans instead of draws
- When Space released: return to draw mode

### 5. Coordinate Transform Architecture

**Decision**: Add zoom/pan transform step in the existing coordinate pipeline.

```
Screen coords → Canvas-relative → Apply inverse(zoom, pan) → Normalized (0-1)
                                          ↑
                                    NEW STEP
```

For rendering:
```
Normalized → Apply (zoom, pan) → Canvas pixels
                    ↑
              NEW STEP
```

**Key insight**: Annotations stay in normalized coordinates. Only the view transform changes.

### 6. Zoom Limits: 0.5x to 5x

**Decision**: Clamp zoom between 50% and 500%.

**Rationale**:
- 0.5x: See full context even for large manuscripts
- 5x: Sufficient for fine neume details without performance issues

## Risks / Trade-offs

**[Canvas resize during zoom]** → Pan offset could become invalid. Mitigation: Clamp pan to valid bounds on resize.

**[Space key conflicts with text input]** → If annotation editor has focus, Space types in text field. Mitigation: Only enable Space+pan when canvas has focus or no text input is focused.

**[Drawing accuracy at high zoom]** → Small mouse movements = large coordinate changes. Mitigation: The normalized coordinate system handles this naturally; no additional work needed.
