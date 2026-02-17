## Context

The recognition pipeline runs Kraken segmentation to find text lines (as boundary polygons), then OCR to get characters with cut positions, then syllabification to group characters into syllables. Currently, syllables and lines are returned to the client as rectangular bounding boxes — the polygon data is discarded.

During training export, the system re-runs Kraken segmentation from scratch and masks all detected text regions. User corrections (removing syllable boxes that were actually over neume regions) are ignored because the export never consults the stored annotations for masking decisions.

The contribution storage format uses rectangular bboxes for syllables. There are 4 existing contributions that need migration.

## Goals / Non-Goals

**Goals:**
- Return precise boundary polygons from `/recognize` so the client can render accurate text region outlines
- Slice line-level polygons into per-syllable polygons so users can edit at syllable granularity
- Store syllable polygons in contributions so user corrections (removing wrong syllables) are preserved
- Use stored syllable polygons for text masking during training export — no more re-segmentation
- Migrate existing 4 contributions to the new polygon-based format

**Non-Goals:**
- Changing neume detection or YOLO inference pipeline
- Modifying Kraken segmentation parameters or models
- Client-side implementation (frontend changes are out of scope for this backend change)
- Changing the train/val split or tiling strategy in export

## Decisions

### 1. Polygon slicing via Shapely box intersection

Slice line boundary polygons into per-syllable polygons by intersecting the line polygon with vertical strips at character cut x-positions.

For syllable spanning characters at x-positions `x_left` to `x_right`:
```
strip = shapely.geometry.box(x_left, y_min_global, x_right, y_max_global)
syllable_polygon = line_polygon.intersection(strip)
```

**Why this over alternatives:**
- Simpler than manually walking polygon edges and interpolating points
- Handles complex polygon shapes (curved, concave) correctly
- Shapely is already a dependency
- Produces clean polygons that follow the line's actual contour

Edge cases:
- First syllable: strip extends from negative infinity (or 0) to the cut after the last character
- Last syllable: strip extends from the cut before the first character to positive infinity (or image width)
- The y-range of the strip is set to cover the full image height so only x-positions do the clipping

### 2. Syllable polygons as the masking source during export

During export, collect all syllable `boundary` polygons from `annotations.json` and pass them to `mask_text_regions` as a list of coordinate lists. No Kraken re-segmentation.

**Why this over storing full Kraken Segmentation:**
- Directly represents user intent — only confirmed text regions are masked
- Simpler storage (just polygon coordinates in JSON, no Kraken-specific serialization)
- No need for segmentation-to-annotation cross-referencing logic
- Per-syllable granularity means removing one syllable leaves a precise unmask hole

### 3. Add polygon list overload to mask_text_regions

Add a new function `mask_polygon_regions(image, polygons)` that accepts a list of `list[tuple[int, int]]` polygon coordinate lists. The existing `mask_text_regions(image, segmentation)` remains unchanged for use during inference.

**Why a new function instead of modifying the existing one:**
- Inference still uses the Kraken Segmentation path (mask everything Kraken finds)
- Export uses the annotation polygon path (mask only what the user confirmed)
- Clean separation, no conditional logic

### 4. Nested line/syllable response structure

Replace the flat `syllables` list (with `line_index`) with syllables nested under their parent line. Each line carries its `boundary` polygon and `baseline`. Each syllable carries its own `boundary` polygon.

**Why nested over flat:**
- Natural grouping for the polygon data — syllable polygons only make sense relative to their line
- Client already needs to group syllables by line for display
- Eliminates the `line_index` indirection

### 5. Migration by re-running pipeline and matching

For existing contributions, re-run Kraken segmentation + OCR on each image to obtain line boundaries and character cuts, then match existing syllable texts/bboxes to the OCR results and derive polygon boundaries.

**Matching strategy:**
- For each existing line of syllables, find the Kraken line whose boundary polygon overlaps the most with the syllable bboxes
- Use the character cuts from that Kraken line to slice polygons
- Match syllables by text content and position
- If a Kraken line has no matching syllables in the annotations, it was removed by the user — discard it

## Risks / Trade-offs

**[Risk] Polygon slicing produces degenerate geometries** → Shapely intersection can produce `MultiPolygon`, `GeometryCollection`, or empty geometries for edge cases. Mitigation: extract the largest polygon from multi-geometries, skip empty results, use `buffer(0)` to fix self-intersections.

**[Risk] Re-running OCR during migration produces different text than original** → Kraken OCR is deterministic for the same image+model, so results should match. Mitigation: match by spatial overlap as primary signal, text as secondary confirmation. Log warnings for unmatched syllables.

**[Risk] Breaking API change affects frontend** → This is intentional and coordinated. The frontend needs to update to use polygon boundaries instead of rectangular bboxes.

**[Trade-off] Per-syllable masking is slightly less complete than line-level masking** → Individual syllable polygon strips may leave thin gaps between syllables (at character boundaries). This is acceptable because those gaps contain minimal ink (spaces between characters/words), and the benefit of precise user correction outweighs slight masking imprecision.

## Migration Plan

1. Deploy the updated backend with both old and new annotation formats supported in storage (read old format, write new format)
2. Run the migration script on existing 4 contributions to convert to new format
3. Update frontend to use the new API structure
4. Remove old format support once frontend is updated
