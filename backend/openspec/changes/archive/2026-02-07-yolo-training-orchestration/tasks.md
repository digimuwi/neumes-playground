## 1. Training Status Types

- [x] 1.1 Add `TrainingState` literal type and `TrainingStatus` Pydantic model to `models/types.py` — states: `idle`, `exporting`, `training`, `deploying`, `complete`, `failed`; fields: `state`, `current_epoch`, `total_epochs`, `metrics`, `model_version`, `error`, `started_at`, `completed_at`
- [x] 1.2 Add `TrainingStartRequest` model with optional `epochs` (default 100) and `imgsz` (default 640) fields

## 2. YOLO Trainer Module

- [x] 2.1 Create `training/yolo_trainer.py` with module-level `_training_status: TrainingStatus` initialized to idle
- [x] 2.2 Implement `get_training_status()` that returns the current `TrainingStatus`
- [x] 2.3 Implement `start_training(epochs, imgsz)` that checks for concurrent run (raises if active), sets state to `exporting`, and spawns a background `threading.Thread` running `_training_loop`
- [x] 2.4 Implement `_training_loop(epochs, imgsz)`: call `export_dataset()` from `yolo_export`, then call `ultralytics` `model.train(data=dataset.yaml, epochs=..., imgsz=...)` with `yolov8n.pt` as base model
- [x] 2.5 Implement epoch progress callback: update `_training_status.current_epoch` after each epoch using ultralytics callbacks
- [x] 2.6 Implement model versioning: after training, copy best weights to `models/neume_versions/YYYYMMDD_HHMMSS.pt`, create directory if needed
- [x] 2.7 Implement atomic deployment: write best weights to temp file in `models/`, then `os.replace()` to `models/neume_detector.pt`
- [x] 2.8 Handle errors: wrap `_training_loop` in try/except, set state to `"failed"` with error message on any exception

## 3. API Endpoints

- [x] 3.1 Add `POST /training/start` endpoint to `api.py` — accepts optional `TrainingStartRequest` body, calls `start_training()`, returns HTTP 202 with current status; returns HTTP 409 if already running
- [x] 3.2 Add `GET /training/status` endpoint to `api.py` — calls `get_training_status()`, returns HTTP 200 with `TrainingStatus`

## 4. Update Neume Detection Warning

- [x] 4.1 Update the warning message in `pipeline/neume_detection.py` `detect_neumes()` to reference `POST /training/start` instead of "see Changes 7-8"

## 5. Tests

- [x] 5.1 Test `start_training` rejects concurrent runs (raises or returns appropriate error)
- [x] 5.2 Test `start_training` sets state to `exporting` then `training` then `deploying` then `complete`
- [x] 5.3 Test model versioning: verify timestamped `.pt` file created in `models/neume_versions/`
- [x] 5.4 Test atomic deployment: verify `models/neume_detector.pt` exists after training completes
- [x] 5.5 Test `_training_loop` exception handling: verify state set to `"failed"` with error message
- [x] 5.6 Test `POST /training/start` returns 202 on success and 409 when already running
- [x] 5.7 Test `GET /training/status` returns idle state initially and reflects training progress
- [x] 5.8 Test updated warning message in neume detection references `/training/start`
