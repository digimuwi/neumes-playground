### Requirement: Accept optional type parameter on /recognize endpoint
The `/recognize` endpoint SHALL accept an optional `type` form field with values `"neume"` or `"text"`. When `type` is absent or null, the existing full pipeline SHALL run unchanged.

#### Scenario: Type parameter is absent
- **WHEN** client POSTs to `/recognize` without a `type` field
- **THEN** the full pipeline runs (segmentation → recognition → syllabification → detection)

#### Scenario: Type parameter is "neume"
- **WHEN** client POSTs to `/recognize` with `type="neume"` and a region
- **THEN** only neume detection runs on the cropped region (no segmentation, no text recognition, no text masking)

#### Scenario: Type parameter is "text"
- **WHEN** client POSTs to `/recognize` with `type="text"` and a region
- **THEN** only text recognition and syllabification run on the cropped region (no segmentation, no neume detection)

#### Scenario: Invalid type value
- **WHEN** client POSTs to `/recognize` with `type="invalid"`
- **THEN** the endpoint SHALL return an error event with a message indicating the invalid type value

### Requirement: Direct YOLO neume detection without SAHI
The system SHALL provide a `detect_neumes_direct` function that accepts a PIL RGB image and runs YOLO inference directly (without SAHI tiling, without text masking). It SHALL use the same YOLO model cache and confidence threshold (0.25) as the existing `detect_neumes` function.

#### Scenario: Detect neumes on a small cropped region
- **WHEN** `detect_neumes_direct` is called with a cropped region image
- **THEN** it returns a list of `NeumeDetection` objects detected by YOLO without tiling

#### Scenario: No YOLO model available
- **WHEN** `detect_neumes_direct` is called and no YOLO model file exists
- **THEN** it returns an empty list and logs a warning

### Requirement: Synthetic single-line segmentation for targeted text recognition
When `type="text"`, the system SHALL construct a Kraken `Segmentation` object with a single `BaselineLine` spanning the full cropped image dimensions. The baseline SHALL be a horizontal line at the vertical center. The boundary SHALL be the full image rectangle.

#### Scenario: Synthetic segmentation for cropped text region
- **WHEN** a 400x80 pixel cropped region is processed with `type="text"`
- **THEN** a `Segmentation` is created with one `BaselineLine` having baseline `[(0, 40), (400, 40)]` and boundary `[(0, 0), (400, 0), (400, 80), (0, 80)]`

### Requirement: Type-targeted pipeline returns only relevant results
When `type="neume"`, the response SHALL contain neume detections and an empty lines array. When `type="text"`, the response SHALL contain text lines with syllables and an empty neumes array. The response schema (`RecognitionResponse`) SHALL remain unchanged.

#### Scenario: Neume-only response
- **WHEN** recognition completes with `type="neume"`
- **THEN** the complete event contains `RecognitionResponse(lines=[], neumes=[...])`

#### Scenario: Text-only response
- **WHEN** recognition completes with `type="text"`
- **THEN** the complete event contains `RecognitionResponse(lines=[...], neumes=[])`
