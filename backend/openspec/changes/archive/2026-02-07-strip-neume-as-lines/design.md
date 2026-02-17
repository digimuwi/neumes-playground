## Context

The recognition pipeline currently has two code paths: a text path (default Kraken segmentation → `rpred` → syllabification) and a neume path (custom segmentation model → `mm_rpred` → neume bbox extraction). The neume path is broken — the custom segmentation model produces 0 lines, and Kraken's line-based OCR is architecturally wrong for neumes. A future change will replace neume detection with YOLOv8 object detection on text-masked images.

This change strips out the neume-as-lines machinery, leaving a clean text-only recognition pipeline. The neume detection capability goes dormant until YOLO integration restores it.

**Current recognition flow:**
```
image → segment_image() ──┐
         (custom or        │
          default model)   │
                           ▼
              recognize_lines()
              ├─ mm_rpred (if neume model + typed lines)
              ├─ rpred_skip_neumes (if typed lines, no neume model)
              └─ rpred (fallback)
                           │
                           ▼
              api.py stream generator
              ├─ text lines → syllabify → syllables
              └─ neume lines → extract_neume_bboxes → neumes
```

**After this change:**
```
image → segment_image() ──┐
         (default Kraken   │
          blla.segment)    │
                           ▼
              recognize_lines()
              └─ rpred (always, Tridis model)
                           │
                           ▼
              api.py stream generator
              └─ all lines → syllabify → syllables
                 (neumes = [])
```

## Goals / Non-Goals

**Goals:**
- Remove all neume-via-Kraken recognition code (mm_rpred routing, neume model loading, custom segmentation branching, neume bbox extraction)
- Simplify `recognize_lines()` to always use single-model `rpred`
- Simplify `segment_image()` to always use default Kraken
- Remove unused `_binarize_image()` from api.py
- Clean up associated tests
- Maintain the `RecognitionResponse` shape (neumes field stays as empty list)

**Non-Goals:**
- Deleting model files from disk (Change 2)
- Removing training infrastructure (Change 2)
- Modifying the `/contribute` endpoint or contribution storage (Change 2)
- Adding YOLO-based neume detection (Change 5)
- Changing `NeumeInput` or `ContributionAnnotations` types (Change 6)

## Decisions

### 1. Keep `RecognitionResponse.neumes` as empty list
**Rationale:** The frontend already handles `neumes: []`. Removing the field would be a breaking API change for zero benefit — the field comes back in Change 5 with YOLO detections.

**Alternative considered:** Remove the field entirely and re-add later. Rejected — unnecessary churn for frontend consumers.

### 2. Keep `NeumeInput` and `ContributionAnnotations` types untouched
**Rationale:** The `/contribute` endpoint still accepts neume annotations in its request body. Change 2 will make `/contribute` silently ignore neumes, and Change 6 redesigns the contribution format entirely. Touching these types now would create conflicts with those changes.

### 3. Simplify model_loader.py rather than deleting it
**Rationale:** `model_loader.py` still serves the Tridis text model with caching. We remove the neume-specific functions (`has_neume_recognition`, `load_neume_recognition_model`, `get_available_recognition_models`) and the custom segmentation check (`has_custom_segmentation`), but keep the text model loading. Change 2 may further simplify this when removing all training-related model management.

### 4. Remove `NeumeBBox` and `extract_neume_bboxes` from geometry.py
**Rationale:** These are exclusively used by the neume-as-lines code path in api.py. No other consumers exist. `extract_char_bboxes` and `CharBBox` stay — they're used by the syllabification path.

### 5. Remove `_binarize_image` from api.py
**Rationale:** This function is defined but not called anywhere in the current pipeline. It was written as a preprocessing step but segmentation works better on RGB images. Dead code — remove it.

### 6. Simplify recognition.py to a single function
**Rationale:** With mm_rpred gone, the three internal functions (`_recognize_with_mm_rpred`, `_recognize_with_rpred_skip_neumes`, `_recognize_with_rpred`) collapse into one. The `RecognitionResult.line_type` field also becomes unnecessary since all lines are text, but we can keep it as always-None for simplicity or remove it — either is fine. We'll remove it since no downstream code will check it.

## Risks / Trade-offs

**[Risk] Custom segmentation model used elsewhere** → Mitigated: grep confirms it's only used in `segmentation.py` and `model_loader.py`. No external consumers.

**[Risk] Frontend depends on non-empty neumes array** → Mitigated: Frontend already handles empty neumes (it's the common case when no neume model is loaded). The response shape is unchanged.

**[Trade-off] Neume detection is temporarily unavailable** → Accepted: This is intentional. The Kraken-based neume detection doesn't work anyway (0 lines detected). Users won't notice a capability loss.
