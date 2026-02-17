### Requirement: Browse contributions button in toolbar
The toolbar SHALL display a "Browse Contributions" button with the FolderOpen icon.

#### Scenario: Button visible in toolbar
- **WHEN** the application loads
- **THEN** a "Browse Contributions" button with FolderOpen icon is visible in the toolbar

### Requirement: Contributions dialog displays list
The contributions dialog SHALL display a list of stored contributions fetched from `GET /contributions`, showing each contribution's image filename, dimensions, line count, syllable count, and neume count.

#### Scenario: Dialog opens and shows contributions
- **WHEN** user clicks the "Browse Contributions" button
- **THEN** a dialog opens and fetches the contribution list from the backend
- **THEN** each contribution displays: image filename, dimensions (width x height), line count, syllable count, and neume count

#### Scenario: Dialog shows empty state
- **WHEN** user opens the contributions dialog AND no contributions exist
- **THEN** the dialog displays a message indicating no contributions are available

#### Scenario: Dialog shows loading state
- **WHEN** the contributions dialog is fetching the list
- **THEN** a loading indicator is displayed

#### Scenario: Dialog shows error state
- **WHEN** the contribution list fetch fails
- **THEN** the dialog displays an error message

### Requirement: Load contribution into editor
When the user clicks a contribution in the dialog, the system SHALL fetch the full contribution data from `GET /contributions/{id}` and load it into the editor, replacing the current state.

#### Scenario: Load contribution successfully
- **WHEN** user clicks a contribution in the list
- **THEN** the system fetches the full contribution data including base64 image
- **THEN** the editor state is replaced with the contribution's image, annotations, and line boundaries
- **THEN** the contribution dialog closes
- **THEN** the `contributionId` is set to the loaded contribution's ID

#### Scenario: Loading indicator while fetching contribution
- **WHEN** the system is fetching a contribution's full data after user clicks it
- **THEN** a loading indicator is shown

### Requirement: Service function for listing contributions
The `htrService` module SHALL export a `listContributions()` function that calls `GET /contributions` and returns the typed summary array.

#### Scenario: Successful list fetch
- **WHEN** `listContributions()` is called
- **THEN** it returns an array of `ContributionSummary` objects with id, image metadata, and counts

### Requirement: Service function for getting a contribution
The `htrService` module SHALL export a `getContribution(id)` function that calls `GET /contributions/{id}` and returns the image data URL, annotations, and line boundaries converted to frontend format.

#### Scenario: Successful contribution fetch
- **WHEN** `getContribution(id)` is called with a valid ID
- **THEN** it returns `{ imageDataUrl, annotations, lineBoundaries }` with annotations converted from pixel coordinates to normalized coordinates via `responseToAnnotations()`

#### Scenario: Contribution not found
- **WHEN** `getContribution(id)` is called with a non-existent ID
- **THEN** it throws an error with the 404 status information
