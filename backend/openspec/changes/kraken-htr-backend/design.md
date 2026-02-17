## Context

The neumes-playground frontend is a React/TypeScript annotation tool for medieval manuscripts with musical neumes. Users currently draw bounding boxes manually for each syllable. The backend will automate syllable detection using Kraken HTR with the TRIDIS medieval Latin model.

**Current state**: No backend exists. Frontend is purely client-side.

**Constraints**:
- Python 3.11 required (Kraken compatibility)
- TRIDIS model is ~50MB .mlmodel file
- Target is local development only (no auth/rate limiting needed yet)

## Goals / Non-Goals

**Goals:**
- Provide an HTTP API that accepts an image region and returns syllable bounding boxes
- Use Kraken for line segmentation and character-level OCR
- Use pyphen with hyphen-la liturgical patterns for Latin syllabification
- Return pixel coordinates (not normalized) and all confidence values
- Keep the service simple and focused on the HTR pipeline

**Non-Goals:**
- Authentication or rate limiting (local dev only)
- Neume recognition (future feature, separate model needed)
- Training new HTR models
- Frontend integration (separate change)
- Batch processing / queue system

## Decisions

### 1. Kraken for HTR

**Decision**: Use Kraken 6.x from GitHub with TRIDIS model

**Rationale**:
- Kraken provides baseline segmentation + OCR in one package
- TRIDIS model specifically trained on medieval Latin manuscripts
- Crucially, Kraken provides `cuts` - character-level geometry needed for syllable bbox merging
- Validated in spike: recognizes the St. Gallen manuscript text accurately

**Alternatives considered**:
- Tesseract: Less accurate on medieval scripts, harder to get character positions
- EasyOCR: Good accuracy but no character-level geometry
- Custom model: Out of scope, significant training effort

### 2. pyphen + hyphen-la for syllabification

**Decision**: Use pyphen library with hyphen-la liturgical Latin patterns

**Rationale**:
- pyphen is pure Python, well-maintained
- hyphen-la patterns are specifically for ecclesiastical Latin (Gregorio Project)
- Validated in spike: correctly syllabifies words like "Benedictus" → "Be-ne-dic-tus"
- MIT licensed, can include patterns in repo

**Alternatives considered**:
- Frontend's `hyphen` JS lib via subprocess: Adds complexity, Node dependency
- Rule-based custom syllabifier: Less accurate, maintenance burden
- SyllabiPy: Beta Latin support, requires macrons for accuracy

### 3. FastAPI for HTTP layer

**Decision**: Use FastAPI with uvicorn

**Rationale**:
- Native async support
- Automatic OpenAPI documentation
- Pydantic for request/response validation
- Simple and lightweight

**Alternatives considered**:
- Flask: Heavier, less modern async story
- Direct CLI tool: Would require frontend to spawn processes

### 4. Pixel coordinates (not normalized)

**Decision**: Return bounding boxes in pixel coordinates

**Rationale**:
- Simpler mental model
- Frontend can normalize if needed
- Avoids precision loss from normalization round-trips

### 5. Project structure

**Decision**: Single-package structure under `backend/src/htr_service/`

```
backend/
├── pyproject.toml
├── src/
│   └── htr_service/
│       ├── __init__.py
│       ├── api.py              # FastAPI routes
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── segmentation.py # Kraken segmentation wrapper
│       │   ├── recognition.py  # Kraken OCR wrapper
│       │   └── geometry.py     # Character bbox extraction from cuts
│       ├── syllabification/
│       │   ├── __init__.py
│       │   └── latin.py        # pyphen + bbox merging
│       └── models/
│           └── types.py        # Pydantic models
├── models/
│   └── Tridis_Medieval_EarlyModern.mlmodel
├── patterns/
│   └── hyph_la_liturgical.dic  # Latin hyphenation patterns
└── tests/
```

## Risks / Trade-offs

**[Risk] Kraken performance on large images** → Mitigation: Process regions, not full pages. Frontend sends cropped area.

**[Risk] TRIDIS model accuracy varies by manuscript style** → Mitigation: Return confidence scores, let user review/correct in frontend.

**[Risk] 50MB model file in repo** → Mitigation: Acceptable for now (local dev). Could move to Git LFS or download script later.

**[Risk] pyphen patterns may not handle all medieval Latin variants** → Mitigation: Liturgical patterns cover most cases. Edge cases can be manually corrected.

**[Trade-off] Synchronous processing vs async queue** → Chose sync for simplicity. A single image region processes in ~5s, acceptable for interactive use.
