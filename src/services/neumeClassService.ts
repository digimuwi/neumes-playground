import { NeumeClass } from '../state/types';

const HTR_BASE_URL = import.meta.env.VITE_HTR_BASE_URL
  || (import.meta.env.DEV ? '/api' : `${window.location.protocol}//${window.location.hostname}:8000`);

export interface CreateNeumeClassRequest {
  key: string;
  name: string;
  description?: string;
}

export interface UpdateNeumeClassRequest {
  name?: string;
  description?: string;
  active?: boolean;
}

async function parseError(response: Response, fallback: string): Promise<never> {
  const text = await response.text();
  let detail: string | null = null;
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed.detail === 'string' && parsed.detail) {
      detail = parsed.detail;
    }
  } catch (_error) {
    // Fall through to raw text/fallback below.
  }

  if (detail) {
    throw new Error(detail);
  }
  if (text) {
    throw new Error(text);
  }
  throw new Error(fallback);
}

export async function listNeumeClasses(): Promise<NeumeClass[]> {
  const response = await fetch(`${HTR_BASE_URL}/neume-classes`);
  if (!response.ok) {
    await parseError(response, `Failed to list neume classes: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export async function createNeumeClass(
  payload: CreateNeumeClassRequest
): Promise<NeumeClass> {
  const response = await fetch(`${HTR_BASE_URL}/neume-classes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    await parseError(response, `Failed to create neume class: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export async function updateNeumeClass(
  id: number,
  payload: UpdateNeumeClassRequest
): Promise<NeumeClass> {
  const response = await fetch(`${HTR_BASE_URL}/neume-classes/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    await parseError(response, `Failed to update neume class: ${response.status} ${response.statusText}`);
  }
  return response.json();
}
