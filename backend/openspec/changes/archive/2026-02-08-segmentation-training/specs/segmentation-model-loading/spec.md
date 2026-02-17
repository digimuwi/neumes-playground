## ADDED Requirements

### Requirement: Use custom segmentation model when available
The `segment_image` function SHALL check for a custom model at `models/seg_model.mlmodel`. If it exists, that model SHALL be used for segmentation. Otherwise, the Kraken default model SHALL be used.

#### Scenario: Custom model exists
- **WHEN** `models/seg_model.mlmodel` exists on disk
- **THEN** `segment_image` uses that model for baseline segmentation

#### Scenario: No custom model
- **WHEN** `models/seg_model.mlmodel` does not exist
- **THEN** `segment_image` uses Kraken's built-in default segmentation model (current behavior)

#### Scenario: Custom model deployed during runtime
- **WHEN** a new `seg_model.mlmodel` is deployed while the server is running
- **THEN** subsequent calls to `segment_image` pick up the new model

### Requirement: Cache loaded segmentation model
The segmentation model SHALL be cached at module level to avoid reloading on every call. The cache SHALL be invalidated when the model file changes (by checking the file path or modification time).

#### Scenario: Model cached between calls
- **WHEN** `segment_image` is called multiple times with the same model file
- **THEN** the model is loaded only once

#### Scenario: Model file updated
- **WHEN** `seg_model.mlmodel` is replaced with a new version via atomic deploy
- **THEN** the next call to `segment_image` loads the updated model
