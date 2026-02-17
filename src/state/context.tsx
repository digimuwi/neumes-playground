import React, { createContext, useContext, useReducer, useEffect, useRef, useState } from 'react';
import { Action, AppState, HistoryState, RecognitionMode } from './types';
import { historyReducer, loadStateFromStorage, saveStateToStorage } from './reducer';

interface AppContextValue {
  state: AppState;
  historyState: HistoryState;
  dispatch: React.Dispatch<Action>;
  canUndo: boolean;
  canRedo: boolean;
  recognitionMode: RecognitionMode;
  setRecognitionMode: React.Dispatch<React.SetStateAction<RecognitionMode>>;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [historyState, dispatch] = useReducer(historyReducer, null, loadStateFromStorage);
  const state = historyState.states[historyState.currentIndex];
  const [recognitionMode, setRecognitionMode] = useState<RecognitionMode>('manual');
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

  return (
    <AppContext.Provider value={{ state, historyState, dispatch, canUndo, canRedo, recognitionMode, setRecognitionMode }}>
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
