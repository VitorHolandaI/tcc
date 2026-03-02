import { API_BASE_URL, WEBCAM_SERVICE_URL } from "./apiConfig";

export const recordingService = {
    getScreenRecordingUrl(provaId: number, alunoId: number, token: string): string {
        // This endpoint is on the main backend, not the recording service
        return `${API_BASE_URL}/recordings/video/${provaId}/${alunoId}`;
    },

    getWebcamVideoUrl(provaId: number, alunoId: number): string {
        return `${WEBCAM_SERVICE_URL}/video/${provaId}/${alunoId}`;
    }
};
