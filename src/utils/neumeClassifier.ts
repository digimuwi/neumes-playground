/**
 * Neume Classification Module
 *
 * Classifies neume images using skeletonization and stroke analysis.
 * Ported from dudu.py - preserving algorithm structure and variable names.
 */

// =============================================================================
// TYPES
// =============================================================================

/**
 * Binary image representation.
 * data: Uint8Array where 1 = foreground (ink), 0 = background
 */
export interface BinaryImage {
  data: Uint8Array;
  width: number;
  height: number;
}

/**
 * Point in image coordinates.
 * x = column, y = row (note: y increases downward in image coords)
 */
export interface Point {
  x: number;
  y: number;
}

/**
 * Graph representation of a skeleton.
 * coords: array of (row, col) for each node
 * adj: adjacency list (array of neighbor indices per node)
 */
export interface SkeletonGraph {
  coords: Point[];
  adj: number[][];
}

/**
 * A stroke extracted from the skeleton.
 */
export interface Stroke {
  type: 'stroke' | 'dot';
  points: Point[];
  moves: string[];
}

/**
 * A neume type suggestion with alignment score.
 */
export interface NeumeSuggestion {
  name: string;
  score: number;
}

// =============================================================================
// LEXICON
// =============================================================================

/**
 * Neume type patterns for classification.
 * Each pattern is a sequence of tokens like 'uL' (up-long), 'dS' (down-short), '0' (dot).
 */
export const LEXICON: Record<string, string[]> = {
  'punctum': ['0'],
  'pes': ['dS', 'uL'],
  'pes subbipunctis': ['dS', 'uL', '0', '0'],
  'pes subtripunctis': ['dS', 'uL', '0', '0', '0'],
  'pes praebipunctis': ['0', '0', 'dS', 'uL'],
  'clivis': ['uM', 'dM'],
  'torculus': ['dS', 'uM', 'dS'],
  'virga': ['uL'],
  'bivirga': ['uL', 'uL'],
  'trivirga': ['uL', 'uL', 'uL'],
  'pressus': ['uL', 'dS', 'uS', '0'],
  'climacus': ['uL', '0', '0'],
  'porrectus': ['uS', 'dS', 'uL'],
  'scandicus': ['0', '0', '0', 'uL'],
  'scandicus flexus': ['0', '0', 'uL', 'dL'],
  'scandicus climacus': ['0', '0', '0', 'uL', '0', '0'],
  'clivis episema praebipunctis': ['0', '0', 'uM', 'dM'],
  'stropha': ['uS', 'dL'],
  'bistropha': ['uM', 'dL', 'uM', 'dL'],
  'tristropha': ['uM', 'dL', 'uM', 'dL', 'uM', 'dL'],
  'torculus resupinus': ['dS', 'uM', 'dS', 'uL'],
  'porrectus flexus': ['uS', 'dS', 'uM', 'dM'],
  'uncinus': ['uL', 'dS', 'uS'],
  'bistropha(2)': ['0', '0'],
  'tristropha(2)': ['0', '0', '0'],
  'celeriter': ['dL', 'uS'],
  'salicus': ['uL', 'uM', 'dM', 'uL'],
};

// =============================================================================
// ZHANG-SUEN THINNING (SKELETONIZATION)
// =============================================================================

/**
 * Get pixel value at (row, col) from binary image.
 * Returns 0 for out-of-bounds access.
 */
function getPixel(img: BinaryImage, row: number, col: number): number {
  if (row < 0 || row >= img.height || col < 0 || col >= img.width) {
    return 0;
  }
  return img.data[row * img.width + col];
}

/**
 * Set pixel value at (row, col) in binary image.
 */
function setPixel(img: BinaryImage, row: number, col: number, value: number): void {
  if (row >= 0 && row < img.height && col >= 0 && col < img.width) {
    img.data[row * img.width + col] = value;
  }
}

/**
 * Return 8-neighbours of image point P1(x,y), in order P2..P9.
 * x = row, y = col in the Python code.
 *
 * Neighbor ordering (clockwise from top):
 *   P9 P2 P3
 *   P8 P1 P4
 *   P7 P6 P5
 */
