## Context

The application stores annotations as normalized (0-1) coordinates with type metadata. Syllables have text content; neumes have a type classification. The existing `useNeumeAssignment` hook computes which neumes belong to which syllables based on spatial relationships. The existing `useTextLines` hook groups syllables into text lines with linear regression for tilt handling.

MEI (Music Encoding Initiative) is the standard XML format for encoding medieval music. It requires:
- Full document hierarchy: `mei > music > (facsimile + body)`
- Facsimile section with `zone` elements containing pixel coordinates
- Syllables containing `syl` (text) and `neume` children
- Neumes must have `@type` attribute from MEI vocabulary

## Goals / Non-Goals

**Goals:**
- Export valid MEI XML that can be opened in MEI-aware tools
- Preserve spatial relationships via facsimile zones
- Support reading-order output (text lines top-to-bottom, syllables left-to-right)
- Provide one-click export from the toolbar

**Non-Goals:**
- Pitch encoding (no `<nc>` elements - we don't capture pitch data)
- Round-trip import of MEI files
- Validation against MEI schema (trust the structure)
- Image embedding in MEI (just reference placeholder filename)

## Decisions

### 1. Pure function for MEI generation

**Decision**: Create a standalone function `generateMEI(annotations, imageDimensions)` that returns an XML string. No React hooks or side effects in the generation logic.

**Rationale**: Easier to test, reusable, keeps concerns separated. The UI layer handles triggering the download.

**Alternatives considered**:
- Hook-based approach: Would couple generation to React lifecycle unnecessarily
- Class-based builder: Overkill for one-time string generation

### 2. Manual XML string construction

**Decision**: Build XML via template literals rather than using a DOM-based XML library.

**Rationale**: The MEI structure is fixed and predictable. No need for xmldom/fast-xml-parser dependencies. Template literals give readable output with proper indentation.

**Alternatives considered**:
- xmldom: Adds dependency, verbose API for simple structure
- fast-xml-parser: Good for parsing, less ergonomic for generation

### 3. Coordinate denormalization at export time

**Decision**: Keep annotations stored as normalized (0-1) coordinates. Denormalize to pixels only during MEI generation.

**Rationale**: Preserves the existing data model. Pixel coordinates are only needed for MEI output. The image dimensions needed for denormalization can be extracted from the dataUrl when export is triggered.

### 4. Reuse existing assignment and text line logic

**Decision**: Extract the core logic from `useNeumeAssignment` and `useTextLines` into pure functions that can be called from the export utility without React hooks.

**Rationale**: The hooks already implement correct assignment and ordering logic. DRY principle - don't duplicate the algorithm. The hook versions can call the pure functions.

### 5. Export button in Toolbar component

**Decision**: Add export button to existing Toolbar, next to undo/redo buttons.

**Rationale**: Toolbar is the natural location for document-level actions. Keeps UI changes minimal.

## Risks / Trade-offs

**[Risk] Image dimensions not stored in state** → Extract dimensions from dataUrl by loading into an Image element at export time. This is async but fast since image is already cached.

**[Risk] Empty syllables (no text)** → Export with empty `<syl/>` element. MEI allows this.

**[Risk] Orphan neumes (no assigned syllable)** → Skip them in export. Log warning to console for debugging.

**[Trade-off] No MEI schema validation** → Keeps implementation simple, but invalid output possible. Mitigated by following MEI examples closely.

**[Trade-off] Placeholder image filename** → We only have dataUrl, not original filename. Use "source-image.jpg" as placeholder. Users can edit the MEI if needed.
