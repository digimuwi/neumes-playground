## Context

The segmentation training export (`seg_export.py`) generates PageXML files with alternating MusicRegion/TextRegion pairs — one per text line and its associated neumes. These regions systematically overlap by 20-50px vertically because user-drawn text boundaries extend beyond the text baseline into adjacent neume areas. Kraken trains a pixel-level classifier, so overlapping regions produce conflicting labels — the same pixels are simultaneously labeled "text" and "neume", degrading training.

## Goals / Non-Goals

**Goals:**
- Eliminate pixel-level label conflicts by clipping overlapping region boundaries at the vertical midpoint of the overlap zone
- Preserve the existing alternating neume-text structure and all type attributes

**Non-Goals:**
- Changing how baselines are computed
- Changing the neume-to-line grouping logic
- Changing region type attributes or element names
- Modifying Kraken's class mapping

## Decisions

**1. Clip at vertical midpoint of overlap zone**

After building all regions, iterate through adjacent region pairs. When a region's Y_max > the next region's Y_min (overlap), compute `clip_y = (region_y_max + next_region_y_min) // 2`. Clip the first region's boundary from below and the second region's boundary from above.

Alternative considered: clip at the baseline Y. Rejected because baselines can be irregular and the midpoint approach distributes the trim evenly between both regions.

**2. Clip polygons by horizontal scanline**

Boundary polygons are complex (100+ points). Clipping a polygon at a horizontal Y threshold: walk the polygon edges, keep vertices on the correct side, and interpolate crossing points on edges that span the threshold. This produces a clean polygon. For rectangular neume bounding boxes (4 points), the same algorithm works but could also just adjust Y coordinates.

**3. Clip after all regions are built**

Build all regions first (as today), then run a clipping pass over adjacent pairs. This keeps the core build logic simple and isolates the clipping concern.

**4. Also clip TextLine Coords to match**

When a TextRegion boundary is clipped, the enclosed TextLine Coords (which are identical to the TextRegion Coords) must be clipped the same way to stay consistent.

## Risks / Trade-offs

- [Polygon clipping edge cases] Very small overlaps or degenerate polygons could produce tiny sliver regions → Mitigation: only clip if overlap exceeds a minimum (e.g., 2px)
- [Baseline points outside clipped boundary] After clipping a TextRegion, some baseline points may fall outside the new boundary → Acceptable: Kraken uses baselines independently from region boundaries for baseline detection
