## Why

When annotating neumes, users must manually select the neume type from a list. For manuscripts with many neumes, this is tedious and error-prone. The system already suggests syllable text based on Cantus Index; a similar suggestion mechanism for neume types would accelerate annotation workflows.

## What Changes

- Port the neume classification algorithms from `dudu.py` to TypeScript (skeletonization, stroke analysis, token matching)
- Run classification entirely client-side using the existing binarization infrastructure
- Display the top suggestion as ghost text in the neume type autocomplete
- Allow Tab/Enter to accept the suggestion (mirroring syllable suggestion UX)

## Capabilities

### New Capabilities
- `neume-classification`: Client-side TypeScript module that classifies neume images using skeletonization, stroke analysis, and lexicon matching
- `neume-type-suggestions`: Frontend integration that crops annotation regions, binarizes them, classifies locally, and displays suggestions as ghost text

### Modified Capabilities
_None_

## Impact

- New `src/utils/neumeClassifier.ts` with ported algorithms
- New `src/hooks/useNeumeSuggestion.ts` hook
- Modified `InlineAnnotationEditor.tsx` to show neume suggestions
- Modified `AnnotationCanvas.tsx` to wire up the hook
- No external dependencies or services required
