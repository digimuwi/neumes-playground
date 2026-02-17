## 1. PageXML Export

- [x] 1.1 Create `src/htr_service/training/seg_export.py` with `export_segmentation_dataset()` — loads contributions, computes baselines from syllable bottoms, constructs text + neume regions, writes PageXML files to `datasets/segmentation/`
- [x] 1.2 Implement baseline computation: for each line, collect bottom-center of each syllable boundary, sort by X, produce polyline
- [x] 1.3 Implement neume region grouping: for each text line, collect neumes whose vertical center is above it (between previous baseline Y and current baseline Y), compute bounding rectangle
- [x] 1.4 Implement PageXML writer: produce valid PageXML with `TextRegion` (type text) containing `TextLine` with `Baseline`/`Coords`, and `ImageRegion` (type neume) with `Coords`
- [x] 1.5 Verify exported PageXML is parseable by Kraken's XML reader

## 2. Segmentation Training

- [x] 2.1 Create `src/htr_service/training/seg_trainer.py` with `run_segmentation_training()` — calls Kraken's `SegmentationModel` API to fine-tune from default `blla.mlmodel` with `resize=union`
- [x] 2.2 Implement model versioning: save to `models/seg_versions/<timestamp>.mlmodel`
- [x] 2.3 Implement atomic deployment: write-to-temp + `os.replace()` to `models/seg_model.mlmodel`

## 3. Model Loading

- [x] 3.1 Update `pipeline/segmentation.py` to check for `models/seg_model.mlmodel` and use it when present, falling back to default. Cache at module level, invalidate on file change.

## 4. Orchestration

- [x] 4.1 Update `training/yolo_trainer.py` `start_training()` to launch segmentation training in a second independent daemon thread alongside YOLO
- [x] 4.2 Update training status tracking to reflect both pipelines — state is `"complete"` only when both finish

## 5. Verification

- [x] 5.1 Run export on existing contributions and verify PageXML output is valid
- [x] 5.2 Run full training pipeline via `POST /training/start` and verify both models are produced
