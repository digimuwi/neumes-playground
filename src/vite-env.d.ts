/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_HTR_BASE_URL?: string;
  readonly VITE_HTR_PROXY_TARGET?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
