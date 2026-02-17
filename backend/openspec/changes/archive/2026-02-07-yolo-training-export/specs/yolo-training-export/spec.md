## ADDED Requirements

### Requirement: Export contributions to YOLO dataset format

The system SHALL provide a batch export command (`python -m htr_service.training.yolo_export`) that converts all stored contributions into a YOLOv8-compatible training dataset.

For each contribution, the export SHALL:
1. Load the image from `contributions/<uuid>/image.{ext}`
2. Run Kraken segmentation (`blla.segment`) to obtain text boundary polygons
3. Mask text regions on the RGB image using `mask_text_regions()`
4. Read neume annotations from `contributions/<uuid>/annotations.json`
5. Convert each neume bbox to YOLO normalized format: `class_id x_center y_center width height`
6. Save the masked image and label file to the output dataset directory

The YOLO normalized format SHALL compute coordinates as:
- `x_center = (bbox.x + bbox.width / 2) / image_width`
- `y_center = (bbox.y + bbox.height / 2) / image_height`
- `width = bbox.width / image_width`
- `height = bbox.height / image_height`

#### Scenario: Export single contribution with neumes
- **WHEN** a contribution exists with image and annotations containing neumes of known types
- **THEN** export produces a masked JPEG image and a `.txt` label file with one YOLO-format line per neume

#### Scenario: Contribution with no neumes
- **WHEN** a contribution has annotations with empty neumes array
- **THEN** export skips that contribution entirely (no image or label file produced)

#### Scenario: Contribution with only unknown neume types
- **WHEN** all neume types in a contribution are absent from `neume_classes.yaml`
- **THEN** export logs a warning for each unknown type and skips the contribution

#### Scenario: Contribution with mixed known and unknown types
- **WHEN** a contribution contains some neumes with known types and some with unknown types
- **THEN** export includes the contribution, writing only the known-type neumes to the label file, and logs warnings for each unknown type

### Requirement: Neume class mapping via neume_classes.yaml

The system SHALL use a `neume_classes.yaml` file at the project root to map neume type strings to integer class IDs.

The file format SHALL be:
```yaml
classes:
  - punctum      # class ID 0
  - clivis       # class ID 1
  - podatus      # class ID 2
  # ...
```

Class IDs SHALL be assigned by list position (0-indexed). The file SHALL be append-only: new types are added at the end, existing types are never removed or reordered.

#### Scenario: Known neume type mapped to class ID
- **WHEN** a neume annotation has type "clivis" and "clivis" is at index 1 in `neume_classes.yaml`
- **THEN** the YOLO label line uses class ID `1`

#### Scenario: Unknown neume type
- **WHEN** a neume annotation has a type not present in `neume_classes.yaml`
- **THEN** that neume is excluded from the label file and a warning is logged naming the unknown type and contribution ID

#### Scenario: Missing neume_classes.yaml
- **WHEN** the `neume_classes.yaml` file does not exist
- **THEN** export exits with an error message indicating the file is required

### Requirement: Dataset directory structure

The export SHALL write output to a configurable directory (default: `datasets/neumes/` relative to project root) with the following structure:

```
<output_dir>/
├── images/
│   ├── train/
│   │   └── <uuid>.jpg
│   └── val/
│       └── <uuid>.jpg
├── labels/
│   ├── train/
│   │   └── <uuid>.txt
│   └── val/
│       └── <uuid>.txt
└── dataset.yaml
```

Image files SHALL be saved as JPEG regardless of original format. Label files SHALL use the contribution UUID as filename (matching the corresponding image).

The export SHALL clear and recreate the output directory on each run.

#### Scenario: Output directory created from scratch
- **WHEN** export runs and the output directory does not exist
- **THEN** the full directory structure is created with images/, labels/, train/, val/ subdirectories

#### Scenario: Output directory already exists
- **WHEN** export runs and the output directory already exists from a previous run
- **THEN** the old directory is removed and a fresh dataset is created

### Requirement: Generate dataset.yaml

The export SHALL generate a `dataset.yaml` file in the output directory with the following content:

```yaml
path: <absolute_path_to_output_dir>
train: images/train
val: images/val

names:
  0: punctum
  1: clivis
  # ... all classes from neume_classes.yaml
```

This file SHALL be directly usable with `yolo train data=dataset.yaml`.

#### Scenario: dataset.yaml generated with all classes
- **WHEN** export completes successfully
- **THEN** `dataset.yaml` contains all classes from `neume_classes.yaml` with correct ID-to-name mapping

#### Scenario: dataset.yaml has correct paths
- **WHEN** export writes to a directory
- **THEN** `dataset.yaml` `path` field contains the absolute path to that directory

### Requirement: Configurable train/val split

The export SHALL split contributions into training and validation sets with a configurable ratio (default: 0.8 train / 0.2 val).

The split SHALL use a fixed random seed (default: 42) for reproducibility across runs.

#### Scenario: Default 80/20 split
- **WHEN** export runs with 10 exportable contributions and default settings
- **THEN** 8 contributions go to train/ and 2 go to val/

#### Scenario: Custom split ratio
- **WHEN** export runs with `--val-ratio 0.3`
- **THEN** 30% of contributions go to val/ and 70% to train/

#### Scenario: Reproducible split
- **WHEN** export runs twice with the same contributions and same seed
- **THEN** the same contributions end up in train/ and val/ both times

### Requirement: CLI interface

The export SHALL be invocable as `python -m htr_service.training.yolo_export` with the following options:

- `--output-dir`: Output directory path (default: `datasets/neumes`)
- `--val-ratio`: Fraction of contributions for validation (default: 0.2)
- `--seed`: Random seed for train/val split (default: 42)

The export SHALL print a summary on completion: number of contributions exported, number skipped, train/val counts, and output directory path.

#### Scenario: Run with defaults
- **WHEN** user runs `python -m htr_service.training.yolo_export`
- **THEN** export runs with default output dir, 0.2 val ratio, and seed 42

#### Scenario: Run with custom options
- **WHEN** user runs `python -m htr_service.training.yolo_export --output-dir /tmp/yolo --val-ratio 0.3 --seed 123`
- **THEN** export writes to `/tmp/yolo` with 30% validation split using seed 123

#### Scenario: Completion summary
- **WHEN** export finishes processing 10 contributions (8 exported, 2 skipped)
- **THEN** output shows exported count, skipped count, train/val breakdown, and output path
