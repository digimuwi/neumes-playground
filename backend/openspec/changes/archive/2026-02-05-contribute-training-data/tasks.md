## 1. Data Models

- [x] 1.1 Add Pydantic models for contribution request (ContributionAnnotations with lines/neumes, SyllableInput, NeumeInput, BBox reuse)
- [x] 1.2 Add Pydantic model for contribution response (ContributionResponse with id and message)

## 2. PAGE XML Generation

- [x] 2.1 Create `contribution/page_xml.py` module with function to generate PAGE XML string from annotations and image dimensions
- [x] 2.2 Implement bbox-to-Coords conversion (rectangle corners as "x1,y1 x2,y2 x3,y3 x4,y4" format)
- [x] 2.3 Implement synthetic baseline generation (horizontal line at ~85% of bbox height)
- [x] 2.4 Generate text TextRegion with TextLines containing Word elements for syllables
- [x] 2.5 Generate neume TextRegion with individual TextLines for each neume

## 3. Storage

- [x] 3.1 Create `contribution/storage.py` module with function to save image and XML to `contributions/<uuid>/` directory
- [x] 3.2 Handle image format detection (JPEG vs PNG) and appropriate file extension

## 4. API Endpoint

- [x] 4.1 Add `POST /contribute` endpoint to `api.py` accepting multipart form with image and annotations JSON
- [x] 4.2 Parse and validate annotations JSON into Pydantic models
- [x] 4.3 Load image to get dimensions, generate PAGE XML, save contribution, return response

## 5. Testing

- [x] 5.1 Add unit tests for PAGE XML generation (correct structure, coords format, baseline calculation)
- [x] 5.2 Add integration test for `/contribute` endpoint (successful contribution, missing image, invalid JSON)
