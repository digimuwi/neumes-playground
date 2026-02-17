## Context

The OCR pipeline (`/recognize` endpoint) processes images through multiple stages: image loading, line segmentation, text recognition (per-line), and syllabification. Processing takes ~20 seconds with no feedback to the client.

Current architecture:
- `api.py`: FastAPI endpoint, orchestrates pipeline
- `recognition.py`: Kraken OCR, already iterates line-by-line via `rpred.rpred()` generator
- Response: Single JSON `RecognitionResponse` after all processing completes

## Goals / Non-Goals

**Goals:**
- Provide real-time progress updates during OCR processing
- Show which stage is active (loading, segmenting, recognizing, syllabifying)
- Show per-line progress during recognition (the slowest stage)
- Deliver final result through the same stream

**Non-Goals:**
- Cancellation support (not needed per requirements)
- Backward compatibility with non-streaming clients (can be added later if needed)
- Percentage-based progress (stage names sufficient)

## Decisions

### Decision 1: Use Server-Sent Events (SSE)

**Choice**: SSE via FastAPI's `StreamingResponse`

**Alternatives considered**:
- WebSockets: More complex, bidirectional not needed
- Polling with job IDs: Requires job storage, more infrastructure

**Rationale**: SSE is simplest for one-way server-to-client streaming. Native browser support via `EventSource`. FastAPI handles it cleanly with `StreamingResponse`.

### Decision 2: Event schema

**Choice**: JSON events with `stage` field and optional metadata

```json
{"stage": "loading"}
{"stage": "segmenting"}
{"stage": "recognizing", "current": 1, "total": 4}
{"stage": "syllabifying"}
{"stage": "complete", "result": { /* RecognitionResponse */ }}
```

**Rationale**: Simple, extensible. `current`/`total` on recognition gives meaningful progress for the slowest stage.

### Decision 3: Modify existing endpoint vs new endpoint

**Choice**: Modify `/recognize` to always stream SSE

**Alternatives considered**:
- New `/recognize/stream` endpoint: Maintains backward compatibility but duplicates logic

**Rationale**: Simpler to have one endpoint. Client update is planned anyway. If backward compatibility needed later, can add content negotiation via `Accept` header.

### Decision 4: Progress callback pattern

**Choice**: Pass a callback function through the pipeline that emits events

```python
async def recognize(image, region):
    async def emit(stage, **kwargs):
        yield f"data: {json.dumps({'stage': stage, **kwargs})}\n\n"

    # Pipeline calls emit() at each stage
```

**Rationale**: Keeps pipeline functions pure - they call the callback, don't know about SSE. Easy to test.

## Risks / Trade-offs

- **[Breaking change]** → Client must be updated to handle SSE. Mitigation: Plan client update as follow-up.
- **[Slightly more complex response handling]** → SSE parsing vs simple JSON. Mitigation: `EventSource` API handles this natively in browsers.
- **[Error handling in streams]** → Errors mid-stream need careful handling. Mitigation: Emit error event with details, close stream.
