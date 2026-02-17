## Context

The neumes-playground frontend allows users to annotate manuscript images with syllable bounding boxes (text) and neume bounding boxes (musical notation). Currently, annotations are only exportable as MEI XML for music encoding. To improve Kraken HTR models, we need to collect training data in PAGE XML format, which Kraken natively supports for both segmentation and recognition training.

The frontend already:
- Groups syllables into text lines via `useTextLines.ts`
- Stores annotations with normalized (0-1) coordinates
- Has 25+ neume types defined in `NeumeType` enum

## Goals / Non-Goals

**Goals:**
- Accept image + annotation data via a simple API endpoint
- Generate PAGE XML compatible with Kraken's `ketos train` and `ketos segtrain` commands
- Store contributions persistently for later training use
- Support both syllable (text) and neume (music notation) annotations

**Non-Goals:**
- User authentication or contributor tracking (anonymous contributions)
- Validation of annotation quality or completeness
- Automatic training pipeline integration
- Serving or listing existing contributions
- Frontend changes (separate work)

## Decisions

### 1. Input format: Multipart form with pixel coordinates

**Decision**: Accept `multipart/form-data` with image file + JSON annotations. Annotations use pixel coordinates (frontend converts from normalized).

**Rationale**:
- Matches existing `/recognize` endpoint pattern
- Pixel coordinates are what PAGE XML needs
- Frontend already has conversion logic (`normalizedToPixels`)

**Alternatives considered**:
- Base64 image in JSON body → larger payload, more complex parsing
- Normalized coordinates → would require image dimensions separately, extra conversion

### 2. PAGE XML structure: Two TextRegions (text + neumes)

**Decision**:
- Syllables go in a `TextRegion type="paragraph"` with `TextLine` elements containing `Word` elements
- Neumes go in a `TextRegion type="music-notation"` with each neume as its own `TextLine`

**Rationale**:
- Keeps text and music annotation separate for targeted training
- Syllables grouped into lines (from frontend's line detection) for natural text line training
- Neumes as individual TextLines because they don't follow consistent line structure
- Neume type names (`punctum`, `clivis`, etc.) become the "text" content for recognition training

**Alternatives considered**:
- Single TextRegion with mixed content → harder to train separate models
- Custom XML format → would require custom Kraken integration

### 3. Storage: UUID-based directories

**Decision**: Store as `contributions/<uuid>/image.{ext}` + `contributions/<uuid>/page.xml`

**Rationale**:
- Simple, collision-free naming
- Self-contained directories easy to manage
- Image filename referenced in PAGE XML's `imageFilename` attribute

**Alternatives considered**:
- Flat files with UUID prefix → harder to delete/manage pairs
- Date-based hierarchy → unnecessary complexity for this use case

### 4. Baseline computation: Synthetic from bbox

**Decision**: Compute baseline as horizontal line at ~85% of bbox height (bottom of text area).

**Rationale**:
- Baselines are required for Kraken segmentation training
- Users don't annotate baselines explicitly
- 85% is typical for Latin text sitting on a baseline

## Risks / Trade-offs

**[No baseline annotation]** → Synthetic baselines may not match actual text baselines perfectly
- *Mitigation*: 85% heuristic works well for most Latin scripts; can refine later if needed

**[No validation]** → Malformed or empty contributions could be accepted
- *Mitigation*: Basic validation (image loads, annotations non-empty) is sufficient for MVP; quality review is out of scope

**[Disk space]** → Contributions accumulate without cleanup
- *Mitigation*: Out of scope for MVP; can add cleanup/archival later

**[No deduplication]** → Same image could be contributed multiple times
- *Mitigation*: Acceptable for training data; different annotations of same image are still valuable
