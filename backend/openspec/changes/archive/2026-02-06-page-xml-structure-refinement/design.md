## Context

The PAGE XML generation in `page_xml.py` currently produces structures optimized for a generic document model rather than Kraken's specific training requirements for neumatic notation manuscripts. Key issues identified:

1. **Syllable hyphens**: Text like `CI-` includes trailing hyphens that indicate syllable position (initial/medial/final) for MEI export, but these characters don't appear in the manuscript images, confusing OCR training.

2. **Neume structure**: Each neume is wrapped in its own `TextLine`, treating them as isolated elements. However, neumes form continuous visual bands above text lines and should be grouped accordingly.

3. **Region overlap**: Separate `TextRegion` elements for text and neumes result in two near-full-page regions with slight vertical offset, providing no useful segmentation boundaries.

The current structure in `page_xml.py`:
- Text: `TextRegion(paragraph)` → `TextLine` per line → `Word` per syllable
- Neumes: `TextRegion(music-notation)` → `TextLine` per neume (no Word children)

## Goals / Non-Goals

**Goals:**
- Produce PAGE XML that trains effective Kraken models for both segmentation and recognition
- Enable line-type filtering via `--valid-baselines` for segmentation training
- Preserve all spatial information (coordinates, baselines) for accurate training
- Keep the structure simple and aligned with Kraken's expectations

**Non-Goals:**
- Migrating existing contribution data (can be regenerated if needed)
- Changing the client-side annotation workflow or MEI export
- Supporting other OCR engines beyond Kraken
- Grouping neumes by their associated syllables (syllable↔neume linking is not needed for OCR)

## Decisions

### Decision 1: Strip trailing hyphens from syllable text

**Choice**: Remove `-` suffix from syllable text during PAGE XML generation.

**Rationale**: The hyphen is a transcription convention, not a visual element in the manuscript. OCR models should learn to recognize what's actually written. The position information (initial/medial/final) is only needed for MEI export, which happens client-side.

**Implementation**: Strip trailing `-` from `syl.text` when building Word elements.

**Alternative considered**: Keep hyphens and train OCR to expect them → Rejected because it teaches the model to "hallucinate" characters that don't exist in the input images.

### Decision 2: Group neumes into TextLines with Word children

**Choice**: Each "neume band" (horizontal row of neumes) becomes one `TextLine` containing `Word` elements for individual neumes.

**Rationale**:
- Mirrors the text structure (`TextLine` → `Word` children)
- Reflects the visual manuscript structure where neumes form continuous bands
- Enables meaningful baseline-level filtering in Kraken

**Implementation**:
- Group neumes by their y-coordinate proximity into bands
- Each band becomes a `TextLine` with `type:neume` in the custom attribute
- Individual neumes become `Word` children with their bounding boxes and type names

**Alternative considered**: Keep one TextLine per neume → Rejected because a "line" containing a single glyph is semantically odd and doesn't reflect the manuscript structure.

### Decision 3: Add type attribute to TextLines via `custom` attribute

**Choice**: Use PAGE XML's `custom` attribute with format `structure {type:neume;}` or `structure {type:text;}`.

**Rationale**: Kraken's `--valid-baselines` option filters by baseline type. The `custom` attribute with `structure {type:...}` is the PAGE XML convention for line typing that Kraken recognizes.

**Implementation**: Add `custom="structure {type:neume;}"` to neume TextLines and `custom="structure {type:text;}"` to text TextLines.

### Decision 4: Single content TextRegion

**Choice**: Use one `TextRegion` containing all TextLines (both text and neumes), typed by their custom attribute.

**Rationale**: Two overlapping near-full-page regions don't provide useful segmentation boundaries. A single region with typed lines is cleaner and lets Kraken filter at the line level.

**Implementation**: Replace separate text/neume regions with single `TextRegion id="content" type="music-notation"` containing all lines in reading order (interleaved neume and text lines).

**Alternative considered**: Per-system regions (one region per neume+text pair) → More complex, and Kraken's line-level filtering makes region boundaries less important.

### Decision 5: Neume band grouping heuristic

**Choice**: Group neumes into bands based on y-coordinate overlap.

**Rationale**: Neumes that visually belong to the same band should be in the same TextLine. The grouping should be automatic based on spatial proximity.

**Implementation**:
- Sort neumes by y-coordinate
- Group neumes whose bounding boxes overlap vertically (or are within a small threshold)
- Each group becomes one neume TextLine
- Within a band, order neumes left-to-right by x-coordinate

## Risks / Trade-offs

**[Risk] Neume band grouping may misalign with text lines**
→ Mitigation: The grouping is purely spatial based on neume positions. Syllable↔neume correlation is not needed for OCR training; each model trains independently.

**[Risk] Existing contributions have old PAGE XML structure**
→ Mitigation: Contributions can be regenerated from stored annotation data. The image + annotation JSON are preserved; only the derived PAGE XML changes.

**[Risk] Custom attribute format may not match Kraken's expectations**
→ Mitigation: Verified that `custom="structure {type:...;}"` is the standard PAGE XML format and is recognized by Kraken's filtering options.

**[Trade-off] Losing separate region boundaries for text vs neumes**
→ Accepted: Line-level typing with `--valid-baselines` filtering is more useful for Kraken training than region boundaries.
