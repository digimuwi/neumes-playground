## MODIFIED Requirements

### Requirement: Start training via API endpoint
The system SHALL provide a `POST /training/start` endpoint that triggers YOLOv8 and/or Kraken segmentation fine-tuning in independent background threads based on the requested `training_type`. The endpoint SHALL return HTTP 202 Accepted with the training run's status.

#### Scenario: Training started successfully with default training_type
- **WHEN** `POST /training/start` is called with no `training_type` (or `training_type: "both"`) and no training is currently in progress
- **THEN** the endpoint returns HTTP 202 with `{"state": "exporting", "started_at": "<iso-timestamp>"}`
- **AND** both YOLO and segmentation pipelines run (same as current behavior)

#### Scenario: Training only neumes
- **WHEN** `POST /training/start` is called with `{"training_type": "neumes"}`
- **THEN** only the YOLO export + training + deployment pipeline runs
- **AND** the segmentation pipeline is skipped entirely

#### Scenario: Training only segmentation
- **WHEN** `POST /training/start` is called with `{"training_type": "segmentation"}`
- **THEN** only the segmentation export + training + deployment pipeline runs
- **AND** the YOLO pipeline is skipped entirely

#### Scenario: Training already in progress
- **WHEN** `POST /training/start` is called while a training run is active
- **THEN** the endpoint returns HTTP 409 Conflict with `{"detail": "Training already in progress"}`

#### Scenario: Training complete with single pipeline
- **WHEN** only one pipeline was requested and it finishes successfully
- **THEN** the overall training state becomes `"complete"`

#### Scenario: Training complete with both pipelines
- **WHEN** both pipelines were requested and both finish (regardless of individual success/failure)
- **THEN** the overall training state becomes `"complete"` (or `"failed"` if either failed)

### Requirement: Accept optional training parameters
The `POST /training/start` endpoint SHALL accept an optional JSON body with training configuration overrides, including a `training_type` field.

#### Scenario: Select training type
- **WHEN** `POST /training/start` is called with `{"training_type": "neumes"}` or `{"training_type": "segmentation"}`
- **THEN** only the specified pipeline runs

#### Scenario: Custom epochs and image size
- **WHEN** `POST /training/start` is called with `{"epochs": 50, "imgsz": 320}`
- **THEN** training uses 50 epochs and 320px image size instead of defaults

#### Scenario: Default parameters used when body is empty
- **WHEN** `POST /training/start` is called with no body or an empty body
- **THEN** training uses defaults: 100 epochs, 640px image size, yolov8n.pt base model, `training_type: "both"`
