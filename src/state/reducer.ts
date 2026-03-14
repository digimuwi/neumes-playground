import { produce, enableMapSet } from 'immer';
import { Action, AppState, HistoryState } from './types';

// Enable Immer's MapSet plugin to support Set in state
enableMapSet();

const STORAGE_KEY = 'neume-annotations';

export const initialAppState: AppState = {
  imageDataUrl: null,
  annotations: [],
  selectedAnnotationIds: new Set<string>(),
  isNewlyCreated: false,
  ocrDialogState: { mode: 'closed' },
  errorMessage: null,
  lineBoundaries: [],
  contributionId: null,
};

export const initialHistoryState: HistoryState = {
  states: [initialAppState],
  currentIndex: 0,
};

interface PersistedAppState extends Omit<AppState, 'selectedAnnotationIds' | 'ocrDialogState' | 'errorMessage' | 'lineBoundaries' | 'contributionId' | 'metadata'> {
  lineBoundaries?: AppState['lineBoundaries'];
  contributionId?: string | null;
  metadata?: AppState['metadata'];
  selectedAnnotationIds?: string[];
  // Legacy field for backward compatibility
  selectedAnnotationId?: string | null;
}

export function loadStateFromStorage(): HistoryState {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const persisted = JSON.parse(stored) as PersistedAppState;
      // Convert array back to Set, with fallback for legacy single-selection format
      let selectedIds: Set<string>;
      if (persisted.selectedAnnotationIds) {
        selectedIds = new Set(persisted.selectedAnnotationIds);
      } else if (persisted.selectedAnnotationId) {
        selectedIds = new Set([persisted.selectedAnnotationId]);
      } else {
        selectedIds = new Set();
      }
      const appState: AppState = {
        imageDataUrl: persisted.imageDataUrl,
        annotations: persisted.annotations,
        selectedAnnotationIds: selectedIds,
        isNewlyCreated: persisted.isNewlyCreated,
        ocrDialogState: { mode: 'closed' },
        errorMessage: null,
        lineBoundaries: persisted.lineBoundaries || [],
        contributionId: persisted.contributionId ?? null,
        metadata: persisted.metadata,
      };
      return {
        states: [appState],
        currentIndex: 0,
      };
    }
  } catch (e) {
    console.error('Failed to load state from localStorage:', e);
  }
  return initialHistoryState;
}

