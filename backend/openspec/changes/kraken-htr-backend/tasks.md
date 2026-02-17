## 1. Project Setup

- [x] 1.1 Create pyproject.toml with dependencies (kraken, pyphen, fastapi, uvicorn, pillow)
- [x] 1.2 Set up src/htr_service/ package structure with __init__.py files
- [x] 1.3 Copy TRIDIS model to models/ directory
- [x] 1.4 Download and include hyphen-la liturgical patterns in patterns/ directory
- [x] 1.5 Create .gitignore for Python (venv, __pycache__, etc.)

## 2. HTR Recognition Pipeline

- [x] 2.1 Implement segmentation.py - wrap Kraken blla.segment() to return line objects
- [x] 2.2 Implement recognition.py - wrap Kraken rpred.rpred() to return text + cuts + confidences
- [x] 2.3 Implement geometry.py - extract character bboxes from cuts (consecutive cuts → bbox)
- [x] 2.4 Add region cropping support - crop image before processing, transform coords back

## 3. Latin Syllabification

- [x] 3.1 Implement latin.py - load pyphen with liturgical dictionary
- [x] 3.2 Add syllabify_text() function - split text into syllables per word
- [x] 3.3 Implement character-to-syllable mapping - track which chars belong to each syllable
- [x] 3.4 Implement bbox merging - merge character bboxes into syllable bboxes

## 4. Pydantic Models

- [x] 4.1 Define BBox model (x, y, width, height as int)
- [x] 4.2 Define Syllable model (text, bbox, confidence, line_index)
- [x] 4.3 Define Line model (text, bbox)
- [x] 4.4 Define RecognitionRequest model (image, optional region)
- [x] 4.5 Define RecognitionResponse model (syllables list, lines list)

## 5. FastAPI Service

- [x] 5.1 Create api.py with FastAPI app instance
- [x] 5.2 Implement POST /recognize endpoint - accept image upload
- [x] 5.3 Add region parameter handling - validate and apply cropping
- [x] 5.4 Wire up pipeline: segment → recognize → syllabify → merge → respond
- [x] 5.5 Add CORS middleware for localhost origins
- [x] 5.6 Add error handling (400, 422, 500 responses)

## 6. Integration & Testing

- [x] 6.1 Create run script or __main__.py for `python -m htr_service`
- [x] 6.2 Test with sample manuscript image via curl/httpie
- [x] 6.3 Verify syllable bboxes align correctly with image
