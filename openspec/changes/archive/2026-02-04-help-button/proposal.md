## Why

Researchers unfamiliar with power-user conventions struggle to discover the app's navigation and annotation shortcuts. Key features like zoom/pan, tab cycling, and shift-drag OCR go unused because they're not visible anywhere in the UI.

## What Changes

- Add a floating help button (MUI Fab) in the bottom-right corner of the canvas
- Clicking the button opens a compact MUI Dialog showing all keyboard shortcuts and features
- Add `?` keyboard shortcut to trigger the help dialog
- Organize help content by task: navigation, annotation cycling, drawing/OCR, undo/redo
- Include documentation of non-obvious features: neume-to-syllable assignment curves, auto-tightening bounding boxes, editor suggestions

## Capabilities

### New Capabilities
- `help-dialog`: Floating help button and keyboard shortcut reference dialog

### Modified Capabilities
<!-- None - this is purely additive UI that doesn't change existing behavior -->

## Impact

- New component: `HelpButton.tsx` (Fab + Dialog)
- Modify: `App.tsx` or `AnnotationCanvas.tsx` to include the help button
- Modify: Keyboard event handling to capture `?` key
- No changes to state management, annotations, or existing shortcuts
