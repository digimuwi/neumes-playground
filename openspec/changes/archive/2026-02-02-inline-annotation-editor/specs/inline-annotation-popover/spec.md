## ADDED Requirements

### Requirement: Inline popover appears next to annotation

When an annotation is selected, an inline editor popover SHALL appear adjacent to the annotation rectangle on the canvas.

#### Scenario: Popover appears on new annotation
- **WHEN** user draws a new rectangle to create an annotation
- **THEN** the inline editor popover appears next to the rectangle

#### Scenario: Popover appears on click
- **WHEN** user clicks on an existing annotation rectangle
- **THEN** the inline editor popover appears next to that rectangle

#### Scenario: Popover closes on deselect
- **WHEN** the popover is open
- **AND** user presses Escape or clicks outside the popover and annotation
- **THEN** the popover closes and no annotation is selected

### Requirement: Smart popover positioning

The popover SHALL position itself to remain fully visible within the canvas bounds.

#### Scenario: Default position right of annotation
- **WHEN** there is sufficient space to the right of the annotation
- **THEN** the popover appears to the right of the annotation with an 8px gap

#### Scenario: Position left when right edge is near
- **WHEN** the annotation is near the right edge of the canvas
- **AND** the popover would extend beyond the canvas boundary
- **THEN** the popover appears to the left of the annotation instead

#### Scenario: Vertical adjustment when near bottom
- **WHEN** the popover would extend below the canvas bottom edge
- **THEN** the popover shifts upward to remain fully visible

#### Scenario: Position updates with zoom/pan
- **WHEN** the user zooms or pans the canvas while the popover is open
- **THEN** the popover position updates to remain adjacent to the annotation

### Requirement: Popover contains type toggle and input

The popover SHALL contain controls for editing the annotation type and its associated data.

#### Scenario: Type toggle is present
- **WHEN** the popover is open
- **THEN** it displays radio buttons to toggle between Syllable and Neume types

#### Scenario: Text field for syllable
- **WHEN** the annotation type is Syllable
- **THEN** the popover displays a text input field for the syllable text

#### Scenario: Dropdown for neume
- **WHEN** the annotation type is Neume
- **THEN** the popover displays a dropdown to select the neume type

#### Scenario: Switching type updates input
- **WHEN** user changes the type via radio buttons
- **THEN** the input field changes to match the new type (text field or dropdown)

### Requirement: Auto-close on data entry completion

The popover SHALL close automatically when the user completes data entry.

#### Scenario: Close on Enter for syllable
- **WHEN** the annotation type is Syllable
- **AND** user presses Enter in the text field
- **THEN** the popover closes and the annotation is deselected

#### Scenario: Close on neume selection
- **WHEN** the annotation type is Neume
- **AND** user selects a neume type from the dropdown
- **THEN** the popover closes and the annotation is deselected

#### Scenario: Type change does not close popover
- **WHEN** user changes the annotation type via radio buttons
- **THEN** the popover remains open with the new input type displayed
