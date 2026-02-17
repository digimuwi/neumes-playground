## 1. Image Processing Utilities

- [x] 1.1 Add `detectMargins(imageData: ImageData): number` function that returns marginThreshold (0 or 30) based on percentage of dark pixels
- [x] 1.2 Modify `computeOtsuThreshold` to accept optional `minIntensity` parameter and exclude pixels below it from histogram
- [x] 1.3 Modify `tightenRectangle` to accept `marginThreshold` parameter and use band check `marginThreshold <= gray < otsuThreshold` for foreground detection

## 2. Integration

- [x] 2.1 Update `AnnotationCanvas.tsx` to call `detectMargins` on image load and store both marginThreshold and otsuThreshold
- [x] 2.2 Update `handleRectangleDrawn` to pass marginThreshold to `tightenRectangle`
