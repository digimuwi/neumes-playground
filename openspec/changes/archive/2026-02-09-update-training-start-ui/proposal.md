## Why

The backend `/training/start` API has been extended with new parameters (`from_scratch`, `seg_epochs`, optional `epochs`) and its response now includes a `mode` field ("fresh" vs "incremental"). The frontend training dialog still sends the old two-parameter format and doesn't expose the new options, nor does it display the training mode. The UI needs to catch up with the backend.

## What Changes

- Update `TrainingStartRequest` to support all backend parameters: optional `epochs` (auto-selects based on mode), `imgsz`, `seg_epochs`, and `from_scratch`
- Update `TrainingStatus` type to include the new `mode` field (`"fresh" | "incremental" | null`)
- Redesign the training dialog: parameters are collapsed under an "Advanced Settings" section so users can click "Start" immediately with all defaults, or expand to configure
- Show training mode in the progress chip (e.g., "Training (fresh) 5/100")
- Update dialog description to reflect that both YOLO and segmentation models are trained

## Capabilities

### New Capabilities

### Modified Capabilities
- `training-ui`: Update dialog to support new backend parameters (optional epochs, from_scratch, seg_epochs), add collapsible advanced settings, display training mode in progress chip

## Impact

- `src/services/htrService.ts`: Update `TrainingStatus` type (add `mode`), update `startTraining()` signature and request body
- `src/hooks/useTrainingStatus.ts`: Update `start()` signature to accept new parameter shape
- `src/components/Toolbar.tsx`: Redesign training dialog with collapsible advanced section, update progress chip to show mode
