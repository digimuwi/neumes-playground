## MODIFIED Requirements

### Requirement: Export contributions to YOLO dataset format

The system SHALL provide a batch export command (`python -m htr_service.training.yolo_export`) that converts all stored contributions into a YOLOv8-compatible training dataset.

For each contribution, the export SHALL:
1. Load the image from `contributions/<uuid>/image.{ext}`
2. Collect all syllable boundary polygons from `contributions/<uuid>/annotations.json`
3. Mask the collected syllable polygon regions on the RGB image using `mask_polygon_regions()`
4. Read neume annotations from `contributions/<uuid>/annotations.json`
5. Convert each neume bbox to YOLO normalized format: `class_id x_center y_center width height`
6. Save the masked image and label file to the output dataset directory

The export SHALL NOT re-run Kraken segmentation. Text masking SHALL be driven entirely by the contributed syllable polygon boundaries.

#### Scenario: Export contribution with user-corrected annotations
- **WHEN** a contribution exists where the user removed syllable boxes that were over neume regions
- **THEN** export masks only the remaining syllable polygon regions, leaving neume areas unmasked and visible in training images

#### Scenario: Export single contribution with neumes
- **WHEN** a contribution exists with image and annotations containing neumes of known types and syllable polygon boundaries
- **THEN** export produces masked JPEG tile images and `.txt` label files with one YOLO-format line per neume

#### Scenario: Contribution with no neumes
- **WHEN** a contribution has annotations with empty neumes array
- **THEN** export skips that contribution entirely (no image or label file produced)

#### Scenario: Contribution with only unknown neume types
- **WHEN** all neume types in a contribution are absent from `neume_classes.yaml`
- **THEN** export logs a warning for each unknown type and skips the contribution

#### Scenario: Contribution with no syllable polygons
- **WHEN** a contribution has annotations with empty lines array (no text regions at all)
- **THEN** export proceeds without masking (the full image is used for neume detection training)
