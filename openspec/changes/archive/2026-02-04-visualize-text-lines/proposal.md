## Why

Users need visual orientation while annotating manuscripts and a way to understand how syllables are grouped into text lines. The computed text lines (which determine neume-to-syllable assignments and become `<lb>` elements in MEI export) are currently invisible—users can't verify or understand the grouping logic.

## What Changes

- Add visual rendering of text line baselines on the canvas
- Display tilted baselines that follow the linear regression slope computed by `useTextLines`
- Show circled line numbers at the start of each baseline (corresponding to MEI `<lb n="X"/>`)
- Render as a passive background layer (behind annotations, on top of image)

## Capabilities

### New Capabilities
- `text-line-visualization`: Renders computed text line baselines on the canvas with line numbers, showing the slope/tilt and extent of each detected line

### Modified Capabilities
<!-- None - this is purely additive visualization of existing computed data -->

## Impact

- `src/components/AnnotationCanvas.tsx`: Add text line drawing step in the render loop
- `src/hooks/useTextLines.ts`: Will be imported into AnnotationCanvas (already exists, no changes needed)
- Visual only—no changes to data model, state management, or undo/redo
