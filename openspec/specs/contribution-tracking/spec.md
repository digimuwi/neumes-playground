### Requirement: contributionId field in app state
The `AppState` SHALL include a `contributionId: string | null` field that tracks which contribution is currently being edited.

#### Scenario: Initial state
- **WHEN** the application starts with no persisted state
- **THEN** `contributionId` is null

### Requirement: SET_CONTRIBUTION_ID action
The reducer SHALL handle a `SET_CONTRIBUTION_ID` action that sets the `contributionId` field without creating an undo/redo history entry.

#### Scenario: Set contribution ID
- **WHEN** `SET_CONTRIBUTION_ID` is dispatched with a string ID
- **THEN** `contributionId` is set to that ID
- **THEN** no new undo/redo history entry is created

#### Scenario: Clear contribution ID
- **WHEN** `SET_CONTRIBUTION_ID` is dispatched with null
- **THEN** `contributionId` is set to null

### Requirement: Clear contributionId on new image
The reducer SHALL clear `contributionId` to null when the `SET_IMAGE` action is dispatched, since uploading a new image means the user is no longer editing an existing contribution.

#### Scenario: New image clears contribution tracking
- **WHEN** user uploads a new image (SET_IMAGE dispatched)
- **THEN** `contributionId` is set to null

### Requirement: Persist contributionId in localStorage
The `contributionId` SHALL be persisted to and loaded from localStorage alongside the rest of the app state.

#### Scenario: Persist on state change
- **WHEN** state is saved to localStorage
- **THEN** `contributionId` is included in the persisted data

#### Scenario: Restore on load
- **WHEN** state is loaded from localStorage
- **THEN** `contributionId` is restored from the persisted data (or null if absent)

### Requirement: Contribution ID chip in toolbar
When `contributionId` is set, the toolbar SHALL display a small Chip showing the contribution ID (truncated).

#### Scenario: Chip visible when editing contribution
- **WHEN** `contributionId` is set to a non-null value
- **THEN** a Chip is displayed in the toolbar showing the contribution ID

#### Scenario: Chip hidden for new work
- **WHEN** `contributionId` is null
- **THEN** no contribution ID chip is displayed
