import { useEffect, useRef, useState } from "react";
import { EditorState } from "@codemirror/state";
import { EditorView, keymap } from "@codemirror/view";
import { python } from "@codemirror/lang-python";
import { autocompletion } from "@codemirror/autocomplete";
import { defaultKeymap } from "@codemirror/commands";

export default function App() {
  const editorRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);

  const [pyodide, setPyodide] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [output, setOutput] = useState("");
  const [timings, setTimings] = useState<{ key: string; delta: number }[]>([]);
  const lastKeyTimeRef = useRef<number | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">("light");

  // Carrega Pyodide
  useEffect(() => {
    const loadPyodideScript = async () => {
      const script = document.createElement("script");
      script.src = "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js";
      script.onload = async () => {
        // @ts-ignore
        const py = await window.loadPyodide({
          indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/",
        });
        setPyodide(py);
        setLoading(false);
      };
      document.body.appendChild(script);
    };
    loadPyodideScript();
  }, []);

  // Inicializa editor
  useEffect(() => {
    if (editorRef.current && !viewRef.current) {
      const state = EditorState.create({
        doc: `# Digite seu código Python aqui\nprint("Hello World")`,
        extensions: [
          python(),
          keymap.of(defaultKeymap),
          autocompletion({
            override: [
              async (context) => {
                const word = context.matchBefore(/\w+(\.\w*)?$/);
                if (!word) return null;

                const suggestions: any[] = [];
                const text = word.text;

                if (pyodide) {
                  try {
                    if (text.includes(".")) {
                      const parts = text.split(".");
                      const objName = parts[0];
                      const prefix = parts[1] || "";

                      await pyodide.runPythonAsync(`
try:
    import ${objName}
except:
    pass
`);

                      const methods = pyodide.runPython(`
try:
    [m for m in dir(${objName}) if m.startswith("${prefix}")]
except:
    []
`).toJs();

                      methods.forEach((m: string) => {
                        suggestions.push({ label: m, type: "function" });
                      });
                    } else {
                      const globals = pyodide.runPython("list(globals().keys())").toJs();
                      globals.forEach((g: string) => {
                        if (g.startsWith(text)) suggestions.push({ label: g, type: "variable" });
                      });
                      ["print", "len", "range", "int", "str"].forEach((f) => {
                        if (f.startsWith(text)) suggestions.push({ label: f, type: "function" });
                      });
                    }
                  } catch {}
                }

                return { from: word.from, options: suggestions };
              },
            ],
          }),
          EditorView.domEventHandlers({
            keydown: (event, view) => {
              const now = performance.now();
              const key = event.key;

              // Keystroke dynamics
              if (lastKeyTimeRef.current !== null) {
                const delta = now - lastKeyTimeRef.current;
                setTimings((prev) => [...prev, { key, delta }]);
              }
              lastKeyTimeRef.current = now;

              // Tab para indentação
              if (key === "Tab") {
                event.preventDefault();
                view.dispatch({
                  changes: { from: view.state.selection.main.from, insert: "  " },
                });
              }

              return false;
            },
          }),
        ],
      });

      viewRef.current = new EditorView({
        state,
        parent: editorRef.current,
        // Tema inline
        style: theme === "dark"
          ? { backgroundColor: "#1e1e1e", color: "#d4d4d4" }
          : { backgroundColor: "#fefefe", color: "#000" },
      });
    }
  }, [pyodide, theme]);

  const runCode = async () => {
    if (!pyodide || !viewRef.current) return;
    setOutput("Executando...");
    try {
      const code = viewRef.current.state.doc.toString();
      const result = await pyodide.runPythonAsync(`
import sys, io
sys.stdout = io.StringIO()
sys.stderr = sys.stdout
${code}
sys.stdout.getvalue()
      `);
      setOutput(result.toString());
    } catch (err: any) {
      setOutput(err.message);
    }
  };

  if (loading) return <p>Carregando Python...</p>;

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Python IDE Híbrido</h1>

      <div style={{ marginBottom: 10 }}>
        <label>
          Tema:
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as "light" | "dark")}
            style={{ marginLeft: 10, padding: 4 }}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </label>
      </div>

      <div ref={editorRef} style={theme === "dark" ? styles.editorDark : styles.editor}></div>
      <button style={styles.button} onClick={runCode}>
        Run
      </button>

      <div style={styles.outputContainer}>
        <h3>Output:</h3>
        <pre style={styles.output}>{output}</pre>
      </div>

      <div style={styles.outputContainer}>
        <h3>Keystroke dynamics:</h3>
        <pre style={styles.output}>
          {timings
            .filter((t) => t.delta !== undefined)
            .map((t, i) => `${i + 1}. ${t.key} → ${t.delta.toFixed(1)} ms`)
            .join("\n")}
        </pre>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { padding: 20, fontFamily: "monospace", maxWidth: 800, margin: "0 auto" },
  title: { textAlign: "center", marginBottom: 20 },
  editor: { border: "1px solid #ccc", minHeight: 250, borderRadius: 6, fontSize: 16, padding: 10, backgroundColor: "#fefefe", marginBottom: 10 },
  editorDark: { border: "1px solid #444", minHeight: 250, borderRadius: 6, fontSize: 16, padding: 10, backgroundColor: "#1e1e1e", color: "#d4d4d4", marginBottom: 10 },
  button: { padding: "8px 16px", marginBottom: 20, backgroundColor: "#007acc", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" },
  outputContainer: { marginTop: 10, padding: 10, backgroundColor: "#1e1e1e", color: "#d4d4d4", borderRadius: 6 },
  output: { whiteSpace: "pre-wrap", wordBreak: "break-word" },
};

