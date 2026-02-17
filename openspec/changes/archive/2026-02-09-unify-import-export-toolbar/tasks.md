## 1. Inline ImageUploader into Toolbar

- [x] 1.1 Move the image file input (`<input type="file" accept="image/*">`) and its `onChange` handler from `ImageUploader.tsx` into `Toolbar.tsx`, alongside the existing JSON file input
- [x] 1.2 Delete `src/components/ImageUploader.tsx` and remove its import from `Toolbar.tsx`

## 2. Add Import dropdown menu

- [x] 2.1 Add MUI `Menu` state (`importAnchorEl`) and an "Import" `Button` with `ArrowDropDown` icon that opens the menu
- [x] 2.2 Add "Image" `MenuItem` that programmatically clicks the hidden image file input and closes the menu
- [x] 2.3 Add "JSON" `MenuItem` that programmatically clicks the hidden JSON file input and closes the menu

## 3. Add Export dropdown menu

- [x] 3.1 Add MUI `Menu` state (`exportAnchorEl`) and an "Export" `Button` with `ArrowDropDown` icon that opens the menu
- [x] 3.2 Add "MEI" `MenuItem` that calls `handleExport()` and closes the menu; disabled when `!canExport`
- [x] 3.3 Add "JSON" `MenuItem` that calls `handleExportJSON()` and closes the menu; disabled when `!canExport`

## 4. Restructure toolbar layout

- [x] 4.1 Replace the old individual import/export buttons and `<ImageUploader />` with the Import and Export dropdown menus as the first group
- [x] 4.2 Add a vertical divider after the Import/Export group, followed by the contributions group (Browse, Contribute, Train) unchanged
- [x] 4.3 Verify the remaining groups (OCR, Undo/Redo) and their dividers are unchanged
