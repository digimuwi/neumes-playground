## 1. Service Layer Types

- [x] 1.1 Add `TrainingMode` type (`'fresh' | 'incremental'`) and `mode` field to `TrainingStatus` in `htrService.ts`
- [x] 1.2 Replace `startTraining(epochs, imgsz)` with `startTraining(options?: TrainingStartOptions)` where options has optional `epochs`, `imgsz`, `seg_epochs`, and `from_scratch` fields
- [x] 1.3 Send options object as JSON body in the POST request (empty `{}` when no options provided)

## 2. Training Status Hook

- [x] 2.1 Update `useTrainingStatus.start()` signature from `(epochs, imgsz)` to `(options?: TrainingStartOptions)`

## 3. Training Dialog

- [x] 3.1 Replace inline dialog fields with a collapsible "Advanced Settings" section (collapsed by default)
- [x] 3.2 Change epochs field to empty by default with placeholder "Auto (100 fresh / 30 incr.)"
- [x] 3.3 Add segmentation epochs field (default 50)
- [x] 3.4 Add "Train from scratch" checkbox (default unchecked)
- [x] 3.5 Update dialog description text to reflect both segmentation and neume detection training
- [x] 3.6 Wire Start button to build options object from form state (omitting defaults/empty values) and call `training.start(options)`

## 4. Progress Chip

- [x] 4.1 Update progress chip to show training mode when available: "Training (fresh) 5/100" or "Training (incremental) 5/30"
