## 1. Types and State

- [x] 1.1 Add `RecognitionMode` type (`'manual' | 'neume' | 'text'`) to `src/state/types.ts`
- [x] 1.2 Add `'detecting'` to `OcrStage` and `OcrProgressEvent` union in `src/state/types.ts`
- [x] 1.3 Extend `AppContext` in `src/state/context.tsx` with `recognitionMode` state and `setRecognitionMode` setter (useState alongside existing reducer, not in history)

## 2. Backend Service

- [x] 2.1 Add optional `type?: 'neume' | 'text'` parameter to `recognizeRegion` in `src/services/htrService.ts` and append it to FormData when provided
- [x] 2.2 Handle `detecting` SSE stage in `parseSSEStream` — forward it as a progress event

## 3. Canvas Drawing Hook

- [x] 3.1 Remove `isShiftHeld` tracking from `useCanvasDrawing` — remove it from `DrawingState`, `handleMouseDown`, `handleMouseUp`, and the `onRectangleDrawn` callback signature

## 4. AnnotationCanvas — Mode-Aware Drawing

- [x] 4.1 Add keyboard handlers for `n` and `t` in the existing `handleKeyDown` effect to toggle `recognitionMode` (guarded by `isInInput`), and extend `Escape` to also clear recognition mode
- [x] 4.2 Add `loadingRegion: Rectangle | null` local state and a `blinkPhase` state driven by `requestAnimationFrame` (active only when `loadingRegion` is set)
- [x] 4.3 Update `handleRectangleDrawn` — when `recognitionMode` is `'neume'` or `'text'`, set `loadingRegion`, call `recognizeRegion` with `type` parameter, clear `loadingRegion` on response/error, and add resulting annotations
- [x] 4.4 Remove Shift+draw OCR path from `handleRectangleDrawn` (and remove `handleOCRRegion` if no longer referenced)
- [x] 4.5 Draw the `loadingRegion` in the canvas draw `useEffect` with pulsing opacity computed from `blinkPhase`

## 5. Toolbar — Mode Chip

- [x] 5.1 Read `recognitionMode` from context in `Toolbar` and render a `Chip` showing `"Neume mode (n)"` or `"Text mode (t)"` when mode is not `'manual'`; hide when manual