export function saveStateToStorage(state: AppState): void {
  try {
    // Convert Set to Array for JSON serialization (exclude transient state)
    const persisted: PersistedAppState = {
      imageDataUrl: state.imageDataUrl,
      annotations: state.annotations,
      selectedAnnotationIds: Array.from(state.selectedAnnotationIds),
      isNewlyCreated: state.isNewlyCreated,
      lineBoundaries: state.lineBoundaries,
      contributionId: state.contributionId,
      metadata: state.metadata,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
  } catch (e) {
    console.error('Failed to save state to localStorage:', e);
  }
}

export function historyReducer(state: HistoryState, action: Action): HistoryState {
  if (action.type === 'UNDO') {
    if (state.currentIndex <= 0) return state;
    return { ...state, currentIndex: state.currentIndex - 1 };
  }

  if (action.type === 'REDO') {
    if (state.currentIndex >= state.states.length - 1) return state;
    return { ...state, currentIndex: state.currentIndex + 1 };
  }

  if (action.type === 'LOAD_STATE') {
    return {
      states: [action.payload],
      currentIndex: 0,
    };
  }

  const currentAppState = state.states[state.currentIndex];
  const newAppState = appReducer(currentAppState, action);

  if (newAppState === currentAppState) {
    return state;
  }

  // Selection actions, CLEAR_NEW_FLAG, dialog state, and error state don't create history entries
  if (
    action.type === 'SELECT_ANNOTATION' ||
    action.type === 'SELECT_ANNOTATIONS' ||
    action.type === 'TOGGLE_ANNOTATION_SELECTION' ||
    action.type === 'CLEAR_NEW_FLAG' ||
    action.type === 'SET_OCR_DIALOG' ||
    action.type === 'SET_ERROR' ||
    action.type === 'SET_LINE_BOUNDARIES' ||
    action.type === 'SET_CONTRIBUTION_ID' ||
    action.type === 'SET_METADATA'
  ) {
    const newStates = [...state.states];
    newStates[state.currentIndex] = newAppState;
    return { ...state, states: newStates };
  }

  // Truncate future states and add new state
  return {
    states: [...state.states.slice(0, state.currentIndex + 1), newAppState],
    currentIndex: state.currentIndex + 1,
  };
}

function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_IMAGE':
      return produce(state, (draft) => {
        draft.imageDataUrl = action.payload;
        draft.annotations = [];
        draft.selectedAnnotationIds = new Set<string>();
        draft.lineBoundaries = [];
        draft.contributionId = null;
      });

    case 'ADD_ANNOTATION':
      return produce(state, (draft) => {
        draft.annotations.push(action.payload);
        draft.selectedAnnotationIds = new Set([action.payload.id]);
        draft.isNewlyCreated = true;
      });

    case 'ADD_ANNOTATIONS':
      return produce(state, (draft) => {
        draft.annotations.push(...action.payload);
        draft.selectedAnnotationIds = new Set(action.payload.map((a) => a.id));
        draft.isNewlyCreated = false;
      });

    case 'UPDATE_ANNOTATION':
      return produce(state, (draft) => {
        const index = draft.annotations.findIndex((a) => a.id === action.payload.id);
        if (index !== -1) {
          Object.assign(draft.annotations[index], action.payload.updates);
        }
      });

    case 'DELETE_ANNOTATION':
      return produce(state, (draft) => {
        const index = draft.annotations.findIndex((a) => a.id === action.payload);
        if (index !== -1) {
          draft.annotations.splice(index, 1);
          draft.selectedAnnotationIds.delete(action.payload);
        }
      });

    case 'DELETE_ANNOTATIONS':
      return produce(state, (draft) => {
        const idsToDelete = new Set(action.payload);
        draft.annotations = draft.annotations.filter((a) => !idsToDelete.has(a.id));
        for (const id of action.payload) {
          draft.selectedAnnotationIds.delete(id);
        }
      });

    case 'SELECT_ANNOTATION':
      return produce(state, (draft) => {
        if (action.payload === null) {
          draft.selectedAnnotationIds = new Set<string>();
        } else {
          draft.selectedAnnotationIds = new Set([action.payload]);
        }
      });

    case 'SELECT_ANNOTATIONS':
      return produce(state, (draft) => {
        draft.selectedAnnotationIds = new Set(action.payload);
      });

    case 'TOGGLE_ANNOTATION_SELECTION':
      return produce(state, (draft) => {
        if (draft.selectedAnnotationIds.has(action.payload)) {
          draft.selectedAnnotationIds.delete(action.payload);
        } else {
          draft.selectedAnnotationIds.add(action.payload);
        }
      });

    case 'CLEAR_NEW_FLAG':
      return produce(state, (draft) => {
        draft.isNewlyCreated = false;
      });

    case 'SET_OCR_DIALOG':
      return produce(state, (draft) => {
        draft.ocrDialogState = action.payload;
      });

    case 'SET_ERROR':
      return produce(state, (draft) => {
        draft.errorMessage = action.payload;
      });

    case 'CLEAR_ANNOTATIONS':
      return produce(state, (draft) => {
        draft.annotations = [];
        draft.selectedAnnotationIds = new Set<string>();
        draft.lineBoundaries = [];
      });

    case 'SET_LINE_BOUNDARIES':
      return produce(state, (draft) => {
        draft.lineBoundaries = action.payload;
      });

    case 'SET_CONTRIBUTION_ID':
      return produce(state, (draft) => {
        draft.contributionId = action.payload;
      });

    case 'SET_METADATA':
      return produce(state, (draft) => {
        draft.metadata = { ...draft.metadata, ...action.payload };
      });

    default:
      return state;
  }
}