function neighbours(x: number, y: number, img: BinaryImage): number[] {
  return [
    getPixel(img, x - 1, y),     // P2 (top)
    getPixel(img, x - 1, y + 1), // P3 (top-right)
    getPixel(img, x, y + 1),     // P4 (right)
    getPixel(img, x + 1, y + 1), // P5 (bottom-right)
    getPixel(img, x + 1, y),     // P6 (bottom)
    getPixel(img, x + 1, y - 1), // P7 (bottom-left)
    getPixel(img, x, y - 1),     // P8 (left)
    getPixel(img, x - 1, y - 1), // P9 (top-left)
  ];
}

/**
 * Count 0→1 transitions in circular sequence of neighbours.
 */
function transitions(neigh: number[]): number {
  let count = 0;
  for (let i = 0; i < 8; i++) {
    const n1 = neigh[i];
    const n2 = neigh[(i + 1) % 8];
    if (n1 === 0 && n2 === 1) {
      count++;
    }
  }
  return count;
}

/**
 * Skeletonize a binary image using the Zhang–Suen thinning algorithm.
 * Input: BinaryImage with values {0,1}. 1 = foreground.
 * Output: new BinaryImage with skeleton.
 */
export function zhangSuenThinning(image: BinaryImage): BinaryImage {
  // Create a copy
  const img: BinaryImage = {
    data: new Uint8Array(image.data),
    width: image.width,
    height: image.height,
  };

  let changing1: [number, number][] = [];
  let changing2: [number, number][] = [];
  let hasChanges = true;

  while (hasChanges) {
    // Step 1
    changing1 = [];
    for (let x = 1; x < img.height - 1; x++) {
      for (let y = 1; y < img.width - 1; y++) {
        const P1 = getPixel(img, x, y);
        if (P1 !== 1) continue;

        const neigh = neighbours(x, y, img);
        const C = transitions(neigh);
        const N = neigh.reduce((a, b) => a + b, 0);

        if (
          N >= 2 && N <= 6 &&
          C === 1 &&
          neigh[0] * neigh[2] * neigh[4] === 0 &&
          neigh[2] * neigh[4] * neigh[6] === 0
        ) {
          changing1.push([x, y]);
        }
      }
    }
    for (const [x, y] of changing1) {
      setPixel(img, x, y, 0);
    }

    // Step 2
    changing2 = [];
    for (let x = 1; x < img.height - 1; x++) {
      for (let y = 1; y < img.width - 1; y++) {
        const P1 = getPixel(img, x, y);
        if (P1 !== 1) continue;

        const neigh = neighbours(x, y, img);
        const C = transitions(neigh);
        const N = neigh.reduce((a, b) => a + b, 0);

        if (
          N >= 2 && N <= 6 &&
          C === 1 &&
          neigh[0] * neigh[2] * neigh[6] === 0 &&
          neigh[0] * neigh[4] * neigh[6] === 0
        ) {
          changing2.push([x, y]);
        }
      }
    }
    for (const [x, y] of changing2) {
      setPixel(img, x, y, 0);
    }

    hasChanges = changing1.length > 0 || changing2.length > 0;
  }

  return img;
}

// =============================================================================
// GRAPH EXTRACTION
// =============================================================================

/**
 * Build a graph from a skeleton image (1 = foreground).
 * Returns coords (row, col for each node) and adjacency list.
 */
export function skeletonToGraph(skel: BinaryImage): SkeletonGraph {
  const coords: Point[] = [];
  const coordToIdx = new Map<string, number>();

  // Find all foreground pixels
  for (let r = 0; r < skel.height; r++) {
    for (let c = 0; c < skel.width; c++) {
      if (getPixel(skel, r, c) === 1) {
        const idx = coords.length;
        coords.push({ x: c, y: r }); // x=col, y=row
        coordToIdx.set(`${r},${c}`, idx);
      }
    }
  }

  // Build adjacency list
  const adj: number[][] = coords.map(() => []);
  const dirs = [
    [-1, -1], [-1, 0], [-1, 1],
    [0, -1],           [0, 1],
    [1, -1],  [1, 0],  [1, 1],
  ];

  for (let i = 0; i < coords.length; i++) {
    const r = coords[i].y;
    const c = coords[i].x;
    for (const [dr, dc] of dirs) {
      const nr = r + dr;
      const nc = c + dc;
      const j = coordToIdx.get(`${nr},${nc}`);
      if (j !== undefined) {
        adj[i].push(j);
      }
    }
  }

  return { coords, adj };
}

/**
 * Find connected components in the skeleton graph.
 * Returns a list of components, each a list of node indices.
 */
