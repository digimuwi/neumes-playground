## Context

The application currently provides syllable suggestions via the Cantus Index API. Users want similar assistance when classifying neume types. An existing prototype (`dudu.py`) demonstrates that neume classification via stroke analysis is feasible: it binarizes images, extracts skeletons, converts strokes to directional tokens, and matches against a lexicon using Needleman-Wunsch alignment.

The client already has sophisticated binarization logic (Otsu threshold with margin detection for scanner beds). The remaining algorithms (skeletonization through classification) are pure computational algorithms that can be ported to TypeScript.

## Goals / Non-Goals

**Goals:**
- Provide automatic neume type suggestions when creating neume annotations
- Port the proven stroke-analysis algorithms from `dudu.py` to TypeScript
- Run entirely client-side with no external services
- Mirror the syllable suggestion UX (ghost text, Tab/Enter to accept)
- Ensure algorithm correctness through careful, methodical porting

**Non-Goals:**
- Using ML/neural networks (the stroke-token approach works well)
- Making the lexicon configurable at runtime
- Optimizing for very large images (neume crops are small)
- Supporting Web Workers (can add later if needed)

## Decisions

### 1. Pure TypeScript implementation
**Decision**: Port all algorithms to TypeScript, run entirely in browser.

**Rationale**:
- No server to run, no Python dependency
- Simpler deployment (static files only)
- No network latency
- Neume crops are small (~100x100 pixels), computation is fast

**Alternatives considered**:
- Python microservice: Adds operational complexity, requires users to run two processes.
- WebAssembly: Overkill for these algorithms, harder to debug.

### 2. Use Uint8Array for binary images
**Decision**: Represent binary images as `Uint8Array` with width/height metadata.

**Rationale**: TypedArrays are fast and memory-efficient. Matches the mental model of numpy arrays. Easy to index with `y * width + x`.

**Alternatives considered**:
- 2D array of arrays: Slower, more memory overhead.
- ImageData directly: Works but carries unused RGBA channels.

### 3. Methodical algorithm porting strategy
**Decision**: Port algorithms one at a time, preserving structure and variable names from Python where possible.

**Rationale**: The Python code is tested and working. Preserving structure makes it easier to verify correctness by comparing implementations side-by-side. Variable names like `neighbours`, `transitions`, `adj` should match.

**Porting order** (by dependency):
1. Zhang-Suen thinning (standalone, foundational)
2. Graph extraction (skeleton → adjacency list)
3. Connected components (uses graph)
4. Gap closing (uses graph + geometry)
5. Longest endpoint path (uses graph)
6. RDP simplification (standalone geometry)
7. Movement sequence extraction (uses simplified path)
8. Tokenization (run-length encoding)
9. Needleman-Wunsch alignment (standalone DP)
10. Classification (combines tokens + lexicon)

### 4. Synchronous classification
**Decision**: Run classification synchronously on the main thread.

**Rationale**: For typical neume regions (~100x100 pixels), Zhang-Suen converges in <50ms. This is imperceptible. If profiling shows issues, we can move to a Web Worker later.

**Alternatives considered**:
- Web Worker: Adds complexity (message passing, worker bundling). Premature optimization.

### 5. Reuse existing binarization
**Decision**: Use the existing `computeOtsuThreshold` and margin detection from `imageProcessing.ts`.

**Rationale**: Already handles scanner bed artifacts correctly. No need to duplicate logic.

## Algorithm Porting Notes

### Zhang-Suen Thinning
The core skeletonization algorithm. Key details to preserve:
- Neighbor ordering: P2-P9 in specific clockwise order
- Two sub-iterations per pass with different conditions
- Convergence check: stop when no pixels change in either sub-iteration

### Gap Closing
Connects broken strokes. Key details:
- Uses endpoint direction estimation (walk 6 steps along skeleton)
- Angle threshold for directional consistency (20°)
- Maximum gap distance (70 pixels)
- Only bridges between different connected components

### Needleman-Wunsch
Global sequence alignment. Key details:
- Custom scoring: direction match (+3), direction mismatch (-3), magnitude mismatch (+1), gap penalty (-2)
- Treats 's' (straight) vs 'u'/'d' as mild mismatch (-1)
- Dot token '0' has its own scoring

## Risks / Trade-offs

**[Algorithm bugs during porting]** → Mitigate by preserving Python structure, adding test cases that compare outputs.

**[Performance on large regions]** → Unlikely issue for typical neumes. Can add Web Worker later if needed.

**[Lexicon coverage]** → Current lexicon has ~24 neume types. Users can always manually select unlisted types.
