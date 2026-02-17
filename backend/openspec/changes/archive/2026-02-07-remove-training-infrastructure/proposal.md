## Why

The Kraken-based training infrastructure (segmentation training, neume recognition training, synthetic data generation) is dead code. Change 1 removed neume-as-lines from the recognition pipeline, so there is nothing left to train via Kraken. Neume detection will move to YOLOv8 in later changes with its own training pipeline. Keeping this code adds confusion, maintenance burden, and ~1,800 lines of unused code plus ~26 MB of obsolete model files.

## What Changes

- **Remove** the entire `training/` module: orchestrator (ketos segtrain/train), triggers (threshold-based async training), lock (concurrency), and filter_page_xml (type-specific dataset filtering)
- **Remove** `contribution/counter.py` (contribution counting that drove training thresholds)
- **Remove** training trigger integration from `storage.py`
- **Remove** scripts: `trigger_training.py`, `generate_synthetic_data.py`, `compose_manuscripts.py`, `generate_from_contribution.py`
- **Remove** obsolete model files: `segmentation_old.mlmodel`, `segmentation_broken.mlmodel`, `recognition_neume.mlmodel`, `training.log`
- **Remove** `synthetic_data/` directory (generated training data)
- **Simplify** `page_xml.py` — remove neume-band grouping logic (`_group_neumes_into_bands`), keep text-only PAGE XML generation
- **Simplify** `/contribute` endpoint — silently ignore neumes in submitted annotations, only store text as PAGE XML (transitional — Change 6 replaces PAGE XML entirely)
- **Remove** related tests: `test_filter_page_xml.py`, `test_training_integration.py`, `test_counter.py`, and neume-band tests in `test_contribution.py`

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `training-data-contribution`: Remove neume-band grouping requirements and all Kraken training-related scenarios. PAGE XML becomes text-only. Neumes in contribution input are silently ignored. Mark as transitional (Change 6 replaces PAGE XML with JSON).

## Impact

- **Code**: `training/` module deleted entirely, `contribution/` simplified, `page_xml.py` simplified, `storage.py` simplified
- **API**: `/contribute` still accepts neumes in input (no breaking API change) but silently ignores them — neume data is not stored until Change 6 introduces JSON storage
- **Dependencies**: No new dependencies. `ketos` remains as a dependency for Kraken inference (segmentation/recognition) but is no longer used for training
- **Models**: 3 obsolete `.mlmodel` files (~26 MB) removed from `models/`
- **Tests**: 3 test files removed, 1 test file simplified
