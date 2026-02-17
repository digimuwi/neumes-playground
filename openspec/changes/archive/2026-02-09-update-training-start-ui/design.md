## Context

The backend `POST /training/start` API has been extended with two new parameters (`from_scratch: bool`, `seg_epochs: int`) and `epochs` is now optional (auto-selects 100 for fresh, 30 for incremental). The `TrainingStatus` response now includes a `mode` field (`"fresh" | "incremental" | null`). The current UI dialog always requires explicit `epochs` and `imgsz` values and doesn't know about the new parameters or mode.

The training dialog lives in `Toolbar.tsx` as inline JSX with local state (`trainingEpochs`, `trainingImgsz`). The `useTrainingStatus` hook manages polling and exposes `start(epochs, imgsz)`. The `startTraining()` service function sends `{ epochs, imgsz }` as JSON.

## Goals / Non-Goals

**Goals:**
- Expose all backend training parameters in the UI
- Allow users to start training immediately with zero configuration (all defaults)
- Display training mode (fresh/incremental) in the progress chip
- Update types to match current backend API

**Non-Goals:**
- Changing the polling mechanism or interval
- Adding training history/logs viewer
- Backend changes

## Decisions

### 1. Collapsible "Advanced Settings" in the dialog

The dialog opens with all parameters hidden under a collapsed accordion. The "Start" button is immediately accessible. Users who want to customize expand the section.

This pattern (MUI `Accordion` or a simple collapse toggle) keeps the common case fast while exposing power-user options. Alternative considered: removing the dialog entirely and starting on click — rejected because there's no cancel/confirmation, and users would need a separate path to access settings.

### 2. Epochs field: empty by default, sends null

The epochs field defaults to empty (no value). The placeholder text shows "Auto (100 fresh / 30 incr.)". When the user leaves it empty, `null` is sent to the backend, which auto-selects. When the user types a number, that number is sent.

This leverages the backend's smart defaulting. The previous hardcoded default of 100 is removed.

### 3. Options object instead of positional args

`startTraining()` and `useTrainingStatus.start()` change from positional `(epochs, imgsz)` to an options object: `startTraining(options?: TrainingStartOptions)`. All fields are optional with backend-matching defaults. This is cleaner for optional parameters and avoids positional ambiguity.

### 4. Progress chip shows mode

When `training.status.mode` is available, the chip label includes it: "Training (fresh) 5/100" or "Training (incremental) 5/30". When mode is null (shouldn't happen during active training, but defensive), falls back to "Training 5/100".

### 5. Dialog description text update

Changes from "Configure YOLO neume detection training parameters" to reflect that both segmentation and neume detection models are trained.

## Risks / Trade-offs

- **Stale defaults if backend changes again**: The placeholder text mentions "100 fresh / 30 incr." which mirrors current backend logic. If the backend changes these defaults, the placeholder becomes misleading. Mitigation: this is informational only; the actual default is server-side.
- **Accordion adds visual complexity**: Even collapsed, it signals "there's more here." Acceptable trade-off for discoverability.
