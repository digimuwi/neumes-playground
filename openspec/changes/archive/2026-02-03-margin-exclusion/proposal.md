## Why

Medieval manuscript scans often include dark black margins from the scanner bed or book binding shadows. These margins skew the Otsu threshold calculation, causing poor ink detection and incorrect bounding box tightening.

## What Changes

- Detect presence of black margins by analyzing the histogram for a significant peak in the very dark range (intensity < 30)
- Exclude margin pixels from Otsu threshold computation when margins are detected
- Exclude margin pixels from foreground detection during rectangle tightening
- No change in behavior for scans without margins

## Capabilities

### New Capabilities
<!-- None - this modifies an existing capability -->

### Modified Capabilities
- `bounding-box-tightening`: Otsu threshold computation and foreground detection now exclude black margin pixels when margins are detected

## Impact

- `src/utils/imageProcessing.ts` - Modify `computeOtsuThreshold` to accept optional min intensity, modify `tightenRectangle` to accept margin threshold
- `src/components/AnnotationCanvas.tsx` - Detect margins and pass both thresholds
