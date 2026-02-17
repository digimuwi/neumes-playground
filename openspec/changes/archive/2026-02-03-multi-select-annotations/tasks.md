## 1. State Layer Changes

- [x] 1.1 Update `AppState` type: replace `selectedAnnotationId: string | null` with `selectedAnnotationIds: Set<string>`
- [x] 1.2 Add `SELECT_ANNOTATIONS` action (takes `string[]`, replaces entire selection)
- [x] 1.3 Add `TOGGLE_ANNOTATION_SELECTION` action (adds/removes single ID from set)
- [x] 1.4 Add `DELETE_ANNOTATIONS` action (takes `string[]`, removes all in single history entry)
- [x] 1.5 Update existing `SELECT_ANNOTATION` usages to use new actions
- [x] 1.6 Update localStorage persistence to serialize/deserialize Set as Array

## 2. Canvas Interaction

- [x] 2.1 Detect Cmd/Ctrl modifier in click handler (`event.metaKey || event.ctrlKey`)
- [x] 2.2 Implement plain click: select only clicked annotation (clear others)
- [x] 2.3 Implement Cmd/Ctrl+click: toggle clicked annotation in selection
- [x] 2.4 Implement click on empty canvas: deselect all
- [x] 2.5 Add Cmd/Ctrl+A keyboard handler to select all annotations
- [x] 2.6 Update Escape handler to deselect all

## 3. Batch Deletion

- [x] 3.1 Update Delete/Backspace handler to dispatch `DELETE_ANNOTATIONS` with all selected IDs
- [x] 3.2 Verify undo restores all deleted annotations atomically

## 4. Editor Visibility

- [x] 4.1 Update `InlineAnnotationEditor` to only render when `selectedAnnotationIds.size === 1`
- [x] 4.2 Pass the single selected ID to editor when size is 1

## 5. Tab Navigation

- [x] 5.1 Update Tab handler to clear selection and select next annotation in reading order
- [x] 5.2 Update Shift+Tab handler similarly for previous annotation

## 6. Visual Rendering

- [x] 6.1 Update canvas rendering to draw yellow border on all annotations in `selectedAnnotationIds`
