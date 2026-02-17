## Why

The `/contribute` endpoint stores annotations as PAGE XML — a format designed for Kraken HTR training. Since neume detection moved from Kraken to YOLO (Changes 3-5), PAGE XML no longer serves any consumer. Neume annotations are silently discarded because PAGE XML has no way to represent them. We need a storage format that faithfully preserves both text and neume annotations as the user submitted them.

## What Changes

- **Remove `page_xml.py`** — PAGE XML generation is no longer needed. No downstream consumer exists.
- **Replace storage format** — Contributions store `annotations.json` instead of `page.xml`. The JSON captures exactly what the frontend sends: lines with syllables, neumes with type and bbox, plus image metadata. No transformation at storage time (e.g., no hyphen stripping — that's an export concern for Change 7).
- **Store neume annotations** — **BREAKING** for stored data format. Neumes are no longer silently discarded. The `neumes` array is persisted as-is. Neume type strings are stored verbatim with no validation against a fixed class list (class mapping is deferred to Change 7).
- **Simplify `/contribute` endpoint** — Remove PAGE XML generation step. The endpoint validates input, stores image + JSON, returns the contribution ID. Same API contract (multipart form with image + annotations JSON), same response shape.

## Capabilities

### New Capabilities

_(none — this is a redesign of an existing capability)_

### Modified Capabilities

- `training-data-contribution`: Full rewrite. Storage format changes from PAGE XML to JSON. Neumes are now stored instead of discarded. PAGE XML requirements removed entirely.

## Impact

- **Files removed**: `contribution/page_xml.py`
- **Files rewritten**: `contribution/storage.py`, `contribution/__init__.py`
- **Files modified**: `api.py` (`/contribute` endpoint), `types.py` (may add image metadata model)
- **Tests rewritten**: `test_contribution.py` — all PAGE XML assertions replaced with JSON storage assertions, neume storage assertions added
- **Stored data format**: New contributions use `annotations.json` instead of `page.xml`. Existing contributions on disk are not migrated.
- **API contract**: Unchanged — same multipart form input, same response shape. Not a breaking API change.
