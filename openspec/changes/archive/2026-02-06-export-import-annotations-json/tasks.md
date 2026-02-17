## 1. Export

- [x] 1.1 Create `src/utils/jsonExport.ts` with an `exportAnnotationsJSON` function that serializes `imageDataUrl`, `annotations`, and `metadata` into a JSON string and triggers a browser download as a `.json` file
- [x] 1.2 Add an export JSON button to the Toolbar (with tooltip "Export JSON"), disabled when no image is loaded, that calls `exportAnnotationsJSON`

## 2. Import

- [x] 2.1 Create `src/utils/jsonImport.ts` with a `parseAnnotationsJSON` function that reads a File, parses JSON, validates the expected structure (`imageDataUrl`, `annotations` array), and returns the parsed data or throws on invalid input
- [x] 2.2 Add an import JSON button to the Toolbar that opens a hidden `<input type="file" accept=".json">` to select a file
- [x] 2.3 On file selection, if annotations already exist, show a confirmation dialog before replacing state; if no annotations exist, load immediately
- [x] 2.4 On confirmed import, dispatch `LOAD_STATE` with the parsed image, annotations, and metadata; on invalid file, dispatch `SET_ERROR` with an error message
