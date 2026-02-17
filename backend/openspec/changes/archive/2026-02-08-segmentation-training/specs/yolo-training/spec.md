## MODIFIED Requirements

### Requirement: Start training via API endpoint
The system SHALL provide a `POST /training/start` endpoint that triggers both YOLOv8 and Kraken segmentation fine-tuning in independent background threads. The endpoint SHALL return HTTP 202 Accepted with the training run's status. Both training processes run independently — neither depends on the other.

#### Scenario: Training started successfully
- **WHEN** `POST /training/start` is called and no training is currently in progress
- **THEN** the endpoint returns HTTP 202 with `{"state": "exporting", "started_at": "<iso-timestamp>"}`
- **AND** two independent background threads begin: one for YOLO export+training, one for segmentation export+training

#### Scenario: Training already in progress
- **WHEN** `POST /training/start` is called while a training run is active
- **THEN** the endpoint returns HTTP 409 Conflict with `{"detail": "Training already in progress"}`

#### Scenario: Training complete
- **WHEN** both YOLO and segmentation training finish (regardless of individual success/failure)
- **THEN** the overall training state becomes `"complete"` (or `"failed"` if either failed)
