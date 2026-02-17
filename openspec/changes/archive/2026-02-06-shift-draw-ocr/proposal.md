## Why

Manually drawing and labeling individual syllable bounding boxes is tedious when annotating manuscript regions with multiple text syllables. The backend HTR service can automatically detect syllables and their bounding boxes within a user-marked region, significantly accelerating the annotation workflow.

## What Changes

- Add Shift+draw modifier to trigger OCR recognition on a drawn region
- Call backend `/recognize` endpoint with the drawn region
- Auto-create syllable annotations for each detected syllable with pre-filled text
- Normal draw (without Shift) continues to create single annotations as before

## Capabilities

### New Capabilities
- `region-ocr`: Shift+draw triggers HTR recognition on a region, creating multiple syllable annotations from backend response

### Modified Capabilities
<!-- No existing spec requirements are changing - this adds a new interaction mode -->

## Impact

- `src/hooks/useCanvasDrawing.ts`: Track Shift key state, branch behavior on Shift+draw
- `src/components/AnnotationCanvas.tsx`: Wire up OCR service call and batch annotation creation
- New service module for backend API communication
- State actions may need batch annotation support (or reuse existing ADD_ANNOTATION in loop)
