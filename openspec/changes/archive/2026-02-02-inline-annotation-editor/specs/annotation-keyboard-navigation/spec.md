## ADDED Requirements

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

Annotations SHALL be ordered for navigation by their position on the page, simulating reading order.

#### Scenario: Top-to-bottom ordering
- **WHEN** two annotations are at different vertical positions
- **THEN** the annotation closer to the top comes first in navigation order

#### Scenario: Left-to-right for same row
- **WHEN** two annotations are at approximately the same vertical position
- **THEN** the annotation closer to the left comes first in navigation order

#### Scenario: Row threshold
- **WHEN** two annotations have vertical centers within 2% of the image height
- **THEN** they are considered to be on the same row for ordering purposes

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
