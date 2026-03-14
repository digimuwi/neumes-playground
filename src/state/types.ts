export enum NeumeType {
  // Basic neumes
  PUNCTUM = 'punctum',
  VIRGA = 'virga',

  // Two-note neumes
  PES = 'pes',
  CLIVIS = 'clivis',

  // Three-note neumes
  TORCULUS = 'torculus',
  PORRECTUS = 'porrectus',
  SCANDICUS = 'scandicus',
  CLIMACUS = 'climacus',

  // Compound neumes
  PES_SUBBIPUNCTIS = 'pes subbipunctis',
  PES_SUBTRIPUNCTIS = 'pes subtripunctis',
  PES_PRAEBIPUNCTIS = 'pes praebipunctis',
  SCANDICUS_FLEXUS = 'scandicus flexus',
  TORCULUS_RESUPINUS = 'torculus resupinus',
  PORRECTUS_FLEXUS = 'porrectus flexus',
  SCANDICUS_CLIMACUS = 'scandicus climacus',

  // Repeated notes
  BIVIRGA = 'bivirga',
  TRIVIRGA = 'trivirga',
  STROPHA = 'stropha',
  BISTROPHA = 'bistropha',
  TRISTROPHA = 'tristropha',

  // Special neumes
  PRESSUS = 'pressus',
  UNCINUS = 'uncinus',
  CELERITER = 'celeriter',
  QUILISMA = 'quilisma',
  SALICUS = 'salicus',
  APOSTROPHA = 'apostropha',

  // Episema variants
  VIRGA_EPISEMA = 'virga episema',
  CLIVIS_EPISEMA = 'clivis episema',
  CLIVIS_EPISEMA_PRAEBIPUNCTIS = 'clivis episema praebipunctis',
  CLIMACUS_EPISEMA = 'climacus episema',
  APOSTROPHA_EPISEMA = 'apostropha episema',

  // Liquescent and quadratus variants
  ORISCUS = 'oriscus',
  TRIGON = 'trigon',
  PES_LIQUESCENS = 'pes liquescens',
  TORCULUS_LIQUESCENS = 'torculus liquescens',
  PES_QUADRATUS = 'pes quadratus',
  PES_QUADRATUS_SUBBIPUNCTIS = 'pes quadratus subbipunctis',
  TENETE = 'tenete',
  PORRECTUS_SUBBIPUNCTIS = 'porrectus subbipunctis',
  EXPECTATE = 'expectate',

  // Additional neume types
  CEPHALICUS = 'cephalicus',
  EQUALITER = 'equaliter',
  INFERIUS = 'inferius',
  LEVARE = 'levare',
  MEDIOCRITER = 'mediocriter',
  PRESSIONEM = 'pressionem',
  SURSUM = 'sursum',
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
  neumeType?: NeumeType;
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
  | { type: 'SET_METADATA'; payload: DocumentMetadata };
