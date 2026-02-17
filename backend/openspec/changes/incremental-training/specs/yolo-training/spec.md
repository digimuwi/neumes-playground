## MODIFIED Requirements

### Requirement: Fine-tune from pretrained YOLOv8 backbone
Training SHALL auto-detect whether a previously trained neume model exists at `models/neume_detector.pt`. If it exists, training SHALL load it as the base model (incremental mode). If it does not exist, training SHALL load `yolov8n.pt` as the base model (fresh mode).

#### Scenario: Incremental training when trained model exists
- **WHEN** a training run starts and `models/neume_detector.pt` exists and `from_scratch` is not set
- **THEN** the model is loaded from `models/neume_detector.pt`
- **AND** default epochs is 30
- **AND** initial learning rate (`lr0`) is 0.001

#### Scenario: Fresh training when no trained model exists
- **WHEN** a training run starts and `models/neume_detector.pt` does not exist
- **THEN** the model is loaded from `yolov8n.pt`
- **AND** default epochs is 100
- **AND** initial learning rate (`lr0`) is 0.01 (ultralytics default)

#### Scenario: Force fresh training with from_scratch
- **WHEN** a training run starts with `from_scratch=true`
- **THEN** the model is loaded from `yolov8n.pt` regardless of whether `models/neume_detector.pt` exists
- **AND** default epochs is 100
- **AND** initial learning rate (`lr0`) is 0.01

### Requirement: Accept optional training parameters
The `POST /training/start` endpoint SHALL accept an optional JSON body with training configuration overrides.

#### Scenario: Custom epochs and image size
- **WHEN** `POST /training/start` is called with `{"epochs": 50, "imgsz": 320}`
- **THEN** training uses 50 epochs and 320px image size instead of defaults

#### Scenario: Default parameters used when body is empty
- **WHEN** `POST /training/start` is called with no body or an empty body
- **THEN** training uses mode-appropriate defaults: 100 epochs for fresh mode, 30 epochs for incremental mode; 640px image size

#### Scenario: Force fresh retrain
- **WHEN** `POST /training/start` is called with `{"from_scratch": true}`
- **THEN** training starts from `yolov8n.pt` with fresh-mode defaults (100 epochs) regardless of whether a trained model exists

## ADDED Requirements

### Requirement: Report training mode in status
The training status SHALL include a `mode` field indicating whether the current or last run used fresh or incremental training.

#### Scenario: Status reflects incremental mode
- **WHEN** `GET /training/status` is called during or after an incremental training run
- **THEN** the response includes `"mode": "incremental"`

#### Scenario: Status reflects fresh mode
- **WHEN** `GET /training/status` is called during or after a fresh training run
- **THEN** the response includes `"mode": "fresh"`

#### Scenario: No training has been run
- **WHEN** `GET /training/status` is called and no training has been started
- **THEN** the `mode` field is `null`
