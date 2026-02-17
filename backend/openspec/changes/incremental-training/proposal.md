## Why

Training currently always starts from generic COCO-pretrained weights (`yolov8n.pt`), discarding all prior neume knowledge. As annotated pages accumulate, each training run redundantly re-learns what the previous model already knew. Resuming from the last trained model would converge faster and produce better results with fewer epochs.

## What Changes

- Auto-detect whether a previously trained neume model exists and resume from it instead of starting from scratch
- Automatically adjust training hyperparameters (epochs, learning rate) based on whether this is a fresh or incremental run
- Add a `from_scratch` API parameter to force a full retrain when needed
- Report the training mode (fresh vs. incremental) in the training status

## Capabilities

### New Capabilities

_(none — this enhances an existing capability)_

### Modified Capabilities

- `yolo-training`: Training start now auto-detects incremental vs. fresh mode, adjusts defaults accordingly, and accepts a `from_scratch` override

## Impact

- **Code**: `training/yolo_trainer.py` (model loading logic, epoch/lr defaults), `models/types.py` (request/status models)
- **API**: `POST /training/start` gains optional `from_scratch` field; status response gains `mode` field
- **No breaking changes**: Existing API calls with no body continue to work, now with smarter defaults
