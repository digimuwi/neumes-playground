## Why

Users annotate manuscripts with syllable bounding boxes and neume bounding boxes in the frontend. Currently, these annotations can only be exported locally as MEI. To improve Kraken HTR/segmentation models, we need a way for users to contribute their corrected annotations as training data that can be directly consumed by Kraken.

## What Changes

- Add a new `POST /contribute` endpoint that accepts an image and annotation data
- Convert annotations to PAGE XML format (compatible with Kraken training)
- Store contributions in a file-based `contributions/` directory structure
- Each contribution stored as `contributions/<uuid>/image.{ext}` + `contributions/<uuid>/page.xml`

## Capabilities

### New Capabilities
- `training-data-contribution`: API endpoint for submitting annotated manuscript images as Kraken-compatible PAGE XML training data

### Modified Capabilities
<!-- None - this is a new, independent feature -->

## Impact

- **New API endpoint**: `POST /contribute`
- **New directory**: `contributions/` for storing submitted training data
- **New dependency**: None (PAGE XML generation is pure Python string formatting)
- **Frontend integration**: Will need to add a "Contribute" button that sends annotations to this endpoint
