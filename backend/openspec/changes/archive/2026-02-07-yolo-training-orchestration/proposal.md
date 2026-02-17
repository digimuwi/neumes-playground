## Why

The YOLO training export pipeline (Change 7) produces a complete dataset, and the neume detection module (Change 4) can load and run a YOLO model — but there is no way to actually *train* a model from exported data and deploy it to the running server. This is the final piece needed to close the active learning loop: annotate pages in the frontend, export training data, train a YOLO model, and have the server pick up the new model automatically.

## What Changes

- New `training/yolo_trainer.py` module that wraps the `ultralytics` training API to fine-tune YOLOv8 from an exported dataset
- New `POST /training/start` endpoint to trigger training as a background task
- New `GET /training/status` endpoint to poll training progress (epoch, metrics, completion)
- Model versioning: trained models saved to `models/neume_versions/` with timestamps, atomically swapped into `models/neume_detector.pt` via `os.replace()`
- Training runs in a background thread so the API remains responsive
- Only one training run at a time (concurrent requests rejected)

## Capabilities

### New Capabilities
- `yolo-training`: Fine-tune YOLOv8 from exported training data, manage model versions, and deploy trained models to the running detection pipeline

### Modified Capabilities
- `neume-detection`: Add model version reporting — `detect_neumes` now also returns which model version is active (for frontend display / debugging)

## Impact

- **New files**: `training/yolo_trainer.py`, tests
- **Modified files**: `api.py` (two new endpoints), `pipeline/neume_detection.py` (version info), `models/types.py` (training status types)
- **Dependencies**: `ultralytics` already present in `pyproject.toml`
- **Runtime**: Training is CPU/GPU-intensive; runs in background thread, does not block API
- **Disk**: Each model version ~6-25 MB; old versions accumulate in `models/neume_versions/`
