## Why

The current annotation editor lives in a fixed sidebar, far from the rectangle being annotated. This forces users to context-switch between where they're looking (the manuscript) and where they're typing (the sidebar). Moving the editor inline—appearing right next to the rectangle—keeps attention focused on the annotation work.

## What Changes

- **Remove sidebar entirely**: Delete AnnotationList and AnnotationEditor components from sidebar
- **Canvas takes full width**: Layout changes to give the canvas all available horizontal space
- **Inline popover editor**: A popover appears next to rectangles for editing, with:
  - Type toggle (syllable/neume radio buttons)
  - Text field (for syllables) or dropdown (for neumes)
  - Smart positioning: prefers right of rectangle, adapts when near canvas edges
- **Auto-close on completion**: Popover closes when Enter pressed (syllable) or neume type selected
- **Keyboard navigation**: Tab/Shift+Tab cycles through annotations in reading order (top-to-bottom, left-to-right)
- **Click to edit**: Clicking an existing rectangle opens its popover

## Capabilities

### New Capabilities

- `inline-annotation-popover`: Popover component that appears next to annotations for inline editing, with smart positioning logic and auto-close behavior
- `annotation-keyboard-navigation`: Tab/Shift+Tab cycling through annotations in reading order

### Modified Capabilities

- `rapid-annotation-input`: Auto-focus behavior now applies to inline popover instead of sidebar editor; sticky type inheritance unchanged

## Impact

- **Deleted files**: `src/components/AnnotationList.tsx`, `src/components/AnnotationEditor.tsx`
- **Modified files**: `src/App.tsx` (remove sidebar, full-width canvas), `src/components/AnnotationCanvas.tsx` (integrate popover, handle Tab navigation)
- **New files**: Inline popover component (location TBD in design)
- **State changes**: May need to track popover open/closed state; existing selection state reused
