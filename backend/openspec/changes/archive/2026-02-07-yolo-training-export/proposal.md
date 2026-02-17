## Why

Contributions store neume annotations as free-form JSON, but there is no way to convert them into the YOLO training format needed to actually train a neume detection model. Without this export pipeline, the `neume_detector.pt` model cannot be created, and the entire neume detection branch (`pipeline/neume_detection.py`) returns empty results.

## What Changes

- Add `training/yolo_export.py` module that batch-converts stored contributions into a YOLO-format dataset (text-masked images + normalized label files)
- Add `neume_classes.yaml` config file defining the canonical neume-type-to-class-ID mapping needed for YOLO labels
- Add an export CLI script that runs the conversion and generates `dataset.yaml` with configurable train/val split
- Text masking is applied to training images (reusing `pipeline/text_masking.py`) so training data matches inference preprocessing

## Capabilities

### New Capabilities
- `yolo-training-export`: Batch export of stored contributions to YOLO object detection training format, including text masking, bbox normalization, class mapping, train/val splitting, and dataset config generation

### Modified Capabilities
- `training-data-contribution`: Add requirement that contributions must be discoverable by the export pipeline (listing all contribution directories)

## Impact

- New files: `training/yolo_export.py`, `neume_classes.yaml`, export script, tests
- Depends on: `pipeline/text_masking.py`, `pipeline/segmentation.py` (Kraken segmentation at export time)
- No API changes — export is a batch CLI operation, not an endpoint
- No new dependencies — uses existing `ultralytics`, `kraken`, `pillow`, `numpy`
