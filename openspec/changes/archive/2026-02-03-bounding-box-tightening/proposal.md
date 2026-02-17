## Why

When users draw bounding boxes around neumes or syllables, the selection is typically slightly larger than the actual content. This requires manual adjustment or results in imprecise annotations. Automatic tightening would improve annotation accuracy and speed up the workflow.

## What Changes

- Add automatic bounding box tightening when rectangles are drawn
- Compute a global Otsu threshold when an image is loaded
- Shrink (never expand) drawn rectangles to fit the actual ink content
- Keep original rectangle if no foreground content is detected

## Capabilities

### New Capabilities
- `bounding-box-tightening`: Automatically shrinks user-drawn rectangles to fit the actual ink content using Otsu-based binarization

### Modified Capabilities
<!-- None - this is additive behavior that doesn't change existing spec requirements -->

## Impact

- `src/utils/imageProcessing.ts` - New file for Otsu threshold computation and rectangle tightening
- `src/components/AnnotationCanvas.tsx` - Integration point: compute threshold on image load, apply tightening before creating annotations
- Undo/redo unaffected (tightened rectangles stored like any other annotation)
- Normalized coordinate system preserved (tightening works in normalized space)
