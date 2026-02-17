## Why

Manuscript images often contain fine details (individual neume strokes, faded text) that are difficult to annotate accurately at the default zoom level. Users need to zoom in for precision work and pan around large documents efficiently.

## What Changes

- Add zoom capability to the annotation canvas (0.5x to 5x range)
- Zoom anchors at mouse cursor position for intuitive navigation
- Add pan capability when zoomed in via Space+drag
- Visual feedback: cursor changes to indicate current mode (crosshair for draw, grab for pan)
- Double-click to reset zoom to fit-to-container
- Zoom/pan state is local view state (not undoable, not persisted)

## Capabilities

### New Capabilities
- `canvas-zoom-pan`: Zoom and pan controls for the annotation canvas, including keyboard/mouse interactions and coordinate transforms

### Modified Capabilities
<!-- No existing specs to modify -->

## Impact

- `src/components/AnnotationCanvas.tsx`: Add zoom/pan state and rendering transforms
- `src/hooks/useCanvasDrawing.ts`: Update coordinate calculations to account for zoom/pan offset, add pan interaction handling
- Coordinate transform chain gains a new step (apply zoom/pan before converting to normalized coordinates)
