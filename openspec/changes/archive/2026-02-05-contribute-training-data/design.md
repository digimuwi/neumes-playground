## Context

The backend already has a `/contribute` endpoint that accepts:
- `image`: File (JPEG or PNG)
- `annotations`: JSON string with structure `{ lines: [{ syllables }], neumes: [] }`

The frontend stores annotations as a flat list with normalized coordinates (0-1). The existing `computeTextLines()` function in `useTextLines.ts` already clusters syllables into lines based on geometric analysis.

## Goals / Non-Goals

**Goals:**
- Enable users to submit corrected annotations for HTR model training
- Provide clear feedback during submission (loading, success, error)
- Reuse existing infrastructure (service patterns, snackbar, text line grouping)

**Non-Goals:**
- Tracking contribution history or allowing users to view past contributions
- Offline queuing of contributions
- Batch contribution of multiple pages

## Decisions

### 1. Service function location: Add to htrService.ts
**Rationale**: The contribution endpoint is part of the same HTR backend service. Keeping related API calls together maintains cohesion. The file already has the base URL constant and coordinate conversion utilities.

**Alternative considered**: New `contributionService.ts` - rejected as unnecessary separation for a single function.

### 2. Button placement: After Export MEI, before divider
**Rationale**: Export and Contribute are both "output" actions - getting data out of the tool. Grouping them together is logical. Using the existing Import/Export group avoids adding another divider.

### 3. Icon: VolunteerActivism (gift/donate hand)
**Rationale**: Conveys the idea of giving back to the community. More meaningful than generic upload icons. Available in MUI icons.

### 4. Loading state: Button-level, not dialog
**Rationale**: Keep it simple per user request. A spinning icon on the button itself is sufficient for a quick POST request. No need for a modal dialog.

### 5. Success feedback: Snackbar message
**Rationale**: Consistent with existing error handling pattern (ErrorSnackbar). Non-blocking, auto-dismisses. May need to add success variant to existing snackbar or add separate component.

### 6. Data transformation approach
**Rationale**:
1. Extract `computeTextLines` usage to get syllables grouped by line
2. Convert normalized coords to pixels using image dimensions from blob
3. Map neumes to backend format (type + bbox)

This reuses existing line-grouping logic rather than reimplementing.

## Risks / Trade-offs

**[Risk] Image dimension mismatch** → Get dimensions from the actual image blob, not from any cached state, to ensure pixel coordinates match the submitted image.

**[Risk] Large image upload timeout** → The backend already handles this for `/recognize`. Same infrastructure should work. Not adding timeout handling initially.

**[Trade-off] No confirmation dialog** → User requested simplicity. Risk of accidental submission is low given the specific enable conditions (must have image + syllables + neumes).
