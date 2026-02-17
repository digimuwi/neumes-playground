## ADDED Requirements

### Requirement: Crop annotation region to binary image
The system SHALL crop the annotation bounding box from the loaded image and convert it to a `BinaryImage` using the pre-computed Otsu threshold and margin threshold, where:
- Pixels with intensity in `[marginThreshold, otsuThreshold)` become foreground (1)
- All other pixels become background (0)

#### Scenario: Binarization produces correct foreground
- **WHEN** neume annotation region is cropped and binarized
- **THEN** ink pixels become foreground (1) and parchment becomes background (0)

#### Scenario: Margin threshold excludes scanner bed
- **WHEN** image has scanner bed margins (detected margin threshold > 0)
- **THEN** pixels darker than margin threshold become background, not foreground

### Requirement: Classify on neume creation
The system SHALL automatically classify neume type when a new neume annotation is created.

#### Scenario: New neume triggers classification
- **WHEN** user creates a new annotation with type "neume"
- **THEN** system crops the region, binarizes it, and runs classification

#### Scenario: Existing neume selected does not trigger
- **WHEN** user selects an existing neume annotation (not newly created)
- **THEN** system does NOT run classification

#### Scenario: Syllable annotation does not trigger
- **WHEN** user creates a new syllable annotation
- **THEN** system does NOT run neume classification

### Requirement: Display suggestion as ghost text
The system SHALL display the top neume type suggestion as ghost/placeholder text in the neume type autocomplete field for newly created neume annotations.

#### Scenario: Suggestion shown as placeholder
- **WHEN** classifier returns suggestions AND annotation is newly created neume
- **THEN** autocomplete field shows top suggestion name as grayed placeholder text

#### Scenario: No suggestion available
- **WHEN** classifier returns empty suggestions
- **THEN** autocomplete field shows no placeholder text

### Requirement: Accept suggestion with Tab or Enter
The system SHALL accept the ghost suggestion when the user presses Tab or Enter on the autocomplete field before typing.

#### Scenario: Tab accepts suggestion
- **WHEN** ghost text shows "pes" AND user presses Tab without typing
- **THEN** neume type is set to "pes" AND editor closes

#### Scenario: Enter accepts suggestion
- **WHEN** ghost text shows "pes" AND user presses Enter without typing
- **THEN** neume type is set to "pes" AND editor closes

### Requirement: Typing dismisses suggestion
The system SHALL dismiss the ghost suggestion when the user types any character, allowing manual neume type selection via the autocomplete filter.

#### Scenario: Typing clears ghost text
- **WHEN** ghost text shows "pes" AND user types "c"
- **THEN** ghost text disappears AND autocomplete filters to types starting with "c"

### Requirement: Helper text indicates acceptance
The system SHALL show helper text "Tab/Enter to accept" below the autocomplete field when a ghost suggestion is displayed.

#### Scenario: Helper text shown with suggestion
- **WHEN** ghost suggestion is displayed
- **THEN** helper text "Tab/Enter to accept" appears below the field

#### Scenario: No helper text without suggestion
- **WHEN** no ghost suggestion is displayed
- **THEN** no helper text appears

### Requirement: Classification does not block UI
The system SHALL run classification without blocking user interaction. If classification is slow, the UI remains responsive and suggestion appears when ready.

#### Scenario: User can interact during classification
- **WHEN** classification is running
- **THEN** user can still type in the autocomplete or close the editor

### Requirement: Stale suggestion prevention
The system SHALL discard classification results if the user has already selected a different annotation or closed the editor before classification completes.

#### Scenario: User switches annotations quickly
- **WHEN** user creates neume A, then immediately creates neume B
- **THEN** suggestion for A is discarded, only suggestion for B is shown
