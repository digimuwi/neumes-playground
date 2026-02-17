## Context

Recognition mode (neume/text/manual) is currently managed as React state in `AppProvider` via `useState<RecognitionMode>`. The Toolbar displays a conditional `Chip` when mode is non-manual, and keyboard shortcuts in `AnnotationCanvas` toggle modes. MUI's `ToggleButtonGroup` is already used in the codebase (training dialog) so the pattern is established.

## Goals / Non-Goals

**Goals:**
- Replace the conditional Chip with an always-visible ToggleButtonGroup for mode switching
- Support both mouse clicks and keyboard shortcuts for mode selection
- Change keyboard behavior from toggle (press again → manual) to direct selection

**Non-Goals:**
- Changing recognition backend behavior or mode semantics
- Moving `recognitionMode` state into the reducer/history (it's ephemeral UI state, not document state)

## Decisions

**1. ToggleButtonGroup with `exclusive` mode**
The MUI `ToggleButtonGroup` with `exclusive` prop ensures exactly one mode is always selected — there's no "nothing selected" state. This matches the requirement that manual is always the fallback. The `value` prop is controlled by `recognitionMode` from context, and `onChange` calls `setRecognitionMode`.

*Alternative*: Three separate `ToggleButton` components with manual active tracking — rejected because `ToggleButtonGroup` handles this natively and is already used in the training dialog.

**2. Keyboard shortcuts as direct selection, not toggles**
`n` always sets neume, `t` always sets text, `m` always sets manual, `Escape` also sets manual. This is simpler logic (no conditional toggling) and more predictable for users.

**3. Button labels include key hints**
Labels: "Neume (n)", "Text (t)", "Manual (m)". This makes keyboard shortcuts discoverable without a separate help reference.

**4. Styling: `size="small"` in the AppBar**
Matches the compact toolbar aesthetic. The ToggleButtonGroup will sit in the same position where the Chip was, between the Recognize Page button and the Cantus ID search button.

## Risks / Trade-offs

- **Slightly more visual weight** — The always-visible ToggleButtonGroup takes more space than the conditional Chip. → Acceptable because discoverability is the goal.
- **`m` key could conflict with future shortcuts** → Low risk; `m` for "manual" is intuitive and no current conflict exists.
