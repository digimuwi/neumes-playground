## 1. Assignment Logic

- [x] 1.1 In `src/hooks/useNeumeAssignment.ts`, change neume anchor from center (`x + width/2`, `y + height/2`) to lower-left (`x`, `y + height`) in `computeNeumeAssignments()`
- [x] 1.2 Verify `findClosestSyllable` works correctly with the new lower-left X (the `s.rect.x <= neumeX` comparison already uses syllable left edge)

## 2. Curve Rendering

- [x] 2.1 In `src/components/AnnotationCanvas.tsx`, change the curve start point from neume center to lower-left (`rect.x`, `rect.y + rect.height`) in the assignment curve drawing section
