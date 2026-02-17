## Context

The annotation tool currently treats syllables and neumes as independent rectangles. In medieval manuscripts, neumes are positioned above the syllables they belong to. Users need to see these relationships to understand and verify the musical structure.

The challenge: handwritten text lines often drift up or down across the page, so simple horizontal bands won't correctly group neumes with their syllables. We need a model that accounts for tilted text lines.

## Goals / Non-Goals

**Goals:**
- Automatically assign each neume to its owning syllable based on spatial relationships
- Handle tilted/drifting text lines common in handwritten manuscripts
- Visualize assignments with smooth bezier curves
- Recalculate assignments in real-time as annotations change

**Non-Goals:**
- Storing assignments in state (they are derived/computed)
- Manual override of automatic assignments
- Multi-line syllable handling (rare edge case)
- OCR or automatic neume/syllable detection

## Decisions

### 1. Text Line Model: Linear Regression per Cluster

**Decision**: Model each text line as `y = mx + b` fitted to syllable bottom positions.

**Alternatives considered**:
- Horizontal bands (fixed Y thresholds): Fails for tilted handwriting
- User-defined line regions: Too manual, poor UX
- Adaptive bands from syllable heights: Doesn't handle tilt

**Rationale**: Linear regression captures the natural drift of handwritten lines while remaining simple to compute. The bottom Y of syllables defines the baseline; neumes in the vertical band above belong to that line.

### 2. Clustering Threshold: 3% of Normalized Height

**Decision**: Syllables within 0.03 (normalized) vertical distance are clustered into the same line.

**Rationale**: Typical manuscripts have 4-8 text lines per page, making 3% a reasonable threshold. Can be tuned if needed.

### 3. Single-Syllable Lines: Inherit Slope

**Decision**: Lines with only one syllable inherit the slope from the nearest multi-syllable line.

**Alternatives considered**:
- Use slope = 0 (horizontal): Inconsistent with neighboring lines
- Use global average slope: Less accurate for local variation

**Rationale**: Neighboring lines in the same manuscript tend to have similar tilt. Inheriting maintains visual consistency.

### 4. Assignment Rule: Closest Left, Exception for Leftmost

**Decision**: Assign neume to the syllable whose center X is closest to and ≤ the neume's center X. Exception: if neume is left of all syllables, assign to the leftmost syllable.

**Rationale**: Neumes typically sit above or slightly right of their syllable. The exception handles edge cases where neumes precede the first syllable.

### 5. Computed vs Stored Assignments

**Decision**: Compute assignments on every render, do not store in state.

**Alternatives considered**:
- Store `assignedSyllableId` on neume annotations: Requires sync logic, migration

**Rationale**: Assignments are purely derived from geometry. Computing them avoids sync bugs and keeps state minimal. Performance is acceptable (O(n·m) where n=neumes, m=lines).

### 6. Visualization: Bezier Curves to Closest Edge

**Decision**: Draw quadratic bezier curves from neume center to the closest point on the syllable box edge.

**Curve control points**:
- Start: neume center `(nx, ny)`
- CP1: `(nx, ny + 0.4 * Δy)` — pulls curve down from neume
- CP2: `(ex, ny + 0.6 * Δy)` — pulls curve toward endpoint
- End: closest point on syllable rect `(ex, ey)`

**Styling**:
- Normal: `rgba(120, 120, 120, 0.4)`, lineWidth 1.5
- Highlighted (on hover/selection): `rgba(80, 80, 80, 0.8)`, lineWidth 2.5

### 7. Implementation Location: Custom Hook

**Decision**: Create `useNeumeAssignment` hook that takes annotations and returns a `Map<neumeId, syllableId>`.

**Rationale**: Separates assignment logic from rendering. Hook can memoize results for performance.

## Risks / Trade-offs

**[Performance on large annotation sets]** → Memoize with `useMemo`, recalculate only when annotations array changes. Linear regression is O(n) per cluster.

**[Edge case: neume exactly on line boundary]** → Use `<=` comparison consistently; document behavior.

**[Crossing text lines (unusual manuscript)]** → Sort lines by intercept; if lines cross, behavior may be unexpected. Accept as rare edge case.

**[Clustering threshold too strict/loose]** → Start with 3%, can expose as configurable later if needed.
