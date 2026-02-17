## Context

The backend accumulates contributions (image + PAGE XML pairs) in the `contributions/` directory. Currently these are stored but never used. Kraken provides the training infrastructure (`ketos segtrain`, `ketos train`) and multi-model inference (`mm_rpred`), but the integration doesn't exist.

Key constraints from Kraken:
- Segmentation training CAN filter by baseline type (`--valid-baselines neume,text`)
- Recognition training CANNOT filter - requires pre-filtered PAGE XML files
- `mm_rpred` routes lines to models based on tags in segmentation output

Current state:
- Default Kraken segmentation model (text lines only, no neume awareness)
- Tridis text recognition model (medieval/early modern text)
- No neume recognition model exists anywhere

## Goals / Non-Goals

**Goals:**
- Build complete training pipeline infrastructure that triggers on contribution thresholds
- Create PAGE XML filtering to separate text/neume training data
- Update inference to use multi-model recognition when models are available
- Graceful degradation when custom models don't exist yet

**Non-Goals:**
- GPU optimization or distributed training
- Model versioning or rollback (auto-promote, no history)
- Training progress UI or status endpoints
- Validation/evaluation of trained models

## Decisions

### 1. Contribution counting via file

**Decision**: Store contribution count in `contributions/.count` as plain integer.

**Alternatives considered**:
- SQLite database: Overkill for a single counter
- Count directory entries: O(n) on each contribution, slow as data grows

**Rationale**: Simple, atomic writes, survives restarts, easy to inspect/reset.

### 2. Background training via subprocess

**Decision**: Spawn training as detached subprocess, don't wait for completion.

**Alternatives considered**:
- Celery/RQ job queue: Adds infrastructure complexity
- Synchronous training: Blocks API for extended time
- Separate training service: Overkill for testing phase

**Rationale**: Simple, no new dependencies, acceptable for single-machine testing. Training runs independently; if it fails, next threshold will retry.

### 3. Model file locations

**Decision**: Place trained models in `models/` directory with fixed names:
- `models/segmentation.mlmodel` - custom segmentation (optional)
- `models/recognition_text.mlmodel` - text recognition (optional, falls back to Tridis)
- `models/recognition_neume.mlmodel` - neume recognition (optional, skip neumes if missing)

**Rationale**: Fixed names allow simple existence checks. No versioning per non-goal.

### 4. Inference fallback chain

**Decision**:
```
if custom segmentation exists:
    use it (produces typed lines)
else:
    use default kraken segmentation (text lines only)

if both text + neume recognition models exist:
    use mm_rpred with tag routing
elif only text model exists (Tridis or custom):
    use rpred with single model, ignore neume-typed lines
else:
    error (no recognition possible)
```

**Rationale**: Enables incremental adoption. System works from day one with current behavior, gradually upgrades as models appear.

### 5. Training intervals

**Decision**:
- Segmentation: every 10 contributions
- Recognition: every 30 contributions

**Rationale**: Segmentation is faster to train and benefits from smaller increments. Recognition needs more data for meaningful improvement.

### 6. PAGE XML filtering approach

**Decision**: Python script that reads PAGE XML, filters TextLines by `custom` attribute type, writes filtered XML to temp directories.

**Rationale**: Kraken's `ketos train` has no built-in filtering. Must pre-process data.

## Risks / Trade-offs

**[Risk] Training fails silently** → Log training output to file in `models/training.log`. Check exit codes.

**[Risk] Training corrupts model mid-write** → Train to temp file, atomic rename on success.

**[Risk] Concurrent training runs** → Use lockfile `models/.training.lock`. Skip if locked.

**[Risk] Insufficient data for neume model** → Neume recognition training will produce poor model initially. This is expected - quality improves with more data.

**[Trade-off] No model quality validation** → Accepting potentially worse models. Mitigated by: users will notice and can re-annotate. Non-goal for testing phase.

**[Trade-off] Subprocess management** → No job monitoring, no retry logic, no cancellation. Acceptable for testing phase.
