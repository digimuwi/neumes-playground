## 1. Model & API Layer

- [x] 1.1 Add `TrainingType = Literal["neumes", "segmentation", "both"]` and `training_type` field to `TrainingStartRequest` in `models/types.py`
- [x] 1.2 Pass `training_type` from the `/training/start` endpoint handler in `api.py` through to `start_training()`

## 2. Training Orchestration

- [x] 2.1 Add `training_type` parameter to `start_training()` in `yolo_trainer.py` and update thread spawning to only launch the requested pipeline(s)
- [x] 2.2 Update `_check_both_done()` to pre-fill the skipped pipeline's result as `{}` so completion triggers correctly when only one pipeline runs
- [x] 2.3 Update `_sequential_training_loop()` to conditionally run only the requested pipeline(s)
