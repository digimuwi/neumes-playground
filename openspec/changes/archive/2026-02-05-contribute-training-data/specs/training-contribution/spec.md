## ADDED Requirements

### Requirement: Contribute button in toolbar
The toolbar SHALL display a "Contribute" button with the VolunteerActivism icon, positioned after the Export MEI button.

#### Scenario: Button visible in toolbar
- **WHEN** the application loads
- **THEN** the Contribute button is visible in the toolbar after Export MEI

### Requirement: Contribute button enabled state
The Contribute button SHALL be enabled only when an image is loaded AND annotations contain at least one syllable AND at least one neume.

#### Scenario: Button disabled without image
- **WHEN** no image is loaded
- **THEN** the Contribute button is disabled

#### Scenario: Button disabled without syllables
- **WHEN** an image is loaded AND annotations contain neumes but no syllables
- **THEN** the Contribute button is disabled

#### Scenario: Button disabled without neumes
- **WHEN** an image is loaded AND annotations contain syllables but no neumes
- **THEN** the Contribute button is disabled

#### Scenario: Button enabled with complete annotations
- **WHEN** an image is loaded AND annotations contain at least one syllable AND at least one neume
- **THEN** the Contribute button is enabled

### Requirement: Submit training data on click
When clicked, the Contribute button SHALL submit the current image and annotations to the backend `/contribute` endpoint.

#### Scenario: Successful contribution submission
- **WHEN** user clicks enabled Contribute button
- **THEN** system sends POST request to `/contribute` with image blob and transformed annotations
- **THEN** annotations are transformed: syllables grouped into lines, coordinates converted from normalized (0-1) to pixels

### Requirement: Loading state during submission
The Contribute button SHALL show a loading indicator while the submission is in progress.

#### Scenario: Loading indicator shown
- **WHEN** contribution submission is in progress
- **THEN** the Contribute button displays a loading spinner
- **THEN** the Contribute button is disabled to prevent duplicate submissions

### Requirement: Success feedback
The system SHALL display a success message when contribution is submitted successfully.

#### Scenario: Success snackbar shown
- **WHEN** contribution submission completes successfully
- **THEN** a snackbar displays "Contribution submitted successfully"
- **THEN** the snackbar auto-dismisses after a few seconds

### Requirement: Error feedback
The system SHALL display an error message when contribution submission fails.

#### Scenario: Error snackbar shown on network failure
- **WHEN** contribution submission fails due to network error
- **THEN** the error snackbar displays an appropriate error message

#### Scenario: Error snackbar shown on server error
- **WHEN** contribution submission fails with server error (4xx or 5xx)
- **THEN** the error snackbar displays the error message from the response
