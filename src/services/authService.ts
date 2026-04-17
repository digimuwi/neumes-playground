import { apiFetch } from './apiFetch';

const HTR_BASE_URL = import.meta.env.VITE_HTR_BASE_URL
  || (import.meta.env.DEV ? '/api' : '');

export interface AuthUser {
  login: string;
  name: string | null;
  avatar_url: string | null;
}

export interface MeResponse {
  authenticated: boolean;
  auth_enabled: boolean;
  user?: AuthUser;
}

export async function fetchMe(): Promise<MeResponse> {
  const response = await fetch(`${HTR_BASE_URL}/auth/me`, { credentials: 'include' });
  if (!response.ok) {
    throw new Error(`Failed to fetch auth state: ${response.status}`);
  }
  return response.json();
}

export function loginUrl(): string {
  const redirect = window.location.href;
  return `${HTR_BASE_URL}/auth/login?redirect=${encodeURIComponent(redirect)}`;
}

export async function logout(): Promise<void> {
  await apiFetch(`${HTR_BASE_URL}/auth/logout`, { method: 'POST' });
}
