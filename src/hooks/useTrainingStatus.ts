import { useCallback, useEffect, useRef, useState } from 'react';
import {
  TrainingStatus,
  TrainingStartOptions,
  startTraining as apiStartTraining,
  getTrainingStatus as apiGetTrainingStatus,
} from '../services/htrService';

const POLL_INTERVAL_MS = 2000;

function isActiveState(state: TrainingStatus['state']): boolean {
  return state === 'exporting' || state === 'training' || state === 'deploying';
}

export function useTrainingStatus() {
  const [status, setStatus] = useState<TrainingStatus | null>(null);
  const [alreadyRunning, setAlreadyRunning] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const poll = useCallback(async () => {
    try {
      const s = await apiGetTrainingStatus();
      setStatus(s);
      if (!isActiveState(s.state)) {
        stopPolling();
      }
    } catch {
      // Silently ignore poll errors — will retry on next interval
    }
  }, [stopPolling]);

  const startPolling = useCallback(() => {
    if (intervalRef.current !== null) return; // already polling
    // Poll immediately, then every POLL_INTERVAL_MS
    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
  }, [poll]);

  const start = useCallback(async (options?: TrainingStartOptions) => {
    setAlreadyRunning(false);
    try {
      const s = await apiStartTraining(options);
      setStatus(s);
      startPolling();
    } catch (err: any) {
      if (err.status === 409) {
        // Training already running — not an error, just start polling
        setAlreadyRunning(true);
        startPolling();
      } else {
        throw err;
      }
    }
  }, [startPolling]);

  // Poll once on mount to detect in-progress training
  useEffect(() => {
    poll().then(() => {
      // If training is active after initial poll, keep polling
      setStatus((current) => {
        if (current && isActiveState(current.state)) {
          startPolling();
        }
        return current;
      });
    });
    return stopPolling;
  }, [poll, startPolling, stopPolling]);

  const isActive = status !== null && isActiveState(status.state);

  return { status, start, isActive, alreadyRunning };
}
