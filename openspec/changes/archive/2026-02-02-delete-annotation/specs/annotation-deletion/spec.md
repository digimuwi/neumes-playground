## ADDED Requirements

### Requirement: Delete annotation via keyboard

The system SHALL delete the currently selected annotation when the user presses Delete or Backspace, unless focus is in a text input field.

#### Scenario: Delete key removes selected annotation
- **WHEN** an annotation is selected AND user presses Delete key AND focus is not in a text input
- **THEN** the annotation is removed from the canvas AND selection is cleared

#### Scenario: Backspace key removes selected annotation
- **WHEN** an annotation is selected AND user presses Backspace key AND focus is not in a text input
- **THEN** the annotation is removed from the canvas AND selection is cleared

#### Scenario: Delete ignored when typing
- **WHEN** user is typing in the syllable text input AND presses Backspace
- **THEN** the key event is handled normally by the text input (deletes text, not annotation)

#### Scenario: Delete ignored when nothing selected
- **WHEN** no annotation is selected AND user presses Delete or Backspace
- **THEN** nothing happens

### Requirement: Delete annotation via button

The system SHALL provide a delete button in the annotation editor popover that removes the annotation when clicked.

#### Scenario: Click delete button removes annotation
- **WHEN** an annotation is selected AND user clicks the delete button in the popover
- **THEN** the annotation is removed from the canvas AND the popover closes

### Requirement: Deletion is undoable

Annotation deletion SHALL be undoable via the existing undo mechanism (Ctrl+Z).

#### Scenario: Undo restores deleted annotation
- **WHEN** user deletes an annotation AND then presses Ctrl+Z
- **THEN** the annotation is restored to its previous state
