## MODIFIED Requirements

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

## ADDED Requirements

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
