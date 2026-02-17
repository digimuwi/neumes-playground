# Help Dialog

Floating help button and keyboard shortcut reference dialog for discoverability.

## Requirements

### Requirement: Floating help button visibility

The system SHALL display a floating help button (MUI Fab) in the bottom-right corner of the canvas area. The button MUST use the HelpOutline icon and remain visible at all times regardless of zoom or pan state.

#### Scenario: Help button always visible
- **WHEN** user loads the application
- **THEN** a circular help button with "?" icon is visible in the bottom-right corner of the canvas

#### Scenario: Help button unaffected by canvas zoom
- **WHEN** user zooms in or out on the canvas
- **THEN** the help button remains in the same screen position (fixed overlay)

### Requirement: Help dialog opens on button click

The system SHALL open a modal dialog when the user clicks the floating help button. The dialog MUST be an MUI Dialog component with compact sizing.

#### Scenario: Open help via button click
- **WHEN** user clicks the floating help button
- **THEN** a modal dialog opens displaying keyboard shortcuts and feature documentation

#### Scenario: Close help dialog
- **WHEN** help dialog is open AND user clicks the close button or clicks outside the dialog
- **THEN** the dialog closes

### Requirement: Help dialog opens on keyboard shortcut

The system SHALL open the help dialog when the user presses the `?` key, provided no text input is focused.

#### Scenario: Open help via ? key
- **WHEN** no text input is focused AND user presses the `?` key
- **THEN** the help dialog opens

#### Scenario: ? key ignored during text input
- **WHEN** user is typing in a text field AND presses the `?` key
- **THEN** the `?` character is typed into the field (dialog does not open)

#### Scenario: Close help dialog with Escape
- **WHEN** help dialog is open AND user presses Escape
- **THEN** the dialog closes

### Requirement: Help content organized by task

The help dialog SHALL organize content into the following sections:
1. **Navigate the Image**: zoom (⌘/Ctrl + scroll), pan (Space + drag), reset view (double-click)
2. **Cycle Through Annotations**: next (Tab), previous (Shift+Tab), select all (⌘/Ctrl+A), deselect (Escape), delete (Delete/Backspace)
3. **Drawing & OCR**: draw annotation (click + drag), OCR region (Shift + drag)
4. **Undo / Redo**: undo (⌘/Ctrl+Z), redo (⌘/Ctrl+Shift+Z)
5. **Tips**: neume-to-syllable assignment curves, automatic bounding box tightening, syllable and neume type suggestions

#### Scenario: All shortcut categories displayed
- **WHEN** user opens the help dialog
- **THEN** all five content sections are visible with their respective shortcuts

### Requirement: Platform-aware modifier key display

The help dialog SHALL display modifier keys appropriate to the user's platform: `⌘` for macOS, `Ctrl` for Windows/Linux.

#### Scenario: Mac user sees Command symbol
- **WHEN** user on macOS opens the help dialog
- **THEN** shortcuts display `⌘` for the modifier key (e.g., `⌘ + Z`)

#### Scenario: Windows user sees Ctrl
- **WHEN** user on Windows opens the help dialog
- **THEN** shortcuts display `Ctrl` for the modifier key (e.g., `Ctrl + Z`)

### Requirement: Compact dialog sizing

The help dialog SHALL use compact sizing to avoid overwhelming the user. Content MUST be scannable without excessive scrolling on typical laptop screens (768px height minimum).

#### Scenario: Dialog fits on laptop screen
- **WHEN** user opens the help dialog on a 768px tall viewport
- **THEN** the dialog content is fully visible without scrolling, or requires minimal scrolling
