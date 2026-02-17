## Context

Currently, the annotation workflow requires users to look at the canvas to draw rectangles, then shift attention to the sidebar to edit annotation properties. The AnnotationEditor component lives in a fixed 320px sidebar alongside AnnotationList. This spatial disconnect slows down annotation work.

The canvas uses normalized coordinates (0-1) for annotations and supports zoom/pan. The popover must work correctly regardless of zoom level and pan position.

## Goals / Non-Goals

**Goals:**
- Inline editing experience: popover appears adjacent to the annotation being edited
- Smart positioning that avoids canvas edges
- Auto-dismiss on data entry completion
- Keyboard navigation through annotations
- Simpler layout with canvas taking full width

**Non-Goals:**
- Bulk editing of multiple annotations
- Drag-to-reposition annotations
- Export/import functionality (future work)

## Decisions

### 1. Popover implementation: MUI Popover vs custom positioned div

**Decision**: Use a custom absolutely-positioned div within the canvas container.

**Rationale**: MUI Popover uses portals and fixed positioning relative to viewport. Since we need to position relative to canvas coordinates (which change with zoom/pan), a custom solution inside the canvas container is simpler. We can compute screen coordinates from normalized annotation coords using the same transform logic already in AnnotationCanvas.

**Alternatives considered**:
- MUI Popover: Would require complex coordinate transforms and re-anchoring on zoom/pan
- MUI Popper: Same issues as Popover

### 2. Popover component location

**Decision**: Create `src/components/InlineAnnotationEditor.tsx` as a standalone component, rendered inside AnnotationCanvas container.

**Rationale**: Keeps AnnotationCanvas focused on drawing/interaction, while the editor component handles its own form logic. The parent provides position and annotation data.

### 3. Position calculation

**Decision**: Compute popover position in AnnotationCanvas using existing coordinate transform helpers. Pass screen-space position to InlineAnnotationEditor.

**Algorithm**:
```
1. Get annotation rect in normalized coords
2. Transform to screen coords using existing toScreenX/Y helpers
3. Preferred position: right edge of rect + 8px gap
4. If right edge + popover width > container width: position left of rect
5. Vertical: align top of popover with top of rect
6. If bottom of popover > container height: shift up to fit
```

Popover width: fixed 280px (accommodates neume dropdown comfortably)

### 4. State management for popover visibility

**Decision**: Derive popover visibility from existing state:
- `selectedAnnotationId !== null` means popover is open
- Selecting annotation (via click or Tab) opens popover
- Deselecting (via Escape, click outside, or data entry completion) closes it

No new state field needed. The `isNewlyCreated` flag continues to control auto-focus behavior.

### 5. Close triggers

**Decision**:
- **Syllable**: Close on Enter key in text field
- **Neume**: Close on dropdown selection (onChange event)
- **Both**: Close on Escape key or click outside popover/annotation

**Rationale**: Matches common inline-edit patterns. Enter commits text, selection commits choice.

### 6. Tab navigation order

**Decision**: Sort annotations by position: primary sort by Y (top to bottom), secondary sort by X (left to right). Use annotation center point for comparison.

```typescript
const sortedAnnotations = [...annotations].sort((a, b) => {
  const aY = a.rect.y + a.rect.height / 2;
  const bY = b.rect.y + b.rect.height / 2;
  if (Math.abs(aY - bY) > 0.02) return aY - bY; // ~2% threshold for "same row"
  return (a.rect.x + a.rect.width / 2) - (b.rect.x + b.rect.width / 2);
});
```

The 2% threshold groups annotations on roughly the same horizontal line.

### 7. Handling zoom/pan while popover is open

**Decision**: Re-render popover position on zoom/pan changes. Since AnnotationCanvas already re-renders on zoom/panX/panY changes, the popover position will update automatically if computed in the render function.

## Risks / Trade-offs

**[Popover obscures other annotations]** → Popover has higher z-index; user can close with Escape and pan if needed. Keeping popover compact (280px) minimizes occlusion.

**[Tab order threshold is arbitrary]** → 2% may not work for all manuscript layouts. Could be made configurable later if needed.

**[Click-outside detection complexity]** → Need to distinguish clicks on: other annotations (should select that one), canvas background (should deselect), popover itself (should not close). Will use event target checking.

**[Loss of annotation list overview]** → Users can no longer see all annotations at a glance. Acceptable trade-off for focused annotation workflow; export/review features can address this later.