export function connectedComponents(adj: number[][]): number[][] {
  const n = adj.length;
  const visited = new Array(n).fill(false);
  const components: number[][] = [];

  for (let i = 0; i < n; i++) {
    if (visited[i]) continue;

    const stack = [i];
    visited[i] = true;
    const comp: number[] = [];

    while (stack.length > 0) {
      const v = stack.pop()!;
      comp.push(v);
      for (const nb of adj[v]) {
        if (!visited[nb]) {
          visited[nb] = true;
          stack.push(nb);
        }
      }
    }
    components.push(comp);
  }

  return components;
}

// =============================================================================
// GAP CLOSING
// =============================================================================

/**
 * Yield pixels on a Bresenham line from (r0,c0) to (r1,c1).
 */
function* bresenhamLine(r0: number, c0: number, r1: number, c1: number): Generator<[number, number]> {
  let dr = Math.abs(r1 - r0);
  let dc = Math.abs(c1 - c0);
  const sr = r0 < r1 ? 1 : -1;
  const sc = c0 < c1 ? 1 : -1;

  if (dc > dr) {
    let err = Math.floor(dc / 2);
    while (c0 !== c1) {
      yield [r0, c0];
      err -= dr;
      if (err < 0) {
        r0 += sr;
        err += dc;
      }
      c0 += sc;
    }
    yield [r0, c0];
  } else {
    let err = Math.floor(dr / 2);
    while (r0 !== r1) {
      yield [r0, c0];
      err -= dc;
      if (err < 0) {
        c0 += sc;
        err += dr;
      }
      r0 += sr;
    }
    yield [r0, c0];
  }
}

/**
 * Estimate local stroke direction at an endpoint by walking forward
 * up to maxSteps along the skeleton.
 * Returns a normalized 2D vector [dy, dx] or null.
 */
function endpointDirection(
  idx: number,
  adj: number[][],
  coords: Point[],
  maxSteps: number = 6
): [number, number] | null {
  let current = idx;
  let prev: number | null = null;
  let steps = 0;
  const startR = coords[idx].y;
  const startC = coords[idx].x;
  let lastR = startR;
  let lastC = startC;

  while (steps < maxSteps) {
    const neighbors = adj[current].filter(n => n !== prev);

    if (neighbors.length === 0) break;
    if (neighbors.length > 1) break; // hit a junction

    const nxt = neighbors[0];
    lastR = coords[nxt].y;
    lastC = coords[nxt].x;

    prev = current;
    current = nxt;
    steps++;
  }

  const dy = lastR - startR;
  const dx = lastC - startC;
  const norm = Math.hypot(dy, dx);
  if (norm === 0) return null;

  return [dy / norm, dx / norm];
}

/**
 * Compute angle between vectors, treating opposite directions as aligned.
 * Returns angle in degrees (0 to 90).
 */
function collinearAngle(v1: [number, number], v2: [number, number]): number {
  const dot = v1[0] * v2[0] + v1[1] * v2[1];
  const n1 = Math.hypot(v1[0], v1[1]);
  const n2 = Math.hypot(v2[0], v2[1]);

  if (n1 === 0 || n2 === 0) return 180.0;

  let cosA = dot / (n1 * n2);
  cosA = Math.max(-1.0, Math.min(1.0, cosA));
  // abs() makes 0° and 180° both map to cos = 1
  cosA = Math.abs(cosA);

  return (Math.acos(cosA) * 180) / Math.PI;
}

/**
 * Attempt to connect broken strokes on a skeleton image.
 * Joins endpoints that are:
 *   - within maxGap pixels
 *   - in different components
 *   - directionally consistent (angle < angleThreshDeg)
 */
