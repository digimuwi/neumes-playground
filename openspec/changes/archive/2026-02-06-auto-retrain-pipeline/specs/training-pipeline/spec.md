## ADDED Requirements

### Requirement: Contribution counting
The system SHALL maintain a persistent count of contributions in `contributions/.count`.

#### Scenario: Count incremented on contribution
- **WHEN** a new contribution is saved successfully
- **THEN** the count in `contributions/.count` is incremented by 1

#### Scenario: Count file created if missing
- **WHEN** a contribution is saved AND `contributions/.count` does not exist
- **THEN** the file is created with value 1

### Requirement: Segmentation training trigger
The system SHALL trigger segmentation model training when the contribution count reaches a multiple of 10.

#### Scenario: Training triggered at threshold
- **WHEN** contribution count becomes 10, 20, 30, etc.
- **THEN** segmentation training is initiated in background

#### Scenario: Training not triggered between thresholds
- **WHEN** contribution count is not a multiple of 10
- **THEN** no segmentation training is triggered

### Requirement: Recognition training trigger
The system SHALL trigger recognition model training when the contribution count reaches a multiple of 30.

#### Scenario: Training triggered at threshold
- **WHEN** contribution count becomes 30, 60, 90, etc.
- **THEN** recognition training is initiated in background

### Requirement: Background training execution
Training processes SHALL run as detached subprocesses that do not block the API.

#### Scenario: API remains responsive during training
- **WHEN** training is running in background
- **THEN** the `/contribute` endpoint continues to accept new contributions

### Requirement: Training lock file
The system SHALL use a lock file to prevent concurrent training runs.

#### Scenario: Training skipped when locked
- **WHEN** training would be triggered AND `models/.training.lock` exists
- **THEN** training is skipped with a log message

#### Scenario: Lock file created during training
- **WHEN** training starts
- **THEN** `models/.training.lock` is created
- **WHEN** training completes (success or failure)
- **THEN** `models/.training.lock` is removed

### Requirement: Atomic model replacement
Trained models SHALL be written atomically to prevent corruption.

#### Scenario: Model written via temp file
- **WHEN** training completes successfully
- **THEN** model is written to temp file first
- **THEN** temp file is renamed to final location

### Requirement: PAGE XML filtering for recognition training
The system SHALL filter PAGE XML files by line type before recognition training.

#### Scenario: Text lines extracted
- **WHEN** recognition training starts
- **THEN** all PAGE XML files are processed
- **THEN** TextLines with `type:text` in custom attribute are written to `text_only/` directory

#### Scenario: Neume lines extracted
- **WHEN** recognition training starts
- **THEN** all PAGE XML files are processed
- **THEN** TextLines with `type:neume` in custom attribute are written to `neume_only/` directory

### Requirement: Segmentation training command
Segmentation training SHALL use ketos segtrain with appropriate options.

#### Scenario: Segtrain command executed
- **WHEN** segmentation training runs
- **THEN** command is: `ketos segtrain -f page -o models/segmentation contributions/*/page.xml`

### Requirement: Recognition training commands
Recognition training SHALL train separate models for text and neumes.

#### Scenario: Text recognition training
- **WHEN** recognition training runs
- **THEN** command includes: `ketos train -f page -o models/recognition_text text_only/*.xml`

#### Scenario: Neume recognition training
- **WHEN** recognition training runs
- **THEN** command includes: `ketos train -f page -o models/recognition_neume neume_only/*.xml`

### Requirement: Training log output
Training output SHALL be captured to a log file for debugging.

#### Scenario: Logs written
- **WHEN** training runs
- **THEN** stdout and stderr are appended to `models/training.log`
