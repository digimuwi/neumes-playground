## Why

The recognition mode (neume/text/manual) is currently displayed as a conditional Chip in the toolbar that only appears when a non-manual mode is active, and can only be switched via keyboard shortcuts. This makes mode switching undiscoverable for mouse users and hides the current state when in manual mode.

## What Changes

- Replace the conditional recognition mode Chip with an always-visible `ToggleButtonGroup` showing all three modes (Neume | Text | Manual)
- Mode can now be switched by clicking the toggle buttons in addition to keyboard shortcuts
- Keyboard shortcuts change from toggle behavior to direct selection: `n` → neume, `t` → text, `m` → manual, `Escape` → manual (silent)
- Each toggle button label includes its keyboard hint: "Neume (n)", "Text (t)", "Manual (m)"

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `targeted-recognition`: Keyboard shortcuts change from toggle to direct-select behavior; toolbar display changes from conditional Chip to always-visible ToggleButtonGroup with mouse interaction

## Impact

- `src/components/Toolbar.tsx` — replace Chip with ToggleButtonGroup
- `src/components/AnnotationCanvas.tsx` — simplify keyboard handlers, add `m` shortcut
- `openspec/specs/targeted-recognition/spec.md` — update keyboard and toolbar requirements