export function closeSkeletonGaps(
  skel: BinaryImage,
  maxGap: number = 70.0,
  angleThreshDeg: number = 20.0
): BinaryImage {
  // Create a copy
  const result: BinaryImage = {
    data: new Uint8Array(skel.data),
    width: skel.width,
    height: skel.height,
  };

  const { coords, adj } = skeletonToGraph(result);
  if (coords.length === 0) return result;

  // Connected components
  const components = connectedComponents(adj);
  const nodeToComp = new Map<number, number>();
  for (let cid = 0; cid < components.length; cid++) {
    for (const idx of components[cid]) {
      nodeToComp.set(idx, cid);
    }
  }

  // Find endpoints (degree 1)
  const endpoints = adj
    .map((nbs, i) => ({ i, deg: nbs.length }))
    .filter(({ deg }) => deg === 1)
    .map(({ i }) => i);

  if (endpoints.length < 2) return result;

  // Precompute endpoint directions
  const endpointDirs = new Map<number, [number, number] | null>();
  for (const i of endpoints) {
    endpointDirs.set(i, endpointDirection(i, adj, coords));
  }

  const usedEndpoints = new Set<number>();
  const H = result.height;
  const W = result.width;

  // Try bridging endpoint pairs
  for (let iIdx = 0; iIdx < endpoints.length; iIdx++) {
    const i = endpoints[iIdx];
    if (usedEndpoints.has(i)) continue;

    const ci = nodeToComp.get(i) ?? -1;
    const ri = coords[i].y;
    const ciPix = coords[i].x;

    for (let jIdx = iIdx + 1; jIdx < endpoints.length; jIdx++) {
      const j = endpoints[jIdx];
      if (usedEndpoints.has(j)) continue;

      const cj = nodeToComp.get(j) ?? -1;

      // Only bridge between different components
      if (ci === cj) continue;

      const rj = coords[j].y;
      const cjPix = coords[j].x;

      // Distance check
      const dr = ri - rj;
      const dc = ciPix - cjPix;
      const dist = Math.hypot(dr, dc);
      if (dist > maxGap) continue;

      // Join direction (from i to j)
      const joinNorm = dist + 1e-9;
      const joinDir: [number, number] = [(rj - ri) / joinNorm, (cjPix - ciPix) / joinNorm];

      const di = endpointDirs.get(i);
      const dj = endpointDirs.get(j);
      if (di === null || dj === null || di === undefined || dj === undefined) continue;

      // Direction consistency
      const ai = collinearAngle(di, joinDir);
      const aj = collinearAngle(dj, [-joinDir[0], -joinDir[1]]);

      if (ai > angleThreshDeg || aj > angleThreshDeg) continue;

      // Draw line between endpoints
      for (const [r, c] of bresenhamLine(ri, ciPix, rj, cjPix)) {
        if (r >= 0 && r < H && c >= 0 && c < W) {
          setPixel(result, r, c, 1);
        }
      }

      usedEndpoints.add(i);
      usedEndpoints.add(j);
    }
  }

  return result;
}

// =============================================================================
// STROKE EXTRACTION
// =============================================================================

/**
 * Check if any pixel in component lies on the image border.
 */
function componentTouchesBorder(
  compNodes: number[],
  coords: Point[],
  h: number,
  w: number,
  margin: number = 0
): boolean {
  const top = margin;
  const left = margin;
  const bottom = h - 1 - margin;
  const right = w - 1 - margin;

  for (const idx of compNodes) {
    const r = coords[idx].y;
    const c = coords[idx].x;
    if (r <= top || r >= bottom || c <= left || c >= right) {
      return true;
    }
  }
  return false;
}

/**
 * BFS shortest path between start and goal.
 * allowed: optional set of node indices we can visit.
 */
function shortestPath(
  start: number,
  goal: number,
  adj: number[][],
  allowed?: Set<number>
): number[] | null {
  const allowedSet = allowed ?? new Set(adj.map((_, i) => i));

  const queue: number[] = [start];
  const prev = new Map<number, number | null>();
  prev.set(start, null);

  while (queue.length > 0) {
    const v = queue.shift()!;
    if (v === goal) break;

    for (const nb of adj[v]) {
      if (!allowedSet.has(nb)) continue;
      if (!prev.has(nb)) {
        prev.set(nb, v);
        queue.push(nb);
      }
    }
  }

  if (!prev.has(goal)) return null;

  const path: number[] = [];
  let cur: number | null = goal;
  while (cur !== null) {
    path.push(cur);
    cur = prev.get(cur) ?? null;
  }
  return path.reverse();
}

/**
 * Find the longest shortest path between any two endpoints (degree 1)
 * in the given subset of nodes. Used as the main stroke.
 */
