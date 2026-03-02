import axios from 'axios';
import { ANALYSIS_SERVICE_URL, AUDIO_SERVICE_URL, KEYSTROKE_SERVICE_URL, SIMILARITY_SERVICE_URL } from './apiConfig';

export interface GazeAnalysisResult {
    status: string;
    metrics?: {
        percentage_down: number;
        percentage_forward: number;
        percentage_left: number;
        percentage_no_face: number;
        percentage_right: number;
        percentage_up: number;
        position_changes_per_minute: number;
        total_position_changes: number;
    };
    suspicious_periods?: {
        direction: string;
        duration: number;
        end: number;
        start: number;
    }[];
}

export interface AudioAnalysisResult {
    status: string;
    results?: {
        total_speakers: number;
        has_multiple_speakers: boolean;
        total_duration_seconds: number;
        silence_percentage: number;
    };
    speaker_timeline?: any[];
}

export interface KeystrokeAnalysisResult {
    status: string;
    typing_metrics?: {
        total_events: number;
        hold_time_avg: number;
        hold_time_std: number;
        flight_time_avg: number;
        flight_time_std: number;
    };
    suspicious_commands?: {
        command_counts: Record<string, number>;
        suspicious_percentage: number;
        total_commands: number;
        avg_manhattan_distance: number;
        command_sequences: number;
    };
}

export interface SimilarityPair {
    aluno_a: { id: number; nome: string; email: string };
    aluno_b: { id: number; nome: string; email: string };
    text_similarity: number;
    normalized_similarity: number;
    max_similarity: number;
    flagged: boolean;
}

export interface SimilarityQuestion {
    questao_id: number;
    questao_titulo: string;
    total_submissions: number;
    total_pairs: number;
    flagged_pairs: number;
    pairs: SimilarityPair[];
}

export interface SimilarityAnalysisResult {
    status: string;
    prova_id?: number;
    total_students?: number;
    total_flagged_pairs?: number;
    threshold_used?: number;
    questions?: SimilarityQuestion[];
    completed_at?: string;
    message?: string;
    error?: string;
}

export const analysisService = {
    // Gaze Analysis
    async startGazeAnalysis(provaId: number, alunoId: number, token: string) {
        const response = await axios.post(
            `${ANALYSIS_SERVICE_URL}/analyze/${provaId}/${alunoId}`,
            {},
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    async getGazeAnalysis(provaId: number, alunoId: number, token: string): Promise<GazeAnalysisResult> {
        const response = await axios.get(
            `${ANALYSIS_SERVICE_URL}/analysis/${provaId}/${alunoId}`,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    // Audio Analysis
    async startAudioAnalysis(provaId: number, alunoId: number, token: string) {
        const response = await axios.post(
            `${AUDIO_SERVICE_URL}/analyze/${provaId}/${alunoId}`,
            {},
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    async getAudioAnalysis(provaId: number, alunoId: number, token: string): Promise<AudioAnalysisResult> {
        const response = await axios.get(
            `${AUDIO_SERVICE_URL}/analysis/${provaId}/${alunoId}`,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    // Keystroke Analysis
    async startKeystrokeAnalysis(provaId: number, alunoId: number, token: string) {
        const response = await axios.post(
            `${KEYSTROKE_SERVICE_URL}/analyze/${provaId}/${alunoId}`,
            {},
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    async getKeystrokeAnalysis(provaId: number, alunoId: number, token: string): Promise<KeystrokeAnalysisResult> {
        const response = await axios.get(
            `${KEYSTROKE_SERVICE_URL}/analysis/${provaId}/${alunoId}`,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    // Similarity Analysis
    async startSimilarityAnalysis(provaId: number, token: string) {
        const response = await axios.post(
            `${SIMILARITY_SERVICE_URL}/analyze/${provaId}`,
            {},
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },

    async getSimilarityAnalysis(provaId: number, token: string): Promise<SimilarityAnalysisResult> {
        const response = await axios.get(
            `${SIMILARITY_SERVICE_URL}/analysis/${provaId}`,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return response.data;
    },
};
