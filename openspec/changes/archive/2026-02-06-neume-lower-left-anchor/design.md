## Context

Neume-to-syllable assignment currently uses the center of each neume's bounding box as the anchor point for both vertical (text line) and horizontal (syllable) matching. Wide neumes — especially compound neume groups — have centers that drift rightward into adjacent syllables, producing incorrect assignments. Since pen strokes originate on the left, the lower-left corner of the bounding box better represents the scribe's intended syllable association.

The assignment logic lives in `useNeumeAssignment.ts` and the visual curve rendering in `AnnotationCanvas.tsx`. Both compute the neume center independently.

## Goals / Non-Goals

**Goals:**
- Use the neume's lower-left coordinate (`x`, `y + height`) as the anchor for assignment and curve rendering
- Improve assignment accuracy for wide neumes

**Non-Goals:**
- Changing the syllable-side coordinate logic (already uses left edge for comparison)
- Changing text line detection or clustering
- Changing curve styling or shape

## Decisions

### Use lower-left corner for both vertical and horizontal matching

**Decision:** Replace `(x + width/2, y + height/2)` with `(x, y + height)` everywhere the neume anchor is computed.

**Rationale:** The lower-left point represents where the pen stroke begins. Using the bottom Y tightens association with the text line below. Using the left X prevents wide strokes from drifting into adjacent syllable territory.

**Alternatives considered:**
- *Bottom-center* (`x + width/2`, `y + height`): Fixes vertical but not horizontal drift. Rejected because the horizontal correction is the primary motivation.
- *Configurable anchor point*: Over-engineered for this use case. Lower-left is the correct musicological choice.

### Same anchor for assignment logic and curve origin

**Decision:** The curve rendering in `AnnotationCanvas.tsx` will use the same lower-left coordinate as the assignment algorithm.

**Rationale:** The visual connection should reflect the actual assignment logic. If the curve starts from center while assignment uses lower-left, the visual feedback misrepresents the computation.

## Risks / Trade-offs

- **Small neumes shift slightly:** For small, narrow neumes the difference between center and lower-left is minimal. No practical risk — lower-left is still correct. → No mitigation needed.
- **Curve aesthetics:** Curves originating from lower-left instead of center may look slightly different. → The `closestPointOnRect` endpoint and bezier control points still produce smooth arcs.
