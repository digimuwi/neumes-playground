## Context

The backend already provides `POST /training/start` (202, accepts `epochs` and `imgsz`) and `GET /training/status` for YOLO neume detection training. The frontend Toolbar currently has a "Contribute" button that submits training data. The natural next step is letting users trigger and monitor training from the same toolbar.

The Toolbar component (`src/components/Toolbar.tsx`, ~310 lines) manages all AppBar actions. It uses local state for transient UI concerns (loading spinners, snackbars). The `htrService.ts` service layer handles all backend communication.

## Goals / Non-Goals

**Goals:**
- Let users start YOLO training from the toolbar with configurable parameters
- Show live training progress as a chip in the toolbar
- Handle edge cases: already running (409), failures, page refresh mid-training

**Non-Goals:**
- Training history or logs viewer
- Advanced training configuration (learning rate, augmentation, etc.)
- Backend changes — all endpoints already exist
- Websocket-based real-time updates (polling is sufficient for epoch-level granularity)

## Decisions

### 1. Local state + custom hook (not global context)

Training status is a transient UI concern — it doesn't affect annotations, canvas, or undo/redo. This matches the pattern used by the "Contribute" button (`isContributing` local state) and `useCantusLookup` hook.

A `useTrainingStatus` hook encapsulates:
- Current `TrainingStatus` from the backend
- `start(epochs, imgsz)` function
- Polling lifecycle (start/stop)
- Derived `isActive` boolean

Alternative considered: Adding training state to the global AppProvider reducer. Rejected because training state is independent of annotation state and doesn't need undo/redo.

### 2. Polling interval: 2 seconds

Training epochs take seconds to minutes each. A 2-second poll provides responsive UI without excessive network traffic. Polling starts on mount (to catch in-progress training after page refresh) and continues while `state` is not `idle`, `complete`, or `failed`.

Alternative considered: SSE streaming like the OCR endpoint. Rejected because the training endpoint doesn't support SSE, and polling is adequate for epoch-level updates.

### 3. Configuration dialog before starting

A small MUI Dialog with two numeric fields (epochs, imgsz) opens when the user clicks the training button. Defaults match the backend: epochs=100, imgsz=640. This avoids accidental training starts and lets users tune parameters.

### 4. Progress chip + snackbar for outcomes

- **Chip in toolbar**: Persistent, shows live state ("Exporting...", "Training 34/100", "Deploying..."). Visible as long as training is active.
- **Snackbar**: Transient, shows final outcome ("Training complete!" or error message). Uses the existing `successMessage` state and `ErrorSnackbar` component patterns.

This hybrid avoids the snackbar-for-progress problems (auto-dismiss, conflict with other snackbars) while reusing snackbar for what it's good at (transient notifications).

### 5. Button placement: after Contribute, same group

The "Contribute Training Data" and "Start Training" buttons form a logical workflow (contribute → train). Placing them adjacent in the Import/Export group, separated from the OCR group by the existing divider, keeps related actions together.

### 6. Service layer functions in htrService.ts

Two new exported functions:
- `startTraining(epochs, imgsz): Promise<TrainingStatus>` — POST to `/training/start`
- `getTrainingStatus(): Promise<TrainingStatus>` — GET to `/training/status`

These follow the existing pattern in `htrService.ts` (fetch, error handling, JSON parsing).

## Risks / Trade-offs

- **Stale status on 409**: If training is already running (started externally or from another tab), the 409 response doesn't include current status. Mitigation: immediately poll `GET /training/status` after a 409 to get and display current progress.
- **Polling after page refresh**: If the user refreshes mid-training, we poll on mount to recover state. Small window where chip won't show until first poll completes (~2s).
- **No cancel support**: The backend doesn't expose a cancel endpoint. If the user starts training accidentally, it runs to completion. Acceptable for now — the confirmation dialog mitigates accidental starts.
