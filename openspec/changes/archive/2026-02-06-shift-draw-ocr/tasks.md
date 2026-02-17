## 1. State Management

- [x] 1.1 Add `ADD_ANNOTATIONS` (plural) action type to support batch annotation creation in single history entry
- [x] 1.2 Add `addAnnotations` action creator that takes array of annotations
- [x] 1.3 Handle `ADD_ANNOTATIONS` in reducer to add all annotations atomically

## 2. HTR Service

- [x] 2.1 Create `src/services/htrService.ts` with types for API request/response
- [x] 2.2 Implement `recognizeRegion(imageBlob, region, imageDimensions)` function
- [x] 2.3 Add coordinate transformation: normalized → pixels for request, pixels → normalized for response

## 3. Canvas Drawing Integration

- [x] 3.1 Track Shift key state in `useCanvasDrawing` hook
- [x] 3.2 Pass `isShiftHeld` flag to `onRectangleDrawn` callback
- [x] 3.3 Update `AnnotationCanvas` to branch on Shift: call OCR service or create single annotation

## 4. OCR Flow in AnnotationCanvas

- [x] 4.1 Implement `handleOCRRegion` function that calls HTR service and dispatches batch annotations
- [x] 4.2 Add error handling with user feedback (console.error or simple alert for now)
- [x] 4.3 Handle empty results gracefully (no annotations created, no history entry)
