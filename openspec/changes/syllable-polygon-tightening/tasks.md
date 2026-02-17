## 1. Polygon Utilities

- [x] 1.1 Add Douglas-Peucker simplification function to `src/utils/polygonUtils.ts` — takes a `number[][]` polygon and a tolerance (in normalized coordinates), returns simplified polygon

## 2. Column-Scan Contour Algorithm

- [x] 2.1 Add `tightenToPolygon()` function in `src/utils/imageProcessing.ts` — takes a rect, imageData, threshold, marginThreshold, and image dimensions; scans 4px-wide vertical columns to find top/bottom foreground pixels; returns a simplified contour polygon in normalized coordinates
- [x] 2.2 Implement small-region fallback: if fewer than 2 non-empty columns, fall back to `tightenRectangle()` + `rectToPolygon()`

## 3. State Actions

- [x] 3.1 Add `addAnnotationWithPolygon(polygon: number[][], annotationType)` action creator in `src/state/actions.ts` that creates an annotation directly from a polygon (no rect-to-polygon conversion)

## 4. Canvas Integration

- [x] 4.1 Update `AnnotationCanvas.tsx` draw-complete handler to branch on annotation type: call `tightenToPolygon()` for syllables, keep existing `tightenRectangle()` + `rectToPolygon()` for neumes
- [x] 4.2 Use `addAnnotationWithPolygon()` for syllable annotations and existing `addAnnotation()` for neume annotations
