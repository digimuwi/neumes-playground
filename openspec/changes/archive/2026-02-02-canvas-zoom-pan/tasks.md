## 1. Zoom State and Basic Zoom

- [x] 1.1 Add zoom and pan state to AnnotationCanvas (zoom: number, panX: number, panY: number)
- [x] 1.2 Implement Ctrl+wheel zoom handler with cursor-anchored zoom calculation
- [x] 1.3 Clamp zoom level to 0.5x - 5x range
- [x] 1.4 Update canvas rendering to apply zoom transform when drawing image

## 2. Pan Implementation

- [x] 2.1 Add Space key tracking (isSpaceHeld state via keydown/keyup listeners)
- [x] 2.2 Implement pan drag handling in useCanvasDrawing hook
- [x] 2.3 Prevent annotation drawing when Space is held
- [x] 2.4 Clamp pan offset to keep image partially visible

## 3. Coordinate Transforms

- [x] 3.1 Update getCanvasCoordinates in useCanvasDrawing to account for zoom/pan
- [x] 3.2 Update annotation rendering to apply zoom/pan transform
- [x] 3.3 Update annotation hit detection to work with zoom/pan

## 4. Visual Feedback and Reset

- [x] 4.1 Implement cursor changes (crosshair → grab → grabbing) based on mode
- [x] 4.2 Add double-click handler to reset zoom/pan to default
- [x] 4.3 Ensure double-click on annotation does not trigger reset
