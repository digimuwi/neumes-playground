## 1. Types

- [x] 1.1 Add `OcrStage` type and `OcrProgressEvent` type to `src/state/types.ts`
- [x] 1.2 Extend `OcrDialogState` loading mode to include `stage`, `current?`, and `total?` fields

## 2. Service Layer

- [x] 2.1 Add shared `parseSSEStream` helper function in `src/services/htrService.ts` that reads SSE events from a fetch Response
- [x] 2.2 Update `recognizeRegion` to use SSE parsing and accept `onProgress` callback
- [x] 2.3 Update `recognizePage` to use SSE parsing and accept `onProgress` callback

## 3. Dialog UI

- [x] 3.1 Update `OcrDialog` to display stage-specific messages based on `state.stage`
- [x] 3.2 Add determinate `LinearProgress` for recognition stage showing line progress
- [x] 3.3 Use indeterminate `CircularProgress` for other stages (loading, segmenting, syllabifying)

## 4. Integration

- [x] 4.1 Update `ImageUploader` (or wherever `recognizePage` is called) to dispatch progress updates via `onProgress` callback
- [x] 4.2 Update `AnnotationCanvas` (or wherever `recognizeRegion` is called) to dispatch progress updates via `onProgress` callback

## 5. Error Handling

- [x] 5.1 Add error mode to `OcrDialogState` with message field
- [x] 5.2 Update `OcrDialog` to display error state with dismissible message
- [x] 5.3 Handle stream errors in SSE parser and convert to error progress events
