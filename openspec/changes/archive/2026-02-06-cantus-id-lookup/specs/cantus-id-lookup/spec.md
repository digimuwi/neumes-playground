## ADDED Requirements

### Requirement: Find Cantus ID button

The toolbar SHALL display a "Find Cantus ID" button that triggers Cantus Index lookup when clicked.

#### Scenario: User clicks Find Cantus ID button
- **WHEN** user clicks the "Find Cantus ID" button in the toolbar
- **THEN** the system queries the Cantus Index API using the text from syllable annotations

#### Scenario: Button disabled without annotations
- **WHEN** no syllable annotations with text exist
- **THEN** the "Find Cantus ID" button SHALL be disabled

#### Scenario: Button disabled during lookup
- **WHEN** a Cantus lookup is in progress
- **THEN** the button SHALL be disabled and show loading state

### Requirement: Text collection for query

The system SHALL collect text from syllable annotations in reading order to construct the Cantus Index query.

#### Scenario: Text collected in reading order
- **WHEN** syllable annotations exist on multiple text lines
- **THEN** the system collects text from top line to bottom, left to right within each line

#### Scenario: Hyphens stripped from syllables
- **WHEN** syllables contain trailing hyphens (e.g., "Do-", "mi-", "ne")
- **THEN** the query text joins them as words with hyphens removed (e.g., "Domine")

#### Scenario: Empty syllables skipped
- **WHEN** some syllable annotations have no text
- **THEN** those syllables are skipped in query construction

### Requirement: Progressive query matching

The system SHALL use progressive query shortening when no exact match is found.

#### Scenario: Exact match found
- **WHEN** the full query text matches one or more chants in Cantus Index
- **THEN** those chants are returned as results

#### Scenario: No exact match triggers shortening
- **WHEN** no chants match the full query text
- **THEN** the system drops the first word and retries until results are found or query is exhausted

### Requirement: No match handling

The system SHALL display a message when no matching chants are found.

#### Scenario: No results after all attempts
- **WHEN** the Cantus Index returns no results even after progressive shortening
- **THEN** the system displays "No matching chant found" message

### Requirement: Single match auto-selection

The system SHALL automatically select a chant when exactly one result matches.

#### Scenario: Single result auto-selected
- **WHEN** the Cantus Index query returns exactly one matching chant
- **THEN** the system automatically stores that chant's cid and genre in document metadata

#### Scenario: Success feedback for auto-selection
- **WHEN** a single match is auto-selected
- **THEN** the system displays confirmation showing the selected Cantus ID and genre

### Requirement: Multiple match selection dialog

The system SHALL display a selection dialog when multiple chants match the query.

#### Scenario: Dialog shown for multiple matches
- **WHEN** the Cantus Index query returns more than one matching chant
- **THEN** a modal dialog opens displaying the list of matches

#### Scenario: Match list displays cid, genre, and text preview
- **WHEN** the selection dialog is shown
- **THEN** each match displays its Cantus ID, genre, and a preview of the fulltext

#### Scenario: User selects a match
- **WHEN** user selects a chant from the list and confirms
- **THEN** that chant's cid and genre are stored in document metadata

#### Scenario: User cancels selection
- **WHEN** user closes the dialog without selecting
- **THEN** no metadata is stored and the dialog closes

### Requirement: Document-level metadata storage

The system SHALL store Cantus metadata at the document level in AppState.

#### Scenario: Metadata field structure
- **WHEN** Cantus metadata is stored
- **THEN** it is stored in `AppState.metadata` as `{ cantusId: string, genre: string }`

#### Scenario: Metadata persists across sessions
- **WHEN** metadata is set and the page is reloaded
- **THEN** the metadata is restored from localStorage

#### Scenario: Metadata change is undoable
- **WHEN** Cantus metadata is set via lookup
- **THEN** the change can be undone with the undo action

### Requirement: Metadata display

The system SHALL display current Cantus metadata when present.

#### Scenario: Show current Cantus ID
- **WHEN** document has Cantus metadata stored
- **THEN** the UI displays the current Cantus ID somewhere visible

#### Scenario: Indicate no Cantus ID
- **WHEN** document has no Cantus metadata
- **THEN** the UI indicates no Cantus ID is set
