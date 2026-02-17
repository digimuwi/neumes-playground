## 1. State Management

- [x] 1.1 Add `metadata` field to `AppState` interface in `src/state/types.ts`
- [x] 1.2 Add `SET_METADATA` action type to `Action` union in `src/state/types.ts`
- [x] 1.3 Handle `SET_METADATA` action in reducer (`src/state/reducer.ts`)
- [x] 1.4 Verify metadata persists to localStorage and restores on reload

## 2. Cantus Lookup Service

- [x] 2.1 Create `collectQueryText()` function to gather syllable text in reading order
- [x] 2.2 Create `lookupCantusId()` function that uses `fetchChants()` and returns results
- [x] 2.3 Create `useCantusLookup` hook that manages lookup state (loading, results, error)

## 3. Selection Dialog Component

- [x] 3.1 Create `CantusSelectionDialog` component with Material-UI Dialog
- [x] 3.2 Display list of matches with cid, genre, and text preview
- [x] 3.3 Implement radio button selection and confirm/cancel actions

## 4. Toolbar Integration

- [x] 4.1 Add "Find Cantus ID" button to toolbar
- [x] 4.2 Wire button to trigger `useCantusLookup` hook
- [x] 4.3 Disable button when no syllable annotations or lookup in progress
- [x] 4.4 Handle single match auto-selection with success feedback
- [x] 4.5 Handle no match with "No matching chant found" message
- [x] 4.6 Open selection dialog for multiple matches

## 5. Metadata Display

- [x] 5.1 Display current Cantus ID and genre when metadata is present
- [x] 5.2 Show indicator when no Cantus ID is set

## 6. MEI Export Update

- [x] 6.1 Update `generateMEI()` to accept optional metadata parameter
- [x] 6.2 Add `<workList>` with Cantus identifier when metadata present
- [x] 6.3 Add `<classification>` with genre term when metadata present
