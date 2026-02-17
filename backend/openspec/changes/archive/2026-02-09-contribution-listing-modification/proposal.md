## Why

Contributions (annotated training data) are stored on the backend but invisible to the frontend. If data is lost or needs editing, there's no way to access existing contributions from the UI. Users need the ability to browse, load, edit, and save back contributions directly from the frontend editor.

## What Changes

- Add `GET /contributions` endpoint returning a summary list of all stored contributions (ID, image metadata, annotation counts)
- Add `GET /contributions/{id}` endpoint returning full contribution data including base64-encoded image
- Add `PUT /contributions/{id}` endpoint to update annotations on an existing contribution (preserving the original image and image metadata)
- Add storage functions `get_contribution()` and `update_contribution_annotations()` to support the new endpoints
- Add `ContributionSummary` and `ContributionDetail` response models
- Add input validation for contribution IDs (path traversal protection)

## Capabilities

### New Capabilities
- `contribution-retrieval`: Retrieving individual contributions with full data (image + annotations) and listing all contributions with summary info
- `contribution-update`: Updating annotations on existing contributions while preserving image data

### Modified Capabilities
_None_ - the existing `training-data-contribution` spec covers creation and storage; the new capabilities extend the system without changing existing behavior.

## Impact

- **Code**: `storage.py` (2 new functions), `types.py` (2 new models), `api.py` (3 new endpoints), `test_contribution.py` (new test classes)
- **APIs**: Three new REST endpoints under `/contributions`
- **Dependencies**: `base64` (stdlib) for image encoding in GET response
- **Systems**: Read-only access to existing contribution directories; write access limited to `annotations.json` replacement
