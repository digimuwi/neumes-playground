## Context

The `/contribute` endpoint currently accepts image + annotations (lines with syllables, neumes), converts text annotations to PAGE XML via `page_xml.py`, and stores `image.{ext}` + `page.xml` per contribution. Neumes are silently discarded because PAGE XML has no representation for them.

Since Changes 3-5 moved neume detection to YOLO, PAGE XML serves no consumer. Change 7 will need neume annotations for YOLO training export. The contribution store must preserve both text and neume annotations faithfully.

Current flow:
```
Frontend → /contribute → parse annotations → generate_page_xml() → save image + page.xml
                                                  ↑
                                            neumes discarded
```

Target flow:
```
Frontend → /contribute → parse annotations → save image + annotations.json
                                                  ↑
                                            neumes preserved, no transformation
```

## Goals / Non-Goals

**Goals:**
- Store both text and neume annotations in a single JSON file
- Preserve annotations exactly as submitted (no transformation at storage time)
- Remove all PAGE XML generation code
- Keep the API contract unchanged (same input format, same response)

**Non-Goals:**
- Migrating existing contributions from PAGE XML to JSON format
- Validating neume types against a class list (deferred to Change 7)
- Any training export functionality (Change 7)
- Changing the annotations input format from the frontend

## Decisions

### Store raw annotations with image metadata

Store annotations as JSON with an added `image` metadata block containing filename, width, and height. This metadata is needed by downstream consumers (Change 7 YOLO export) without having to re-read the image file.

The annotations JSON schema:
```json
{
  "image": {"filename": "image.jpg", "width": 3328, "height": 4992},
  "lines": [{"syllables": [{"text": "Be-", "bbox": {"x": 100, "y": 200, "width": 40, "height": 30}}]}],
  "neumes": [{"type": "punctum", "bbox": {"x": 120, "y": 170, "width": 15, "height": 12}}]
}
```

**Why not transform at storage time?** The contribution store should be a faithful record. Transformations (hyphen stripping, coordinate normalization, class ID mapping) are export concerns. This makes the store format-agnostic — any future export pipeline reads the same canonical JSON.

**Alternative considered:** Storing as a Pydantic `.json()` dump of the existing `ContributionAnnotations` model. Rejected because it doesn't include image metadata, and coupling storage format to a specific Pydantic model version creates fragility.

### Delete page_xml.py entirely

No deprecation period. PAGE XML has zero consumers after Changes 1-2 removed Kraken training. The module is a clean delete — no other code imports from it except `contribution/__init__.py` and the `/contribute` endpoint.

**Alternative considered:** Keeping `page_xml.py` as an optional export. Rejected — there's no use case. If Kraken training data is ever needed again, it can be regenerated from `annotations.json`.

### Reuse existing Pydantic models for validation

The existing `ContributionAnnotations`, `LineInput`, `SyllableInput`, `NeumeInput`, and `BBox` models already define the input schema correctly. No new models needed for input validation.

Add a lightweight `ImageMetadata` model (or just a dict) for the `image` block in `annotations.json`. This doesn't need to be a separate Pydantic model — it's constructed in the endpoint from the uploaded image's properties.

### Keep storage.py's structure, change its internals

`save_contribution()` keeps the same directory layout (`contributions/<uuid>/`) but writes `annotations.json` instead of `page.xml`. The function signature changes: accepts annotations dict + image metadata instead of a PAGE XML string.

## Risks / Trade-offs

- **Existing contributions become orphaned** → Acceptable. This is early development with test data only. No migration needed.
- **No schema versioning on annotations.json** → Low risk for now. If the schema evolves, we can add a `"version"` field later. Current simplicity is worth it.
- **Neume type strings are free-form** → By design. Validation against a class list happens at YOLO export time (Change 7), not at contribution time. This allows the frontend to introduce new neume types without backend changes.
