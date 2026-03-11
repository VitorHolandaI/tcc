export const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";
export const RECORDING_SERVICE_URL = import.meta.env.VITE_RECORDING_SERVICE_URL || "/api/recording";
export const ANALYSIS_SERVICE_URL = import.meta.env.VITE_ANALYSIS_SERVICE_URL || "/api/analysis";
export const WEBCAM_SERVICE_URL = import.meta.env.VITE_WEBCAM_SERVICE_URL || "/api/webcam";
export const AUDIO_SERVICE_URL = import.meta.env.VITE_AUDIO_SERVICE_URL || "/api/audio";
export const KEYSTROKE_SERVICE_URL = import.meta.env.VITE_KEYSTROKE_SERVICE_URL || "/api/keystroke";
export const SIMILARITY_SERVICE_URL = import.meta.env.VITE_SIMILARITY_SERVICE_URL || "/api/similarity";
//This with fallback one uses dev mode but using build will use the nginx one with url to the containers