## Why

Users need a way to remove annotations they no longer want. Currently there's no delete functionality - once an annotation is created, it cannot be removed.

## What Changes

- Add keyboard shortcut (Delete/Backspace) to delete the currently selected annotation
- Add delete button (trash icon) in the InlineAnnotationEditor popover
- Both methods dispatch the existing `deleteAnnotation` action

## Capabilities

### New Capabilities
- `annotation-deletion`: Ability to delete annotations via keyboard shortcut or UI button

### Modified Capabilities
<!-- None - the deleteAnnotation action and reducer logic already exist, just not exposed to the user -->

## Impact

- `src/components/AnnotationCanvas.tsx`: Add keyboard handler for Delete/Backspace
- `src/components/InlineAnnotationEditor.tsx`: Add delete IconButton, new `onDelete` prop
- Undo/redo will work automatically (deletion creates a history entry)
