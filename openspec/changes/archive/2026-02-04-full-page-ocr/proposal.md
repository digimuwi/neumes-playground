## Why

Manually drawing and labeling individual syllable bounding boxes for an entire manuscript page is time-consuming. While region-based OCR (shift+drag) helps with specific areas, users often want to recognize text across the full page in one action. Additionally, when uploading a new manuscript image, users typically want OCR as their first step, so prompting immediately saves a manual action.

## What Changes

- Add "Recognize Page" button to the AppBar that triggers full-page OCR
- Show modal dialog on image upload asking if user wants to run OCR
- Add blocking loading dialog with progress message for all OCR operations (full-page and region)
- Handle existing annotations gracefully when running full-page OCR (ask user whether to keep or replace)
- Show snackbar notification on OCR errors

## Capabilities

### New Capabilities
- `full-page-ocr`: AppBar button and upload prompt for recognizing text across the entire manuscript page, with loading states and error handling

### Modified Capabilities
<!-- No existing spec requirements are changing - this adds new UI entry points that use the existing HTR service -->

## Impact

- `src/components/Toolbar.tsx`: Add "Recognize Page" button with DocumentScanner icon
- `src/components/ImageUploader.tsx`: Trigger upload OCR prompt dialog after image loads
- `src/components/AnnotationCanvas.tsx`: Wire up full-page OCR, add loading dialog for shift+drag
- `src/components/dialogs/` (new): Dialog components for prompts and loading state
- `src/services/htrService.ts`: Add function for full-page recognition (no region parameter)
- State: May need loading state flag to control dialog visibility
