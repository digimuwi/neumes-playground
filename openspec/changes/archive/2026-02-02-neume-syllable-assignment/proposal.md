## Why

When annotating manuscript pages, neumes (musical notation symbols) need to be associated with the syllables they belong to. Currently, annotations are independent rectangles with no relationship between them. Users need to see which neumes belong to which syllables to understand the musical structure.

## What Changes

- Add automatic assignment of neumes to syllables based on spatial relationships
- Compute text line boundaries from syllable positions, accounting for tilted/drifting handwriting
- Assign each neume to the closest syllable "down and to the left" within its text line band
- Visualize assignments with bezier curves connecting neumes to their syllables
- Recalculate assignments dynamically whenever annotations change

## Capabilities

### New Capabilities

- `text-line-detection`: Cluster syllables into text lines based on bottom Y positions, fit linear models to handle tilted handwriting, define vertical bands for neume ownership
- `neume-assignment`: Assign each neume to a syllable based on text line membership and horizontal proximity (closest to the left, with exception for leftmost syllable when neume is left of all)
- `assignment-visualization`: Render bezier curves from neume centers to closest edge of assigned syllable boxes, with normal/highlighted states

### Modified Capabilities

<!-- No existing specs to modify -->

## Impact

- **State**: Assignment is computed/derived, not stored (no schema changes needed)
- **Canvas rendering**: New curve drawing logic in AnnotationCanvas
- **Performance**: Recalculation on every annotation change; needs efficient algorithm
- **Undo/redo**: No impact (assignments are derived from annotation positions)
