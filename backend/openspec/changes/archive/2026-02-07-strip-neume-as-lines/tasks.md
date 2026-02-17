## 1. Simplify segmentation

- [x] 1.1 Remove `has_custom_segmentation()` and custom segmentation model loading from `model_loader.py` (constants, cache, function)
- [x] 1.2 Simplify `segment_image()` in `segmentation.py` to always use default Kraken `blla.segment()` — remove custom model branching and `model_loader` import

## 2. Simplify recognition

- [x] 2.1 Remove `mm_rpred` import and `_recognize_with_mm_rpred()` from `recognition.py`
- [x] 2.2 Remove `_recognize_with_rpred_skip_neumes()` from `recognition.py`
- [x] 2.3 Remove `_get_line_type()` helper and `line_type` field from `RecognitionResult` in `recognition.py`
- [x] 2.4 Simplify `recognize_lines()` to always call single-model `rpred` with Tridis model — remove neume model checks and routing logic
- [x] 2.5 Remove neume recognition functions from `model_loader.py`: `has_neume_recognition()`, `load_neume_recognition_model()`, `get_available_recognition_models()`, and related constants/caches

## 3. Simplify API stream generator

- [x] 3.1 Remove neume processing branch (neume-typed line handling, `extract_neume_bboxes` call) from `_generate_recognition_stream()` in `api.py` — all lines go through syllabification
- [x] 3.2 Remove `_binarize_image()` function from `api.py`
- [x] 3.3 Remove unused imports from `api.py` (`extract_neume_bboxes`, `NeumeInput`, and any other now-unused imports)

## 4. Clean up geometry module

- [x] 4.1 Remove `NeumeBBox` class and `extract_neume_bboxes()` function from `geometry.py`

## 5. Update tests

- [x] 5.1 Remove `TestNeumeAnnotationResponse` class from `test_sse_progress.py` and update remaining recognition tests to assert `neumes: []`
- [x] 5.2 Remove neume bbox tests from `test_geometry.py` (keep `extract_char_bboxes` tests)
- [x] 5.3 Remove neume recognition and mm_rpred tests from `test_model_loader.py` — keep tests for Tridis text model loading
- [x] 5.4 Remove `test_pipeline_debug.py` neume-related debug tests (or the whole file if all tests are neume/custom-model related)

## 6. Verify

- [x] 6.1 Run full test suite — all tests pass with no neume-related failures
- [x] 6.2 Verify `/recognize` endpoint returns valid response with `neumes: []`
