import { useState, useCallback } from 'react';
import { CantusChant, lookupCantusId } from '../services/cantusIndex';
import { Annotation } from '../state/types';

export type CantusLookupState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; results: CantusChant[] }
  | { status: 'error'; message: string };

export interface UseCantusLookupResult {
  state: CantusLookupState;
  lookup: (annotations: Annotation[]) => Promise<CantusChant[]>;
  reset: () => void;
}

export function useCantusLookup(): UseCantusLookupResult {
  const [state, setState] = useState<CantusLookupState>({ status: 'idle' });

  const lookup = useCallback(async (annotations: Annotation[]): Promise<CantusChant[]> => {
    setState({ status: 'loading' });
    try {
      const results = await lookupCantusId(annotations);
      setState({ status: 'success', results });
      return results;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Lookup failed';
      setState({ status: 'error', message });
      return [];
    }
  }, []);

  const reset = useCallback(() => {
    setState({ status: 'idle' });
  }, []);

  return { state, lookup, reset };
}
