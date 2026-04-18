import { v4 as uuidv4 } from 'uuid';
import { Annotation, Rectangle, LineBoundary, OcrProgressEvent } from '../state/types';
import { computeTextLines } from '../hooks/useTextLines';
import { normalizePolygon, denormalizePolygon, rectToPolygon, polygonBounds } from '../utils/polygonUtils';
import { apiFetch } from './apiFetch';

const HTR_BASE_URL = import.meta.env.VITE_HTR_BASE_URL
  || (import.meta.env.DEV ? '/api' : '');

// --- Backend response types (new nested format) ---

interface BBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface SyllableResult {
  text: string;
  boundary: number[][];
  confidence: number;
}

interface LineResult {
  text: string;
  boundary: number[][];
  baseline: number[][];
  syllables: SyllableResult[];
}

interface NeumeResult {
  type: string;
  bbox: BBox;
  confidence: number;
}

interface RecognitionResponse {
  lines: LineResult[];
  neumes: NeumeResult[];
}

interface ImageDimensions {
  width: number;
  height: number;
}

interface SSEEvent {
  stage: string;
  current?: number;
  total?: number;
  message?: string;
  result?: RecognitionResponse;
}

export interface RecognitionResult {
  annotations: Annotation[];
  lineBoundaries: LineBoundary[];
}

/**
 * Convert a normalized Rectangle to a pixel BBox for the backend region parameter.
 */
function normalizedRectToPixelBBox(rect: Rectangle, dimensions: ImageDimensions): BBox {
  return {
    x: Math.round(rect.x * dimensions.width),
    y: Math.round(rect.y * dimensions.height),
    width: Math.max(1, Math.round(rect.width * dimensions.width)),
    height: Math.max(1, Math.round(rect.height * dimensions.height)),
  };
}

/**
 * Parse SSE stream from fetch response and invoke callbacks for each event.
 * Returns the final recognition result.
 */
async function parseSSEStream(
  response: Response,
  onProgress?: (event: OcrProgressEvent) => void
): Promise<RecognitionResponse> {
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let result: RecognitionResponse | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE events (separated by double newlines)
    const events = buffer.split('\n\n');
    buffer = events.pop() || ''; // Keep incomplete event in buffer

    for (const eventText of events) {
      const dataMatch = eventText.match(/^data:\s*(.+)$/m);
      if (!dataMatch) continue;

      let event: SSEEvent;
      try {
        event = JSON.parse(dataMatch[1]);
      } catch {
        // Ignore malformed JSON in SSE events
        continue;
      }

      if (event.stage === 'complete' && event.result) {
        result = event.result;
      } else if (event.stage === 'error') {
        throw new Error(event.message || 'Unknown error during OCR');
      } else if (onProgress) {
        if (event.stage === 'recognizing' && event.current !== undefined && event.total !== undefined) {
          onProgress({ stage: 'recognizing', current: event.current, total: event.total });
        } else if (event.stage === 'loading' || event.stage === 'segmenting' || event.stage === 'syllabifying' || event.stage === 'detecting') {
          onProgress({ stage: event.stage });
        }
      }
    }
  }

  if (!result) {
    throw new Error('Stream ended without complete event');
  }

  return result;
}

/**
 * Call the HTR backend to recognize syllables in a region.
 * Returns annotations and line boundaries ready to be added to state.
 */
