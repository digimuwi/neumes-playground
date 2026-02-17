## MODIFIED Requirements

### Requirement: Training configuration dialog
Clicking the training button SHALL open a dialog where the user can configure training parameters before starting. Parameters SHALL be hidden under a collapsible "Advanced Settings" section so users can start immediately with defaults.

#### Scenario: Dialog opens on button click
- **WHEN** user clicks the enabled training button
- **THEN** a dialog titled "Start Training" opens with a collapsed "Advanced Settings" section and visible Start/Cancel buttons

#### Scenario: Advanced settings collapsed by default
- **WHEN** the dialog opens
- **THEN** the "Advanced Settings" section SHALL be collapsed
- **THEN** the Start button SHALL be immediately clickable

#### Scenario: Advanced settings expanded
- **WHEN** user expands the "Advanced Settings" section
- **THEN** fields for YOLO epochs, image size, segmentation epochs, and a "Train from scratch" checkbox SHALL be visible

#### Scenario: Default parameter values
- **WHEN** the dialog opens
- **THEN** the YOLO epochs field SHALL be empty with placeholder text "Auto (100 fresh / 30 incr.)"
- **THEN** the image size field SHALL default to 640
- **THEN** the segmentation epochs field SHALL default to 50
- **THEN** the "Train from scratch" checkbox SHALL be unchecked

#### Scenario: User starts training with defaults
- **WHEN** user clicks the "Start" button without expanding advanced settings
- **THEN** a POST request is sent to `/training/start` with JSON body `{}` (all defaults)
- **THEN** the dialog closes

#### Scenario: User starts training with custom parameters
- **WHEN** user configures parameters and clicks "Start"
- **THEN** a POST request is sent to `/training/start` with only the non-default values in the JSON body
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

### Requirement: Service layer functions
The `htrService.ts` module SHALL export functions for training API calls with updated type signatures.

#### Scenario: Start training function
- **WHEN** `startTraining(options?)` is called with an optional `TrainingStartOptions` object
- **THEN** a POST request is sent to `/training/start` with the options as JSON body
- **THEN** the response is parsed as `TrainingStatus`

#### Scenario: TrainingStartOptions shape
- **WHEN** constructing a training start request
- **THEN** the options object SHALL support optional fields: `epochs` (number | null), `imgsz` (number), `seg_epochs` (number), and `from_scratch` (boolean)

#### Scenario: TrainingStatus includes mode
- **WHEN** parsing a `TrainingStatus` response
- **THEN** the type SHALL include a `mode` field of type `"fresh" | "incremental" | null`

#### Scenario: Get training status function
- **WHEN** `getTrainingStatus()` is called
- **THEN** a GET request is sent to `/training/status`
- **THEN** the response is parsed as `TrainingStatus`
