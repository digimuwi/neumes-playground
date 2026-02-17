## Why

Currently, annotations can only be selected and deleted one at a time. When users need to remove multiple annotations (e.g., clearing a section or fixing batch mistakes), they must click and delete each one individually—tedious for large corrections.

## What Changes

- **Multi-selection support**: Users can select multiple annotations simultaneously using standard platform conventions:
  - Cmd/Ctrl+Click to toggle annotations in/out of selection
  - Cmd/Ctrl+A to select all annotations
  - Click on empty canvas or press Escape to deselect all
  - Plain click selects only that annotation (clearing others)
- **Batch deletion**: Delete/Backspace key removes all selected annotations at once
- **Editor visibility**: Inline editor only appears when exactly one annotation is selected (hidden for multi-select)
- **Tab navigation**: Clears multi-selection and selects the next annotation in reading order

## Capabilities

### New Capabilities
- `multi-select`: Multi-annotation selection model with standard keyboard/mouse interactions and batch operations

### Modified Capabilities
<!-- No existing spec-level requirements are changing - this is additive behavior -->

## Impact

- **State**: `selectedAnnotationId: string | null` → `selectedAnnotationIds: Set<string>`
- **Components**: AnnotationCanvas, InlineAnnotationEditor, useCanvasDrawing hook
- **Undo/Redo**: Batch delete must be a single atomic history entry
