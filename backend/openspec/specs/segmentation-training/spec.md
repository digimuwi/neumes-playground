### Requirement: Fine-tune Kraken segmentation model from contributions
The system SHALL provide a `run_segmentation_training` function that fine-tunes Kraken's default segmentation model using the exported PageXML dataset. Training SHALL use Kraken's Python training API (`kraken.lib.train.SegmentationModel`).

#### Scenario: Training from exported dataset
- **WHEN** `run_segmentation_training` is called with a directory containing PageXML files and images
- **THEN** Kraken's segmentation training runs using the default `blla.mlmodel` as the base model with `--resize union` behavior to add new region types

#### Scenario: No exported data
- **WHEN** the export produced zero PageXML files
- **THEN** segmentation training is skipped and logged as a warning

### Requirement: Configurable training parameters
The function SHALL accept optional parameters for epochs (default: 50), learning rate, and device.

#### Scenario: Custom epochs
- **WHEN** `run_segmentation_training` is called with `epochs=30`
- **THEN** training runs for 30 epochs

#### Scenario: Default parameters
- **WHEN** `run_segmentation_training` is called with no parameters
- **THEN** training uses 50 epochs and default learning rate

### Requirement: Save trained models with versioned timestamps
After successful training, the system SHALL save the trained model to `models/seg_versions/<timestamp>.mlmodel` where `<timestamp>` is in `YYYYMMDD_HHMMSS` format.

#### Scenario: Model saved after training
- **WHEN** segmentation training completes successfully
- **THEN** the best model is saved to `models/seg_versions/<timestamp>.mlmodel`

### Requirement: Atomically deploy trained segmentation model
After saving the versioned model, the system SHALL atomically deploy it to `models/seg_model.mlmodel` using write-to-temp + `os.replace()`.

#### Scenario: Atomic deployment
- **WHEN** a trained segmentation model is saved
- **THEN** it is copied to a temporary file and atomically moved to `models/seg_model.mlmodel`
- **AND** the existing model (if any) is replaced without interrupting concurrent inference

### Requirement: Re-enable PyTorch gradients before training
The function SHALL call `torch.set_grad_enabled(True)` before starting Kraken training to counteract Kraken's `blla.segment()` disabling gradients during export.

#### Scenario: Gradient tracking restored
- **WHEN** segmentation training starts after export (which calls `blla.segment` internally or not)
- **THEN** `torch.set_grad_enabled(True)` is called before the training loop
