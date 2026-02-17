## Why

The `/training/start` endpoint always runs both YOLO (neume detection) and Kraken (segmentation) training. Users need the ability to run only one pipeline — for example, when only neume annotations have changed, or when iterating on segmentation alone. Running both wastes time and compute.

## What Changes

- Add a `training_type` parameter to `POST /training/start` accepting `"neumes"`, `"segmentation"`, or `"both"` (default: `"both"`)
- When a single pipeline is selected, only that pipeline's export + training + deployment runs
- The `parallel` flag is silently ignored when only one pipeline is selected
- Status tracking remains unchanged — the same state machine applies regardless of which pipelines run

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `yolo-training`: The `/training/start` endpoint gains a `training_type` parameter that controls which pipelines run. Completion logic changes to account for running a subset of pipelines.

## Impact

- **API**: `POST /training/start` request body gains a new optional field (backwards-compatible, defaults to `"both"`)
- **Code**: `TrainingStartRequest` model, `start_training()`, thread spawning logic, and `_check_both_done()` in `yolo_trainer.py`
- **No breaking changes**: Existing clients that send no `training_type` get today's behavior
