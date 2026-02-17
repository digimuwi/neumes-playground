## Context

Currently, `sortAnnotationsByReadingOrder()` in `AnnotationCanvas.tsx` sorts annotations by vertical position (primary) and horizontal position (secondary), giving a top-to-bottom, left-to-right reading order. Tab navigation uses this sorted list to cycle through annotations.

Users annotate in phases: first labeling syllable text, then classifying neumes. The current mixed ordering disrupts this workflow.

## Goals / Non-Goals

**Goals:**
- Primary sort by annotation type (syllables first, neumes second)
- Preserve reading order as secondary sort within each type
- Support future annotation types via an extensible priority list

**Non-Goals:**
- Changing the reading order algorithm itself
- Adding UI to customize sort order
- Changing any other navigation behavior

## Decisions

### Decision 1: Type priority as a constant array

Define `TYPE_PRIORITY: AnnotationType[] = ['syllable', 'neume']` at module level.

**Rationale**: Simple, explicit, easy to extend. Adding a new type means appending to the array. Unknown types sort after known types.

**Alternatives considered**:
- Numeric priority field on annotations: Over-engineered for current needs
- Hardcoded comparison: Less maintainable when types are added

### Decision 2: Modify existing sort function in place

Rename `sortAnnotationsByReadingOrder` to `sortAnnotationsForCycling` and add type comparison as primary sort key.

**Rationale**: Single location, minimal diff, clear intent in new name.

**Alternatives considered**:
- Separate sort function: Unnecessary abstraction for this use case
- Compose two sorts: Less efficient, harder to reason about

## Risks / Trade-offs

**[Risk] Users expect pure reading order** → The change is intentional to match workflow. Help text already says "next annotation" without specifying order.

**[Trade-off] Type not in priority list** → Falls back to end of list. Defensive but could surprise developers adding new types who forget to update the array.
