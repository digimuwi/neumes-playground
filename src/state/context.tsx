import React, { createContext, useContext, useReducer, useEffect, useRef, useState } from 'react';
import { Action, AppState, HistoryState, NeumeClass, RecognitionMode } from './types';
import { historyReducer, loadStateFromStorage, saveStateToStorage } from './reducer';
import { fallbackNeumeClasses } from '../data/neumeTypes';
import {
  createNeumeClass as createNeumeClassRequest,
  CreateNeumeClassRequest,
  listNeumeClasses,
  updateNeumeClass as updateNeumeClassRequest,
  UpdateNeumeClassRequest,
} from '../services/neumeClassService';

interface AppContextValue {
  state: AppState;
  historyState: HistoryState;
  dispatch: React.Dispatch<Action>;
  canUndo: boolean;
  canRedo: boolean;
  recognitionMode: RecognitionMode;
  setRecognitionMode: React.Dispatch<React.SetStateAction<RecognitionMode>>;
  neumeClasses: NeumeClass[];
  neumeClassesLoading: boolean;
  refreshNeumeClasses: () => Promise<void>;
  createNeumeClass: (payload: CreateNeumeClassRequest) => Promise<NeumeClass>;
  updateNeumeClass: (id: number, payload: UpdateNeumeClassRequest) => Promise<NeumeClass>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [historyState, dispatch] = useReducer(historyReducer, null, loadStateFromStorage);
  const state = historyState.states[historyState.currentIndex];
  const [recognitionMode, setRecognitionMode] = useState<RecognitionMode>('manual');
  const [neumeClasses, setNeumeClasses] = useState<NeumeClass[]>(fallbackNeumeClasses);
  const [neumeClassesLoading, setNeumeClassesLoading] = useState(true);
  const saveTimeoutRef = useRef<number | null>(null);

  const canUndo = historyState.currentIndex > 0;
  const canRedo = historyState.currentIndex < historyState.states.length - 1;

  // Debounced save to localStorage
  useEffect(() => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    saveTimeoutRef.current = window.setTimeout(() => {
      saveStateToStorage(state);
    }, 500);

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [state]);

  const refreshNeumeClasses = React.useCallback(async () => {
    setNeumeClassesLoading(true);
    try {
      const classes = await listNeumeClasses();
      setNeumeClasses(classes);
    } catch (error) {
      console.error('Failed to load neume classes:', error);
    } finally {
      setNeumeClassesLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshNeumeClasses();
  }, [refreshNeumeClasses]);

  const createNeumeClass = React.useCallback(async (payload: CreateNeumeClassRequest) => {
    const created = await createNeumeClassRequest(payload);
    setNeumeClasses((prev) => [...prev, created].sort((a, b) => a.id - b.id));
    return created;
  }, []);

  const updateNeumeClass = React.useCallback(async (id: number, payload: UpdateNeumeClassRequest) => {
    const updated = await updateNeumeClassRequest(id, payload);
    setNeumeClasses((prev) =>
      prev
        .map((entry) => (entry.id === id ? updated : entry))
        .sort((a, b) => a.id - b.id)
    );
    return updated;
  }, []);

  return (
    <AppContext.Provider value={{
      state,
      historyState,
      dispatch,
      canUndo,
      canRedo,
      recognitionMode,
      setRecognitionMode,
      neumeClasses,
      neumeClassesLoading,
      refreshNeumeClasses,
      createNeumeClass,
      updateNeumeClass,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
}
