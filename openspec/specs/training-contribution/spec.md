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
When clicked, the Contribute button SHALL either create a new contribution (POST) or update an existing one (PUT), depending on whether `contributionId` is set.

#### Scenario: Create new contribution (contributionId is null)
- **WHEN** user clicks enabled Contribute button AND `contributionId` is null
- **THEN** system sends POST request to `/contribute` with image blob and transformed annotations
- **THEN** annotations are transformed: syllables grouped into lines with polygon boundaries, coordinates converted from normalized (0-1) to pixels
- **THEN** each line includes its `boundary` polygon (from stored OCR line boundaries or synthesized from syllable polygons)
- **THEN** each syllable includes its `boundary` polygon (denormalized to pixel coordinates)
- **THEN** neumes include `bbox: {x, y, width, height}` computed from their polygon bounding rect (denormalized to pixels)
- **THEN** on success, `contributionId` is set to the returned contribution ID

#### Scenario: Update existing contribution (contributionId is set)
- **WHEN** user clicks enabled Contribute button AND `contributionId` is set
- **THEN** system sends PUT request to `/contributions/{contributionId}` with transformed annotations as JSON body
- **THEN** annotations are transformed using the same logic as create
- **THEN** on success, a success snackbar is displayed

#### Scenario: Tooltip reflects mode
- **WHEN** `contributionId` is null
- **THEN** the Contribute button tooltip reads "Contribute Training Data"
- **WHEN** `contributionId` is set
- **THEN** the Contribute button tooltip reads "Update Contribution"

#### Scenario: Contribution triggers training check
- **WHEN** backend saves contribution successfully
- **THEN** contribution count is incremented
- **THEN** training is triggered if count reaches threshold (10 for segmentation, 30 for recognition)

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

### Requirement: Service function for updating a contribution
The `htrService` module SHALL export an `updateContribution(id, imageDataUrl, annotations, lineBoundaries)` function that transforms annotations to backend format and sends a PUT request to `/contributions/{id}`.

#### Scenario: Successful update
- **WHEN** `updateContribution(id, imageDataUrl, annotations, lineBoundaries)` is called
- **THEN** annotations are transformed using `transformAnnotationsForContribution()`
- **THEN** a PUT request is sent to `/contributions/{id}` with the transformed annotations as JSON body
- **THEN** it returns the `ContributionResponse`

#### Scenario: Update not found
- **WHEN** `updateContribution` is called with a non-existent ID
- **THEN** it throws an error with the 404 status information
