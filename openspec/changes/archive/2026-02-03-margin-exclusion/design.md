## Context

The bounding-box-tightening feature computes an Otsu threshold on image load and uses it to identify ink pixels during rectangle tightening. Medieval manuscript scans often have dark black margins (scanner bed, book binding shadows) that create a trimodal histogram instead of the expected bimodal distribution, causing Otsu to select a poor threshold.

Current state:
- `computeOtsuThreshold(imageData)` operates on all pixels
- `tightenRectangle(rect, imageData, threshold)` considers any pixel darker than threshold as foreground

## Goals / Non-Goals

**Goals:**
- Detect when an image has black margins
- Exclude margin pixels from Otsu threshold computation
- Exclude margin pixels from foreground detection during tightening
- Preserve current behavior for images without margins

**Non-Goals:**
- Adaptive margin threshold detection (using fixed cutoff of 30)
- Spatial detection of margin regions (using intensity-only approach)
- Removing or cropping margins from the displayed image

## Decisions

### Decision 1: Fixed intensity cutoff for margin detection

**Choice**: Use a fixed intensity cutoff of 30 to identify margin pixels.

**Alternatives considered**:
- Adaptive detection via histogram valley finding: More robust but adds complexity
- Spatial edge detection: Would detect page boundaries but overkill for this use case

**Rationale**: Margins are described as "solid black" which means intensity values near 0. A fixed cutoff of 30 provides clear separation from parchment (typically 150+) and ink (typically 50-100). Simple and predictable.

### Decision 2: Percentage threshold for margin presence

**Choice**: Consider margins present if >1% of pixels have intensity < 30.

**Rationale**: Small amounts of very dark pixels could be ink. 1% is enough to indicate significant margin area while avoiding false positives from dark ink spots.

### Decision 3: Band-based foreground detection

**Choice**: Define foreground as `marginThreshold ≤ gray < otsuThreshold` instead of just `gray < otsuThreshold`.

**Alternatives considered**:
- Masking margin regions spatially: Would require connected component analysis
- Pre-cropping image: Would change coordinate system, breaking normalized coordinates

**Rationale**: Simple intensity band check handles the case where user draws a rectangle overlapping a margin. Margin pixels won't be counted as ink.

### Decision 4: Return both thresholds from detection

**Choice**: Image load returns both `marginThreshold` (0 or 30) and `otsuThreshold`. Both are passed to tightening.

**Rationale**: Keeps the logic centralized. When no margins detected, marginThreshold=0 makes the band check equivalent to the original simple check.

## Risks / Trade-offs

**[Risk] Very dark ink might be excluded** → Mitigated by low cutoff (30). Manuscript ink is typically 50-100, well above the cutoff.

**[Risk] Some scans have gray margins, not black** → Current approach won't detect them. Could revisit with adaptive detection if this becomes a problem.

**[Trade-off] Fixed vs adaptive cutoff** → Chose simplicity. Can be made configurable or adaptive later if needed.
