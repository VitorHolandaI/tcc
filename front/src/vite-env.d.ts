/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_FIREBASE_API_KEY: string;
  readonly VITE_FIREBASE_AUTH_DOMAIN: string;
  readonly VITE_FIREBASE_PROJECT_ID: string;
  readonly VITE_FIREBASE_STORAGE_BUCKET: string;
  readonly VITE_FIREBASE_MESSAGING_SENDER_ID: string;
  readonly VITE_FIREBASE_APP_ID: string;
  readonly VITE_API_URL: string;
  readonly VITE_RECORDING_SERVICE_URL: string;
  readonly VITE_ANALYSIS_SERVICE_URL: string;
  readonly VITE_WEBCAM_SERVICE_URL: string;
  readonly VITE_AUDIO_SERVICE_URL: string;
  readonly VITE_KEYSTROKE_SERVICE_URL: string;
  readonly VITE_SIMILARITY_SERVICE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
