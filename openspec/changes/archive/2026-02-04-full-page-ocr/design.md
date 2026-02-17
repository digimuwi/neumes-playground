## Context

The application currently supports region-based OCR via shift+drag, which calls the backend `/recognize` endpoint with a region parameter. The backend already handles full-page recognition when the region parameter is omitted. The frontend needs UI entry points for full-page OCR plus loading states and error handling.

Current state:
- `htrService.ts` has `recognizeRegion()` that always passes a region
- `AnnotationCanvas.tsx` handles shift+drag OCR without loading feedback
- `Toolbar.tsx` has Import/Export buttons and Undo/Redo
- `ImageUploader.tsx` dispatches `setImage()` and has no post-upload hooks

## Goals / Non-Goals

**Goals:**
- Provide one-click full-page OCR via AppBar button
- Prompt users to run OCR immediately after image upload
- Show blocking loading dialog during all OCR operations
- Handle error states with snackbar notifications
- Let users choose what happens to existing annotations when running full-page OCR

**Non-Goals:**
- Cancellable OCR requests (keep it simple for v1)
- Progress percentage (backend doesn't support it)
- Batch processing of multiple images
- Persisting "don't ask again" preference for upload prompt

## Decisions

### 1. Dialog component structure
**Decision**: Create a single reusable `OcrDialog` component that handles all three dialog states (upload prompt, existing annotations prompt, loading).

**Rationale**: All dialogs are modal and OCR-related. A single component with mode prop is cleaner than three separate components, and the states are mutually exclusive (only one shows at a time).

**Alternatives considered**:
- Separate components per dialog type → More files, duplicated dialog boilerplate
- Using MUI Dialog directly each time → Repeated code, inconsistent styling

### 2. State management for dialogs
**Decision**: Add `ocrDialogState` to AppState with discriminated union type for dialog modes.

**Rationale**: Dialog visibility and mode need to be controlled from multiple places (Toolbar, ImageUploader, AnnotationCanvas). Centralizing in state keeps it consistent and enables the loading dialog to persist across the async OCR call.

**Alternatives considered**:
- Local component state → Can't coordinate between Toolbar button and ImageUploader
- Separate boolean flags → Harder to ensure mutual exclusivity

### 3. Full-page OCR service function
**Decision**: Add `recognizePage()` function to `htrService.ts` that calls the same endpoint without region parameter.

**Rationale**: Keeps the API layer clean. `recognizeRegion()` remains for shift+drag, `recognizePage()` for full-page. Both share the same response handling.

### 4. Error handling
**Decision**: Use MUI Snackbar with auto-hide for OCR errors.

**Rationale**: Non-blocking notification that doesn't require user action. Errors are recoverable (user can retry), so a dismissible snackbar is appropriate.

### 5. Existing annotations handling
**Decision**: When user has annotations and clicks "Recognize Page", show dialog with three options: Keep & Add, Replace, Cancel.

**Rationale**: "Keep & Add" is useful when user has manually added annotations they want to preserve. "Replace" for a fresh start. "Cancel" if they clicked by mistake.

## Risks / Trade-offs

**[Risk] Large manuscripts may take 10+ seconds** → Loading dialog with "This may take a minute" messaging sets expectations. Blocking modal prevents user from making conflicting edits during OCR.

**[Risk] Backend failure leaves user stuck** → Snackbar error notification allows retry. Loading dialog closes on both success and error.

**[Trade-off] Blocking vs non-blocking loading** → Chose blocking for simplicity. Non-blocking would require handling race conditions if user draws annotations while OCR is running.

**[Trade-off] No cancel button** → Keeps implementation simple. OCR typically completes in under 30 seconds. Can add cancellation in future if needed.
