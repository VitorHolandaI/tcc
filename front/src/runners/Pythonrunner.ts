import { type CodeRunner, type ExecutionResult } from './types';

const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v0.25.1/full';

export class PythonRunner implements CodeRunner {
    language = 'python';
    private pyodide: any = null;

    async init(): Promise<void> {
        // Carregar script do Pyodide se ainda não está no DOM
        if (!(window as any).loadPyodide) {
            await new Promise<void>((resolve, reject) => {
                const script = document.createElement('script');
                script.src = `${PYODIDE_CDN}/pyodide.js`;
                script.onload = () => resolve();
                script.onerror = () => reject(new Error('Falha ao carregar Pyodide CDN'));
                document.head.appendChild(script);
            });
        }

        this.pyodide = await (window as any).loadPyodide({
            indexURL: `${PYODIDE_CDN}/`,
        });
    }

    isReady(): boolean {
        return this.pyodide !== null;
    }

    async execute(code: string): Promise<ExecutionResult> {
        if (!this.pyodide) {
            return { stdout: '', stderr: '', error: 'Pyodide não inicializado', success: false };
        }

        const py = this.pyodide;

        // Redirecionar stdout/stderr
        py.runPython(`
import sys
from io import StringIO
sys.stdout = StringIO()
sys.stderr = StringIO()
`);

        try {
            py.runPython(code);

            const stdout = py.runPython('sys.stdout.getvalue()') || '';
            const stderr = py.runPython('sys.stderr.getvalue()') || '';

            return { stdout, stderr, error: null, success: true };
        } catch (err: any) {
            const stdout = py.runPython('sys.stdout.getvalue()') || '';
            const stderr = py.runPython('sys.stderr.getvalue()') || '';

            return {
                stdout,
                stderr,
                error: err.message || String(err),
                success: false,
            };
        } finally {
            // Restaurar stdout/stderr
            py.runPython(`
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
`);
        }
    }

    dispose(): void {
        this.pyodide = null;
    }
}
