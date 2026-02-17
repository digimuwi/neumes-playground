## Context

The HTR backend now streams progress via SSE instead of returning a single JSON response. The frontend's `htrService.ts` still uses `response.json()`, ignoring the stream. The `OcrDialog` shows a static "Recognizing text..." message with an indeterminate spinner.

Current data flow:
```
User action → htrService.recognize*() → await response.json() → dispatch annotations
```

Target data flow:
```
User action → htrService.recognize*() → SSE stream → progress callbacks → final result
                                              ↓
                                     dispatch(setOcrDialog({ stage, current, total }))
```

## Goals / Non-Goals

**Goals:**
- Consume SSE stream from backend `/recognize` endpoint
- Display stage-specific messages in OcrDialog (loading, segmenting, recognizing, syllabifying)
- Show determinate progress bar during recognition phase (line X of Y)
- Share SSE parsing logic between `recognizeRegion` and `recognizePage`
- Handle stream errors gracefully

**Non-Goals:**
- Cancellation support (backend doesn't support it yet)
- Progress for Shift+drag vs full-page differentiation (same UI for both)
- Caching or retry logic

## Decisions

### 1. SSE parsing via fetch + ReadableStream (not EventSource)

**Decision**: Parse SSE manually from fetch response stream.

**Rationale**: `EventSource` only supports GET requests. The `/recognize` endpoint uses POST with FormData. Using fetch with `response.body.getReader()` allows POST while still consuming the SSE stream.

**Alternatives considered**:
- EventSource: Doesn't support POST
- Axios: Would need additional streaming setup, fetch is sufficient

### 2. Callback-based progress reporting

**Decision**: Add `onProgress?: (event: OcrProgressEvent) => void` parameter to recognize functions.

**Rationale**: Clean separation - service handles parsing, caller handles state updates. The callback receives typed progress events that map directly to dialog state.

**Type definition**:
```typescript
type OcrProgressEvent =
  | { stage: 'loading' }
  | { stage: 'segmenting' }
  | { stage: 'recognizing'; current: number; total: number }
  | { stage: 'syllabifying' }
  | { stage: 'error'; message: string }
```

### 3. Extend OcrDialogState discriminated union

**Decision**: Add progress fields to the `loading` mode variant.

```typescript
type OcrDialogState =
  | { mode: 'closed' }
  | { mode: 'uploadPrompt' }
  | { mode: 'existingAnnotationsPrompt' }
  | { mode: 'loading'; stage: OcrStage; current?: number; total?: number }

type OcrStage = 'loading' | 'segmenting' | 'recognizing' | 'syllabifying'
```

**Rationale**: Minimal change to existing type structure. The `loading` mode already exists; we're just enriching it with progress data.

### 4. UI presentation

**Decision**:
- Indeterminate spinner for loading, segmenting, syllabifying stages
- Determinate progress bar with "Line X of Y" during recognizing stage
- Stage-specific messages: "Loading model...", "Detecting text regions...", "Recognizing text...", "Processing syllables..."

**Rationale**: Users get meaningful feedback during the longest phase (recognition) while other phases use simple spinners since they're typically fast.

## Risks / Trade-offs

**[Stream parsing complexity]** → Mitigated by keeping parser simple and handling incomplete chunks. SSE format is line-based (`data: {...}\n\n`), straightforward to parse.

**[Error mid-stream]** → Backend sends `{ stage: "error", message: "..." }` event. Frontend will display error in dialog and close gracefully.

**[Progress callbacks on every line]** → Could cause many re-renders for large documents. Mitigated by React's batching; dialog updates are lightweight.
