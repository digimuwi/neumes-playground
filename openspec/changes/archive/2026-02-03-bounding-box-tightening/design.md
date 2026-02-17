## Context

Users draw bounding boxes around neumes and syllables on manuscript images. These selections are typically slightly larger than the actual ink content, requiring manual adjustment or resulting in imprecise annotations.

The application uses normalized coordinates (0-1) for all rectangles and renders via the Canvas API. Image data is available as a base64 data URL stored in React state.

## Goals / Non-Goals

**Goals:**
- Automatically tighten user-drawn rectangles to fit actual ink content
- Compute threshold once per image (not per rectangle) for performance
- Preserve existing behavior when no ink content is detected
- Work within the existing normalized coordinate system

**Non-Goals:**
- Noise filtering or morphological operations (small punctums must be preserved)
- Expanding rectangles (only shrinking)
- User-configurable threshold or manual tightening controls
- Local/adaptive thresholding (global Otsu is sufficient for consistent manuscript ink)

## Decisions

### Decision 1: Global Otsu threshold computed once on image load

**Choice**: Compute Otsu threshold on the full image when loaded, cache it, and reuse for all rectangle tightening operations.

**Alternatives considered**:
- Local Otsu per selection: More adaptive but unstable when selection contains mostly background
- Adaptive thresholding (Sauvola/Niblack): More robust to varying backgrounds but unnecessary complexity for consistent manuscript ink

**Rationale**: Medieval manuscripts have consistent ink darkness within a page. Global Otsu provides stable threshold that won't mistake parchment shade variations for content.

### Decision 2: Tightening in handleRectangleDrawn before annotation creation

**Choice**: Apply tightening in `AnnotationCanvas.tsx`'s `handleRectangleDrawn` callback, before dispatching `ADD_ANNOTATION`.

**Alternatives considered**:
- Tightening in the drawing hook: Would require passing image data into `useCanvasDrawing`
- Tightening in the reducer: Would mix presentation logic with state management

**Rationale**: `AnnotationCanvas` already has access to image data and is the natural integration point between user interaction and state updates.

### Decision 3: Pure utility functions in src/utils/imageProcessing.ts

**Choice**: Create stateless utility functions:
- `computeOtsuThreshold(imageData: ImageData): number`
- `tightenRectangle(rect: Rectangle, imageData: ImageData, threshold: number): Rectangle`

**Rationale**: Keeps image processing logic testable and separate from React component concerns. Functions operate on standard Canvas API types (`ImageData`).

### Decision 4: Return original rectangle when no foreground detected

**Choice**: If binarization yields no foreground pixels, return the original rectangle unchanged.

**Rationale**: User explicitly selected that region; returning empty or failing would be worse UX.

## Risks / Trade-offs

**[Risk] Otsu may fail on low-contrast images** → The algorithm maximizes inter-class variance, so it will always find *some* threshold. For low-contrast images, results may be suboptimal but not catastrophic (original rectangle preserved if no foreground detected).

**[Risk] Small content appears as noise** → No mitigation. By design, we don't filter small content because it might be a legitimate punctum. User drew the box there intentionally.

**[Trade-off] Global vs local threshold** → We sacrifice adaptability for stability. If future manuscripts have significant ink variation across a page, we may need to revisit this.
