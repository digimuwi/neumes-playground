## Why

Users correct OCR output to create accurate annotations, but this corrected data isn't fed back to improve the HTR model. Adding a "Contribute" button lets users submit their corrected annotations as training data, creating a feedback loop that improves recognition quality over time.

## What Changes

- Add "Contribute" button in the toolbar alongside Export MEI
- Button enabled when image loaded AND annotations contain both syllables and neumes
- Submits image + annotations to backend `/contribute` endpoint
- Shows loading state during submission, success/error feedback via snackbar

## Capabilities

### New Capabilities
- `training-contribution`: Submit corrected annotations to backend for HTR model training. Includes data transformation from frontend format (normalized coords, flat list) to backend format (pixel coords, syllables grouped by line).

### Modified Capabilities
<!-- None - this is additive functionality that doesn't change existing behavior -->

## Impact

- **Toolbar.tsx**: New button with icon, loading state, click handler
- **htrService.ts** (or new service file): New `contributeTrainingData()` function
- **useTextLines.ts**: Reuse `computeTextLines()` for grouping syllables into lines
- **Dependencies**: Uses existing ErrorSnackbar for error display, may need success snackbar
