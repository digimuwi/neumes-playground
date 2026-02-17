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
Clicking the training button SHALL open a dialog where the user can configure training parameters before starting. The training type toggle SHALL be displayed prominently at the top, followed by a dynamic description, then parameters hidden under a collapsible "Advanced Settings" section.

#### Scenario: Dialog opens on button click
- **WHEN** user clicks the enabled training button
- **THEN** a dialog titled "Start Training" opens with the training type toggle, dynamic description, a collapsed "Advanced Settings" section, and visible Start/Cancel buttons

#### Scenario: Advanced settings collapsed by default
- **WHEN** the dialog opens
- **THEN** the "Advanced Settings" section SHALL be collapsed
- **THEN** the Start button SHALL be immediately clickable

#### Scenario: Advanced settings expanded
- **WHEN** user expands the "Advanced Settings" section
- **THEN** only the fields relevant to the selected training type SHALL be visible

#### Scenario: Default parameter values
- **WHEN** the dialog opens
- **THEN** the training type toggle SHALL default to "Both"
- **THEN** the YOLO epochs field SHALL be empty with placeholder text "Auto (100 fresh / 30 incr.)"
- **THEN** the image size field SHALL default to 640
- **THEN** the segmentation epochs field SHALL default to 50
- **THEN** the "Train from scratch" checkbox SHALL be unchecked

#### Scenario: User starts training with defaults
- **WHEN** user clicks the "Start" button without changing any settings
- **THEN** a POST request is sent to `/training/start` with JSON body `{}` (all defaults)
- **THEN** the dialog closes

#### Scenario: User starts training with custom parameters
- **WHEN** user configures parameters and clicks "Start"
- **THEN** a POST request is sent to `/training/start` with only the non-default values in the JSON body
- **THEN** the dialog closes

#### Scenario: User starts training with specific pipeline
- **WHEN** user selects "Neumes" or "Segmentation" and clicks "Start"
- **THEN** a POST request is sent to `/training/start` with `training_type` set to the selected value
- **THEN** the dialog closes

#### Scenario: User cancels dialog
- **WHEN** user clicks "Cancel" in the dialog
- **THEN** the dialog closes without starting training

### Requirement: Training progress chip
The toolbar SHALL display a chip showing live training progress while training is active, including the training mode when available.

#### Scenario: Chip shown during exporting phase
- **WHEN** training state is "exporting"
- **THEN** a chip with label "Exporting..." SHALL be displayed in the toolbar

#### Scenario: Chip shown during training phase with mode
- **WHEN** training state is "training" with current_epoch, total_epochs, and mode available
- **THEN** a chip with label "Training ({mode}) {current_epoch}/{total_epochs}" SHALL be displayed

#### Scenario: Chip shown during training phase without mode
- **WHEN** training state is "training" with current_epoch and total_epochs available but mode is null
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
The `htrService.ts` module SHALL export functions for training API calls with updated type signatures.

#### Scenario: Start training function
- **WHEN** `startTraining(options?)` is called with an optional `TrainingStartOptions` object
- **THEN** a POST request is sent to `/training/start` with the options as JSON body
- **THEN** the response is parsed as `TrainingStatus`

#### Scenario: TrainingStartOptions shape
- **WHEN** constructing a training start request
- **THEN** the options object SHALL support optional fields: `epochs` (number | null), `imgsz` (number), `seg_epochs` (number), `from_scratch` (boolean), and `training_type` (`"neumes" | "segmentation" | "both"`)

#### Scenario: TrainingStatus includes mode
- **WHEN** parsing a `TrainingStatus` response
- **THEN** the type SHALL include a `mode` field of type `"fresh" | "incremental" | null`

#### Scenario: Get training status function
- **WHEN** `getTrainingStatus()` is called
- **THEN** a GET request is sent to `/training/status`
- **THEN** the response is parsed as `TrainingStatus`

### Requirement: Training type selection toggle
The training dialog SHALL display a ToggleButtonGroup above the description text, allowing the user to select which pipeline(s) to train.

#### Scenario: Toggle visible with three options
- **WHEN** the training dialog opens
- **THEN** a ToggleButtonGroup SHALL be displayed with three options: "Neumes", "Segmentation", and "Both"

#### Scenario: Default selection is "Both"
- **WHEN** the training dialog opens
- **THEN** the "Both" option SHALL be selected by default

#### Scenario: User selects a training type
- **WHEN** the user clicks a different toggle option
- **THEN** that option SHALL become the active selection

#### Scenario: Selection is exclusive
- **WHEN** the user selects one option
- **THEN** the previously selected option SHALL be deselected

#### Scenario: Selection cannot be cleared
- **WHEN** the user clicks the already-selected option
- **THEN** it SHALL remain selected (enforce at least one selection)

### Requirement: Dynamic dialog description
The training dialog description text SHALL update to reflect the selected training type.

#### Scenario: Description when "Both" is selected
- **WHEN** the selected training type is "both"
- **THEN** the description SHALL read "Train neume detection and line segmentation models from current contributions."

#### Scenario: Description when "Neumes" is selected
- **WHEN** the selected training type is "neumes"
- **THEN** the description SHALL read "Train the neume detection model from current contributions."

#### Scenario: Description when "Segmentation" is selected
- **WHEN** the selected training type is "segmentation"
- **THEN** the description SHALL read "Train the line segmentation model from current contributions."

### Requirement: Conditional advanced settings visibility
Advanced settings fields SHALL only be visible when relevant to the selected training type.

#### Scenario: All fields visible for "Both"
- **WHEN** the selected training type is "both"
- **THEN** YOLO Epochs, Image Size, Segmentation Epochs, and Train from Scratch fields SHALL all be visible

#### Scenario: Neume fields visible for "Neumes"
- **WHEN** the selected training type is "neumes"
- **THEN** YOLO Epochs, Image Size, and Train from Scratch fields SHALL be visible
- **THEN** Segmentation Epochs SHALL NOT be visible

#### Scenario: Segmentation fields visible for "Segmentation"
- **WHEN** the selected training type is "segmentation"
- **THEN** Segmentation Epochs and Train from Scratch fields SHALL be visible
- **THEN** YOLO Epochs and Image Size SHALL NOT be visible
