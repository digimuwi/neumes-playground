## 1. Service Layer

- [x] 1.1 Add `TrainingStatus` and `TrainingStartRequest` TypeScript interfaces to `src/services/htrService.ts`
- [x] 1.2 Add `startTraining(epochs, imgsz)` function that POSTs to `/training/start` and returns `TrainingStatus`
- [x] 1.3 Add `getTrainingStatus()` function that GETs `/training/status` and returns `TrainingStatus`

## 2. Training Status Hook

- [x] 2.1 Create `src/hooks/useTrainingStatus.ts` hook that exposes `status`, `start(epochs, imgsz)`, and `isActive`
- [x] 2.2 Implement poll-on-mount to detect in-progress training
- [x] 2.3 Implement polling loop (every 2s) that runs while training is active and stops when idle/complete/failed
- [x] 2.4 Handle 409 (already running) by starting the polling loop instead of showing an error

## 3. Toolbar UI

- [x] 3.1 Add training icon button (FitnessCenterIcon) after the Contribute button in `Toolbar.tsx`
- [x] 3.2 Show loading spinner on the button and disable it while training is active
- [x] 3.3 Add training configuration dialog with epochs and imgsz number fields (defaults: 100, 640)
- [x] 3.4 Wire dialog "Start" button to call `start(epochs, imgsz)` from the hook
- [x] 3.5 Add training progress chip that shows current state ("Exporting...", "Training 34/100", "Deploying...")
- [x] 3.6 Show success snackbar ("Training complete!") when training finishes
- [x] 3.7 Show error via existing error snackbar when training fails
