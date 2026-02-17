## Why

The frontend annotation tool requires users to manually draw bounding boxes around each syllable in medieval manuscript images. This is time-consuming and tedious. An HTR (Handwritten Text Recognition) backend can automatically detect text lines, recognize characters, and produce syllable-level bounding boxes, dramatically reducing manual annotation effort.

## What Changes

- Add a Python-based backend service for automated syllable recognition
- Integrate Kraken HTR with the TRIDIS medieval Latin model for text recognition
- Implement Latin liturgical syllabification using pyphen with hyphen-la patterns
- Provide a FastAPI endpoint that accepts image regions and returns syllable objects with bounding boxes
- Enable the frontend to import auto-detected syllables as editable annotations

## Capabilities

### New Capabilities

- `htr-recognition`: Core HTR pipeline - image segmentation, character recognition via Kraken, and character-level geometry extraction
- `latin-syllabification`: Latin text syllabification using pyphen with ecclesiastical Latin hyphenation patterns, plus character-to-syllable bbox merging
- `recognition-api`: FastAPI HTTP endpoint for processing image regions and returning syllable JSON

### Modified Capabilities

(none - this is a new backend component)

## Impact

- **New code**: Entire `backend/` Python service (src/, tests/, pyproject.toml)
- **Dependencies**: kraken, pyphen, fastapi, uvicorn, pillow
- **Model files**: TRIDIS model (~50MB) stored in repo
- **Frontend**: Will need integration code to call the API and import results (separate change)
- **Infrastructure**: Requires Python 3.11 environment for local development
