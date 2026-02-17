## 1. Setup

- [x] 1.1 Add `shapely` dependency to `pyproject.toml`

## 2. Core Implementation

- [x] 2.1 Create `pipeline/text_masking.py` with `mask_text_regions(image, segmentation)` function
- [x] 2.2 Implement per-polygon dilation via Shapely `buffer()` and sampling ring computation
- [x] 2.3 Implement local parchment color sampling (median of ring pixels per channel)
- [x] 2.4 Implement polygon fill with sampled color, handling edge cases (no lines, missing boundaries, edge clipping)

## 3. Tests

- [x] 3.1 Test that text polygon regions are filled and non-polygon pixels are unchanged
- [x] 3.2 Test that the input image is not modified (returned image is a copy)
- [x] 3.3 Test local color sampling: image with two distinct background colors produces per-polygon fill
- [x] 3.4 Test zero-lines segmentation returns image unchanged
- [x] 3.5 Test lines with empty/missing boundary polygons are skipped without error
- [x] 3.6 Test polygon near image edge (sampling ring clipped to bounds)
