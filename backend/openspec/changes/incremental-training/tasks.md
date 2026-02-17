## 1. Update Request/Status Models

- [x] 1.1 Add `from_scratch: bool = False` field to `TrainingStartRequest` in `models/types.py`
- [x] 1.2 Add `mode: Optional[Literal["fresh", "incremental"]] = None` field to `TrainingStatus` in `models/types.py`

## 2. Training Mode Detection and Hyperparameters

- [x] 2.1 Update `start_training()` signature to accept `from_scratch: bool = False` parameter
- [x] 2.2 In `_training_loop`, add mode detection logic: if `from_scratch` is false and `YOLO_MODEL_PATH` exists, set mode to `"incremental"`; otherwise set mode to `"fresh"`
- [x] 2.3 Set epoch default based on mode: 30 for incremental, 100 for fresh — but only when the caller did not pass an explicit `epochs` value
- [x] 2.4 Load model from `YOLO_MODEL_PATH` in incremental mode, `yolov8n.pt` in fresh mode
- [x] 2.5 Pass `lr0=0.001` to `model.train()` in incremental mode (omit in fresh mode to use ultralytics default 0.01)
- [x] 2.6 Set `mode` field on `_training_status` when transitioning to `"training"` state

## 3. API Endpoint Update

- [x] 3.1 Pass `request.from_scratch` through from `training_start()` in `api.py` to `start_training()`

## 4. Verification

- [x] 4.1 Verify: calling `POST /training/start` with no body and no existing model → fresh mode, 100 epochs
- [x] 4.2 Verify: calling `POST /training/start` with no body and existing `neume_detector.pt` → incremental mode, 30 epochs
- [x] 4.3 Verify: calling `POST /training/start` with `{"from_scratch": true}` and existing model → fresh mode, 100 epochs
- [x] 4.4 Verify: calling `POST /training/start` with `{"epochs": 50}` → user value 50 used regardless of mode
- [x] 4.5 Verify: `GET /training/status` returns `mode` field reflecting the active training mode
