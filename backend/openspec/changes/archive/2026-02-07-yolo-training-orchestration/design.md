## Context

Changes 1-7 have built the full pipeline from annotation collection through YOLO dataset export and inference. The export pipeline (`training/yolo_export.py`) produces a ready-to-train YOLO dataset. The detection module (`pipeline/neume_detection.py`) already supports mtime-based model hot-swap — replacing the `.pt` file on disk automatically triggers a reload on the next inference call.

What's missing is the bridge: triggering a training run, managing model versions, and atomically deploying trained models so the live server picks them up.

This is a single-user research tool, not a production ML platform. The design prioritizes simplicity and debuggability over scalability.

## Goals / Non-Goals

**Goals:**
- Trigger YOLOv8 fine-tuning from the exported dataset via an API endpoint
- Run training in a background thread so the API stays responsive
- Save each trained model with a timestamp, keep history for rollback
- Atomically deploy new models so the detection pipeline picks them up
- Report training progress (epoch, metrics) via a polling endpoint

**Non-Goals:**
- Automatic/threshold-based training triggers (manual only for now)
- GPU cluster orchestration or distributed training
- Model comparison UI or A/B testing
- Hyperparameter tuning / experiment tracking
- Pruning old model versions (manual cleanup is fine)
- Training queue (one run at a time, reject concurrent requests)

## Decisions

### 1. Background thread, not subprocess

**Choice:** `threading.Thread` inside the FastAPI process.

**Alternatives considered:**
- **Subprocess**: More isolated but harder to report progress, more complex error handling, needs IPC for status updates.
- **Celery/task queue**: Massive overkill for a single-user research tool.

**Rationale:** A background thread shares the process, making progress reporting trivial (shared state via a module-level status dict). Training is CPU/GPU-bound and releases the GIL during ultralytics C++ operations, so it won't block the async event loop. The thread writes status updates to a shared `TrainingStatus` object; the polling endpoint reads it.

### 2. Model versioning: directory + atomic swap

**Choice:** Save trained models to `models/neume_versions/<timestamp>.pt`, then atomically copy to `models/neume_detector.pt` via write-to-temp + `os.replace()`.

```
models/
  neume_detector.pt               ← active model (written atomically)
  neume_versions/
    20260207_143022.pt
    20260208_091500.pt
```

**Alternatives considered:**
- **Overwrite in place**: Loses rollback capability and risks corrupt reads if inference happens mid-write.
- **Symlink**: Clean but platform-dependent (Windows) and adds a layer of indirection.

**Rationale:** `os.replace()` is atomic on POSIX, ensuring the detection module never reads a half-written file. Timestamped versions in a subdirectory give free rollback — just copy an old version back. No symlink complexity.

### 3. Training always re-exports first

**Choice:** `POST /training/start` runs the export pipeline before training, ensuring the dataset reflects the latest contributions.

**Rationale:** Decoupling export from training would require the user to remember to export first. Since export is fast (seconds), always doing it prevents stale-data bugs. The export output directory is passed directly to the YOLO training command.

### 4. Training concurrency: reject, don't queue

**Choice:** If a training run is already in progress, `POST /training/start` returns HTTP 409 Conflict.

**Rationale:** Queuing adds complexity (what if the user wants to cancel the queued run?). For a single-user tool, "try again later" is a perfectly adequate UX. The status endpoint lets the user check when training finishes.

### 5. YOLOv8 training configuration

**Choice:** Hardcode sensible defaults, allow override via request body.

Defaults:
- **Base model**: `yolov8n.pt` (nano — fast training, good enough for ~17 classes with limited data)
- **Epochs**: 100
- **Image size**: 640
- **Augmentation**: YOLOv8 defaults (mosaic, flip, scale, HSV jitter) — good enough to start

The endpoint accepts optional overrides for `epochs` and `imgsz`. Other hyperparameters use ultralytics defaults.

### 6. Progress reporting granularity

**Choice:** Module-level `TrainingStatus` dataclass updated by the training thread, read by `GET /training/status`.

Fields: `state` (idle/exporting/training/deploying/complete/failed), `current_epoch`, `total_epochs`, `metrics` (last epoch's mAP/loss if available), `model_version` (timestamp of deployed model), `error` (message if failed), `started_at`, `completed_at`.

**Rationale:** Polling is simpler than SSE for training status (training takes minutes, not milliseconds). The status object is small and read-only from the endpoint's perspective.

## Risks / Trade-offs

**[Risk] Training thread crashes silently** → The status object captures exceptions and sets state to `"failed"` with the error message. The polling endpoint surfaces this to the user.

**[Risk] Model file written while inference is reading** → Mitigated by atomic `os.replace()`. The old file descriptor remains valid until closed; the new file appears atomically.

**[Risk] Training on CPU is very slow** → Expected for a research tool without GPU. YOLOv8 nano + 640px images keeps it tractable. Can be improved later with GPU support — no architectural changes needed.

**[Risk] Export + training in same thread could OOM on large datasets** → Unlikely with the small annotation counts expected early on. If it becomes an issue, the subprocess approach can be revisited.

**[Trade-off] No auto-trigger** → Simplicity over convenience. The user must manually start training. This is intentional — early in the annotation process, training after every contribution would be wasteful.
