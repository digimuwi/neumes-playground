## Why

The toolbar's first group has 7 individual icon buttons (Import Image, Export MEI, Export JSON, Import JSON, Browse Contributions, Contribute, Train). This is visually crowded and hard to scan. Import and export actions are closely related but scattered across separate buttons with different icons. Unifying them into two dropdown menus reduces visual clutter and groups related actions logically.

## What Changes

- Replace the 4 separate import/export buttons (Import Image, Export MEI, Export JSON, Import JSON) with 2 dropdown menu buttons:
  - **Import** dropdown: Image, JSON
  - **Export** dropdown: MEI, JSON
- Reorder the first toolbar group so Import and Export come first, followed by a divider, then Contributions (Browse, Contribute, Train) as they are today
- Import/Export buttons are always enabled; individual menu items are disabled based on state (e.g., Export MEI/JSON disabled when no image is loaded)

## Capabilities

### New Capabilities

- `toolbar-dropdown-menus`: Dropdown menu buttons for grouping related toolbar actions (Import and Export)

### Modified Capabilities

- `annotation-export-import`: Toolbar controls requirement changes from individual buttons to dropdown menu items
- `mei-export`: Toolbar export button requirement changes from standalone button to Export dropdown menu item

## Impact

- `src/components/Toolbar.tsx` — primary change: restructure the import/export section to use MUI Menu components
- `src/components/ImageUploader.tsx` — may need to expose its file input trigger as a callable function rather than wrapping its own button
- No changes to export/import logic, state management, or any other components
- No new dependencies (MUI Menu is already available in MUI v5)
