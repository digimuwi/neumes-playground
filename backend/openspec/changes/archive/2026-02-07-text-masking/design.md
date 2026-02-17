## Context

The backend is being restructured to replace Kraken-based neume detection with YOLOv8 object detection. The text masking module is the first piece of this new pipeline. It sits between Kraken segmentation and YOLO inference: Kraken provides text boundary polygons, this module erases text from the image, and YOLO (Change 4) will detect neumes on the cleaned result.

Kraken's `blla.segment()` returns a `Segmentation` object whose `.lines` each have a `.boundary` — a polygon (list of `(x, y)` tuples) tightly wrapping the text. These polygons are already used in the codebase for computing line bounding boxes (`api.py:_compute_line_bbox`).

## Goals / Non-Goals

**Goals:**
- Provide a `mask_text_regions(image, segmentation)` function that erases text from an RGB image
- Fill masked regions with locally-sampled parchment color (not flat white)
- Handle edge cases: zero lines, polygons near image edges, images with varying parchment color
- Keep the module self-contained — no ML dependencies, just PIL and numpy

**Non-Goals:**
- Neume detection (Change 4)
- API integration (Change 5)
- Handling neumes that overlap with text boundary polygons (acceptable loss — YOLO tolerates partial occlusion)
- Performance optimization for batch processing (single-image is sufficient)

## Decisions

### 1. Per-polygon local color sampling via dilation

**Decision**: For each text polygon, dilate it slightly outward, sample pixel colors in the ring between the original and dilated boundary, and fill with the median color.

**Why not flat white**: White rectangles are artificial features that YOLO could learn to associate with text regions. Using local parchment color produces natural-looking masked images.

**Why not global median**: Manuscripts have uneven parchment color due to aging, stains, and lighting gradients. A single fill color would create visible patches.

**Why dilation ring**: It gives a clean, consistent sampling region around each polygon. The ring captures the parchment immediately adjacent to the text — the most representative background.

**Alternative considered**: Sampling random points outside all polygons. Rejected because it mixes distant regions with different parchment tones.

**Dilation amount**: A few pixels (3-5px) is sufficient. The ring only needs enough pixels for a reliable median. This is not a tunable hyperparameter — it just needs to be "enough to sample parchment."

### 2. Implementation with numpy array operations

**Decision**: Convert the PIL Image to a numpy array, use PIL's `ImageDraw` to create polygon masks, use numpy boolean indexing for sampling and filling.

**Rationale**: PIL's `ImageDraw.polygon()` handles arbitrary polygon rasterization correctly. Numpy gives fast array operations for median computation and bulk fill. Both are already in the dependency tree.

**Flow**:
1. Convert image to numpy array (H, W, 3)
2. For each line's boundary polygon:
   a. Rasterize original polygon to a binary mask
   b. Rasterize dilated polygon to a binary mask
   c. Sampling ring = dilated mask AND NOT original mask
   d. Sample pixels in the ring, compute per-channel median
   e. Fill original polygon region with the median color
3. Convert back to PIL Image

### 3. Polygon dilation via Shapely

**Decision**: Use Shapely's `Polygon.buffer()` for dilation.

**Why**: Implementing correct polygon dilation (Minkowski sum) from scratch is error-prone. Shapely handles convex/concave polygons, self-intersections, and edge clipping correctly. It's a lightweight, well-tested geometry library.

**Alternative considered**: Manual vertex offsetting. Rejected — breaks on concave polygons and sharp angles.

### 4. Function signature follows existing pipeline patterns

**Decision**: The function takes a PIL `Image.Image` and a Kraken `Segmentation`, returns a PIL `Image.Image`. This mirrors the existing pipeline functions (`segment_image`, `recognize_lines`) that work with PIL images and Kraken types.

```python
def mask_text_regions(image: Image.Image, segmentation: Segmentation) -> Image.Image:
```

The function returns a new image — it does not modify the input.

## Risks / Trade-offs

**[Risk] Neumes partially inside text boundary polygons** → Accept. Kraken's boundary polygons wrap text tightly. Neumes in the interlinear space are almost always outside. Any neumes clipped at polygon edges will be partially visible — YOLO handles partial occlusion well.

**[Risk] Shapely as new dependency** → Acceptable. Shapely is a standard, well-maintained geometry library. It's the only clean way to dilate arbitrary polygons. It adds ~5MB to the environment.

**[Risk] Sampling ring has too few pixels near image edges** → Fall back to global image median for that polygon. If the dilated polygon extends beyond the image boundary, clip it. If the ring after clipping has fewer than some minimum number of pixels, use a broader sampling strategy (e.g., median of all non-text pixels in the polygon's bounding box).

**[Trade-off] Per-polygon processing is sequential** → For a single manuscript image with ~20 lines, this takes negligible time compared to Kraken segmentation and YOLO inference. No parallelization needed.