export async function recognizeRegion(
  imageBlob: Blob,
  region: Rectangle,
  imageDimensions: ImageDimensions,
  onProgress?: (event: OcrProgressEvent) => void,
  type?: 'neume' | 'text'
): Promise<RecognitionResult> {
  const pixelRegion = normalizedRectToPixelBBox(region, imageDimensions);

  const formData = new FormData();
  formData.append('image', imageBlob, 'image.jpg');
  formData.append('region', JSON.stringify(pixelRegion));
  if (type) {
    formData.append('type', type);
  }

  const response = await apiFetch(`${HTR_BASE_URL}/recognize`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTR service error: ${response.status} ${response.statusText}`);
  }

  const data = await parseSSEStream(response, onProgress);

  return responseToAnnotations(data, imageDimensions);
}

/**
 * Call the HTR backend to recognize syllables and neumes across the entire page.
 * Returns annotations and line boundaries ready to be added to state.
 */
export async function recognizePage(
  imageBlob: Blob,
  imageDimensions: ImageDimensions,
  onProgress?: (event: OcrProgressEvent) => void
): Promise<RecognitionResult> {
  const formData = new FormData();
  formData.append('image', imageBlob, 'image.jpg');

  const response = await apiFetch(`${HTR_BASE_URL}/recognize`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTR service error: ${response.status} ${response.statusText}`);
  }

  const data = await parseSSEStream(response, onProgress);

  return responseToAnnotations(data, imageDimensions);
}

/**
 * Convert a RecognitionResponse (pixels) into annotations with polygons and line boundaries.
 */
export function responseToAnnotations(data: RecognitionResponse, imageDimensions: ImageDimensions): RecognitionResult {
  const annotations: Annotation[] = [];
  const lineBoundaries: LineBoundary[] = [];

  for (const line of data.lines) {
    const syllableIds: string[] = [];

    for (const syllable of line.syllables) {
      const id = uuidv4();
      syllableIds.push(id);
      annotations.push({
        id,
        type: 'syllable' as const,
        polygon: normalizePolygon(syllable.boundary, imageDimensions),
        text: syllable.text,
      });
    }

    // Compute per-line confidence as average of syllable confidences
    const syllableConfidences = line.syllables
      .map(s => s.confidence)
      .filter(c => c !== undefined && c !== null);
    const lineConfidence = syllableConfidences.length > 0
      ? syllableConfidences.reduce((sum, c) => sum + c, 0) / syllableConfidences.length
      : undefined;

    lineBoundaries.push({
      boundary: normalizePolygon(line.boundary, imageDimensions),
      syllableIds,
      confidence: lineConfidence,
    });
  }

  for (const neume of data.neumes) {
    const bboxPolygon = rectToPolygon(neume.bbox);
    annotations.push({
      id: uuidv4(),
      type: 'neume' as const,
      polygon: normalizePolygon(bboxPolygon, imageDimensions),
      neumeType: neume.type,
    });
  }

  return { annotations, lineBoundaries };
}

// --- Contribution types ---

interface ContributionSyllable {
  text: string;
  boundary: number[][];
}

interface ContributionLine {
  boundary: number[][];
  syllables: ContributionSyllable[];
}

interface ContributionNeume {
  type: string;
  bbox: BBox;
}

interface ContributionAnnotations {
  lines: ContributionLine[];
  neumes: ContributionNeume[];
}

interface ContributionResponse {
  id: string;
  message: string;
  version?: string;
}

/**
 * Thrown when a PUT/PATCH is rejected because the contribution was modified
 * by someone else since this client last loaded it. Callers should prompt the
 * user to reload before re-saving.
 */
export class ContributionConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ContributionConflictError';
  }
}

/**
 * Convert imageDataUrl to a Blob and get its dimensions.
 */
async function imageDataUrlToBlob(imageDataUrl: string): Promise<{ blob: Blob; dimensions: ImageDimensions }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const dimensions = { width: img.width, height: img.height };

      // Convert data URL to blob
      fetch(imageDataUrl)
        .then(res => res.blob())
        .then(blob => resolve({ blob, dimensions }))
        .catch(reject);
    };
    img.onerror = () => reject(new Error('Failed to load image'));
    img.src = imageDataUrl;
  });
}

/**
 * Transform frontend annotations to backend contribution format.
 * Groups syllables into lines with polygon boundaries, converts to pixels.
 */
