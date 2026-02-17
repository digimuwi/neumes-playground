## Context

The `/recognize` SSE stream generator in `api.py` currently runs: load → segment → recognize → syllabify → complete. Text masking and neume detection modules exist as standalone functions but are not called. The `neumes` array in the response is always empty.

The stream generator already has the segmentation result and the original image available. We need to add text masking + detection as one additional step.

## Goals / Non-Goals

**Goals:**
- Wire `mask_text_regions()` → `detect_neumes()` into the recognition stream
- Emit a `"detecting"` progress event so the frontend can show detection status
- Apply region coordinate offsets to neume bboxes (same pattern as syllable bboxes)
- Populate the `neumes` array in the response

**Non-Goals:**
- Changing the detection module itself (done in Change 4)
- Adding neume filtering or confidence thresholds in the API layer
- Associating neumes with specific text lines or syllables

## Decisions

### Place detection after syllabifying, before complete
**Choice**: The stage sequence becomes: loading → segmenting → recognizing → syllabifying → detecting → complete.
**Rationale**: Detection is independent of syllabification and could run in parallel, but for simplicity in a synchronous generator, placing it after syllabifying keeps the flow linear. Detection is fast compared to recognition so it won't noticeably delay the response.
**Alternative**: Run detection in parallel with recognition/syllabification — rejected for now because the generator is synchronous and the complexity isn't justified.

### Reuse the existing region offset pattern for neume bboxes
**Choice**: Apply the same `region_obj.x` / `region_obj.y` offset to neume bboxes as is done for syllable bboxes and line bboxes.
**Rationale**: Detection runs on the cropped region image. Bboxes need to be mapped back to full-image coordinates, same as all other bboxes.

### Skip detection gracefully when no lines are found
**Choice**: If segmentation finds no lines, skip detection entirely (no masking needed, nothing to detect).
**Rationale**: Already handled — the early return for empty segmentation produces an empty response before detection would run.

## Risks / Trade-offs

- **Detection with no model** → Returns empty neumes array, same as today. No user-visible change until a model is trained. The `"detecting"` stage still emits briefly.
- **Added latency** → Text masking + YOLO inference add time to the pipeline. Mitigated: when no model exists, detection is instant (returns empty). When a model exists, SAHI tiling keeps inference manageable.
