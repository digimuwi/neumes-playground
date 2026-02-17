## 1. Core Types and Data Structures

- [x] 1.1 Define `BinaryImage` type: `{ data: Uint8Array, width: number, height: number }` where 1=foreground, 0=background
- [x] 1.2 Define `Point` type: `{ x: number, y: number }` (note: x=col, y=row in image coords)
- [x] 1.3 Define `SkeletonGraph` type: `{ coords: Point[], adj: number[][] }` (coords per node, adjacency list)
- [x] 1.4 Define `Stroke` type: `{ type: 'stroke' | 'dot', points: Point[], moves: string[] }`
- [x] 1.5 Define `NeumeSuggestion` type: `{ name: string, score: number }`
- [x] 1.6 Add `LEXICON` constant mapping neume names to token patterns (copy from dudu.py)

## 2. Zhang-Suen Thinning (Skeletonization)

- [x] 2.1 Port `neighbours(x, y, image)` - returns 8 neighbors P2-P9 in clockwise order
- [x] 2.2 Port `transitions(neigh)` - counts 0→1 transitions in circular neighbor sequence
- [x] 2.3 Port `zhangSuenThinning(image)` - main thinning loop with two sub-iterations
- [x] 2.4 Verify: thinning preserves connectivity (no isolated pixels created)
- [x] 2.5 Verify: output is 1-pixel wide skeleton

## 3. Graph Extraction

- [x] 3.1 Port `skeletonToGraph(skel)` - converts skeleton to coords + adjacency list
- [x] 3.2 Port `connectedComponents(adj)` - finds connected components via DFS/BFS
- [x] 3.3 Verify: number of components matches visible separate strokes

## 4. Gap Closing

- [x] 4.1 Port `bresenhamLine(r0, c0, r1, c1)` - yields pixels on line between two points
- [x] 4.2 Port `endpointDirection(idx, adj, coords)` - estimates stroke direction at endpoint by walking 6 steps
- [x] 4.3 Port `collinearAngle(v1, v2)` - computes angle between vectors (treating opposite as aligned)
- [x] 4.4 Port `closeSkeletonGaps(skel, maxGap=70, angleThresh=20)` - main gap closing logic
- [x] 4.5 Verify: gaps are only closed between different components
- [x] 4.6 Verify: directionally misaligned endpoints are not connected

## 5. Stroke Extraction

- [x] 5.1 Port `componentTouchesBorder(nodes, coords, h, w, margin=0)` - checks if component touches edge
- [x] 5.2 Port `shortestPath(start, goal, adj, allowed)` - BFS shortest path
- [x] 5.3 Port `longestEndpointPath(coords, adj, nodesSubset)` - finds main stroke path
- [x] 5.4 Port `pathLength(points)` - computes Euclidean length of polyline
- [x] 5.5 Add logic to filter small border-touching components (<50px)
- [x] 5.6 Add logic to classify short strokes (<40px) as dots
- [x] 5.7 Verify: branches are removed, only main path remains

## 6. Path Simplification

- [x] 6.1 Port `rdp(points, epsilon)` - Ramer-Douglas-Peucker simplification
- [x] 6.2 Verify: simplified path has fewer points while preserving shape

## 7. Movement Sequence

- [x] 7.1 Port `chooseNumSegments(points, pixelsPerSegment=10)` - determines sampling density
- [x] 7.2 Port `resampleByLength(points, numSamples)` - resamples path at equal arc-length intervals
- [x] 7.3 Port `verticalMovementSequenceAuto(points)` - classifies segments as u/d/s
- [x] 7.4 Verify: ascending strokes produce 'u', descending produce 'd'

## 8. Tokenization

- [x] 8.1 Port `movesToRuns(moves)` - groups consecutive same-direction moves
- [x] 8.2 Port `normalizeRunLengths(runs)` - converts to fractions
- [x] 8.3 Port `bucketLength(frac)` - maps fraction to S/M/L
- [x] 8.4 Port `runsToTokens(runs)` - combines direction + bucket, filters 's'
- [x] 8.5 Port `strokeToTokens(stroke)` - handles dots vs strokes
- [x] 8.6 Port `strokesToSymbolTokens(strokes)` - orders strokes left-to-right, combines tokens
- [x] 8.7 Verify: known neume shapes produce expected token sequences

## 9. Needleman-Wunsch Alignment

- [x] 9.1 Port `tokenMatchScore(a, b)` - scoring function for token pairs
- [x] 9.2 Port `needlemanWunschTokens(seq1, seq2, gap=-2)` - DP alignment
- [x] 9.3 Verify: identical sequences score highest
- [x] 9.4 Verify: similar sequences (one magnitude off) score positively

## 10. Classification Pipeline

- [x] 10.1 Port `classifyNeumeTokens(tokens, lexicon, n=5)` - matches against lexicon, returns top-n
- [x] 10.2 Create main `classifyNeume(binaryImage): NeumeSuggestion[]` entry point that runs full pipeline
- [x] 10.3 Handle empty images (return empty array)
- [x] 10.4 Verify: punctum image → "punctum" suggestion
- [x] 10.5 Verify: pes image → "pes" suggestion

## 11. Image Cropping and Binarization

- [x] 11.1 Create `cropRegion(imageData, rect, width, height)` - crops normalized rect to pixel region
- [x] 11.2 Create `binarizeRegion(imageData, rect, otsuThreshold, marginThreshold)` - returns BinaryImage
- [x] 11.3 Verify: ink becomes foreground (1), parchment becomes background (0)

## 12. Suggestion Hook

- [x] 12.1 Create `useNeumeSuggestion` hook following `useSuggestion` pattern
- [x] 12.2 Trigger only for newly created neume annotations
- [x] 12.3 Call crop → binarize → classify pipeline
- [x] 12.4 Handle stale results (discard if annotation changed)
- [x] 12.5 Return top suggestion name or null

## 13. UI Integration

- [x] 13.1 Add `neumeSuggestion` prop to `InlineAnnotationEditor`
- [x] 13.2 Show suggestion as placeholder text in neume Autocomplete
- [x] 13.3 Add Tab/Enter handling to accept suggestion before user types
- [x] 13.4 Show "Tab/Enter to accept" helper text when suggestion displayed
- [x] 13.5 Wire up `useNeumeSuggestion` hook in `AnnotationCanvas`
