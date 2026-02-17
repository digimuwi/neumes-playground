## 1. Response Model

- [x] 1.1 Add `neumes: list[NeumeInput]` field to `RecognitionResponse` in `models/types.py` (default empty list)

## 2. Neume Bbox Extraction

- [x] 2.1 Add `extract_neume_bboxes(text, cuts, confidences)` function to `pipeline/geometry.py` that splits text on whitespace, groups character bboxes by word, and merges each group into a single bbox with neume type

## 3. Response Assembly

- [x] 3.1 In `api.py` response assembly loop, branch on `rec_result.line_type`: route `"neume"` lines to neume extraction, route `"text"` / `None` lines to syllabification as before
- [x] 3.2 For neume lines, call `extract_char_bboxes` + `extract_neume_bboxes`, apply region coordinate transformation, and append to `all_neumes` list
- [x] 3.3 Pass `all_neumes` to `RecognitionResponse` in the `complete` SSE event

## 4. Tests

- [x] 4.1 Add unit test for `extract_neume_bboxes` with multi-word and single-word input
- [x] 4.2 Add integration test verifying neume lines produce neume annotations (not syllables) in the response
- [x] 4.3 Update `test_pipeline_debug.py` to print neume vs syllable counts from a real recognition run
