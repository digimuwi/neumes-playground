## Why

The backend exposes `POST /training/start` and `GET /training/status` endpoints for YOLO neume detection model training, but the frontend has no way to trigger or monitor training. Users must currently use the API directly. Adding a training button to the AppBar lets users kick off training from the UI and see live progress.

## What Changes

- Add a "Start Training" icon button to the toolbar, placed next to the existing "Contribute" button
- Add a configuration dialog that opens on click, allowing the user to set epochs and image size before starting
- Add a progress chip in the toolbar that shows live training state (e.g., "Training 34/100") by polling `GET /training/status`
- Add service functions in `htrService.ts` for `startTraining()` and `getTrainingStatus()`
- Add a `useTrainingStatus` hook to encapsulate polling logic and state management
- Show success/error outcomes via the existing snackbar pattern
- Handle 409 (already running) gracefully

## Capabilities

### New Capabilities
- `training-ui`: Frontend training trigger button, configuration dialog, progress chip, and status polling

### Modified Capabilities

## Impact

- `src/components/Toolbar.tsx`: New button, dialog, and progress chip
- `src/services/htrService.ts`: New `startTraining()` and `getTrainingStatus()` functions
- `src/hooks/`: New `useTrainingStatus` hook
- Backend endpoints consumed: `POST /training/start`, `GET /training/status` (already exist, no backend changes needed)
