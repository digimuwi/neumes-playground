## Context

Annotations (syllables and neumes) are stored in React state as an `Annotation[]` with normalized coordinates. The app already has an MEI export (`src/utils/meiExport.ts`) that converts annotations into a musicology interchange format, triggered from the Toolbar. There is also an "existing annotations" prompt pattern in the OCR dialog that warns users before replacing annotations.

Currently there is no way to save and restore the full annotation state losslessly. MEI export is lossy (different schema, no round-trip). Training contributions are one-way and convert to PAGE XML.

## Goals / Non-Goals

**Goals:**
- Lossless round-trip: export all annotations + image + metadata as JSON, import to restore exact state
- Follow existing patterns: utility function in `src/utils/`, button in Toolbar, confirmation dialog for destructive import
- Self-contained export file: embedded base64 image so a single `.json` file captures everything

**Non-Goals:**
- Backend involvement — this is purely client-side
- Partial import/merge — import replaces all state
- Format versioning — keep it simple, no version field
- Compression of the base64 image data

## Decisions

### JSON file structure
The export file contains three top-level keys matching the `AppState` fields directly:

```json
{
  "imageDataUrl": "data:image/jpeg;base64,...",
  "annotations": [ ... ],
  "metadata": { "cantusId": "...", "genre": "..." }
}
```

**Rationale**: This mirrors `AppState` directly, making export/import trivial — serialize the relevant fields out, deserialize them back in. No transformation needed. Annotations keep their IDs, normalized coordinates, types, and all properties.

**Alternative considered**: Separate image file + JSON — rejected because the user explicitly wants a single self-contained file.

### Import triggers LOAD_STATE action
On import, dispatch a `LOAD_STATE` action with the parsed data. This replaces the entire state (image, annotations, metadata) in one atomic operation and creates a clean undo history entry.

**Rationale**: `LOAD_STATE` already exists in the reducer and handles full state replacement. Using it avoids new action types.

### Confirmation prompt before import
When the user has existing annotations and triggers import, show a confirmation dialog before proceeding. Reuse the same MUI Dialog pattern as the OCR "existing annotations" prompt (`existingAnnotationsPrompt` in `OcrDialogState`).

**Rationale**: The pattern already exists and users are familiar with it. However, this will use a separate dialog state (not the OCR dialog) since it's a different flow — a simple `window.confirm()` or a small standalone confirm dialog is sufficient.

### File download via blob URL
Export creates a Blob from `JSON.stringify()`, generates an object URL, and triggers download via a temporary `<a>` element — same pattern used by `exportMEI`.

### File import via hidden input[type=file]
Import uses a hidden `<input type="file" accept=".json">` element triggered programmatically, same pattern as the existing `ImageUploader` component.

## Risks / Trade-offs

- **Large file size** — Embedding the image as base64 increases file size ~33% vs raw binary. For high-res manuscript images this could mean 10-30MB JSON files. → Acceptable trade-off for single-file simplicity. Users explicitly requested embedded images.
- **No validation of annotation IDs on import** — If a user manually edits the JSON and creates duplicate IDs, the app may behave unexpectedly. → Accept this; the feature is for save/restore, not as a public interchange format.
- **Undo history reset on import** — `LOAD_STATE` starts a fresh history stack. The user cannot undo back to before the import. → This matches the behavior of loading an image or running OCR.
