## Context

The `useTextLines` hook already computes text lines by clustering syllables by Y position and fitting linear regressions to handle tilted handwriting. Each `TextLine` has:
- `slope`: tilt angle (from `y = mx + b`)
- `intercept`: baseline Y position
- `syllables`: annotations on that line

This data drives neume-to-syllable assignment and MEI export (`<lb>` elements), but users cannot currently see it. The canvas rendering loop in `AnnotationCanvas.tsx` draws: image → annotations → assignment curves → preview rectangle.

## Goals / Non-Goals

**Goals:**
- Visualize computed text line baselines on the canvas
- Show line numbers corresponding to MEI `<lb n="X"/>` elements
- Render tilted baselines following the regression slope
- Provide passive orientation (no interaction)

**Non-Goals:**
- Interactive line editing or manual correction
- Hover/click behavior on text lines
- Slope clamping or visual smoothing (show computed values honestly)
- Toggle visibility (always visible when syllables exist)

## Decisions

### 1. Rendering Layer Position

**Decision**: Draw text lines after the image, before annotations.

**Rationale**: Text lines are a background reference layer. Drawing them before annotations ensures they don't obscure syllable/neume rectangles or assignment curves.

**Alternatives considered**:
- After annotations: Would draw over rectangles, reducing clarity
- Separate canvas layer: Overkill for static visualization

### 2. Visual Style

**Decision**: Dashed purple lines (`rgba(147, 112, 219, 0.6)`) with circled line numbers.

**Rationale**:
- Dashed style indicates computed/derived (not user-drawn)
- Purple is distinct from existing colors (blue=syllables, red=neumes, green=preview, yellow=selected)
- Line numbers provide direct MEI correspondence

### 3. Line Extent Calculation

**Decision**: Extend from leftmost syllable's left edge to rightmost syllable's right edge, with small padding (0.01 normalized units).

**Rationale**: Shows the span of each line without extending arbitrarily. Padding prevents the line number from overlapping the first syllable.

### 4. Integration Approach

**Decision**: Call `useTextLines` directly in `AnnotationCanvas`, add drawing logic inline in the render `useEffect`.

**Rationale**:
- Hook already exists and is memoized
- Drawing is simple enough to inline (no need for separate hook)
- Follows existing pattern for assignment curves

## Risks / Trade-offs

**[Visual clutter on dense pages]** → Subtle color and dashed style minimize distraction. Could add toggle later if needed.

**[Single-syllable lines look odd]** → They inherit slope from neighbors (existing behavior). Visualization will show this honestly—if it looks wrong, the detection algorithm should be investigated.

**[Performance with many lines]** → Text lines are O(syllables), drawing is O(lines). Negligible compared to existing annotation rendering.
