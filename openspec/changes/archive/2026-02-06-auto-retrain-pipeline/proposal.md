## Why

Contributions (annotated manuscript pages with syllables and neumes) accumulate but are never used to improve the recognition models. Implementing automatic retraining creates a feedback loop where user corrections continuously improve segmentation and recognition accuracy.

## What Changes

- Add contribution counting and threshold-based retraining triggers
- Create PAGE XML filtering script to separate text lines from neume lines (required because `ketos train` cannot filter by line type)
- Implement background training orchestration for segmentation and recognition models
- Update inference pipeline to use multi-model recognition (`mm_rpred`) when specialized models are available
- Add graceful fallback to current behavior when custom models don't exist yet

## Capabilities

### New Capabilities
- `training-pipeline`: Orchestrates Kraken model training triggered by contribution thresholds. Handles segmentation training (every 10 contributions) and recognition training (every 30 contributions) with PAGE XML filtering for text vs neume lines.
- `multi-model-inference`: Routes segmented lines to appropriate recognition models based on line type tags. Falls back to single-model inference when specialized models aren't available.

### Modified Capabilities
- `contribution`: Add contribution counting and training trigger after save

## Impact

- Backend: New training module, updated recognition pipeline, modified contribution endpoint
- Models directory: Will contain dynamically updated models (segmentation, text recognition, neume recognition)
- Dependencies: No new dependencies (uses existing Kraken CLI tools)
- API: No breaking changes (graceful fallback maintains current behavior)
