## 1. Setup

- [x] 1.1 Import `useTextLines` hook in `AnnotationCanvas.tsx`
- [x] 1.2 Add color constants for text line visualization (purple dashed style)

## 2. Core Implementation

- [x] 2.1 Call `useTextLines` to get computed text lines from annotations
- [x] 2.2 Create helper function to calculate line extent (leftmost to rightmost syllable with padding)
- [x] 2.3 Create helper function to draw a single text line baseline (tilted dashed line)
- [x] 2.4 Create helper function to draw circled line number at baseline start

## 3. Canvas Integration

- [x] 3.1 Add text line drawing step in render useEffect (after image, before annotations)
- [x] 3.2 Loop through text lines and render each baseline with line number

## 4. Verification

- [ ] 4.1 Test with multiple text lines - verify baselines appear with correct tilt
- [ ] 4.2 Test with single-syllable lines - verify inherited slope displays correctly
- [ ] 4.3 Test with no syllables - verify no baselines are rendered
- [ ] 4.4 Test that line numbers match expected MEI export order (top-to-bottom)
