## MODIFIED Requirements

### Requirement: Auto-focus input on new annotation

When a new annotation is created by drawing a rectangle, the system SHALL automatically focus the appropriate input field in the inline popover.

#### Scenario: Focus text input for syllable
- **WHEN** user draws a rectangle and a new syllable annotation is created
- **THEN** the syllable text input field in the inline popover receives focus automatically

#### Scenario: Focus dropdown for neume
- **WHEN** user draws a rectangle and a new neume annotation is created
- **THEN** the neume type dropdown in the inline popover receives focus automatically

#### Scenario: No auto-focus when selecting existing annotation
- **WHEN** user clicks on an existing annotation to select it
- **THEN** focus SHALL NOT automatically move to the input field
