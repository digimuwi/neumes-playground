## MODIFIED Requirements

### Requirement: Export button in toolbar

The Export dropdown menu in the toolbar SHALL include a "MEI" item that triggers the MEI export when clicked.

#### Scenario: User clicks MEI export menu item
- **WHEN** user clicks "MEI" in the Export dropdown menu
- **THEN** the browser downloads a file named "export.mei" containing valid MEI XML

#### Scenario: MEI export menu item disabled without image
- **WHEN** no image is loaded in the application
- **THEN** the "MEI" item in the Export dropdown SHALL be disabled
