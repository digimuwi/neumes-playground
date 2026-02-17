## 1. Contribution Counting

- [x] 1.1 Create `contribution/counter.py` with functions to read/increment count from `contributions/.count`
- [x] 1.2 Update `save_contribution()` in storage.py to call counter increment after successful save
- [x] 1.3 Add unit tests for counter (create if missing, increment, read)

## 2. Training Orchestration

- [x] 2.1 Create `training/` module directory with `__init__.py`
- [x] 2.2 Implement lock file management (`acquire_lock`, `release_lock`, `is_locked`)
- [x] 2.3 Implement `trigger_segmentation_training()` that spawns ketos segtrain as detached subprocess
- [x] 2.4 Implement `trigger_recognition_training()` that spawns ketos train for both models
- [x] 2.5 Add training log capture to `models/training.log`
- [x] 2.6 Implement atomic model writes (temp file + rename)

## 3. PAGE XML Filtering

- [x] 3.1 Create `training/filter_page_xml.py` with function to filter TextLines by type attribute
- [x] 3.2 Implement `filter_contributions(source_dir, output_dir, line_type)` function
- [x] 3.3 Add unit tests for PAGE XML filtering (text only, neume only, mixed input)

## 4. Training Trigger Integration

- [x] 4.1 Create `training/triggers.py` with `check_and_trigger_training(count)` function
- [x] 4.2 Call training trigger from storage.py after incrementing count
- [x] 4.3 Add integration test for full contribution → training trigger flow

## 5. Multi-Model Inference

- [x] 5.1 Create `pipeline/model_loader.py` with model existence checks and caching with mtime validation
- [x] 5.2 Update `segmentation.py` to use custom model when available, fall back to default
- [x] 5.3 Update `recognition.py` to use `mm_rpred` when both models available
- [x] 5.4 Add fallback logic: skip neume lines when only text model exists
- [x] 5.5 Add unit tests for model detection and fallback behavior

## 6. End-to-End Verification

- [x] 6.1 Manual test: submit contribution, verify count incremented
- [x] 6.2 Manual test: submit 10th contribution, verify segmentation training triggered
- [x] 6.3 Manual test: verify inference still works with no custom models (fallback to current behavior)
