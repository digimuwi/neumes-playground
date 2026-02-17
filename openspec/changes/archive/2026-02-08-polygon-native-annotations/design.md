## Context

The backend HTR service has migrated from rectangular bounding boxes to polygon boundaries for syllable annotations. The new API response nests syllables inside lines (each with a polygon boundary), while the frontend still expects a flat `syllables[]` array with `{x, y, width, height}` bboxes. The core `Annotation` type uses `rect: Rectangle` throughout the entire codebase — types, rendering, hit-testing, spatial queries, export, and contribution.

## Goals / Non-Goals

**Goals:**
- Make `polygon: number[][]` the single geometry representation for all annotations
- Parse the new nested `lines[].syllables[].boundary` API response format
- Render syllable polygons faithfully on canvas (not just bounding rects)
- Store backend line boundaries for use in contribution payloads
- Maintain all existing spatial features (text line clustering, neume assignment, curve drawing, MEI export) using polygon-derived metrics

**Non-Goals:**
- Polygon editing UI (vertex dragging, reshaping) — annotations remain immutable once created
- Storing line boundaries in the annotation state model — they live in a separate structure
- Supporting mixed rect/polygon annotations — all annotations use polygon uniformly
- Migrating existing localStorage data — a clear/reload is acceptable for this breaking change

## Decisions

### D1: Single `polygon` field replaces `rect` on `Annotation`

**Decision:** Replace `rect: Rectangle` with `polygon: number[][]` (normalized 0-1 coordinates, closed polygon as `[[x,y], ...]`).

**Rationale:** A unified type avoids branching logic ("is this a rect or polygon?") everywhere. Rectangles are just 4-point polygons. User-drawn rects convert to `[[x,y], [x+w,y], [x+w,y+h], [x,y+h]]` at creation time. Neume bboxes from the API convert the same way on ingestion.

**Alternatives considered:**
- Dual `rect` + `polygon?` fields — rejected because it creates ambiguity about which to use and requires null-checking everywhere
- Union type `geometry: Rectangle | Polygon` — rejected because discriminated unions add complexity for minimal benefit when polygons subsume rectangles

### D2: Polygon utility module for derived metrics

**Decision:** Create `src/utils/polygonUtils.ts` with pure functions: `polygonBounds`, `polygonCenterX`, `polygonBottomY`, `polygonMinX`, `pointInPolygon`, `closestPointOnPolygon`, `normalizePolygon`, `denormalizePolygon`.

**Rationale:** Many existing consumers need derived values (centerX, bottomY, bounding rect) that were previously direct field access on `Rectangle`. Centralizing these avoids duplicating geometry math. All functions operate on `number[][]` — no class wrapper needed.

**Key functions:**
- `polygonBounds(poly) → { minX, minY, maxX, maxY }` — for MEI zones, sorting, bounding rect
- `polygonCenterX(poly) → number` — for text line clustering, syllable sorting
- `polygonBottomY(poly) → number` — for text line clustering
- `polygonMinX(poly) → number` — for neume assignment (left edge)
- `pointInPolygon(x, y, poly) → boolean` — for hit-testing (ray casting algorithm)
- `closestPointOnPolygon(px, py, poly) → {x, y}` — for assignment curve endpoints
- `normalizePolygon(poly, dims) → number[][]` — pixel coords to 0-1
- `denormalizePolygon(poly, dims) → number[][]` — 0-1 to pixel coords

### D3: Store backend line boundaries separately from annotations

**Decision:** Store OCR line boundaries in a separate `Map<string, number[][]>` (lineId → boundary polygon), populated when OCR results arrive and keyed by a synthetic line ID. The contribution endpoint uses these stored boundaries. For user-drawn annotations (no backend lines), compute a synthetic line boundary as the convex hull of syllable polygons in each text line cluster.

**Rationale:** Line boundaries are not annotations — they aren't selectable, editable, or exportable. Mixing them into `Annotation[]` would complicate the state model and undo/redo. Keeping them separate is cleaner. The contribution endpoint needs them, so we store them from the OCR response rather than discarding.

**Implementation:** Add `lineBoundaries: LineBoundary[]` to `AppState`, where `LineBoundary = { boundary: number[][]; syllableIds: string[] }`. When OCR results arrive, each line's boundary and its syllable IDs are stored together. The contribution transform function matches text line clusters to stored line boundaries by syllable ID overlap.

**Alternatives considered:**
- Discard line boundaries and recompute from syllable polygons — rejected because the backend provides accurate Kraken-segmented boundaries that are superior to any frontend approximation
- Store line boundaries as annotation objects — rejected because they aren't user-facing entities

### D4: Canvas polygon rendering with beginPath/lineTo

**Decision:** For syllable annotations, render using `ctx.beginPath() → ctx.moveTo(p[0]) → ctx.lineTo(p[1..n]) → ctx.closePath() → ctx.fill() → ctx.stroke()`. Neumes (always 4-point rectangles) use the same polygon path code — no special-casing.

**Rationale:** The Canvas API polygon path is the natural fit. Using the same rendering path for all annotations (regardless of vertex count) keeps the code simple. Performance is not a concern — we're drawing dozens of polygons, not thousands.

### D5: Point-in-polygon hit-testing via ray casting

**Decision:** Replace the current rectangular bounds check in `findAnnotationAtPoint()` with a ray casting point-in-polygon test.

**Rationale:** Ray casting correctly handles irregular polygons. For 4-point rectangles (neumes, user-drawn syllables), it's equivalent to the current bounds check. The algorithm is O(n) per polygon vertex count, which is negligible for our use case.

### D6: Contribution payload uses backend line structure

**Decision:** The contribution transform function sends `lines[].boundary` from stored OCR line boundaries and `lines[].syllables[].boundary` from annotation polygons (denormalized to pixels). Neumes still send `bbox: {x, y, width, height}` as the backend expects.

**Rationale:** The backend `/contribute` endpoint expects `LineInput` with `boundary: list[list[int]]` and `SyllableInput` with `boundary: list[list[int]]`. Neumes use `NeumeInput` with `bbox: BBox`. We match the backend schema exactly.

### D7: Rectangle type retained for drawing interaction only

**Decision:** Keep `Rectangle` as an internal type used only in `useCanvasDrawing.ts` for the drag-to-draw preview. On mouse-up, the drawn rectangle is immediately converted to a 4-point polygon before creating the annotation.

**Rationale:** The drawing interaction is inherently rectangular (drag from corner to corner). Converting to polygon at the boundary (mouse-up) keeps the drawing code simple while ensuring all persisted data is polygon-native.

## Risks / Trade-offs

- **localStorage breakage** → Acceptable: users clear browser data. No migration needed for a development-stage tool.
- **Slightly more code for derived metrics** → Mitigated by centralizing in `polygonUtils.ts`. The `a.rect.x + a.rect.width / 2` pattern becomes `polygonCenterX(a.polygon)` — similar verbosity.
- **Point-in-polygon slightly slower than rect bounds check** → Negligible for <100 annotations. Ray casting is O(vertices) per annotation.
- **Convex hull fallback for user-drawn line boundaries** → Only needed when contributing purely hand-drawn annotations without OCR. Acceptable approximation.
