## Why

Kraken's default segmentation model occasionally detects baselines through neume regions, treating them as text. This produces garbage OCR output and causes text masking to erase neume ink before YOLO detection. Post-hoc filtering (confidence thresholds, uppercase heuristics) proved unreliable — the model needs to learn the difference between text and neume regions at the segmentation level.

## What Changes

- Add a PageXML export pipeline that converts contribution data into Kraken's segmentation training format, computing baselines from syllable positions and constructing typed regions (text vs. neume)
- Add a segmentation training module that fine-tunes Kraken's default `blla.mlmodel` using the exported PageXML data via Kraken's Python training API
- Integrate segmentation training into `start_training()` as an independent process alongside YOLO training (both triggered together, neither depends on the other)
- Use the custom segmentation model in `segment_image()` when one exists, falling back to the default

## Capabilities

### New Capabilities
- `segmentation-training-export`: Export contribution annotations to PageXML format for Kraken segmentation training (baseline computation, region construction)
- `segmentation-training`: Fine-tune Kraken's segmentation model from contribution data, with versioning and atomic deployment
- `segmentation-model-loading`: Load a custom segmentation model in the recognition pipeline when available, falling back to the default

### Modified Capabilities
- `yolo-training`: `start_training()` triggers both YOLO and segmentation training independently

## Impact

- New files: `training/seg_export.py`, `training/seg_trainer.py`
- Modified: `training/yolo_trainer.py` (orchestration), `pipeline/segmentation.py` (model loading)
- New model output: `models/seg_model.mlmodel` + `models/seg_versions/`
- No API contract changes — same endpoints, same response shapes
- Kraken's `ketos` training dependencies already installed
