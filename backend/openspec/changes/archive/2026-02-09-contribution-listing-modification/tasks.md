## 1. Storage Layer

- [x] 1.1 Add `get_contribution(contribution_id: str)` to `storage.py` — reads `annotations.json` and image file, returns dict with `id`, `image` (including base64 `data_url`), `lines`, `neumes`. Raises `FileNotFoundError` if missing.
- [x] 1.2 Add `update_contribution_annotations(contribution_id: str, annotations: ContributionAnnotations)` to `storage.py` — loads existing `annotations.json` to preserve `image` block, replaces `lines` and `neumes`, writes back. Raises `FileNotFoundError` if missing.
- [x] 1.3 Add UUID validation helper `_validate_contribution_id(contribution_id: str)` to `storage.py` — raises `ValueError` for non-UUID strings.

## 2. Response Models

- [x] 2.1 Add `ImageMetadata` model to `types.py` with `filename: str`, `width: int`, `height: int`
- [x] 2.2 Add `ContributionSummary` model to `types.py` with `id: str`, `image: ImageMetadata`, `line_count: int`, `syllable_count: int`, `neume_count: int`
- [x] 2.3 Add `ImageDetail` model to `types.py` extending metadata with `data_url: str`
- [x] 2.4 Add `ContributionDetail` model to `types.py` with `id: str`, `image: ImageDetail`, `lines: list[LineInput]`, `neumes: list[NeumeInput]`

## 3. API Endpoints

- [x] 3.1 Add `GET /contributions` endpoint to `api.py` — calls `list_contributions()`, reads each `annotations.json` to build `ContributionSummary` list, returns `list[ContributionSummary]`
- [x] 3.2 Add `GET /contributions/{id}` endpoint to `api.py` — validates UUID, calls `get_contribution()`, returns `ContributionDetail`. Returns 404 on `FileNotFoundError` or invalid UUID.
- [x] 3.3 Add `PUT /contributions/{id}` endpoint to `api.py` — validates UUID, accepts `ContributionAnnotations` JSON body, calls `update_contribution_annotations()`, returns `ContributionResponse`. Returns 404 on `FileNotFoundError`, 422 on invalid body.
- [x] 3.4 Update `contribution/__init__.py` to export new functions

## 4. Tests

- [x] 4.1 Add `TestListContributionsEndpoint` class — tests: empty list, populated list with correct counts, malformed contributions skipped
- [x] 4.2 Add `TestGetContributionEndpoint` class — tests: successful retrieval with base64 image, 404 for non-existent ID, 404 for invalid UUID format
- [x] 4.3 Add `TestUpdateContributionEndpoint` class — tests: successful update preserves image metadata, 404 for non-existent ID, 422 for invalid annotations, 404 for invalid UUID
- [x] 4.4 Run full test suite to verify no regressions
