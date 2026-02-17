## Why

Annotations created on a manuscript (via manual drawing or OCR) exist only in browser memory and localStorage. There is no way to save a complete snapshot of all annotations and restore them later. Users need to export their work as a JSON file (including the image) and re-import it to resume annotation sessions.

## What Changes

- Add a JSON export function that serializes all annotations plus the embedded image (base64 data URL) and document metadata into a downloadable `.json` file
- Add a JSON import function that reads a `.json` file and restores the annotations, image, and metadata into application state
- When importing, if annotations already exist, prompt the user before replacing them (reuse the existing OCR "existing annotations" prompt pattern)
- Add UI controls (buttons/menu items) to trigger export and import

## Capabilities

### New Capabilities
- `annotation-export-import`: Export all annotations, image, and metadata as a JSON file; import a previously exported JSON file to restore state

### Modified Capabilities

## Impact

- `src/state/` — new actions or use of existing `LOAD_STATE` / `ADD_ANNOTATIONS` actions for import
- `src/utils/` — new export/import utility functions (similar pattern to `meiExport.ts`)
- `src/components/` — UI buttons for export and import
- No backend changes required
- No dependency changes required
