## Why

Contributions (annotated training data) are stored on the backend but invisible after submission. If a contribution needs editing or data is lost locally, there's no way to browse or reload existing contributions from the UI. This change adds the ability to list, load, edit, and update contributions directly from the frontend editor.

## What Changes

- Add `contributionId` tracking to app state so the editor knows when it's working on an existing contribution
- Add service functions to call the new backend endpoints: `GET /contributions`, `GET /contributions/{id}`, `PUT /contributions/{id}`
- Add a "Browse Contributions" dialog listing stored contributions with summary info (dimensions, syllable/neume counts)
- Clicking a contribution loads its image and annotations into the editor
- When editing an existing contribution, the "Contribute" button becomes "Update Contribution" and calls PUT instead of POST
- After a fresh POST `/contribute`, the returned ID is tracked so subsequent saves become updates
- Clear `contributionId` when uploading a new image (detaches from existing contribution)

## Capabilities

### New Capabilities
- `contribution-browsing`: Browse and load existing contributions from the backend. Dialog listing contributions with summary info, click-to-load with image and annotation restoration.
- `contribution-tracking`: Track which contribution is being edited via `contributionId` in app state. Enables update-vs-create logic and persists across sessions.

### Modified Capabilities
- `training-contribution`: The contribute button now supports updating existing contributions (PUT) in addition to creating new ones (POST). After a fresh create, the returned ID is captured for subsequent updates.

## Impact

- **src/state/types.ts**: New `contributionId` field on `AppState`, new `SET_CONTRIBUTION_ID` action
- **src/state/reducer.ts**: New action case, clear on `SET_IMAGE`, persistence
- **src/state/actions.ts**: New `setContributionId` action creator
- **src/services/htrService.ts**: Three new service functions (`listContributions`, `getContribution`, `updateContribution`)
- **src/components/ContributionsDialog.tsx**: New dialog component
- **src/components/Toolbar.tsx**: Browse button, update-vs-create logic, contribution ID chip
