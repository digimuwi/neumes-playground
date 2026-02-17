## 1. Polygon Slicing Geometry

- [x] 1.1 Create `pipeline/polygon_slicing.py` with function to derive syllable x-ranges from character cuts and syllable character spans
- [x] 1.2 Implement `slice_line_polygon` function that intersects a line boundary polygon with vertical strips to produce per-syllable polygons (using Shapely)
- [x] 1.3 Handle degenerate Shapely results (MultiPolygon, GeometryCollection, empty) by extracting largest polygon or skipping
- [x] 1.4 Write tests for polygon slicing: multi-syllable line, single-syllable line, degenerate cases

## 2. API Response Models

- [x] 2.1 Update `models/types.py`: add `boundary` (list of `[x, y]` coordinate pairs) to `Line` model, add `boundary` to `Syllable` model, nest `syllables` under `Line` instead of flat list with `line_index`
- [x] 2.2 Remove top-level `syllables` from `RecognitionResponse`, update response to `{ lines: [...], neumes: [...] }`
- [x] 2.3 Update `ContributionAnnotations` and `LineInput`/`SyllableInput` models to use `boundary` polygon instead of `bbox`

## 3. Recognition Pipeline Integration

- [x] 3.1 Update `_generate_recognition_stream` in `api.py` to call polygon slicing after syllabification — slice each line's boundary polygon into per-syllable polygons using character cuts
- [x] 3.2 Wire polygon data into the nested response structure (lines with boundary + baseline, syllables with boundary)
- [x] 3.3 Handle region offset: translate polygon coordinates to full-image coordinates when a region crop is used

## 4. Text Masking from Polygons

- [x] 4.1 Add `mask_polygon_regions(image, polygons)` function to `pipeline/text_masking.py` that accepts a list of polygon coordinate lists and masks each with parchment color
- [x] 4.2 Write tests for `mask_polygon_regions`: multiple polygons, empty list, input image not modified

## 5. Contribution Storage

- [x] 5.1 Update `save_contribution` in `contribution/storage.py` to store the new annotation format (lines with boundary polygons, syllables with boundary polygons)
- [x] 5.2 Update `/contribute` endpoint in `api.py` to accept the new annotation structure

## 6. Training Export

- [x] 6.1 Update `_export_single_contribution` in `training/yolo_export.py`: remove `segment_image()` call, load syllable polygons from `annotations.json`, pass to `mask_polygon_regions()`
- [x] 6.2 Handle contributions with no syllable polygons (empty lines) — proceed without masking
- [x] 6.3 Update export tests to use new annotation format with polygon boundaries

## 7. Migration Script

- [x] 7.1 Create `scripts/migrate_contributions.py` with CLI entry point
- [x] 7.2 Implement pipeline re-run (segment + OCR) per contribution to obtain line boundaries and character cuts
- [x] 7.3 Implement matching logic: match stored syllable bboxes to Kraken lines by spatial overlap, then match individual syllables by text + position
- [x] 7.4 Implement polygon slicing for matched syllables and fallback (bbox-to-rectangle) for unmatched
- [x] 7.5 Implement backup (`annotations.json.bak`), idempotency check, and summary output
- [x] 7.6 Run migration on existing 4 contributions and verify results (N/A: contributions directory is empty)
