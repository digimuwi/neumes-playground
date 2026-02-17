## Why

The backend has migrated from rectangular bounding boxes (`{x, y, width, height}`) to polygon boundaries (`[[x,y], ...]`) for syllable annotations. Syllable polygons follow the actual contour of text lines — critical for slanted/curved handwriting. The frontend still expects the old flat `syllables[]` array with `bbox` fields and uses `Rectangle` as its core geometry type, so it cannot parse or render the new backend responses.

## What Changes

- **BREAKING**: Replace `Annotation.rect: Rectangle` with `Annotation.polygon: number[][]` (normalized 0-1 coordinates) as the core geometry type for all annotations
- **BREAKING**: Update `RecognitionResponse` parsing to handle the new nested `lines[].syllables[].boundary` structure (instead of flat `syllables[]` with `bbox`)
- Store line boundary polygons from backend OCR results for use in contributions
- Convert user-drawn rectangles to 4-corner polygons on creation
- Convert neume bboxes (still rectangular from YOLO) to 4-corner polygons on ingestion
- Render syllable annotations as filled polygons instead of rectangles on canvas
- Use point-in-polygon for hit-testing instead of rectangular bounds checking
- Derive bounding rect from polygon on demand for operations that need it (MEI export zones, text line clustering, neume assignment, sorting)
- Update contribution endpoint payload to send polygon boundaries for syllables and line boundaries

## Capabilities

### New Capabilities
- `polygon-annotations`: Core polygon geometry type, coordinate conversion utilities, canvas rendering, and hit-testing for polygon-based annotations

### Modified Capabilities
- `region-ocr`: Recognition response parsing changes from flat bbox syllables to nested line/syllable polygons
- `training-contribution`: Contribution payload changes to send polygon boundaries for syllables and line boundaries instead of rectangular bboxes
- `mei-export`: Zone coordinates derived from polygon bounding rect instead of stored rectangle
- `text-line-detection`: Syllable metrics (centerX, bottomY) derived from polygon bounds; backend line boundaries stored for contribution use
- `neume-assignment`: Spatial queries use polygon-derived bounds; curve endpoints use closest-point-on-polygon

## Impact

- **Core types**: `src/state/types.ts` — `Annotation` interface changes from `rect: Rectangle` to `polygon: number[][]`
- **API layer**: `src/services/htrService.ts` — response parsing, coordinate conversion, contribution serialization
- **Canvas rendering**: `src/components/AnnotationCanvas.tsx` — polygon drawing instead of fillRect/strokeRect
- **Interaction**: `src/hooks/useCanvasDrawing.ts` — point-in-polygon hit-testing, rect-to-polygon on draw
- **Spatial hooks**: `src/hooks/useTextLines.ts`, `src/hooks/useNeumeAssignment.ts` — polygon-derived metrics
- **Curve drawing**: `src/hooks/useCurveDrawing.ts` — closestPointOnPolygon replaces closestPointOnRect
- **Export**: `src/utils/meiExport.ts` — polygon bounding rect for MEI zones
- **Cantus**: `src/services/cantusIndex.ts` — polygon-derived centerX for sorting
- **Undo/redo**: No structural change — polygon arrays are Immer-compatible, history stack works as before
- **localStorage**: Saved state format changes — existing saved annotations with `rect` will not load correctly (migration or clear needed)
