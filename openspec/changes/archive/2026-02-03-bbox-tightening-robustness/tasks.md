## 1. Constants and Configuration

- [x] 1.1 Add `OTSU_THRESHOLD_BIAS = 5` constant to `imageProcessing.ts`
- [x] 1.2 Add `MIN_BBOX_SIZE = 4` constant to `imageProcessing.ts`
- [x] 1.3 Add `BBOX_PADDING = 1` constant to `imageProcessing.ts`

## 2. Modify tightenRectangle Function

- [x] 2.1 Add `thresholdBias` parameter to `tightenRectangle` signature (default 0)
- [x] 2.2 Apply threshold bias when checking foreground pixels: `gray < threshold + thresholdBias`
- [x] 2.3 After computing tight bbox, add padding (clamped to original rect bounds)
- [x] 2.4 After padding, check if bbox is smaller than MIN_BBOX_SIZE in either dimension; if so, return original rect

## 3. Update Caller

- [x] 3.1 Update `handleRectangleDrawn` in `AnnotationCanvas.tsx` to pass `OTSU_THRESHOLD_BIAS` to `tightenRectangle`
