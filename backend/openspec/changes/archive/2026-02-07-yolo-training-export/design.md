## Context

Contributions are stored as `contributions/<uuid>/image.{ext}` + `annotations.json` (with lines, syllables, and neumes). The neume detection pipeline (`pipeline/neume_detection.py`) expects a trained YOLOv8 model at `models/neume_detector.pt`, but no model exists yet. To train one, we need to convert stored contributions into YOLO's expected dataset format.

Existing modules already handle the two hardest parts:
- `pipeline/segmentation.py` — Kraken `blla.segment()` for text boundary polygons
- `pipeline/text_masking.py` — erases text from RGB images using those polygons

The export pipeline composes these with bbox normalization and class mapping.

## Goals / Non-Goals

**Goals:**
- Convert stored contributions into a valid YOLOv8 training dataset
- Apply text masking to training images (consistent with inference preprocessing)
- Provide a stable, append-only neume class mapping (`neume_classes.yaml`)
- Generate `dataset.yaml` for direct use with `yolo train`
- Support configurable train/val split

**Non-Goals:**
- Automated training (Change 8)
- Model versioning or hot-swap (Change 8)
- Active learning / pre-annotation (Change 8)
- Incremental export (re-exports everything each time)
- Data augmentation config (built into YOLOv8 training, not export)

## Decisions

### 1. Run Kraken segmentation at export time

**Decision**: Segment each contribution image during export rather than caching segmentation at contribution time.

**Rationale**: Contributions are raw annotations from the frontend — they don't include segmentation data. Caching segmentation results would add storage complexity and a migration step for existing contributions. Export is a batch operation run infrequently (before each training run), so the extra compute is acceptable.

**Alternative considered**: Store segmentation alongside contributions at `/contribute` time. Rejected because it couples the contribution endpoint to Kraken and increases storage per contribution.

### 2. Append-only `neume_classes.yaml` for class mapping

**Decision**: A YAML file at the project root maps neume type strings to integer class IDs. The file is manually maintained and append-only — new types get the next integer, existing types never change ID.

**Rationale**: YOLO labels use integer class IDs. The mapping must be stable across training runs (if "punctum" was class 0 in run 1, it must stay class 0 in run 2). An append-only file is the simplest way to guarantee this.

Unknown neume types in contributions (types not in `neume_classes.yaml`) are logged as warnings and skipped. Contributions with zero exportable neumes (all types unknown) are skipped entirely.

**Alternative considered**: Auto-generate the mapping from all observed types. Rejected because ordering would be non-deterministic and could change between exports, breaking model compatibility.

### 3. Dataset output directory

**Decision**: Export writes to a configurable output directory, defaulting to `datasets/neumes/` relative to the project root.

Layout:
```
datasets/neumes/
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

**Rationale**: Standard YOLOv8 dataset structure. Using the contribution UUID as filename ensures uniqueness without additional bookkeeping.

### 4. Random train/val split by contribution

**Decision**: Split contributions randomly using a configurable ratio (default 80/20) with a fixed random seed for reproducibility.

**Rationale**: Simple and sufficient for initial training. Per-manuscript splitting would be better for data leakage prevention, but contributions don't currently store manuscript provenance metadata. Can be refined in a later change.

### 5. Export as a CLI script, not an API endpoint

**Decision**: The export runs as a Python script (`python -m htr_service.training.yolo_export`) invoked manually before training.

**Rationale**: Export is a batch operation that takes minutes (Kraken segmentation per image). It doesn't belong in the request-response cycle. A script is simpler than a background task queue and matches the manual workflow: annotate → export → train.

### 6. Masked images saved as JPEG

**Decision**: Text-masked images are saved as JPEG regardless of the original image format.

**Rationale**: YOLO training expects image files. JPEG is smaller than PNG and quality loss from JPEG compression is irrelevant for training (the model learns from augmented data anyway). Consistent format simplifies the dataset.

## Risks / Trade-offs

**[Slow export for large contribution sets]** → Each contribution requires Kraken segmentation (~seconds per image). For 100+ contributions, export takes minutes. Acceptable for manual batch workflow; can add parallelism later if needed.

**[Unknown neume types silently skipped]** → If an annotator uses a type not in `neume_classes.yaml`, those annotations are lost from training data. Mitigated by logging warnings with the unknown type and contribution ID, so the user can update the YAML and re-export.

**[No incremental export]** → Full re-export every time. For small datasets (dozens of contributions), this is fine. For larger datasets, could add a manifest tracking already-exported contributions. Deferred.

**[Train/val leakage]** → Random split by contribution doesn't prevent the same manuscript page from appearing in both train and val (if annotated multiple times). Low risk given the small initial dataset and manual annotation workflow.
