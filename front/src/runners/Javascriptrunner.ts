import { type CodeRunner, type ExecutionResult } from './types';

export class JavaScriptRunner implements CodeRunner {
    language = 'javascript';
    private ready = false;

    async init(): Promise<void> {
        // JS não precisa carregar nada — já roda no browser
        this.ready = true;
    }

    isReady(): boolean {
        return this.ready;
    }

    async execute(code: string): Promise<ExecutionResult> {
        const logs: string[] = [];
        const errors: string[] = [];

        const fakeConsole = {
            log: (...args: any[]) => logs.push(args.map(String).join(' ')),
            error: (...args: any[]) => errors.push(args.map(String).join(' ')),
            warn: (...args: any[]) => logs.push(` ${args.map(String).join(' ')}`),
            info: (...args: any[]) => logs.push(args.map(String).join(' ')),
        };

        try {
            const fn = new Function('console', code);
            fn(fakeConsole);

            return {
                stdout: logs.join('\n'),
                stderr: errors.join('\n'),
                error: null,
                success: true,
            };
        } catch (err: any) {
            return {
                stdout: logs.join('\n'),
                stderr: errors.join('\n'),
                error: err.message || String(err),
                success: false,
            };
        }
    }

    dispose(): void {
        this.ready = false;
    }
}
