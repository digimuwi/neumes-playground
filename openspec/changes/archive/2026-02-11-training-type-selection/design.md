## Context

The backend `POST /training/start` now accepts an optional `training_type` field (`"neumes" | "segmentation" | "both"`, default `"both"`). The frontend training dialog currently has no way to select which pipeline to run — it always trains both. We need to surface this choice in the UI.

The existing dialog lives entirely in `Toolbar.tsx` with types in `htrService.ts` and state management in `useTrainingStatus.ts`.

## Goals / Non-Goals

**Goals:**
- Let users choose which training pipeline(s) to run
- Make the choice prominent (not buried in advanced settings)
- Conditionally show only relevant advanced settings for the selected pipeline
- Adapt dialog description text to reflect the selection

**Non-Goals:**
- No changes to the status polling, progress display, or completion feedback
- No changes to `useTrainingStatus.ts` (it passes options through unchanged)
- No backend changes (already done)

## Decisions

### 1. ToggleButtonGroup for pipeline selection

**Choice:** MUI `ToggleButtonGroup` with `exclusive` mode, placed above the description text and advanced settings accordion.

**Why:** Three mutually exclusive options map perfectly to a toggle button group. It's compact, scannable, and more prominent than a dropdown. Radio buttons would also work but take more vertical space for the same information.

### 2. Conditional field visibility in advanced settings

**Choice:** Hide irrelevant fields based on `training_type` selection:
- `"neumes"` → show YOLO Epochs, Image Size; hide Seg Epochs
- `"segmentation"` → show Seg Epochs; hide YOLO Epochs, Image Size
- `"both"` → show all fields

"Train from scratch" remains always visible as it applies to whichever pipeline runs.

**Why:** Showing irrelevant fields (e.g., Seg Epochs when only training neumes) is confusing. The backend ignores them, but the UI should reflect what's actually relevant.

### 3. Dynamic description text

**Choice:** Change the dialog description based on selected training type:
- `"both"` → "Train neume detection and line segmentation models from current contributions."
- `"neumes"` → "Train the neume detection model from current contributions."
- `"segmentation"` → "Train the line segmentation model from current contributions."

### 4. Default to "both"

**Choice:** The toggle defaults to "both", matching the backend default and preserving current behavior for users who don't interact with the toggle.

### 5. Only send training_type when not "both"

**Choice:** Since `"both"` is the backend default, only include `training_type` in the request payload when the user selects `"neumes"` or `"segmentation"`. This keeps backwards compatibility with the existing "only send non-defaults" pattern in `handleTrainingStart`.

## Risks / Trade-offs

- **Discoverability vs. simplicity** — The toggle is always visible (not in accordion), which makes the dialog slightly taller. This is acceptable since it's a primary choice, not a tuning parameter.
- **Field hiding may confuse power users** — A user might wonder where Seg Epochs went after switching to "neumes". The toggle selection makes it clear enough; the fields reappear when switching back.
