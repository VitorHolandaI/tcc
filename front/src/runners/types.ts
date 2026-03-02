export interface ExecutionResult {
    stdout: string;
    stderr: string;
    error: string | null;
    success: boolean;
}

export interface CodeRunner {
    /** Nome da linguagem */
    language: string;

    /** Carrega o runtime (ex: Pyodide). Resolve quando pronto. */
    init(): Promise<void>;

    /** Retorna true quando o runner está pronto para executar */
    isReady(): boolean;

    /** Executa o código e retorna o resultado */
    execute(code: string): Promise<ExecutionResult>;

    /** Libera recursos se necessário */
    dispose(): void;
}
