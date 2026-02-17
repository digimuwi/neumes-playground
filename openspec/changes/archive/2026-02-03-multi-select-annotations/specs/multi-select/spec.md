## ADDED Requirements

### Requirement: Single-click selection clears other selections

When clicking an annotation without modifier keys, the system SHALL select only that annotation, deselecting all others.

#### Scenario: Click annotation without modifier
- **WHEN** user clicks an annotation without Cmd/Ctrl held
- **THEN** that annotation becomes the only selected annotation
- **AND** any previously selected annotations are deselected

#### Scenario: Click different annotation
- **WHEN** annotations A and B are selected
- **AND** user clicks annotation C without modifier
- **THEN** only annotation C is selected
- **AND** annotations A and B are deselected

### Requirement: Modifier-click toggles selection

When clicking an annotation with Cmd (Mac) or Ctrl (Windows/Linux) held, the system SHALL toggle that annotation's selection state without affecting other selections.

#### Scenario: Add to selection with modifier
- **WHEN** annotation A is selected
- **AND** user Cmd/Ctrl+clicks annotation B
- **THEN** both annotations A and B are selected

#### Scenario: Remove from selection with modifier
- **WHEN** annotations A and B are selected
- **AND** user Cmd/Ctrl+clicks annotation A
- **THEN** only annotation B remains selected

#### Scenario: First selection with modifier
- **WHEN** no annotations are selected
- **AND** user Cmd/Ctrl+clicks annotation A
- **THEN** annotation A is selected

### Requirement: Select all annotations

The system SHALL provide a keyboard shortcut (Cmd+A on Mac, Ctrl+A on Windows/Linux) to select all annotations when the canvas is focused.

#### Scenario: Select all with keyboard shortcut
- **WHEN** canvas is focused
- **AND** user presses Cmd/Ctrl+A
- **THEN** all annotations are selected

#### Scenario: Select all prevents browser default
- **WHEN** user presses Cmd/Ctrl+A with canvas focused
- **THEN** browser's native "select all" behavior is prevented

### Requirement: Deselect all annotations

The system SHALL deselect all annotations when the user clicks empty canvas space or presses Escape.

#### Scenario: Click empty canvas
- **WHEN** one or more annotations are selected
- **AND** user clicks empty area of canvas
- **THEN** all annotations are deselected

#### Scenario: Press Escape
- **WHEN** one or more annotations are selected
- **AND** user presses Escape
- **THEN** all annotations are deselected

### Requirement: Batch deletion

When multiple annotations are selected, pressing Delete or Backspace SHALL remove all selected annotations.

#### Scenario: Delete multiple annotations
- **WHEN** annotations A, B, and C are selected
- **AND** user presses Delete or Backspace
- **THEN** all three annotations are removed

#### Scenario: Batch delete is atomic for undo
- **WHEN** user deletes 3 annotations at once
- **AND** user presses Cmd/Ctrl+Z (undo)
- **THEN** all 3 annotations are restored in a single undo operation

### Requirement: Editor visibility with multi-select

The inline annotation editor SHALL only appear when exactly one annotation is selected.

#### Scenario: Single selection shows editor
- **WHEN** exactly one annotation is selected
- **THEN** the inline editor popover appears for that annotation

#### Scenario: Multi-selection hides editor
- **WHEN** two or more annotations are selected
- **THEN** no inline editor popover is displayed

#### Scenario: Zero selection hides editor
- **WHEN** no annotations are selected
- **THEN** no inline editor popover is displayed

### Requirement: Tab navigation clears multi-selection

When using Tab to navigate annotations, the system SHALL clear any multi-selection and select only the next annotation in reading order.

#### Scenario: Tab from multi-selection
- **WHEN** annotations A, B, and C are selected
- **AND** user presses Tab
- **THEN** multi-selection is cleared
- **AND** the next annotation in reading order is selected

### Requirement: Visual feedback for selected annotations

All selected annotations SHALL display the same visual selection indicator (yellow border).

#### Scenario: Multiple annotations show selection border
- **WHEN** annotations A, B, and C are selected
- **THEN** all three annotations display the yellow selection border
