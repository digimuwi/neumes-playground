## 1. Text Line Detection

- [x] 1.1 Create `src/hooks/useTextLines.ts` with types for TextLine (slope, intercept, syllables array)
- [x] 1.2 Implement syllable clustering by bottom Y with 0.03 threshold
- [x] 1.3 Implement linear regression fitting for multi-syllable clusters
- [x] 1.4 Implement slope inheritance for single-syllable clusters
- [x] 1.5 Sort text lines by intercept (top-to-bottom ordering)

## 2. Neume Assignment

- [x] 2.1 Create `src/hooks/useNeumeAssignment.ts` that takes annotations and returns Map<neumeId, syllableId>
- [x] 2.2 Implement band membership: find owning text line for each neume based on line equations
- [x] 2.3 Implement syllable selection: closest syllable to the left within the text line
- [x] 2.4 Implement exception: assign to leftmost syllable when neume is left of all syllables
- [x] 2.5 Memoize assignment computation with useMemo keyed on annotations array

## 3. Visualization Utilities

- [x] 3.1 Implement `closestPointOnRect(px, py, rect)` utility function
- [x] 3.2 Implement bezier curve control point calculation (40%/60% vertical split)
- [x] 3.3 Define curve style constants (normal: gray 0.4 opacity, highlighted: gray 0.8 opacity)

## 4. Canvas Rendering

- [x] 4.1 Integrate useNeumeAssignment hook in AnnotationCanvas
- [x] 4.2 Add curve drawing loop after annotation rendering in the canvas draw effect
- [x] 4.3 Implement normal curve rendering with bezier path and neutral styling
- [x] 4.4 Implement highlighted curve rendering when neume or syllable is selected
- [x] 4.5 Add hover state tracking for curve highlighting

## 5. Integration & Polish

- [x] 5.1 Verify curves update when annotations are added/moved/deleted
- [x] 5.2 Test with tilted text lines (verify slope calculation works)
- [x] 5.3 Test edge cases: neume left of all syllables, single syllable per line, no syllables
