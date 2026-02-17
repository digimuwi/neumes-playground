## Context

The `/recognize` endpoint's response assembly loop (`api.py:239-281`) processes all `RecognitionResult` objects identically — both text and neume lines go through `extract_char_bboxes()` → `process_line_to_syllables()` → `Syllable` response objects. The `line_type` field from recognition is never checked.

Neume recognition produces word-level tokens like `"pitus"`, `"clivis"`, `"ceitus"` separated by spaces. Each word represents one neume, and Kraken's cuts provide per-character bounding boxes that can be merged per-word to get per-neume bounding boxes.

The frontend already supports a dual annotation model: `Annotation.type: 'syllable' | 'neume'`, with syllables rendered as blue boxes and neumes as red boxes. The backend just needs to populate the neume side.

## Goals / Non-Goals

**Goals:**
- Return neume annotations with type and bounding box in the `/recognize` response
- Only syllabify text-typed lines; skip Latin syllabification for neume lines
- Reuse existing `NeumeInput` model structure for response neumes

**Non-Goals:**
- Mapping neume recognition text to a canonical neume type taxonomy (e.g., "pitus" → "punctum") — the raw recognition text is returned as-is for now
- Frontend changes to consume the new `neumes` field (separate change)
- Improving neume recognition accuracy

## Decisions

### Branch on `line_type` in the assembly loop

In the response assembly loop, check `rec_result.line_type`:
- `"text"` or `None` → syllabify as today (text pipeline)
- `"neume"` → extract per-word bounding boxes and return as neume annotations (neume pipeline)

**Rationale:** This is the minimal change — the `line_type` is already available on every `RecognitionResult`, we just need to use it. No upstream changes needed.

### Extract per-word neume bounding boxes using existing `extract_char_bboxes` + word grouping

For neume lines, reuse `extract_char_bboxes()` to get per-character bboxes, then group characters by word (split on spaces) and merge each word's bboxes into a single neume bbox. This mirrors how `map_chars_to_syllables` groups characters by syllable.

**Alternative considered:** Creating a separate neume-specific bbox extractor. Rejected because the character-level cuts from Kraken work the same way for neume recognition output — words are space-separated and each word's characters have sequential cuts.

### Add `neumes` field to `RecognitionResponse` reusing `NeumeInput`

Add `neumes: list[NeumeInput]` to `RecognitionResponse`. The `NeumeInput` model already exists with `type: str` and `bbox: BBox` fields — exactly what we need.

**Alternative considered:** Creating a new `NeumeAnnotation` model. Rejected because `NeumeInput` already has the right shape and reusing it keeps the contribution and recognition data models consistent.

### Add neume extraction as a utility function in `geometry.py`

Add `extract_neume_bboxes(text, cuts, confidences) -> list[NeumeResult]` to `geometry.py`. This function splits text on spaces, groups the corresponding character bboxes by word, and merges each group. Returns a list of `(neume_type, x, y, width, height, confidence)` tuples.

**Rationale:** Keeps the geometry concern in the geometry module, parallel to `extract_char_bboxes`.

## Risks / Trade-offs

- **[Neume type accuracy]** The recognition text (e.g., "pitus") may not match the neume type names the frontend expects (e.g., "punctum"). → For now, return the raw recognition text. A mapping layer can be added later once the neume vocabulary stabilizes.
- **[Space-separated assumption]** We assume neume recognition output uses spaces to separate individual neumes. → This is confirmed by test output (`"pitus peus es cpitus pitus pitus ceitus cetus"`). If the recognition model changes its tokenization, this logic would need updating.
- **[Breaking change]** Adding `neumes` to the response is additive, not breaking — existing clients that don't read `neumes` are unaffected since it defaults to an empty list.
