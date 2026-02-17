## Why

Wide neumes (e.g., compound neume groups) have bounding boxes whose center can drift into the next syllable's territory, causing incorrect syllable assignments. Since pen strokes begin on the left, the lower-left corner of a neume's bounding box is the most meaningful anchor point — it represents where the scribe placed the pen relative to the syllable being annotated.

## What Changes

- The neume-to-syllable assignment algorithm will use the neume's **lower-left coordinate** (`x`, `y + height`) instead of the bounding box center (`x + width/2`, `y + height/2`) for both vertical (text line) and horizontal (syllable) matching.
- The visual connection curve will originate from the neume's lower-left corner instead of its center.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `neume-assignment`: The anchor point for neume-to-syllable matching changes from bounding box center to lower-left corner.
- `assignment-visualization`: The curve origin point changes from neume center to neume lower-left corner.

## Impact

- `src/hooks/useNeumeAssignment.ts` — coordinate calculation for assignment logic
- `src/components/AnnotationCanvas.tsx` — curve start point for visual connections
