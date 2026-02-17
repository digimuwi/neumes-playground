## 1. Toolbar UI

- [x] 1.1 Replace the conditional recognition mode `Chip` in `Toolbar.tsx` with a `ToggleButtonGroup` containing three `ToggleButton`s: "Neume (n)", "Text (t)", "Manual (m)", using `size="small"` and `exclusive` mode
- [x] 1.2 Bind the `ToggleButtonGroup` value to `recognitionMode` from context and onChange to `setRecognitionMode`, ensuring null values are rejected (always one selected)

## 2. Keyboard Shortcuts

- [x] 2.1 Change `n` and `t` key handlers in `AnnotationCanvas.tsx` from toggle logic to direct selection (`setRecognitionMode('neume')` / `setRecognitionMode('text')`)
- [x] 2.2 Add `m` key handler that sets recognition mode to manual
- [x] 2.3 Keep `Escape` handler setting mode to manual (already works, just verify)
