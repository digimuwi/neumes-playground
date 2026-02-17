## Why

The backend now streams OCR progress via Server-Sent Events (SSE), providing stage information (loading, segmenting, recognizing, syllabifying) and per-line progress during recognition. The frontend currently shows a generic "Recognizing text..." spinner, leaving users uncertain about what's happening during long OCR operations.

## What Changes

- Update `htrService.ts` to consume SSE streams instead of JSON responses
- Extend `OcrDialogState` to include progress information (stage, current line, total lines)
- Enhance `OcrDialog` to display stage-specific messages and a progress bar during recognition
- Both `recognizeRegion()` and `recognizePage()` will share SSE parsing logic

## Capabilities

### New Capabilities
- `ocr-progress-streaming`: Frontend consumption of SSE progress events from the HTR backend, including stage transitions and per-line progress during the recognition phase

### Modified Capabilities
<!-- No existing spec requirements are changing - this is additive UI feedback -->

## Impact

- `src/services/htrService.ts`: Change from `response.json()` to SSE parsing with progress callbacks
- `src/state/types.ts`: Extend `OcrDialogState` type to include stage and progress fields
- `src/components/dialogs/OcrDialog.tsx`: Render stage-specific UI with progress bar
- Callers of `recognizeRegion`/`recognizePage` will need to pass progress callbacks