function longestEndpointPath(
  _coords: Point[],
  adj: number[][],
  nodesSubset?: Iterable<number>
): number[] {
  const subset = new Set(nodesSubset ?? adj.map((_, i) => i));

  // Find endpoints within subset
  const endpoints = [...subset].filter(i => adj[i].length === 1);

  // If fewer than 2 endpoints, do a simple walk
  if (endpoints.length < 2) {
    if (subset.size === 0) return [];

    const start = Math.min(...subset);
    const path = [start];
    const visited = new Set([start]);
    let current = start;
    let prev: number | null = null;

    while (true) {
      const neighbors = adj[current].filter(
        nb => subset.has(nb) && nb !== prev && !visited.has(nb)
      );
      if (neighbors.length === 0) break;
      const nxt = neighbors[0];
      path.push(nxt);
      visited.add(nxt);
      prev = current;
      current = nxt;
    }
    return path;
  }

  let bestPath: number[] = [];
  let bestLen = -1;

  for (let i = 0; i < endpoints.length; i++) {
    for (let j = i + 1; j < endpoints.length; j++) {
      const s = endpoints[i];
      const g = endpoints[j];
      const path = shortestPath(s, g, adj, subset);
      if (path !== null && path.length > bestLen) {
        bestLen = path.length;
        bestPath = path;
      }
    }
  }

  return bestPath;
}

/**
 * Compute Euclidean length of a polyline.
 */
export function pathLength(points: Point[]): number {
  let length = 0.0;
  for (let i = 1; i < points.length; i++) {
    const dx = points[i].x - points[i - 1].x;
    const dy = points[i].y - points[i - 1].y;
    length += Math.hypot(dx, dy);
  }
  return length;
}

// =============================================================================
// PATH SIMPLIFICATION (RDP)
// =============================================================================

/**
 * Ramer–Douglas–Peucker simplification.
 */
export function rdp(points: Point[], epsilon: number): Point[] {
  if (points.length < 3) return points;

  const first = points[0];
  const last = points[points.length - 1];

  // Perpendicular distance from point to line (first, last)
  function perpDist(p: Point): number {
    const num = Math.abs(
      (last.y - first.y) * p.x -
      (last.x - first.x) * p.y +
      last.x * first.y -
      last.y * first.x
    );
    const den = Math.hypot(last.y - first.y, last.x - first.x);
    return den !== 0 ? num / den : 0.0;
  }

  let dmax = 0.0;
  let index = 0;

  for (let i = 1; i < points.length - 1; i++) {
    const d = perpDist(points[i]);
    if (d > dmax) {
      dmax = d;
      index = i;
    }
  }

  if (dmax > epsilon) {
    const left = rdp(points.slice(0, index + 1), epsilon);
    const right = rdp(points.slice(index), epsilon);
    return [...left.slice(0, -1), ...right];
  } else {
    return [first, last];
  }
}

// =============================================================================
// MOVEMENT SEQUENCE
// =============================================================================

/**
 * Determine how many segments to use based on stroke length.
 */
function chooseNumSegments(
  points: Point[],
  pixelsPerSegment: number = 10.0,
  minSegments: number = 4,
  maxSegments: number = 20
): number {
  const L = pathLength(points);
  let n = Math.round(L / pixelsPerSegment);
  n = Math.max(minSegments, Math.min(maxSegments, n));
  return Math.max(2, n);
}

/**
 * Resample path at equal arc-length intervals.
 */
function resampleByLength(points: Point[], numSamples: number): Point[] {
  if (points.length < 2) return points;

  // Compute cumulative distances
  const d = [0.0];
  for (let i = 1; i < points.length; i++) {
    const dx = points[i].x - points[i - 1].x;
    const dy = points[i].y - points[i - 1].y;
    d.push(d[d.length - 1] + Math.hypot(dx, dy));
  }
  const total = d[d.length - 1];
  if (total === 0) return points;

  const samples: Point[] = [];
  let j = 0;

  for (let s = 0; s < numSamples; s++) {
    const td = (s / (numSamples - 1)) * total;

    while (j < d.length - 2 && d[j + 1] < td) {
      j++;
    }

    const t = (td - d[j]) / (d[j + 1] - d[j] + 1e-9);
    const x = points[j].x + t * (points[j + 1].x - points[j].x);
    const y = points[j].y + t * (points[j + 1].y - points[j].y);
    samples.push({ x, y });
  }

  return samples;
}

/**
 * Compute vertical movement sequence for a stroke.
 * Returns array of 'u' (up), 'd' (down), 's' (straight).
 */
