## MODIFIED Requirements

### Requirement: Return empty list when no YOLO model exists
When no trained YOLO model file is found at the expected path, `detect_neumes` SHALL return an empty list and log a warning message indicating that no neume detection model is available yet. The warning message SHALL reference `POST /training/start` as the way to train a model.

#### Scenario: No model file present
- **WHEN** `detect_neumes` is called and no YOLO model file exists at the configured path
- **THEN** it returns an empty list
- **AND** a warning is logged indicating the model is not yet available and suggesting to use `POST /training/start`
