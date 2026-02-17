## Context

The `/training/start` endpoint currently always runs both YOLO (neume detection) and Kraken (segmentation) training pipelines. The two pipelines are already independent — separate export, training, versioning, and deployment — but the orchestration in `start_training()` always launches both. Users want to selectively run one or both.

## Goals / Non-Goals

**Goals:**
- Allow users to select which training pipeline(s) to run via a single new parameter
- Maintain full backwards compatibility (default behavior unchanged)
- Minimal changes to status tracking — same state machine, same `TrainingStatus` model

**Non-Goals:**
- Per-pipeline status tracking (separate state for neumes vs segmentation)
- Validation that `parallel` is only set when `training_type="both"` — silently ignore instead
- New API endpoints — this is a parameter addition to the existing endpoint

## Decisions

### 1. Use a `Literal["neumes", "segmentation", "both"]` field (not booleans or a list)

**Rationale:** A single enum-style field is cleaner than two booleans (`run_neumes`, `run_segmentation`) and simpler than a list (`pipelines: ["neumes"]`). Three values is easy to reason about and validate. Default `"both"` preserves backwards compatibility.

**Alternative considered:** Two booleans — more granular but allows the invalid state of both being `false`, requires extra validation.

### 2. Thread spawning branches on `training_type`

The existing branching in `start_training()` already splits on `parallel`. The new `training_type` parameter adds a second dimension:

```
training_type="both" + parallel=True   → two threads (today's behavior)
training_type="both" + parallel=False  → sequential thread (today's behavior)
training_type="neumes"                 → single YOLO thread
training_type="segmentation"           → single seg thread
```

When `training_type` is not `"both"`, the `parallel` flag is irrelevant and ignored.

### 3. Completion check adapts to what was requested

`_check_both_done()` currently waits for both `_yolo_result` and `_seg_result` to be non-None. With selective training, the unrequested pipeline's result should be pre-set to an empty dict (signaling "not requested, nothing to wait for") so the existing completion logic works with minimal changes.

**Rationale:** Pre-filling the skipped result as `{}` (no error key) means `_check_both_done()` sees both results as present and non-errored. The only change needed is initializing the skipped result at the start instead of setting both to `None`.

## Risks / Trade-offs

- **[Minimal]** Status `total_epochs` currently reflects YOLO epochs. When only segmentation runs, it will reflect seg epochs instead. This is acceptable — the field means "total epochs for this run." → No mitigation needed.
- **[Low]** The `parallel` flag becomes a no-op for single-pipeline runs. → Document this in the field description; no validation needed.
