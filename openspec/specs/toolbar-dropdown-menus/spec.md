### Requirement: Import dropdown menu in toolbar
The toolbar SHALL display an "Import" button that opens a dropdown menu with options for importing an image or a JSON file.

#### Scenario: Import button is always visible
- **WHEN** the toolbar is rendered
- **THEN** an "Import" button SHALL be visible in the toolbar

#### Scenario: Import button is always enabled
- **WHEN** the toolbar is rendered regardless of application state
- **THEN** the "Import" button SHALL be enabled and clickable

#### Scenario: Clicking Import opens dropdown menu
- **WHEN** the user clicks the "Import" button
- **THEN** a dropdown menu SHALL appear with items "Image" and "JSON"

#### Scenario: Import Image menu item triggers file picker
- **WHEN** the user clicks "Image" in the Import dropdown
- **THEN** a file picker dialog SHALL open filtered to image files (image/*)

#### Scenario: Import JSON menu item triggers file picker
- **WHEN** the user clicks "JSON" in the Import dropdown
- **THEN** a file picker dialog SHALL open filtered to .json files

#### Scenario: Menu closes after selection
- **WHEN** the user clicks any item in the Import dropdown
- **THEN** the dropdown menu SHALL close

### Requirement: Export dropdown menu in toolbar
The toolbar SHALL display an "Export" button that opens a dropdown menu with options for exporting as MEI or JSON.

#### Scenario: Export button is always visible
- **WHEN** the toolbar is rendered
- **THEN** an "Export" button SHALL be visible in the toolbar

#### Scenario: Export button is always enabled
- **WHEN** the toolbar is rendered regardless of application state
- **THEN** the "Export" button SHALL be enabled and clickable

#### Scenario: Clicking Export opens dropdown menu
- **WHEN** the user clicks the "Export" button
- **THEN** a dropdown menu SHALL appear with items "MEI" and "JSON"

#### Scenario: Export MEI disabled without image
- **WHEN** no image is loaded and the user opens the Export dropdown
- **THEN** the "MEI" menu item SHALL be disabled

#### Scenario: Export JSON disabled without image
- **WHEN** no image is loaded and the user opens the Export dropdown
- **THEN** the "JSON" menu item SHALL be disabled

#### Scenario: Export MEI triggers download
- **WHEN** an image is loaded and the user clicks "MEI" in the Export dropdown
- **THEN** the MEI export SHALL execute and download a .mei file

#### Scenario: Export JSON triggers download
- **WHEN** an image is loaded and the user clicks "JSON" in the Export dropdown
- **THEN** the JSON export SHALL execute and download a .json file

#### Scenario: Menu closes after selection
- **WHEN** the user clicks any item in the Export dropdown
- **THEN** the dropdown menu SHALL close

### Requirement: Toolbar group ordering
The toolbar SHALL organize its controls in the following order, separated by vertical dividers:
1. Import and Export dropdown menus
2. Contributions group (Browse, Contribute, Train)
3. OCR group (Recognize, Cantus ID)
4. Undo/Redo group

#### Scenario: Import/Export group appears first
- **WHEN** the toolbar is rendered
- **THEN** the Import and Export buttons SHALL appear as the first group, before a vertical divider

#### Scenario: Contributions group follows Import/Export
- **WHEN** the toolbar is rendered
- **THEN** the contributions controls (Browse, Contribute, Train) SHALL appear after the first divider
