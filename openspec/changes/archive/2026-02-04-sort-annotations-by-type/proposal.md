## Why

When annotating manuscripts, users typically work in two phases: first labeling all syllable text, then classifying all neumes. The current Tab navigation follows pure reading order (top-to-bottom, left-to-right), mixing syllables and neumes together. This forces users to constantly switch between text input and neume classification as they navigate, breaking their workflow.

## What Changes

- Tab/Shift+Tab navigation will sort annotations primarily by type (syllables first, then neumes), with reading order as the secondary sort
- This allows users to tab through all syllables first, then all neumes, matching the natural annotation workflow

## Capabilities

### New Capabilities

None - this modifies existing keyboard navigation behavior.

### Modified Capabilities

- `annotation-keyboard-navigation`: Reading order sort gains a primary sort by annotation type (syllable → neume)

## Impact

- `src/components/AnnotationCanvas.tsx`: The `sortAnnotationsByReadingOrder` function needs to incorporate type as the primary sort key
- No state changes, no API changes, no breaking changes
- Future annotation types should be added to a type priority list
