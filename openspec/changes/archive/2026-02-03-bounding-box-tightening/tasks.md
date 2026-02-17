## 1. Image Processing Utilities

- [x] 1.1 Create `src/utils/imageProcessing.ts` with `computeOtsuThreshold(imageData: ImageData): number` function
- [x] 1.2 Add `tightenRectangle(rect: Rectangle, imageData: ImageData, threshold: number): Rectangle` function that returns the tightened bounding box

## 2. Integration

- [x] 2.1 Add threshold state to `AnnotationCanvas.tsx` that computes on image load via `useMemo` or `useEffect`
- [x] 2.2 Modify `handleRectangleDrawn` to extract pixel data for the drawn region and call `tightenRectangle` before dispatching `ADD_ANNOTATION`
