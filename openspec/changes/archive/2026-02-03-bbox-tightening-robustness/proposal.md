## Why

When selecting neume regions, the bounding box tightening sometimes reduces the selection to an invisibly small area (essentially 0 pixels). This happens when the Otsu threshold is too aggressive with faint ink, or when detected foreground is just a few noise pixels. Users lose their selection entirely.

## What Changes

- Bias the Otsu threshold slightly towards ink (flat offset, e.g., +5) so faint strokes are less likely to be classified as background
- Enforce a minimum bounding box size (4×4 pixels); if tightened result is smaller, return the original user selection
- Add 1-pixel padding around every tightened bbox (clamped to never exceed the original user selection)

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `bounding-box-tightening`: Add threshold bias, minimum size enforcement, and padding to tightening algorithm

## Impact

- `src/utils/imageProcessing.ts` - Modify `tightenRectangle` function and potentially add constants
- `src/components/AnnotationCanvas.tsx` - May need to apply threshold bias when calling tightening
