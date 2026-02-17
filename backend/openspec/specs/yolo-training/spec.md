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

### Requirement: Poll training status
The system SHALL provide a `GET /training/status` endpoint that returns the current state of the training pipeline.

#### Scenario: No training has been run
- **WHEN** `GET /training/status` is called and no training has been started
- **THEN** it returns HTTP 200 with `{"state": "idle"}`

#### Scenario: Training in progress
- **WHEN** `GET /training/status` is called while training is active
- **THEN** it returns HTTP 200 with state `"training"`, `current_epoch`, `total_epochs`, and latest `metrics` (if available)

#### Scenario: Training completed
- **WHEN** `GET /training/status` is called after a successful training run
- **THEN** it returns HTTP 200 with state `"complete"`, `model_version` (timestamp string), and `completed_at`

#### Scenario: Training failed
- **WHEN** `GET /training/status` is called after a failed training run
- **THEN** it returns HTTP 200 with state `"failed"` and an `error` message describing the failure

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

### Requirement: Export dataset before training
Each training run SHALL re-export the YOLO dataset from current contributions before starting the training loop. This ensures the training data always reflects the latest annotations.

#### Scenario: Fresh export before training
- **WHEN** a training run starts
- **THEN** the system runs the full YOLO export pipeline (same as `python -m htr_service.training.yolo_export`) before calling the ultralytics training API
- **AND** the training status shows state `"exporting"` during this phase

### Requirement: Save trained models with versioned timestamps
After successful training, the system SHALL save the trained model to `models/neume_versions/<timestamp>.pt` where `<timestamp>` is in `YYYYMMDD_HHMMSS` format.

#### Scenario: Model saved after training
- **WHEN** training completes successfully
- **THEN** the best model weights are saved to `models/neume_versions/<timestamp>.pt`
- **AND** the `models/neume_versions/` directory is created if it does not exist

### Requirement: Atomically deploy trained model
After saving the versioned model, the system SHALL atomically deploy it to `models/neume_detector.pt` using write-to-temp + `os.replace()`. This ensures the detection pipeline never reads a partially-written file.

#### Scenario: Atomic model deployment
- **WHEN** a trained model is saved to `models/neume_versions/<timestamp>.pt`
- **THEN** the model is copied to a temporary file in the `models/` directory and atomically moved to `models/neume_detector.pt` via `os.replace()`
- **AND** the existing `neume_detector.pt` (if any) is replaced without interrupting concurrent inference

### Requirement: Single concurrent training run
The system SHALL allow only one training run at a time. Concurrent training requests SHALL be rejected.

#### Scenario: Reject concurrent training
- **WHEN** `POST /training/start` is called while state is `"exporting"`, `"training"`, or `"deploying"`
- **THEN** the endpoint returns HTTP 409 Conflict
- **AND** no new training thread is started

### Requirement: Fine-tune from pretrained YOLOv8 backbone
Training SHALL start from a pretrained YOLOv8 backbone (COCO weights) and fine-tune on the exported neume dataset. This provides transfer learning benefits when per-class training data is limited.

#### Scenario: Training uses pretrained weights
- **WHEN** a training run starts
- **THEN** the ultralytics training API is called with `model="yolov8n.pt"` (nano size) as the base model
- **AND** standard YOLOv8 augmentation is enabled (mosaic, flip, scale, HSV jitter)
