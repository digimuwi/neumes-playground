## ADDED Requirements

### Requirement: Auto-focus input on new annotation

When a new annotation is created by drawing a rectangle, the system SHALL automatically focus the appropriate input field in the annotation editor.

#### Scenario: Focus text input for syllable
- **WHEN** user draws a rectangle and a new syllable annotation is created
- **THEN** the syllable text input field receives focus automatically

#### Scenario: Focus dropdown for neume
- **WHEN** user draws a rectangle and a new neume annotation is created
- **THEN** the neume type dropdown receives focus automatically

#### Scenario: No auto-focus when selecting existing annotation
- **WHEN** user clicks on an existing annotation to select it
- **THEN** focus SHALL NOT automatically move to the input field

### Requirement: Sticky annotation type

New annotations SHALL inherit their type from the most recently created annotation. This reduces the need to switch types when annotating runs of similar items.

#### Scenario: Inherit syllable type
- **WHEN** the most recent annotation is a syllable
- **AND** user draws a new rectangle
- **THEN** the new annotation is created as type syllable

#### Scenario: Inherit neume type
- **WHEN** the most recent annotation is a neume
- **AND** user draws a new rectangle
- **THEN** the new annotation is created as type neume

#### Scenario: Default to syllable when no annotations exist
- **WHEN** no annotations exist yet
- **AND** user draws a rectangle
- **THEN** the new annotation is created as type syllable

#### Scenario: User can still switch type
- **WHEN** a new annotation is created with inherited type
- **THEN** user can still change the type via the radio buttons in the editor
