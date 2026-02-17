## Why

User-drawn syllable annotations are tightened to axis-aligned rectangles, which leaves excess background space around irregular ink shapes. Tightening to contour-hugging polygons would produce more precise annotations that better represent the actual ink extent, improving both visual clarity and downstream data quality.

## What Changes

- Add a column-scan contour algorithm that sweeps vertical strips across the tightened bounding box, recording the topmost and bottommost foreground pixel per strip, then connects these into a closed polygon
- Apply Douglas-Peucker simplification to keep polygon vertex count reasonable (~10-30 points)
- Syllable annotations created from user-drawn rectangles produce N-point contour polygons instead of 4-point rectangles
- Neume annotations remain unchanged — still tightened to axis-aligned rectangles converted to 4-point polygons
- Add a new action variant that accepts a pre-computed polygon directly (instead of always converting from rect)

## Capabilities

### New Capabilities
- `contour-tightening`: Column-scan contour extraction and polygon simplification for producing tight polygons from ink pixel data

### Modified Capabilities
- `bounding-box-tightening`: Syllable annotations now produce contour polygons instead of tight rectangles. Neume tightening is unchanged.

## Impact

- `src/utils/imageProcessing.ts` — new `tightenToPolygon()` function alongside existing `tightenRectangle()`
- `src/state/actions.ts` — new action or overload to accept a polygon directly for syllable annotations
- `src/components/AnnotationCanvas.tsx` — branch on annotation type when tightening: polygon for syllables, rectangle for neumes
- `src/utils/polygonUtils.ts` — possible addition of Douglas-Peucker simplification utility
