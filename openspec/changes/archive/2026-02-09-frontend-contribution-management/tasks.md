## 1. State: contribution tracking

- [x] 1.1 Add `contributionId: string | null` to `AppState` in `src/state/types.ts` and add `SET_CONTRIBUTION_ID` to the `Action` union
- [x] 1.2 Add `contributionId: null` to `initialAppState` in `src/state/reducer.ts`, handle `SET_CONTRIBUTION_ID` (no history entry), and clear `contributionId` on `SET_IMAGE`
- [x] 1.3 Persist and load `contributionId` in `saveStateToStorage` / `loadStateFromStorage` in `src/state/reducer.ts`
- [x] 1.4 Add `setContributionId(id: string | null)` action creator in `src/state/actions.ts`

## 2. Service functions

- [x] 2.1 Export `responseToAnnotations()` from `src/services/htrService.ts` (currently module-private)
- [x] 2.2 Add `listContributions()` function: GET `/contributions`, return typed `ContributionSummary[]`
- [x] 2.3 Add `getContribution(id)` function: GET `/contributions/{id}`, map response through `responseToAnnotations()`, return `{ imageDataUrl, annotations, lineBoundaries }`
- [x] 2.4 Add `updateContribution(id, imageDataUrl, annotations, lineBoundaries)` function: reuse `transformAnnotationsForContribution()`, PUT `/contributions/{id}` with JSON body

## 3. Contributions dialog

- [x] 3.1 Create `src/components/ContributionsDialog.tsx` with props `open`, `onSelect(id: string)`, `onClose`
- [x] 3.2 Fetch contribution list on dialog open, display MUI List with filename, dimensions, counts
- [x] 3.3 Handle loading, empty, and error states in the dialog

## 4. Toolbar integration

- [x] 4.1 Add "Browse Contributions" icon button (FolderOpenIcon) to Toolbar, wired to open ContributionsDialog
- [x] 4.2 Handle contribution selection: call `getContribution(id)`, dispatch `loadState()` + `setContributionId(id)`, show loading state
- [x] 4.3 Change Contribute button behavior: when `contributionId` is set, call `updateContribution()` instead of `contributeTrainingData()`, update tooltip to "Update Contribution"
- [x] 4.4 After successful POST `/contribute`, dispatch `setContributionId()` with the returned ID
- [x] 4.5 Show contribution ID chip in toolbar when `contributionId` is set
