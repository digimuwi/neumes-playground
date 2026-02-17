### Requirement: Tab cycles through annotations

Users SHALL be able to navigate between annotations using the Tab key.

#### Scenario: Tab selects next annotation
- **WHEN** an annotation is selected
- **AND** user presses Tab
- **THEN** the next annotation in reading order is selected
- **AND** the popover opens for the newly selected annotation

#### Scenario: Tab from last annotation wraps to first
- **WHEN** the last annotation in reading order is selected
- **AND** user presses Tab
- **THEN** the first annotation in reading order is selected

#### Scenario: Tab with no selection selects first annotation
- **WHEN** no annotation is selected
- **AND** user presses Tab while canvas is focused
- **THEN** the first annotation in reading order is selected

### Requirement: Shift+Tab cycles backwards

Users SHALL be able to navigate backwards through annotations using Shift+Tab.

#### Scenario: Shift+Tab selects previous annotation
- **WHEN** an annotation is selected
- **AND** user presses Shift+Tab
- **THEN** the previous annotation in reading order is selected
- **AND** the popover opens for the newly selected annotation

#### Scenario: Shift+Tab from first annotation wraps to last
- **WHEN** the first annotation in reading order is selected
- **AND** user presses Shift+Tab
- **THEN** the last annotation in reading order is selected

### Requirement: Reading order navigation

Annotations SHALL be ordered for navigation by their type first, then by their position on the page.

#### Scenario: Type takes priority over position

- **WHEN** a syllable annotation is below a neume annotation
- **THEN** the syllable still comes first in navigation order

#### Scenario: Syllables come before neumes

- **WHEN** annotations include both syllables and neumes
- **THEN** all syllables appear before all neumes in navigation order

#### Scenario: Reading order within type

- **WHEN** multiple annotations have the same type
- **THEN** they are ordered by reading order (top-to-bottom, left-to-right) within that type

#### Scenario: Top-to-bottom ordering within type

- **WHEN** two annotations of the same type are at different vertical positions
- **THEN** the annotation closer to the top comes first in navigation order

#### Scenario: Left-to-right for same row within type

- **WHEN** two annotations of the same type are at approximately the same vertical position
- **THEN** the annotation closer to the left comes first in navigation order

#### Scenario: Row threshold

- **WHEN** two annotations have vertical centers within 2% of the image height
- **THEN** they are considered to be on the same row for ordering purposes

#### Scenario: Unknown types sort last

- **WHEN** an annotation has a type not in the known priority list
- **THEN** it appears after all known types in navigation order

### Requirement: Tab navigation respects input focus

Tab navigation SHALL not interfere with normal form input behavior.

#### Scenario: Tab in text field does not navigate
- **WHEN** focus is in the syllable text field
- **AND** user presses Tab
- **THEN** focus moves to the next form element (normal tab behavior)
- **AND** annotation navigation does not occur

#### Scenario: Canvas must be focused for navigation
- **WHEN** focus is not on the canvas or popover
- **AND** user presses Tab
- **THEN** normal browser tab navigation occurs
