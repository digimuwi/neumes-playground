## Why

The backend `POST /training/start` now accepts a `training_type` field (`"neumes"`, `"segmentation"`, or `"both"`), allowing users to train only the pipeline they need. The frontend doesn't expose this option yet, so users are forced to always train both models even when only one has changed.

## What Changes

- Add a prominent `ToggleButtonGroup` to the training dialog for selecting which pipeline(s) to train
- Make the dialog description text dynamic based on the selected training type
- Conditionally show/hide advanced settings fields based on relevance (e.g., hide "Seg Epochs" when only training neumes)
- Add `training_type` to the `TrainingStartOptions` type and include it in the API request

## Capabilities

### New Capabilities

_(none — this extends existing training UI)_

### Modified Capabilities

- `training-ui`: Add training type selection toggle, conditional field visibility, and dynamic description text

## Impact

- `src/services/htrService.ts` — `TrainingStartOptions` type gains `training_type` field
- `src/components/Toolbar.tsx` — new state, ToggleButtonGroup, conditional rendering, dynamic text
