## ADDED Requirements

### Requirement: Autocomplete input for neume type selection

When editing a neume annotation, the system SHALL display an autocomplete text input instead of a dropdown select for choosing the neume type.

#### Scenario: Focus shows all options
- **WHEN** the neume type input receives focus
- **THEN** the system SHALL display all available neume types in a dropdown list

#### Scenario: Typing filters by prefix
- **WHEN** the user types "cli" into the neume type input
- **THEN** the system SHALL show only neume types whose names start with "cli" (case-insensitive)
- **AND** neume types like "Clivis" and "Climacus" SHALL appear
- **AND** neume types like "Punctum" SHALL NOT appear

#### Scenario: No prefix match shows empty list
- **WHEN** the user types a prefix that matches no neume types (e.g., "xyz")
- **THEN** the system SHALL show an empty dropdown or "no options" message

### Requirement: Keyboard navigation for neume selection

The autocomplete input SHALL support full keyboard navigation.

#### Scenario: Arrow key navigation
- **WHEN** the dropdown is open and user presses arrow down
- **THEN** the system SHALL highlight the next option in the list
- **AND** when user presses arrow up, the system SHALL highlight the previous option

#### Scenario: Enter confirms selection
- **WHEN** an option is highlighted and user presses Enter
- **THEN** the system SHALL select that neume type
- **AND** close the editor

#### Scenario: Escape cancels without changing
- **WHEN** the user presses Escape while the autocomplete is open
- **THEN** the system SHALL close the editor
- **AND** preserve the previous neume type value

### Requirement: Empty or cancelled input preserves previous value

The system SHALL NOT allow an annotation to have an invalid or missing neume type.

#### Scenario: Enter with no selection keeps previous value
- **WHEN** the input is empty or has no matching selection and user presses Enter
- **THEN** the system SHALL keep the previous neume type (or default to Punctum for new annotations)
- **AND** close the editor

#### Scenario: Click outside preserves previous value
- **WHEN** the user clicks outside the editor without making a selection
- **THEN** the system SHALL keep the previous neume type value

### Requirement: Auto-focus on new neume annotation

When a new neume annotation is created, the autocomplete input SHALL receive focus automatically.

#### Scenario: New neume annotation focuses autocomplete
- **WHEN** a new annotation is created with type "neume"
- **THEN** the neume type autocomplete input SHALL receive focus
- **AND** the dropdown SHALL open showing all available neume types
