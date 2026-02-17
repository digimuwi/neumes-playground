## Context

The `/recognize` endpoint currently runs a fixed pipeline: segmentation → text recognition → syllabification → text masking → neume detection. All stages run regardless of what the user is interested in. The frontend is adding a mode where users select a region and declare its type (neume or text), enabling the backend to skip irrelevant stages.

The pipeline lives in `_generate_recognition_stream()` in `api.py` (lines 121–275). Neume detection uses SAHI tiled inference in `neume_detection.py`. Text recognition uses Kraken's `rpred` with a `Segmentation` object in `recognition.py`.

## Goals / Non-Goals

**Goals:**
- Allow the frontend to pass an optional `type` parameter to `/recognize` that triggers a shorter, type-specific pipeline
- For `type="neume"`: bypass segmentation and text masking, run YOLO directly on the cropped region
- For `type="text"`: bypass Kraken segmentation, synthesize a single-line `Segmentation`, run rpred + syllabification
- Keep the existing `type=null` pipeline completely unchanged

**Non-Goals:**
- Multi-line region support for `type="text"` — regions are expected to be single-line
- Changing the response schema — both paths return `RecognitionResponse(lines, neumes)`
- Frontend implementation

## Decisions

### 1. Direct YOLO inference (no SAHI) for targeted neume recognition

**Decision:** When `type="neume"`, run YOLO's `model.predict()` directly on the cropped region instead of using SAHI tiled inference.

**Rationale:** User-selected regions are expected to be small (single staff line). These fit well within YOLO's input range (320–1280px), making tiling unnecessary overhead. SAHI adds complexity (tile generation, NMS merging) that provides no benefit for small crops.

**Alternative considered:** Using SAHI with a default tile size. Rejected because for small images SAHI would create a single tile anyway, adding overhead for the same result.

### 2. Add a `detect_neumes_direct()` function

**Decision:** Add a new function `detect_neumes_direct(image)` in `neume_detection.py` that runs YOLO prediction directly on the input image without SAHI, text masking, or segmentation.

**Rationale:** Keeps the existing `detect_neumes()` function and its SAHI logic untouched. The new function reuses the same YOLO model cache (`_load_yolo_model()`). Clean separation — the caller in `api.py` chooses which path based on `type`.

### 3. Synthetic single-line Segmentation for targeted text recognition

**Decision:** When `type="text"`, construct a `Segmentation` containing a single `BaselineLine` spanning the full cropped image:
- `baseline`: `[(0, h//2), (w, h//2)]` — horizontal center
- `boundary`: `[(0, 0), (w, 0), (w, h), (0, h)]` — full image rectangle

Then pass this to the existing `recognize_lines()` + syllabification pipeline.

**Rationale:** Kraken's `rpred` requires a `Segmentation` with baselines and boundaries. Rather than creating a new text recognition pathway, we synthesize the minimal segmentation and reuse the entire existing text pipeline. This is reliable because the user is selecting a single-line region — the synthetic baseline/boundary accurately describes the content.

**Alternative considered:** Calling Kraken's lower-level API directly without a `Segmentation` object. Rejected because it would duplicate logic and bypass the well-tested `recognize_lines()` function.

### 4. Pipeline branching in `_generate_recognition_stream()`

**Decision:** Add the `type` parameter to `_generate_recognition_stream()` and branch early after loading/cropping. Each branch emits only its relevant SSE stages and returns.

**Rationale:** Keeps changes localized to the orchestration layer. The pipeline modules (`recognition.py`, `neume_detection.py`, `latin.py`) don't need to know about `type` — they just receive the right inputs.

### 5. Skip model/patterns existence checks when not needed

**Decision:** When `type="neume"`, skip the check for `MODEL_PATH` (Tridis) and `PATTERNS_PATH` (syllabifier). When `type="text"`, skip YOLO model concerns. Only check what's actually needed.

**Rationale:** Avoids false errors when a user only has one model available.

## Risks / Trade-offs

**[Synthetic baseline may not match actual text position]** → For single-line crops, a centered horizontal baseline is a reasonable approximation. Kraken's rpred is fairly robust to baseline position since it uses the boundary polygon for feature extraction. If recognition quality is poor, we could later allow the user to draw the baseline explicitly.

**[No text masking for neume path]** → The user is trusted to select a region containing neumes. If text is present in the selected region, YOLO may produce spurious detections. This is acceptable because the user explicitly chose the region type.

**[YOLO confidence threshold hardcoded]** → Direct inference uses the same 0.25 confidence threshold as SAHI. Consistent behavior.
