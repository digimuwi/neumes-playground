## Why

Annotating manuscript pages requires creating many annotations in quick succession. The current workflow requires manually clicking the text input field after each rectangle is drawn, creating friction that slows down batch annotation work.

## What Changes

- Auto-focus the appropriate input field (syllable text or neume dropdown) when a new annotation is created
- New annotations inherit their type from the most recently created annotation ("sticky type")
- First annotation defaults to syllable (current behavior preserved)
- User can still manually switch type via radio buttons at any time

## Capabilities

### New Capabilities
- `rapid-annotation-input`: Auto-focus and sticky type behavior for faster annotation workflow

### Modified Capabilities
<!-- None - this is additive behavior that doesn't change existing spec requirements -->

## Impact

- `src/components/AnnotationEditor.tsx`: Add refs for focus management, track when annotation is newly created vs selected
- `src/state/actions.ts`: Potentially pass last annotation type when creating new annotations
- `src/hooks/useCanvasDrawing.ts`: May need to signal "newly created" vs "clicked existing"