function transformAnnotationsForContribution(
  annotations: Annotation[],
  dimensions: ImageDimensions,
  storedLineBoundaries: LineBoundary[]
): ContributionAnnotations {
  const textLines = computeTextLines(annotations);

  // Build a lookup from syllable ID to stored line boundary
  const syllableToLineBoundary = new Map<string, number[][]>();
  for (const lb of storedLineBoundaries) {
    for (const sid of lb.syllableIds) {
      syllableToLineBoundary.set(sid, lb.boundary);
    }
  }

  const lines: ContributionLine[] = textLines.map(line => {
    // Try to find a stored line boundary via any syllable in the cluster
    let lineBoundary: number[][] | null = null;
    for (const syllable of line.syllables) {
      const stored = syllableToLineBoundary.get(syllable.id);
      if (stored) {
        lineBoundary = stored;
        break;
      }
    }

    // Fallback: compute bounding polygon from syllable polygons
    if (!lineBoundary) {
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (const syllable of line.syllables) {
        const b = polygonBounds(syllable.polygon);
        if (b.minX < minX) minX = b.minX;
        if (b.minY < minY) minY = b.minY;
        if (b.maxX > maxX) maxX = b.maxX;
        if (b.maxY > maxY) maxY = b.maxY;
      }
      lineBoundary = [[minX, minY], [maxX, minY], [maxX, maxY], [minX, maxY]];
    }

    return {
      boundary: denormalizePolygon(lineBoundary, dimensions),
      syllables: line.syllables.map(syllable => ({
        text: syllable.text || '',
        boundary: denormalizePolygon(syllable.polygon, dimensions),
      })),
    };
  });

  // Neumes: convert polygon back to bbox for backend
  const neumes: ContributionNeume[] = annotations
    .filter(a => a.type === 'neume')
    .map(neume => {
      const bounds = polygonBounds(neume.polygon);
      return {
        type: neume.neumeType || 'unknown',
        bbox: {
          x: Math.round(bounds.minX * dimensions.width),
          y: Math.round(bounds.minY * dimensions.height),
          width: Math.max(1, Math.round((bounds.maxX - bounds.minX) * dimensions.width)),
          height: Math.max(1, Math.round((bounds.maxY - bounds.minY) * dimensions.height)),
        },
      };
    });

  return { lines, neumes };
}

/**
 * Submit training data contribution to the backend.
 * Transforms annotations from frontend format to backend format and sends to /contribute.
 */
