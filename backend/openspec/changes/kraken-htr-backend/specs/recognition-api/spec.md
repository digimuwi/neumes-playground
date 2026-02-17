## ADDED Requirements

### Requirement: POST /recognize endpoint

The system SHALL provide a POST endpoint at `/recognize` that accepts an image (multipart form or base64) and an optional region, and returns recognized syllables with bounding boxes.

#### Scenario: Successful recognition request

- **WHEN** a POST request is sent to `/recognize` with an image file
- **THEN** the response contains a JSON object with a `syllables` array

#### Scenario: Recognition with region

- **WHEN** a POST request includes a `region` parameter with x, y, width, height
- **THEN** only the specified region is processed and returned syllables have coordinates relative to the original image (not the cropped region)

### Requirement: Syllable response format

The system SHALL return syllables in a JSON format containing: text (the syllable string), bbox (x, y, width, height in pixels), confidence (average confidence of constituent characters), and line_index (which line the syllable belongs to).

#### Scenario: Response structure

- **WHEN** recognition completes successfully
- **THEN** the response has structure:
  ```json
  {
    "syllables": [
      {
        "text": "Be",
        "bbox": {"x": 100, "y": 50, "width": 55, "height": 42},
        "confidence": 0.97,
        "line_index": 0
      }
    ],
    "lines": [
      {
        "text": "Benedictus es domine",
        "bbox": {"x": 100, "y": 50, "width": 500, "height": 45}
      }
    ]
  }
  ```

### Requirement: Coordinate system

The system SHALL return all bounding box coordinates in pixels, relative to the original input image (not normalized 0-1). If a region was specified, coordinates SHALL be transformed back to full-image coordinates.

#### Scenario: Coordinates relative to full image

- **WHEN** region {x:100, y:200} is processed and a syllable is found at local position {x:50, y:20}
- **THEN** the returned bbox has x=150, y=220 (offset by region origin)

### Requirement: Error handling

The system SHALL return appropriate HTTP error codes for invalid requests: 400 for invalid image format, 422 for invalid region parameters, 500 for processing errors.

#### Scenario: Invalid image format

- **WHEN** a non-image file is uploaded
- **THEN** the response is 400 with an error message

#### Scenario: Invalid region

- **WHEN** region coordinates are outside image bounds
- **THEN** the response is 422 with an error message

### Requirement: CORS support

The system SHALL allow cross-origin requests from localhost origins to enable frontend development.

#### Scenario: CORS preflight

- **WHEN** an OPTIONS request is sent from localhost:5173
- **THEN** the response includes appropriate CORS headers allowing the request
