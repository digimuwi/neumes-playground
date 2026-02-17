## 1. Type Updates

- [x] 1.1 Add `training_type` to `TrainingStartOptions` in `htrService.ts` (`"neumes" | "segmentation" | "both"`)

## 2. Training Dialog UI

- [x] 2.1 Add `trainingType` state to Toolbar (default `"both"`)
- [x] 2.2 Add MUI `ToggleButtonGroup` with three options ("Neumes", "Segmentation", "Both") above the description text, enforcing at least one selection
- [x] 2.3 Make dialog description text dynamic based on selected training type
- [x] 2.4 Conditionally show/hide advanced settings fields based on training type (YOLO Epochs + Image Size for neumes/both, Seg Epochs for segmentation/both, Train from Scratch always visible)

## 3. API Integration

- [x] 3.1 Include `training_type` in the request payload in `handleTrainingStart` (only when not `"both"`)
