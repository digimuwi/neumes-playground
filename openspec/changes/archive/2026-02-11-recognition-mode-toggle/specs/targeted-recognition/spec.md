## MODIFIED Requirements

### Requirement: Keyboard toggles for recognition modes
The system SHALL support three recognition modes — neume, text, and manual — switchable via keyboard shortcuts. Pressing `n` SHALL select neume recognition mode. Pressing `t` SHALL select text recognition mode. Pressing `m` SHALL select manual mode. Pressing `Escape` SHALL also select manual mode. Keyboard shortcuts SHALL be ignored when a text input or textarea is focused.

#### Scenario: Select neume recognition mode
- **WHEN** user presses `n` while in any mode
- **THEN** recognition mode changes to neume

#### Scenario: Select text recognition mode
- **WHEN** user presses `t` while in any mode
- **THEN** recognition mode changes to text

#### Scenario: Select manual mode with m
- **WHEN** user presses `m` while in any mode
- **THEN** recognition mode changes to manual

#### Scenario: Escape selects manual mode
- **WHEN** user presses `Escape` while in any recognition mode
- **THEN** recognition mode changes to manual

#### Scenario: Keyboard shortcuts ignored in text inputs
- **WHEN** user presses `n`, `t`, or `m` while focused on a text input or textarea
- **THEN** recognition mode does not change

### Requirement: Toolbar displays active recognition mode
The toolbar SHALL display a `ToggleButtonGroup` with three options: "Neume (n)", "Text (t)", and "Manual (m)". Exactly one option SHALL be selected at all times, reflecting the current recognition mode. Clicking a toggle button SHALL switch to that recognition mode.

#### Scenario: ToggleButtonGroup reflects current mode
- **WHEN** recognition mode is neume
- **THEN** the "Neume (n)" toggle button is selected

#### Scenario: Click to switch mode
- **WHEN** user clicks the "Text (t)" toggle button
- **THEN** recognition mode changes to text

#### Scenario: Manual mode selected by default
- **WHEN** the application starts
- **THEN** the "Manual (m)" toggle button is selected
