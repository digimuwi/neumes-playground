export interface NeumeClass {
  id: number;
  key: string;
  name: string;
  description: string;
  active: boolean;
}

export type RecognitionMode = 'manual' | 'neume' | 'text';

export interface Rectangle {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Annotation {
  id: string;
  type: 'syllable' | 'neume';
  polygon: number[][];
  text?: string;
  neumeType?: string;
}

export type OcrStage = 'loading' | 'segmenting' | 'recognizing' | 'syllabifying' | 'detecting';

export type OcrProgressEvent =
  | { stage: 'loading' }
  | { stage: 'segmenting' }
  | { stage: 'recognizing'; current: number; total: number }
  | { stage: 'syllabifying' }
  | { stage: 'detecting' }
  | { stage: 'error'; message: string };

export type OcrDialogState =
  | { mode: 'closed' }
  | { mode: 'uploadPrompt' }
  | { mode: 'existingAnnotationsPrompt' }
  | { mode: 'loading'; stage: OcrStage; current?: number; total?: number }
  | { mode: 'error'; message: string };

export interface LineBoundary {
  boundary: number[][];
  syllableIds: string[];
  confidence?: number;
}

export interface DocumentMetadata {
  [key: string]: unknown;
}

export interface AppState {
  imageDataUrl: string | null;
  annotations: Annotation[];
  selectedAnnotationIds: Set<string>;
  isNewlyCreated: boolean;
  ocrDialogState: OcrDialogState;
  errorMessage: string | null;
  lineBoundaries: LineBoundary[];
  contributionId: string | null;
  contributionVersion: string | null;
  metadata?: DocumentMetadata;
}

export interface HistoryState {
  states: AppState[];
  currentIndex: number;
}

export type Action =
  | { type: 'SET_IMAGE'; payload: string }
  | { type: 'ADD_ANNOTATION'; payload: Annotation }
  | { type: 'ADD_ANNOTATIONS'; payload: Annotation[] }
  | { type: 'UPDATE_ANNOTATION'; payload: { id: string; updates: Partial<Annotation> } }
  | { type: 'DELETE_ANNOTATION'; payload: string }
  | { type: 'DELETE_ANNOTATIONS'; payload: string[] }
  | { type: 'SELECT_ANNOTATION'; payload: string | null }
  | { type: 'SELECT_ANNOTATIONS'; payload: string[] }
  | { type: 'TOGGLE_ANNOTATION_SELECTION'; payload: string }
  | { type: 'CLEAR_NEW_FLAG' }
  | { type: 'UNDO' }
  | { type: 'REDO' }
  | { type: 'LOAD_STATE'; payload: AppState }
  | { type: 'SET_OCR_DIALOG'; payload: OcrDialogState }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ANNOTATIONS' }
  | { type: 'SET_LINE_BOUNDARIES'; payload: LineBoundary[] }
  | { type: 'SET_CONTRIBUTION_ID'; payload: string | null }
  | { type: 'SET_CONTRIBUTION_VERSION'; payload: string | null }
  | { type: 'SET_METADATA'; payload: DocumentMetadata };
