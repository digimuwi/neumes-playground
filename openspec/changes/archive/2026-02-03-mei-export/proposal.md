## Why

Users need to export their annotations to MEI (Music Encoding Initiative) format for interoperability with musicological tools and digital edition workflows. MEI is the standard format for encoding medieval music notation, and without export capability, annotations are trapped in the application.

## What Changes

- Add MEI export functionality that transforms annotations into valid MEI XML
- Export includes full MEI hierarchy (meiHead, music, facsimile, body)
- Syllables are ordered in reading order (by text line, then left-to-right)
- Neumes are nested within their assigned syllables, ordered left-to-right
- Facsimile section includes zones with pixel coordinates for each annotation
- Neume elements include `@type` attribute mapping to MEI vocabulary
- Download triggered via toolbar button

## Capabilities

### New Capabilities

- `mei-export`: Export annotations as MEI XML with facsimile zones linking to source image regions

### Modified Capabilities

<!-- None - this is additive functionality -->

## Impact

- New export hook/utility for MEI generation
- Toolbar gains export button
- Requires extracting image dimensions from dataUrl for coordinate denormalization
- No changes to existing annotation or state management logic
