## 1. Polygon Clipping Utility

- [x] 1.1 Add `clip_polygon_below(polygon, y_threshold)` function to `seg_export.py` — removes vertices below `y_threshold`, interpolates new vertices where edges cross the threshold, returns a closed polygon
- [x] 1.2 Add `clip_polygon_above(polygon, y_threshold)` function — removes vertices above `y_threshold`, interpolates crossing edges, returns a closed polygon

## 2. Region Boundary Clipping Pass

- [x] 2.1 Refactor `build_pagexml()` to collect region data (boundary, element, type) into a list before writing XML, so a clipping pass can modify boundaries before they are serialized
- [x] 2.2 After building all regions, iterate adjacent pairs, detect vertical overlaps (region_i Y_max > region_j Y_min), compute `clip_y = (y_max + y_min) // 2`, and clip both boundaries
- [x] 2.3 When clipping a TextRegion, also clip the enclosed TextLine Coords identically

## 3. Verification

- [x] 3.1 Run the export on existing contributions and verify the output PageXML has no vertically overlapping regions
