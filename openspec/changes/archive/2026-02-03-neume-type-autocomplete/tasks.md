## 1. Replace Select with Autocomplete

- [x] 1.1 Import `Autocomplete` from MUI and remove unused `Select`, `MenuItem`, `InputLabel` imports
- [x] 1.2 Replace `<FormControl>/<Select>` block with `<Autocomplete>` component
- [x] 1.3 Configure `options` prop with `neumeTypes` array and `getOptionLabel` for display

## 2. Implement Filtering and Selection Behavior

- [x] 2.1 Add custom `filterOptions` for prefix-only matching (case-insensitive)
- [x] 2.2 Set `openOnFocus={true}` to show all options when input receives focus
- [x] 2.3 Configure `onChange` to call `onNeumeTypeChange` and `onClose` on valid selection
- [x] 2.4 Handle empty/cancelled input to preserve previous neume type value

## 3. Keyboard and Focus Management

- [x] 3.1 Ensure auto-focus works with `isNewlyCreated` flag (input focuses and dropdown opens)
- [x] 3.2 Verify Escape key closes editor via existing `handleKeyDown` listener
- [x] 3.3 Test arrow key navigation and Enter to confirm selection
