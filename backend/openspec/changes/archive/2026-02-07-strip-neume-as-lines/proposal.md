## Why

The current pipeline treats neumes as typed text lines recognized via Kraken OCR (`mm_rpred`), but this approach is fundamentally broken — Kraken's line-based architecture expects characters along a horizontal baseline, while real neumes are stacked, tilted, and spatially irregular. The custom segmentation model produces 0 lines on the test manuscript, while the default Kraken segmentation finds all 21 text lines perfectly. This change strips out the neume-as-lines machinery so the recognition pipeline is clean and correct for text, preparing the ground for a YOLO-based neume detection pipeline in a subsequent change.

## What Changes

- **Remove** multi-model recognition routing (`mm_rpred`) from `recognition.py` — always use single-model `rpred` with the Tridis text model
- **Remove** neume/custom segmentation model loading from `model_loader.py` — no more `has_neume_recognition()`, `load_neume_recognition_model()`, `get_available_recognition_models()`, `has_custom_segmentation()`
- **Remove** custom segmentation model branching from `segmentation.py` — always use default Kraken `blla.segment()`
- **Remove** neume processing branch from `api.py`'s recognition stream generator (the block that calls `extract_neume_bboxes` for neume-typed lines)
- **Remove** `_binarize_image()` from `api.py` — unused preprocessing function
- **Remove** `extract_neume_bboxes()` and `NeumeBBox` from `geometry.py`
- **Keep** `RecognitionResponse.neumes` field as an always-empty list (preserves frontend contract)
- **Keep** `NeumeInput` type (still used by `/contribute` endpoint)
- **Remove** related tests: neume recognition assertions in `test_sse_progress.py`, `test_model_loader.py` neume tests, `test_geometry.py` neume bbox tests

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `neume-annotation-response`: Temporarily inactive — neumes are no longer detected via Kraken OCR. The `neumes` array in the recognition response will always be empty until YOLO-based detection is added in a future change.

## Impact

- **API**: `/recognize` response shape unchanged (neumes field stays, just always empty). No breaking change for frontend consumers.
- **Code**: `api.py`, `recognition.py`, `segmentation.py`, `model_loader.py`, `geometry.py`, `types.py`, and associated tests.
- **Models**: Custom segmentation and neume recognition model files in `models/` become unused (not deleted — Change 2 handles cleanup of training infrastructure and model files).
- **Dependencies**: No dependency changes. Kraken's `mm_rpred` import is removed but Kraken itself stays.
