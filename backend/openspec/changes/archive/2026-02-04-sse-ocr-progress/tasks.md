## 1. SSE Infrastructure

- [x] 1.1 Create progress event model (Pydantic) with `stage`, optional `current`/`total`, optional `result`, optional `message`
- [x] 1.2 Create SSE event formatter function that produces `data: {json}\n\n` format

## 2. Pipeline Progress Callbacks

- [x] 2.1 Add progress callback parameter to `recognize_lines()` function
- [x] 2.2 Call progress callback for each line during recognition loop

## 3. Endpoint Refactoring

- [x] 3.1 Convert `/recognize` endpoint to return `StreamingResponse` with `text/event-stream` content type
- [x] 3.2 Create async generator that orchestrates pipeline and yields progress events at each stage
- [x] 3.3 Emit `loading` event before image loading
- [x] 3.4 Emit `segmenting` event before segmentation
- [x] 3.5 Emit `recognizing` events with `current`/`total` for each line
- [x] 3.6 Emit `syllabifying` event before syllabification
- [x] 3.7 Emit `complete` event with full result at end

## 4. Error Handling

- [x] 4.1 Wrap pipeline in try/except and emit `error` event with message on failure
- [x] 4.2 Ensure stream closes after error event

## 5. Testing

- [x] 5.1 Add test for successful SSE stream with all expected events
- [x] 5.2 Add test for per-line recognition progress
- [x] 5.3 Add test for error event on invalid image
- [x] 5.4 Add test for correct content-type header