export async function contributeTrainingData(
  imageDataUrl: string,
  annotations: Annotation[],
  lineBoundaries: LineBoundary[] = []
): Promise<ContributionResponse> {
  // Convert image data URL to blob and get dimensions
  const { blob, dimensions } = await imageDataUrlToBlob(imageDataUrl);

  // Transform annotations to backend format
  const contributionAnnotations = transformAnnotationsForContribution(annotations, dimensions, lineBoundaries);

  // Build form data
  const formData = new FormData();
  formData.append('image', blob, 'image.jpg');
  formData.append('annotations', JSON.stringify(contributionAnnotations));

  // Send request
  const response = await apiFetch(`${HTR_BASE_URL}/contribute`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `Contribution failed: ${response.status} ${response.statusText}`;
    try {
      const errorJson = JSON.parse(errorText);
      if (errorJson.detail) {
        errorMessage = errorJson.detail;
      }
    } catch {
      // Use default error message
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

// --- Contribution management types ---

export interface ContributionSummary {
  id: string;
  image: { filename: string; width: number; height: number };
  line_count: number;
  syllable_count: number;
  neume_count: number;
}

interface ContributionDetailResponse {
  id: string;
  image: { filename: string; width: number; height: number; data_url: string };
  lines: Array<{ boundary: number[][]; syllables: Array<{ text: string; boundary: number[][] }> }>;
  neumes: Array<{ type: string; bbox: BBox }>;
  version: string;
}

export interface ContributionData {
  imageDataUrl: string;
  annotations: Annotation[];
  lineBoundaries: LineBoundary[];
  imageWidth: number;
  imageHeight: number;
  version: string;
}

/**
 * Fetch the list of stored contributions from the backend.
 */
export async function listContributions(): Promise<ContributionSummary[]> {
  const response = await apiFetch(`${HTR_BASE_URL}/contributions`);

  if (!response.ok) {
    throw new Error(`Failed to list contributions: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a single contribution by ID and convert to frontend format.
 */
export async function getContribution(id: string): Promise<ContributionData> {
  const response = await apiFetch(`${HTR_BASE_URL}/contributions/${encodeURIComponent(id)}`);

  if (!response.ok) {
    throw new Error(`Failed to get contribution: ${response.status} ${response.statusText}`);
  }

  const detail: ContributionDetailResponse = await response.json();
  const dimensions: ImageDimensions = { width: detail.image.width, height: detail.image.height };
  const { annotations, lineBoundaries } = responseToAnnotations(
    detail as unknown as RecognitionResponse,
    dimensions,
  );

  return {
    imageDataUrl: detail.image.data_url,
    annotations,
    lineBoundaries,
    imageWidth: detail.image.width,
    imageHeight: detail.image.height,
    version: detail.version,
  };
}

export interface NeumeCrop {
  type: string;
  contribution_id: string;
  bbox: { x: number; y: number; width: number; height: number };
  crop_data_url: string;
}

/**
 * Fetch neume crops across all contributions, optionally filtered by type.
 */
export async function listNeumes(type?: string): Promise<NeumeCrop[]> {
  const params = type ? `?type=${encodeURIComponent(type)}` : '';
  const response = await apiFetch(`${HTR_BASE_URL}/neumes${params}`);

  if (!response.ok) {
    throw new Error(`Failed to list neumes: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Relabel a single neume in a contribution by matching its bounding box.
 *
 * When `expectedVersion` is passed, it is sent as `If-Match` so the server
 * rejects the request (412) if the contribution was modified concurrently.
 * Returns the new version for the caller to store for their next request.
 */
export async function relabelNeume(
  contributionId: string,
  bbox: { x: number; y: number; width: number; height: number },
  newType: string,
  expectedVersion?: string,
): Promise<string | undefined> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (expectedVersion) headers['If-Match'] = `"${expectedVersion}"`;

  const response = await apiFetch(
    `${HTR_BASE_URL}/contributions/${encodeURIComponent(contributionId)}/neumes`,
    {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ bbox, new_type: newType }),
    },
  );

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `Relabel failed: ${response.status} ${response.statusText}`;
    try {
      const errorJson = JSON.parse(errorText);
      if (errorJson.detail) errorMessage = errorJson.detail;
    } catch {
      // Use default error message
    }
    if (response.status === 412) {
      throw new ContributionConflictError(errorMessage);
    }
    throw new Error(errorMessage);
  }

  const data: ContributionResponse = await response.json();
  return data.version;
}

/**
 * Update an existing contribution's annotations.
 *
 * When `expectedVersion` is passed, it is sent as `If-Match` so the server
 * rejects the request (412) if the contribution was modified concurrently —
 * preventing silent overwrites of another user's edits. Callers should treat
 * a `ContributionConflictError` as non-fatal and prompt the user to reload.
 */
export async function updateContribution(
  id: string,
  imageDataUrl: string,
  annotations: Annotation[],
  lineBoundaries: LineBoundary[] = [],
  expectedVersion?: string,
): Promise<ContributionResponse> {
  const { dimensions } = await imageDataUrlToBlob(imageDataUrl);
  const contributionAnnotations = transformAnnotationsForContribution(annotations, dimensions, lineBoundaries);

  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (expectedVersion) headers['If-Match'] = `"${expectedVersion}"`;

  const response = await apiFetch(`${HTR_BASE_URL}/contributions/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(contributionAnnotations),
  });

  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `Update failed: ${response.status} ${response.statusText}`;
    try {
      const errorJson = JSON.parse(errorText);
      if (errorJson.detail) {
        errorMessage = errorJson.detail;
      }
    } catch {
      // Use default error message
    }
    if (response.status === 412) {
      throw new ContributionConflictError(errorMessage);
    }
    throw new Error(errorMessage);
  }

  return response.json();
}
