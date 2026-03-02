import * as monaco from 'monaco-editor';
import {
    PYTHON_TYPE_COMPLETIONS,
    PYTHON_BUILTINS,
    PYTHON_KEYWORDS,
    inferPythonType,
} from './PythonData';

const registeredLanguages = new Set<string>();

/**
 * Registra o completion provider do Monaco para a linguagem da prova.
 * Chama uma vez só — ignora chamadas repetidas para a mesma linguagem.
 */
export function registerAutocomplete(
    monacoInstance: typeof monaco,
    language: string
): void {
    const key = language.toLowerCase().trim();

    if (registeredLanguages.has(key)) return;
    registeredLanguages.add(key);

    if (key === 'python') {
        registerPythonAutocomplete(monacoInstance);
    }

    // Adicione outros providers aqui:
    // if (key === 'javascript') registerJavaScriptAutocomplete(monacoInstance);
    // if (key === 'java') registerJavaAutocomplete(monacoInstance);
}

// ── Python ────────────────────────────────────────────────────────────────────

function registerPythonAutocomplete(monacoInstance: typeof monaco) {
    monacoInstance.languages.registerCompletionItemProvider('python', {
        triggerCharacters: ['.'],

        provideCompletionItems: (model, position) => {
            const textUntilPosition = model.getValueInRange({
                startLineNumber: position.lineNumber,
                startColumn: 1,
                endLineNumber: position.lineNumber,
                endColumn: position.column,
            });

            const word = model.getWordUntilPosition(position);
            const range = {
                startLineNumber: position.lineNumber,
                endLineNumber: position.lineNumber,
                startColumn: word.startColumn,
                endColumn: word.endColumn,
            };

            const suggestions: any[] = [];
            const fullCode = model.getValue();
            const attributeMatch = textUntilPosition.match(/([\w]+)\.\s*(\w*)$/);

            if (attributeMatch) {
                // object.method completions
                const objName = attributeMatch[1];
                const attrPrefix = (attributeMatch[2] || '').toLowerCase();
                const inferredType = inferPythonType(objName, fullCode);

                if (inferredType && PYTHON_TYPE_COMPLETIONS[inferredType]) {
                    PYTHON_TYPE_COMPLETIONS[inferredType].forEach((method) => {
                        if (method.name.toLowerCase().startsWith(attrPrefix)) {
                            suggestions.push({
                                label: method.name,
                                kind: method.callable
                                    ? monacoInstance.languages.CompletionItemKind.Method
                                    : monacoInstance.languages.CompletionItemKind.Property,
                                insertText: method.name,
                                range,
                                documentation: method.doc,
                                detail: `${inferredType}.${method.name}`,
                                sortText: `0${method.name}`,
                            });
                        }
                    });
                }
            } else {
                const prefix = word.word.toLowerCase();

                // Builtins
                PYTHON_BUILTINS.forEach((b) => {
                    if (b.name.toLowerCase().startsWith(prefix)) {
                        suggestions.push({
                            label: b.name,
                            kind: monacoInstance.languages.CompletionItemKind.Function,
                            insertText: b.name,
                            range,
                            documentation: b.doc,
                            detail: 'built-in function',
                        });
                    }
                });

                // Keywords
                PYTHON_KEYWORDS.forEach((kw) => {
                    if (kw.toLowerCase().startsWith(prefix)) {
                        suggestions.push({
                            label: kw,
                            kind: monacoInstance.languages.CompletionItemKind.Keyword,
                            insertText: kw,
                            range,
                            detail: 'keyword',
                        });
                    }
                });

                // Variables in code
                const varMatches = fullCode.matchAll(/(\w+)\s*=/g);
                const vars = new Set<string>();
                for (const m of varMatches) vars.add(m[1]);
                vars.forEach((v) => {
                    if (v.toLowerCase().startsWith(prefix)) {
                        const t = inferPythonType(v, fullCode);
                        suggestions.push({
                            label: v,
                            kind: monacoInstance.languages.CompletionItemKind.Variable,
                            insertText: v,
                            range,
                            detail: t ? `variable (${t})` : 'variable',
                        });
                    }
                });

                // Functions in code
                for (const m of fullCode.matchAll(/def\s+(\w+)/g)) {
                    if (m[1].toLowerCase().startsWith(prefix)) {
                        suggestions.push({
                            label: m[1],
                            kind: monacoInstance.languages.CompletionItemKind.Function,
                            insertText: m[1],
                            range,
                            detail: 'function',
                        });
                    }
                }

                // Classes in code
                for (const m of fullCode.matchAll(/class\s+(\w+)/g)) {
                    if (m[1].toLowerCase().startsWith(prefix)) {
                        suggestions.push({
                            label: m[1],
                            kind: monacoInstance.languages.CompletionItemKind.Class,
                            insertText: m[1],
                            range,
                            detail: 'class',
                        });
                    }
                }
            }

            // Deduplicate
            const unique = suggestions.filter(
                (item, idx, self) => idx === self.findIndex((t) => t.label === item.label)
            );

            return { suggestions: unique };
        },
    });
}
