## Why

The current PAGE XML generation creates structures that don't align well with Kraken's training requirements: (1) trailing hyphens on syllables indicate position but aren't visible in manuscripts, confusing OCR training; (2) each neume gets its own TextLine, which doesn't reflect the visual "neume band" structure and makes line-type filtering awkward; (3) separate overlapping regions for text and neumes don't provide useful segmentation boundaries.

## What Changes

- **BREAKING**: Remove trailing hyphens (`-`) from syllable text in PAGE XML output. Syllables like `CI-` become `CI`. Position information remains in the client for MEI export but is not included in training data.
- **BREAKING**: Restructure neumes from individual TextLines to Word elements within a parent TextLine. Each neume band becomes one TextLine containing multiple Word children.
- Add `custom` attribute with type information to TextLines (`type:neume` or `type:text`) to enable filtering for Kraken's segmentation training.
- Use a single content TextRegion instead of separate overlapping regions for text and neumes.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `training-data-contribution`: Requirements change for PAGE XML structure - neumes become Word children of TextLines instead of individual TextLines, syllable text no longer includes trailing hyphens, TextLines get type attributes, and region structure changes to single content region.

## Impact

- **PAGE XML generation**: Core changes to how TextRegions, TextLines, and Words are structured
- **Existing contributions**: Previously generated PAGE XML files will have the old structure (may need migration or regeneration)
- **Client MEI export**: No impact - hyphen position info stays client-side
- **Kraken training workflow**: Better alignment with segmentation/recognition training requirements
