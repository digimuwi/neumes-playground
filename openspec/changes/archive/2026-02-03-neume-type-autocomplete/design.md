## Context

The `InlineAnnotationEditor` component currently uses MUI `<Select>` for neume type selection. This works but requires mouse interaction (click dropdown, scroll, click option). With 10 neume types currently and plans to expand, a keyboard-first approach scales better.

Current implementation (lines 142-158 of InlineAnnotationEditor.tsx):
- `<FormControl>` wrapping `<Select>` with `<MenuItem>` for each neume type
- Closes and commits on selection via `handleNeumeTypeChange`
- Auto-focuses via `selectRef` when `isNewlyCreated` is true

## Goals / Non-Goals

**Goals:**
- Enable keyboard-first neume type selection
- Prefix-based filtering as user types
- Preserve discoverability (show all options on focus)
- Maintain existing UX patterns (auto-focus on new, Escape to close)

**Non-Goals:**
- Fuzzy matching or substring search
- Searching by description text
- Custom neume type entry (must select from predefined list)
- Changes to the neume type data structure

## Decisions

### 1. Use MUI Autocomplete with `freeSolo={false}`

**Choice**: MUI `<Autocomplete>` in controlled mode, restricted to predefined options.

**Alternatives considered**:
- Custom autocomplete: More control but significant implementation effort
- Headless UI (Downshift): Good but adds dependency; MUI Autocomplete already available

**Rationale**: MUI Autocomplete is already available (part of MUI core), handles keyboard navigation, filtering, and accessibility out of the box.

### 2. Prefix filtering via custom `filterOptions`

**Choice**: Custom `filterOptions` that matches from the start of the neume name only.

**Rationale**: User requested prefix matching specifically. MUI's default is "contains" matching, so we need a custom filter.

```tsx
filterOptions={(options, { inputValue }) =>
  options.filter(opt =>
    opt.name.toLowerCase().startsWith(inputValue.toLowerCase())
  )
}
```

### 3. Show all options on focus with `openOnFocus`

**Choice**: Set `openOnFocus={true}` to show dropdown immediately when field receives focus.

**Rationale**: Preserves discoverability for users who don't know the neume names. They can still browse like the old dropdown, but power users can type to filter.

### 4. Commit on Enter, cancel preserves previous value

**Choice**:
- `onChange` handler commits selected value
- `onClose` with reason "escape" or "blur" preserves previous value
- Empty input on Enter keeps previous value

**Rationale**: Matches user expectations from exploration session. No "invalid state" possible.

## Risks / Trade-offs

**[Minor UX shift]** → Users accustomed to the dropdown might initially be confused by the text input appearance. Mitigated by showing all options on focus, which mimics dropdown behavior.

**[Focus management complexity]** → Auto-focus with `isNewlyCreated` needs to also open the dropdown. May need `setTimeout` or `autoFocus` prop on Autocomplete. Test thoroughly.
