## Context

The backend now exposes three contribution management endpoints:

- `GET /contributions` → `list[ContributionSummary]` (id, image metadata, counts)
- `GET /contributions/{id}` → `ContributionDetail` (id, image with base64 data URL, lines, neumes)
- `PUT /contributions/{id}` → `ContributionResponse` (accepts `ContributionAnnotations` JSON body)

The frontend can already create contributions via `POST /contribute` but has no way to browse, load, or update them. The existing `responseToAnnotations()` function converts backend line/neume data to frontend annotations — the `ContributionDetail` response uses the same `LineInput`/`NeumeInput` shapes, so conversion logic can be reused.

## Goals / Non-Goals

**Goals:**
- Let users browse stored contributions and load one into the editor
- Track which contribution is being edited so saves become updates (PUT) instead of creates (POST)
- Persist tracking across sessions via localStorage

**Non-Goals:**
- Deleting contributions from the frontend
- Thumbnail previews in the contribution list (would require backend changes or per-item fetches)
- Batch operations on multiple contributions
- Offline caching of contribution data

## Decisions

### 1. Reuse `responseToAnnotations()` for contribution loading

The `ContributionDetail` response has `lines` (with `boundary`, `syllables[].boundary`, `syllables[].text`) and `neumes` (with `type`, `bbox`) — structurally identical to `RecognitionResponse` except syllables lack `confidence`. Since `responseToAnnotations()` already handles optional confidence gracefully, we can reuse it directly by mapping `ContributionDetail` to the `RecognitionResponse` shape.

**Alternative**: Write a separate `contributionToAnnotations()` — rejected because the shapes are identical and duplicating the conversion logic creates maintenance burden.

### 2. State tracking: single `contributionId: string | null` on `AppState`

A nullable string is sufficient. When null, the editor is in "new contribution" mode (POST). When set, it's in "edit existing" mode (PUT). This field:
- Does NOT create undo/redo history entries (like selection state)
- Clears to null on `SET_IMAGE` (new image = new work, detached from any contribution)
- Gets set after successful POST `/contribute` (captures the returned ID)
- Gets set when loading from the contributions list
- Persists in localStorage alongside other state

**Alternative**: Store in a separate React state outside the reducer — rejected because it needs to clear on `SET_IMAGE` which is an action handled by the reducer, and it should persist alongside the rest of the app state.

### 3. Dialog pattern: standalone `ContributionsDialog.tsx` component

Follow the `CantusSelectionDialog` pattern: a standalone component that receives `open`, `onSelect`, and `onClose` props. The dialog fetches the contribution list on open, displays a simple MUI List, and calls `onSelect(id)` when the user picks one. The Toolbar handles loading the actual contribution data.

**Alternative**: Embed dialog logic directly in Toolbar — rejected because Toolbar is already 400+ lines and the dialog has enough self-contained logic (fetching the list, loading states) to justify separation.

### 4. Loading a contribution: Toolbar orchestrates the full flow

When the user selects a contribution from the dialog:
1. Toolbar calls `getContribution(id)` to fetch full data
2. Maps the response through `responseToAnnotations()` with the image dimensions from the response
3. Dispatches `loadState()` with the reconstructed `AppState` (image, annotations, line boundaries)
4. Dispatches `setContributionId(id)`

This keeps the Toolbar as the orchestration point for all contribution actions, consistent with how it handles import and OCR.

### 5. Update button: reuse existing Contribute button with conditional behavior

When `contributionId` is set:
- Tooltip changes from "Contribute Training Data" to "Update Contribution"
- Click calls `updateContribution(id, ...)` instead of `contributeTrainingData(...)`
- A small Chip appears showing the contribution ID (truncated)

When `contributionId` is null, behavior is unchanged — POST to `/contribute`, then set the returned ID.

### 6. Service functions in `htrService.ts`

Keep all three new functions in the existing service file, consistent with Decision 1 from the original contribute-training-data design. The base URL and coordinate conversion utilities are already there.

- `listContributions()` → simple GET, returns typed summary array
- `getContribution(id)` → GET, maps response to `{ imageDataUrl, annotations, lineBoundaries }` via `responseToAnnotations()`
- `updateContribution(id, imageDataUrl, annotations, lineBoundaries)` → reuses `transformAnnotationsForContribution()` to build the PUT body

## Risks / Trade-offs

**[Risk] Large contribution list** → No pagination in the backend API. For now the list is fetched in full. Acceptable for the expected scale (tens to low hundreds of contributions). If this grows, pagination can be added later.

**[Risk] Stale contribution data** → The list is fetched each time the dialog opens, so it's fresh. No caching to go stale.

**[Trade-off] No loading indicator in dialog** → The contribution list fetch should be fast (no image data). A simple disabled state while loading is sufficient. The heavier `getContribution(id)` call happens after dialog closes, with the Contribute button showing a spinner.

**[Trade-off] `responseToAnnotations()` must become exported** → Currently it's a module-private function. Exporting it is a minor visibility change with no behavioral impact.
