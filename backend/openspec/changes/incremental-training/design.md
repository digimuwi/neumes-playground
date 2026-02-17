## Context

Training currently always initializes from `yolov8n.pt` (COCO-pretrained YOLOv8 nano) and runs 100 epochs. As the neume dataset grows through user contributions, each run redundantly re-learns neume features from generic weights. A previously trained model at `models/neume_detector.pt` already encodes neume-specific knowledge that can be leveraged.

The training pipeline runs in a background daemon thread from `yolo_trainer.py`, with model versioning in `models/neume_versions/` and atomic deployment to `models/neume_detector.pt`.

## Goals / Non-Goals

**Goals:**
- Automatically resume training from the last deployed model when one exists
- Reduce default epoch count and learning rate for incremental runs to converge faster
- Preserve the ability to force a full retrain from generic weights
- Report training mode in status so the caller knows which path was taken

**Non-Goals:**
- Training on only new data (we always retrain on the full exported dataset to avoid catastrophic forgetting)
- Automatic learning rate scheduling beyond Ultralytics' built-in cosine annealing
- Model quality comparison or automatic rollback if an incremental run produces a worse model

## Decisions

### 1. Auto-detect mode based on `neume_detector.pt` existence

**Decision**: If `models/neume_detector.pt` exists at training start, load it as the base model (incremental mode). Otherwise, fall back to `yolov8n.pt` (fresh mode).

**Alternatives considered**:
- Check `models/neume_versions/` for the latest version — adds complexity for no benefit since `neume_detector.pt` is always the latest deployed model.
- Require the user to explicitly choose — adds friction. Auto-detect with an override (`from_scratch`) gives the best of both worlds.

### 2. Epoch and learning rate defaults by mode

**Decision**:
| Parameter | Fresh (from `yolov8n.pt`) | Incremental (from `neume_detector.pt`) |
|-----------|--------------------------|---------------------------------------|
| `epochs`  | 100                      | 30                                    |
| `lr0`     | 0.01 (ultralytics default) | 0.001                               |

**Rationale**: Incremental runs start from weights already close to optimal for neumes. Fewer epochs prevent overfitting; a lower learning rate prevents overshooting the existing good weights.

If the user explicitly passes `epochs`, their value takes precedence regardless of mode.

### 3. `from_scratch` parameter on the API

**Decision**: Add an optional `from_scratch: bool = False` field to `TrainingStartRequest`. When `true`, force fresh mode even if a trained model exists. This uses fresh-mode defaults (100 epochs, 0.01 lr) unless the user also passes explicit `epochs`.

### 4. Report mode in training status

**Decision**: Add a `mode` field (`"fresh"` | `"incremental"`) to `TrainingStatus`. Set it when transitioning to `"training"` state. This lets the frontend/caller understand which path was taken.

## Risks / Trade-offs

- **Corrupted model propagation** → If a bad incremental model is deployed, the next incremental run builds on bad weights. Mitigation: `from_scratch=true` resets to generic weights. The version history in `neume_versions/` provides rollback points.
- **30 epochs may be too few for large dataset changes** → If many new classes or pages are added at once, 30 epochs might not be enough. Mitigation: the user can pass explicit `epochs` to override. We can tune the default over time.
- **Learning rate 0.001 is a heuristic** → Ultralytics' cosine annealing will handle the schedule from this starting point, but the optimal value depends on how much the dataset changed. This is a reasonable starting point for iterative refinement.
