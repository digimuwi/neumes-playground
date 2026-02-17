## 1. Contribution listing

- [x] 1.1 Add `list_contributions()` function to `contribution/storage.py` that returns all valid `(id, path)` tuples from the `contributions/` directory, skipping malformed entries with a warning
- [x] 1.2 Add tests for `list_contributions()` — populated dir, empty dir, malformed contribution skipped

## 2. Neume class mapping

- [x] 2.1 Create `neume_classes.yaml` at the project root with initial neume type list (punctum, clivis, podatus, torculus, scandicus, climacus, porrectus, pes, virga, oriscus, quilisma, stropha, pressus, bistropha, tristropha, bivirga, trivirga)
- [x] 2.2 Add `load_neume_classes(path)` function in `training/yolo_export.py` that reads the YAML and returns `dict[str, int]` mapping type names to class IDs (by list position); raise error if file missing

## 3. Core export logic

- [x] 3.1 Create `training/__init__.py` and `training/yolo_export.py` module with the main `export_dataset()` function
- [x] 3.2 Implement single-contribution export: load image, run Kraken segmentation, mask text, read annotations, convert neume bboxes to YOLO normalized format, save masked JPEG + label `.txt` file
- [x] 3.3 Implement train/val splitting with configurable ratio and fixed random seed
- [x] 3.4 Implement `dataset.yaml` generation with absolute path, train/val image dirs, and full class name mapping
- [x] 3.5 Implement output directory management — clear and recreate on each run

## 4. CLI interface

- [x] 4.1 Add `__main__.py` block or argparse CLI in `training/yolo_export.py` with `--output-dir`, `--val-ratio`, and `--seed` options
- [x] 4.2 Add completion summary output (exported count, skipped count, train/val breakdown, output path)

## 5. Tests

- [x] 5.1 Test YOLO bbox normalization — verify `x_center, y_center, width, height` calculation from pixel bbox and image dimensions
- [x] 5.2 Test class mapping — known type maps to correct ID, unknown type returns None/skipped
- [x] 5.3 Test export with mock contributions — verify output directory structure, image files, label file content, dataset.yaml
- [x] 5.4 Test skip logic — contributions with no neumes skipped, contributions with all-unknown types skipped, mixed known/unknown includes only known
- [x] 5.5 Test train/val split reproducibility — same seed produces same split