function verticalMovementSequenceAuto(
  points: Point[],
  pixelsPerSegment: number = 10.0,
  straightTol: number = 3.0,
  minSegments: number = 4,
  maxSegments: number = 20
): string[] {
  if (points.length < 2) return [];

  // Ensure left → right
  let pts = points;
  if (pts[0].x > pts[pts.length - 1].x) {
    pts = [...pts].reverse();
  }

  const numSegments = chooseNumSegments(pts, pixelsPerSegment, minSegments, maxSegments);
  const samples = resampleByLength(pts, numSegments + 1);

  const moves: string[] = [];
  for (let i = 0; i < numSegments; i++) {
    const y1 = samples[i].y;
    const y2 = samples[i + 1].y;
    const dy = y2 - y1; // image coords: down is positive

    if (Math.abs(dy) <= straightTol) {
      moves.push('s');
    } else if (dy < 0) {
      moves.push('u');
    } else {
      moves.push('d');
    }
  }

  return moves;
}

// =============================================================================
// TOKENIZATION
// =============================================================================

/**
 * Group consecutive same-direction moves into runs.
 */
function movesToRuns(moves: string[]): [string, number][] {
  if (moves.length === 0) return [];

  const runs: [string, number][] = [];
  let currentDir = moves[0];
  let length = 1;

  for (let i = 1; i < moves.length; i++) {
    if (moves[i] === currentDir) {
      length++;
    } else {
      runs.push([currentDir, length]);
      currentDir = moves[i];
      length = 1;
    }
  }
  runs.push([currentDir, length]);

  return runs;
}

/**
 * Normalize run lengths to fractions of total.
 */
function normalizeRunLengths(runs: [string, number][]): [string, number][] {
  const total = runs.reduce((sum, [, len]) => sum + len, 0);
  if (total === 0) return runs.map(([d]) => [d, 0.0]);
  return runs.map(([d, len]) => [d, len / total]);
}

/**
 * Map normalized length fraction to bucket: S, M, or L.
 */
function bucketLength(frac: number): string {
  if (frac < 0.25) return 'S';
  if (frac < 0.5) return 'M';
  return 'L';
}

/**
 * Convert runs to tokens like 'uL', 'dS'.
 * Filters out straight ('s') segments.
 */
function runsToTokens(runs: [string, number][]): string[] {
  const norm = normalizeRunLengths(runs);
  const tokens: string[] = [];

  for (const [d, frac] of norm) {
    if (d === 's') continue; // skip straight segments
    const bucket = bucketLength(frac);
    tokens.push(d + bucket);
  }

  return tokens;
}

/**
 * Get x position of stroke (minimum x).
 */
function strokeXPosition(stroke: Stroke): number {
  if (stroke.points.length === 0) return Infinity;
  return Math.min(...stroke.points.map(p => p.x));
}

/**
 * Convert a stroke to tokens.
 */
function strokeToTokens(stroke: Stroke): string[] {
  if (stroke.type === 'dot') {
    return ['0'];
  }
  const runs = movesToRuns(stroke.moves);
  return runsToTokens(runs);
}

/**
 * Convert all strokes to symbol tokens, ordered left-to-right.
 */
function strokesToSymbolTokens(strokes: Stroke[]): string[] {
  const sorted = [...strokes].sort((a, b) => strokeXPosition(a) - strokeXPosition(b));
  const tokens: string[] = [];
  for (const s of sorted) {
    tokens.push(...strokeToTokens(s));
  }
  return tokens;
}

// =============================================================================
// NEEDLEMAN-WUNSCH ALIGNMENT
// =============================================================================

/**
 * Scoring function for token pairs.
 */
function tokenMatchScore(a: string, b: string): number {
  // Dots
  if (a === '0' || b === '0') {
    return a === b ? 2 : -1;
  }

  const dirA = a[0];
  const magA = a[1];
  const dirB = b[0];
  const magB = b[1];

  // Same direction
  if (dirA === dirB) {
    return magA === magB ? 3 : 1; // perfect match vs different magnitude
  }

  // One is straight
  if (dirA === 's' || dirB === 's') {
    return -1; // mild penalty
  }

  // Opposite directions (u vs d)
  return -3;
}

/**
 * Global alignment using Needleman-Wunsch algorithm.
 */
