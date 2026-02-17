## ADDED Requirements

### Requirement: Training button in toolbar
The toolbar SHALL display a "Start Training" icon button, positioned after the "Contribute Training Data" button within the same toolbar group.

#### Scenario: Button visible in toolbar
- **WHEN** the application loads
- **THEN** a training button with the FitnessCenterIcon is visible in the toolbar after the Contribute button

#### Scenario: Button disabled while training is active
- **WHEN** training is in progress (state is "exporting", "training", or "deploying")
- **THEN** the training button SHALL display a loading spinner and be disabled

#### Scenario: Button enabled when idle
- **WHEN** training state is "idle", "complete", or "failed"
- **THEN** the training button SHALL be enabled

### Requirement: Training configuration dialog
Clicking the training button SHALL open a dialog where the user can configure training parameters before starting.

#### Scenario: Dialog opens on button click
- **WHEN** user clicks the enabled training button
- **THEN** a dialog titled "Start Training" opens with fields for epochs and image size

#### Scenario: Default parameter values
- **WHEN** the dialog opens
- **THEN** the epochs field SHALL default to 100
- **THEN** the image size field SHALL default to 640

#### Scenario: User starts training from dialog
- **WHEN** user clicks the "Start" button in the dialog
- **THEN** a POST request is sent to `/training/start` with the configured epochs and imgsz
- **THEN** the dialog closes

#### Scenario: User cancels dialog
- **WHEN** user clicks "Cancel" in the dialog
- **THEN** the dialog closes without starting training

### Requirement: Training progress chip
The toolbar SHALL display a chip showing live training progress while training is active.

#### Scenario: Chip shown during exporting phase
- **WHEN** training state is "exporting"
- **THEN** a chip with label "Exporting..." SHALL be displayed in the toolbar

#### Scenario: Chip shown during training phase
- **WHEN** training state is "training" with current_epoch and total_epochs available
- **THEN** a chip with label "Training {current_epoch}/{total_epochs}" SHALL be displayed

#### Scenario: Chip shown during deploying phase
- **WHEN** training state is "deploying"
- **THEN** a chip with label "Deploying..." SHALL be displayed

#### Scenario: Chip not shown when idle
- **WHEN** training state is "idle"
- **THEN** no training progress chip SHALL be displayed

### Requirement: Training status polling
The system SHALL poll `GET /training/status` to keep the UI in sync with backend training state.

#### Scenario: Poll on application mount
- **WHEN** the application loads
- **THEN** the system SHALL fetch training status once to detect in-progress training

#### Scenario: Poll while training is active
- **WHEN** training state is "exporting", "training", or "deploying"
- **THEN** the system SHALL poll `GET /training/status` every 2 seconds

#### Scenario: Stop polling when training finishes
- **WHEN** training state transitions to "idle", "complete", or "failed"
- **THEN** polling SHALL stop

### Requirement: Training completion feedback
The system SHALL display a success snackbar when training completes.

#### Scenario: Success snackbar on completion
- **WHEN** training state transitions to "complete"
- **THEN** a success snackbar SHALL display "Training complete!"

### Requirement: Training failure feedback
The system SHALL display an error message when training fails.

#### Scenario: Error shown on training failure
- **WHEN** training state transitions to "failed"
- **THEN** the error snackbar SHALL display the error message from the training status

### Requirement: Already-running handling
The system SHALL handle the case where training is already in progress when the user tries to start.

#### Scenario: 409 response triggers status poll
- **WHEN** `POST /training/start` returns 409 (training already running)
- **THEN** the system SHALL poll `GET /training/status` to display current progress
- **THEN** the system SHALL NOT show an error to the user

### Requirement: Service layer functions
The `htrService.ts` module SHALL export functions for training API calls.

#### Scenario: Start training function
- **WHEN** `startTraining(epochs, imgsz)` is called
- **THEN** a POST request is sent to `/training/start` with JSON body `{ epochs, imgsz }`
- **THEN** the response is parsed as `TrainingStatus`

#### Scenario: Get training status function
- **WHEN** `getTrainingStatus()` is called
- **THEN** a GET request is sent to `/training/status`
- **THEN** the response is parsed as `TrainingStatus`
