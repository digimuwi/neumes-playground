## Context

The current `tightenRectangle` function finds foreground pixels within a user selection and shrinks the bbox to fit them exactly. This works well for clear ink, but fails in edge cases:

1. **Faint ink**: Otsu threshold may classify light strokes as background
2. **Noise detection**: A few stray pixels may produce a tiny bbox (e.g., 2×1 pixels)
3. **Tight fit**: No breathing room around detected content

Current flow in `imageProcessing.ts`:
- `computeOtsuThreshold()` finds optimal threshold
- `tightenRectangle()` scans for pixels where `marginThreshold ≤ gray < otsuThreshold`
- Returns bbox of detected pixels, or original rect if none found

## Goals / Non-Goals

**Goals:**
- Prevent empty/invisible selections from threshold being too aggressive
- Ensure tightened boxes are always usably sized
- Add small padding for visual clarity without exceeding user's original selection

**Non-Goals:**
- Changing the fundamental tightening algorithm
- Adding user-configurable threshold parameters
- Modifying margin detection behavior

## Decisions

### Decision 1: Apply flat offset to Otsu threshold

**Choice**: Add a constant offset (e.g., +5) to the computed Otsu threshold.

**Rationale**: A flat offset is simpler and more predictable than a percentage. With typical manuscript images having thresholds around 140-180, +5 represents roughly 3% shift, enough to catch faint ink without dramatically affecting normal cases.

**Alternative considered**: Multiplicative factor (×1.05). Rejected because the effect scales with threshold value, making it harder to reason about.

**Where to apply**: In `AnnotationCanvas.tsx` when passing threshold to `tightenRectangle`, keeping the core function pure.

### Decision 2: Enforce minimum bbox size in pixels

**Choice**: If tightened bbox is smaller than 4×4 pixels, return the original user selection.

**Rationale**:
- Minimum enforced in pixel space (not normalized) because "too small" is about actual rendered size
- 4×4 is small enough to preserve tiny punctum neumes but large enough to reject noise
- Returning original rect (rather than expanding) is simpler and respects user intent

**Where to apply**: Inside `tightenRectangle`, before converting back to normalized coordinates.

### Decision 3: Add 1-pixel padding, clamped to original rect

**Choice**: Expand the tightened bbox by 1 pixel on each side, but never exceed the original user selection.

**Rationale**:
- 1px padding provides minimal breathing room without bloat
- Clamping ensures the final result is always ≤ the user's original selection (a core invariant)
- Applied after minimum size check so tiny noise can still be rejected

**Where to apply**: Inside `tightenRectangle`, after computing the tight bbox and before minimum size check.

## Risks / Trade-offs

**Threshold bias may include parchment noise** → Mitigated by keeping offset small (+5). Can be tuned if issues arise.

**Minimum size may reject valid tiny neumes** → 4×4 is conservative; even the smallest punctum should exceed this. If not, the minimum can be reduced.

**Padding may look inconsistent with zoom** → At 1px, this is imperceptible at most zoom levels. Acceptable trade-off for robustness.