function needlemanWunschTokens(seq1: string[], seq2: string[], gap: number = -2): number {
  const n = seq1.length;
  const m = seq2.length;

  // Initialize DP table
  const dp: number[][] = [];
  for (let i = 0; i <= n; i++) {
    dp.push(new Array(m + 1).fill(0));
  }

  // Base cases
  for (let i = 1; i <= n; i++) {
    dp[i][0] = dp[i - 1][0] + gap;
  }
  for (let j = 1; j <= m; j++) {
    dp[0][j] = dp[0][j - 1] + gap;
  }

  // Fill table
  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      const scoreDiag = dp[i - 1][j - 1] + tokenMatchScore(seq1[i - 1], seq2[j - 1]);
      const scoreUp = dp[i - 1][j] + gap;
      const scoreLeft = dp[i][j - 1] + gap;
      dp[i][j] = Math.max(scoreDiag, scoreUp, scoreLeft);
    }
  }

  return dp[n][m];
}

// =============================================================================
// CLASSIFICATION
// =============================================================================

/**
 * Match tokens against lexicon, return top-n matches.
 */
function classifyNeumeTokens(
  tokens: string[],
  lexicon: Record<string, string[]> = LEXICON,
  n: number = 5
): NeumeSuggestion[] {
  const scores: [string, number][] = [];

  for (const [name, pattern] of Object.entries(lexicon)) {
    const score = needlemanWunschTokens(tokens, pattern);
    scores.push([name, score]);
  }

  // Sort by score descending
  scores.sort((a, b) => b[1] - a[1]);

  // Return top n
  return scores.slice(0, n).map(([name, score]) => ({ name, score }));
}

// =============================================================================
// MAIN PIPELINE
// =============================================================================

const DOT_THRESHOLD = 40.0;
const EDGE_IGNORE_THRESHOLD = 50.0;
const RDP_EPSILON = 2.0;

/**
 * Process a binary image and extract strokes.
 */
function processImage(binaryImage: BinaryImage): Stroke[] {
  // 1) Skeletonize
  let skel = zhangSuenThinning(binaryImage);

  // 2) Close gaps
  skel = closeSkeletonGaps(skel, 70.0, 20.0);

  // 3) Build graph and find components
  const { coords, adj } = skeletonToGraph(skel);
  const components = connectedComponents(adj);

  const strokes: Stroke[] = [];
  const h = skel.height;
  const w = skel.width;

  for (const compNodes of components) {
    if (compNodes.length === 0) continue;

    // Skip small border-touching components
    if (componentTouchesBorder(compNodes, coords, h, w, 0)) {
      // Approximate length as bbox diagonal
      const rs = compNodes.map(i => coords[i].y);
      const cs = compNodes.map(i => coords[i].x);
      const bboxH = Math.max(...rs) - Math.min(...rs) + 1;
      const bboxW = Math.max(...cs) - Math.min(...cs) + 1;
      const approxLen = Math.hypot(bboxH, bboxW);

      if (approxLen < EDGE_IGNORE_THRESHOLD) {
        continue;
      }
    }

    // Extract main path (removes branches)
    const mainIndices = longestEndpointPath(coords, adj, compNodes);
    if (mainIndices.length === 0) continue;

    // Convert to points (x=col, y=row)
    const mainPoints: Point[] = mainIndices.map(i => ({
      x: coords[i].x,
      y: coords[i].y,
    }));

    const strokeLen = pathLength(mainPoints);

    // Classify as dot if short
    if (strokeLen < DOT_THRESHOLD) {
      strokes.push({
        type: 'dot',
        points: mainPoints,
        moves: [],
      });
      continue;
    }

    // Simplify path
    const simplifiedPoints = rdp(mainPoints, RDP_EPSILON);

    // Compute movement sequence
    const movementSequence = verticalMovementSequenceAuto(simplifiedPoints);

    strokes.push({
      type: 'stroke',
      points: simplifiedPoints,
      moves: movementSequence,
    });
  }

  return strokes;
}

/**
 * Main entry point: classify a binary image and return neume suggestions.
 */
export function classifyNeume(binaryImage: BinaryImage): NeumeSuggestion[] {
  // Check for empty image
  let hasForeground = false;
  for (let i = 0; i < binaryImage.data.length; i++) {
    if (binaryImage.data[i] === 1) {
      hasForeground = true;
      break;
    }
  }
  if (!hasForeground) {
    return [];
  }

  // Process image to extract strokes
  const strokes = processImage(binaryImage);
  if (strokes.length === 0) {
    return [];
  }

  // Convert strokes to tokens
  const tokens = strokesToSymbolTokens(strokes);
  if (tokens.length === 0) {
    return [];
  }

  // Classify
  return classifyNeumeTokens(tokens);
}
