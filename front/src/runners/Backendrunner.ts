import { type CodeRunner, type ExecutionResult } from './types';
import axios from 'axios';
const API_BASE_URL = "/back"

/**
 * Runner genérico que delega execução ao backend.
 * Usado para linguagens que NÃO rodam no browser (Java, C, C++, etc.)
 *
 * Espera que o backend tenha:
 *   POST /execucao/executar
 *   Body: { codigo: string, linguagem: string }
 *   Response: { stdout: string, stderr: string, error: string | null }
 */
export class BackendRunner implements CodeRunner {
    language: string;
    private ready = false;
    private getToken: () => Promise<string | null>;

    constructor(language: string, getToken: () => Promise<string | null>) {
        this.language = language;
        this.getToken = getToken;
    }

    async init(): Promise<void> {
        // Pode fazer um health-check no backend se quiser
        this.ready = true;
    }

    isReady(): boolean {
        return this.ready;
    }

    async execute(code: string): Promise<ExecutionResult> {
        try {
            const token = await this.getToken();

            const response = await axios.post(
                `${API_BASE_URL}/execucao/executar`,
                { codigo: code, linguagem: this.language },
                { headers: { Authorization: `Bearer ${token}` } }
            );

            const data = response.data;

            return {
                stdout: data.stdout || data.resultado_execucao || '',
                stderr: data.stderr || '',
                error: data.error || null,
                success: !data.error,
            };
        } catch (err: any) {
            return {
                stdout: '',
                stderr: '',
                error: err.response?.data?.detail || err.message || 'Erro ao executar no servidor',
                success: false,
            };
        }
    }

    dispose(): void {
        this.ready = false;
    }
}
