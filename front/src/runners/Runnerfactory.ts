import { type CodeRunner } from './types';
import { PythonRunner } from './Pythonrunner';
import { JavaScriptRunner } from './Javascriptrunner';
import { BackendRunner } from './Backendrunner';

// Linguagens que rodam localmente no browser
const LOCAL_RUNNERS: Record<string, () => CodeRunner> = {
    python: () => new PythonRunner(),
    javascript: () => new JavaScriptRunner(),
    js: () => new JavaScriptRunner(),
};

/**
 * Cria o runner correto para a linguagem.
 *
 * - python / javascript → execução local (Pyodide / eval)
 * - java / c / c++ / etc → execução via backend API
 *
 * @param language  - linguagem da prova (vem de prova.linguagem)
 * @param getToken  - função para obter o token JWT (necessário pro BackendRunner)
 */
export function createRunner(
    language: string,
    getToken: () => Promise<string | null>
): CodeRunner {
    const key = language.toLowerCase().trim();

    if (LOCAL_RUNNERS[key]) {
        return LOCAL_RUNNERS[key]();
    }

    // Qualquer outra linguagem → backend
    return new BackendRunner(key, getToken);
}
