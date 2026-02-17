## Why

The backend `/recognize` endpoint now supports a `type` parameter (`"neume"` or `"text"`) that runs only the relevant part of the pipeline, returning faster and more focused results. Currently the frontend has no way to leverage this — region OCR always runs the full pipeline via Shift+draw. Users need a quick way to recognize just neumes or just text in a selected region without the overhead of full pipeline processing.

## What Changes

- Add two keyboard-toggled recognition modes: **neume recognition** (press `n`) and **text recognition** (press `t`)
- When a recognition mode is active, drawing a rectangle sends the region to `/recognize` with the corresponding `type` parameter instead of creating a manual annotation
- The drawn region pulses (blinks) on the canvas while the request is in-flight, replacing the OcrDialog for these targeted requests
- A status chip in the toolbar indicates the active recognition mode
- **BREAKING**: Remove the Shift+draw region OCR trigger — replaced by the more explicit mode-based approach
- Add `detecting` SSE stage support for neume recognition responses

## Capabilities

### New Capabilities
- `targeted-recognition`: Keyboard-toggled recognition modes that send drawn regions to the backend with a type parameter, returning focused results (neumes-only or text-only)

### Modified Capabilities
- `region-ocr`: Shift+draw trigger is removed; region recognition is now activated via keyboard mode toggle instead of a modifier key

## Impact

- **State**: `recognitionMode` added to shared context (not in undo/redo history, not persisted)
- **API**: `recognizeRegion` in htrService gains a `type` parameter
- **Types**: New `RecognitionMode` type; `detecting` added to `OcrProgressEvent`/`OcrStage`
- **Components**: AnnotationCanvas (drawing behavior, keyboard handling, blinking animation), Toolbar (mode chip)
- **Hooks**: `useCanvasDrawing` — `isShiftHeld` tracking removed
