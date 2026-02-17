## 1. Core Types and Utilities

- [x] 1.1 Create `src/utils/polygonUtils.ts` with functions: `polygonBounds`, `polygonCenterX`, `polygonBottomY`, `polygonMinX`, `pointInPolygon`, `closestPointOnPolygon`, `normalizePolygon`, `denormalizePolygon`, `rectToPolygon`
- [x] 1.2 Update `Annotation` interface in `src/state/types.ts`: replace `rect: Rectangle` with `polygon: number[][]`
- [x] 1.3 Add `LineBoundary` type (`{ boundary: number[][]; syllableIds: string[] }`) and `lineBoundaries: LineBoundary[]` to `AppState` in `src/state/types.ts`
- [x] 1.4 Add `SET_LINE_BOUNDARIES` and update `CLEAR_ANNOTATIONS` action in reducer to handle `lineBoundaries` state

## 2. API Layer — Response Parsing

- [x] 2.1 Update `RecognitionResponse`, `SyllableResult`, and related interfaces in `src/services/htrService.ts` to match new nested `lines[].syllables[].boundary` backend format
- [x] 2.2 Replace `pixelsToNormalized` / `normalizedToPixels` with polygon-aware equivalents using `normalizePolygon` / `denormalizePolygon` from polygonUtils
- [x] 2.3 Rewrite `responseToAnnotations()` to parse nested line/syllable structure, create syllable annotations with normalized polygon, convert neume bboxes to 4-corner polygons, and return line boundaries alongside annotations

## 3. API Layer — Contribution Payload

- [x] 3.1 Update `ContributionSyllable`, `ContributionLine`, and `ContributionAnnotations` interfaces to use `boundary: number[][]` for syllables/lines and `bbox` for neumes
- [x] 3.2 Rewrite `transformAnnotationsForContribution()` to denormalize syllable polygons to pixels, match stored line boundaries to text line clusters, and convert neume polygons back to `{x, y, width, height}` bboxes

## 4. Canvas Rendering

- [x] 4.1 Update annotation drawing loop in `AnnotationCanvas.tsx` to render polygons using `beginPath/moveTo/lineTo/closePath/fill/stroke` instead of `fillRect/strokeRect`
- [x] 4.2 Update preview rect rendering to use polygon path drawing for visual consistency
- [x] 4.3 Update assignment curve endpoint computation: replace `closestPointOnRect` with `closestPointOnPolygon` in `AnnotationCanvas.tsx`

## 5. Canvas Interaction

- [x] 5.1 Update `findAnnotationAtPoint()` in `useCanvasDrawing.ts` to use `pointInPolygon` instead of rectangular bounds check
- [x] 5.2 Update `handleMouseUp` in `useCanvasDrawing.ts` to convert the drawn `Rectangle` to a 4-corner polygon when creating new annotations

## 6. Spatial Hooks

- [x] 6.1 Update `useTextLines.ts` to derive `centerX` and `bottomY` from polygon using `polygonCenterX` and `polygonBottomY`; update `inheritSlopes` to use polygon-derived metrics
- [x] 6.2 Update `useNeumeAssignment.ts` to derive neume anchor point (`minX`, `maxY`) and syllable left edge (`minX`) from polygon using polygonUtils

## 7. Curve Drawing

- [x] 7.1 Update `closestPointOnRect` in `useCurveDrawing.ts` to `closestPointOnPolygon` (or replace with import from polygonUtils); update function signature from `Rectangle` to `number[][]`
- [x] 7.2 Update `AnnotationCanvas.tsx` curve drawing call site to pass `syllable.polygon` instead of `syllable.rect`

## 8. Export and Services

- [x] 8.1 Update `denormalizeRect` in `meiExport.ts` to compute bounding rect from polygon via `polygonBounds` + `denormalizePolygon`, then derive `ulx/uly/lrx/lry`
- [x] 8.2 Update all sorting/grouping functions in `meiExport.ts` (`getSyllablesInReadingOrder`, `groupNeumesBySyllable`) to use `polygonCenterX` instead of `rect.x + rect.width / 2`
- [x] 8.3 Update `src/services/cantusIndex.ts` syllable sorting to use `polygonCenterX`

## 9. Integration and Wiring

- [x] 9.1 Wire `recognizeRegion` and `recognizePage` to dispatch line boundaries to state alongside annotations
- [x] 9.2 Verify undo/redo works correctly with polygon annotations and line boundaries
- [x] 9.3 Verify TypeScript compilation passes with zero `rect` references remaining on `Annotation`
