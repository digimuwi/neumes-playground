## Why

The current neume type selector is a mouse-based dropdown that requires clicking and scrolling. As the neume vocabulary grows beyond the current 10 types, this becomes increasingly inefficient. An autocomplete input enables keyboard-first selection, improves accessibility, and scales better for power users working with larger neume sets.

## What Changes

- Replace MUI `<Select>` dropdown with MUI `<Autocomplete>` for neume type selection
- Add prefix-based filtering (type "cli" to find Clivis, Climacus)
- Show all options on focus for discoverability
- Keyboard navigation: arrow keys to select, Enter to confirm, Escape to cancel
- Empty/cancel behavior preserves previous value (default: Punctum for new annotations)

## Capabilities

### New Capabilities

- `neume-type-autocomplete`: Keyboard-first neume type selection with prefix filtering and autocomplete suggestions

### Modified Capabilities

<!-- No existing specs to modify -->

## Impact

- `src/components/InlineAnnotationEditor.tsx`: Replace Select with Autocomplete component
- No state changes required (same `neumeType` field, same update flow)
- No impact on undo/redo (annotation updates work the same way)
