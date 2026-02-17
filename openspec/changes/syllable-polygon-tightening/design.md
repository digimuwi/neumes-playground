## Context

Currently, when a user draws a rectangle around a syllable, `tightenRectangle()` shrinks it to the axis-aligned bounding box of foreground pixels, then `rectToPolygon()` converts the result into a 4-point polygon. This produces a tight rectangle but doesn't follow the actual ink contour.

The same pipeline is used for both syllable and neume annotations. Neumes are small, compact glyphs where a tight rectangle is sufficient. Syllables span wider and have more irregular shapes where a contour polygon adds value.

## Goals / Non-Goals

**Goals:**
- Produce contour-hugging polygons for syllable annotations drawn by the user
- Keep the polygon smooth and reasonable (not pixel-level jagged)
- Preserve existing rectangular tightening for neume annotations unchanged

**Non-Goals:**
- Changing how OCR/backend-produced polygons are handled (they already come as polygons)
- Pixel-perfect contour tracing (e.g., marching squares) — too many vertices, too jagged
- Making the column width or simplification tolerance user-configurable

## Decisions

### Column-scan contour extraction over convex hull or alpha shapes

**Decision**: Use a vertical column-scan approach — divide the tightened bounding box into vertical strips, find the topmost and bottommost foreground pixel per strip, and connect these into a closed polygon.

**Alternatives considered**:
- **Convex hull**: Simpler, but includes empty space in concave regions. Neume text flows horizontally with varying vertical extent, so convex hulls would be too loose.
- **Alpha shapes / concave hull**: Tighter, but complex to implement, requires tuning an alpha parameter, and can produce erratic shapes on noisy manuscripts.
- **Marching squares contour**: Pixel-precise but produces hundreds of vertices and jagged edges.

**Rationale**: Column-scan naturally follows the horizontal flow of manuscript text. It captures vertical variation (ascenders, descenders, varying neume heights) while staying smooth horizontally. The column width controls the resolution.

### Fixed column width of 4 pixels

**Decision**: Use a 4-pixel column width for the vertical scan.

**Rationale**: At typical manuscript image resolutions (2000-4000px wide), a syllable annotation spans roughly 50-200 pixels. A 4px column width yields 12-50 columns = 24-100 raw polygon points, which Douglas-Peucker then simplifies down to ~10-30 points. This balances contour fidelity against polygon complexity.

### Douglas-Peucker simplification

**Decision**: Apply Douglas-Peucker line simplification to the raw column-scan polygon to reduce vertex count while preserving shape.

**Rationale**: The raw column-scan output has 2 points per non-empty column (top + bottom). Many adjacent columns will have similar top/bottom values, producing near-collinear sequences. Douglas-Peucker efficiently removes redundant vertices. A tolerance of 1-2 pixels (normalized to image dimensions) should produce clean results.

### Branch on annotation type at the call site

**Decision**: The branching between polygon tightening (syllables) and rectangular tightening (neumes) happens in `AnnotationCanvas.tsx` at the point where the drawn rect is processed, not inside the tightening functions themselves.

**Rationale**: The two paths produce fundamentally different output types (polygon vs rectangle). Keeping them as separate functions called from the same site is clearer than a single function with type-conditional behavior. The `addAnnotation` action already converts rects to polygons via `rectToPolygon()`, so for syllables we need a new action (or overload) that accepts a polygon directly.

### New `addAnnotationWithPolygon` action

**Decision**: Add a new action creator `addAnnotationWithPolygon(polygon: number[][], type)` rather than modifying the existing `addAnnotation`.

**Rationale**: `addAnnotation` takes a rect and converts it. The syllable path now produces a polygon directly. A separate action creator keeps the interface clean — callers that have a rect use `addAnnotation`, callers that have a polygon use `addAnnotationWithPolygon`.

## Risks / Trade-offs

- **Empty columns in the middle of a syllable** (gaps between letter strokes) → The polygon bridges across gaps naturally since we only connect non-empty column edges. This is desired behavior.
- **Very small annotations** (< ~8px wide, fewer than 2 columns) → Fall back to rectangular tightening. The column scan needs at least 2 non-empty columns to produce a meaningful polygon.
- **Performance** → Column scan + simplification adds computation per annotation draw. However, the existing `tightenRectangle` already scans every pixel in the region. The column scan reuses the same pixel data with minimal overhead. Not a concern.
- **Simplification tolerance too aggressive/conservative** → Could produce polygons that are too boxy or too detailed. The 1-2 pixel tolerance is conservative; can be tuned if needed.
