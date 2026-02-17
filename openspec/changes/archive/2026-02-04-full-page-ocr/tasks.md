## 1. State Management

- [x] 1.1 Add `ocrDialogState` discriminated union type to state types (modes: closed, uploadPrompt, existingAnnotationsPrompt, loading)
- [x] 1.2 Add state actions for opening/closing dialog modes and setting error state
- [x] 1.3 Add reducer cases to handle OCR dialog state transitions

## 2. HTR Service

- [x] 2.1 Add `recognizePage()` function to htrService.ts that calls /recognize without region parameter

## 3. Dialog Component

- [x] 3.1 Create OcrDialog component with mode-based rendering (upload prompt, existing annotations prompt, loading)
- [x] 3.2 Implement upload prompt mode with "Yes, recognize" and "No" buttons
- [x] 3.3 Implement existing annotations prompt mode with "Keep & Add", "Replace", "Cancel" buttons
- [x] 3.4 Implement loading mode with spinner, "Recognizing text..." message, and duration note

## 4. Snackbar Error Handling

- [x] 4.1 Add snackbar state to AppState for error messages
- [x] 4.2 Add ErrorSnackbar component that renders when error state is set
- [x] 4.3 Wire up snackbar to auto-dismiss after timeout

## 5. AppBar Integration

- [x] 5.1 Add "Recognize Page" button to Toolbar with DocumentScanner icon
- [x] 5.2 Disable button when no image is loaded
- [x] 5.3 Wire button click to check for existing annotations and open appropriate dialog

## 6. Image Upload Integration

- [x] 6.1 Modify ImageUploader to dispatch action opening upload prompt dialog after image loads

## 7. Full-Page OCR Flow

- [x] 7.1 Implement full-page OCR handler that shows loading dialog, calls recognizePage(), handles response
- [x] 7.2 Handle "Keep & Add" mode (add annotations without clearing)
- [x] 7.3 Handle "Replace" mode (clear annotations before adding)
- [x] 7.4 Close dialog and show error snackbar on OCR failure

## 8. Region OCR Loading State

- [x] 8.1 Modify shift+drag OCR handler in AnnotationCanvas to show loading dialog during request
- [x] 8.2 Close dialog on success or show error snackbar on failure
