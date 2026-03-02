import { useEffect, useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import * as monaco from "monaco-editor";

// Autocomplete hardcoded para tipos Python básicos
const PYTHON_TYPE_COMPLETIONS: Record<string, Array<{name: string, callable: boolean, doc: string}>> = {
  list: [
    { name: "append", callable: true, doc: "L.append(object) -> None -- append object to end" },
    { name: "clear", callable: true, doc: "L.clear() -> None -- remove all items from L" },
    { name: "copy", callable: true, doc: "L.copy() -> list -- a shallow copy of L" },
    { name: "count", callable: true, doc: "L.count(value) -> integer -- return number of occurrences of value" },
    { name: "extend", callable: true, doc: "L.extend(iterable) -> None -- extend list by appending elements from the iterable" },
    { name: "index", callable: true, doc: "L.index(value) -> integer -- return first index of value" },
    { name: "insert", callable: true, doc: "L.insert(index, object) -- insert object before index" },
    { name: "pop", callable: true, doc: "L.pop([index]) -> item -- remove and return item at index" },
    { name: "remove", callable: true, doc: "L.remove(value) -> None -- remove first occurrence of value" },
    { name: "reverse", callable: true, doc: "L.reverse() -> None -- reverse *IN PLACE*" },
    { name: "sort", callable: true, doc: "L.sort() -> None -- stable sort *IN PLACE*" },
  ],
  
  dict: [
    { name: "clear", callable: true, doc: "D.clear() -> None -- remove all items from D" },
    { name: "copy", callable: true, doc: "D.copy() -> a shallow copy of D" },
    { name: "fromkeys", callable: true, doc: "dict.fromkeys(iterable, value=None) -> new dict" },
    { name: "get", callable: true, doc: "D.get(k[,d]) -> D[k] if k in D, else d" },
    { name: "items", callable: true, doc: "D.items() -> a set-like object providing a view on D's items" },
    { name: "keys", callable: true, doc: "D.keys() -> a set-like object providing a view on D's keys" },
    { name: "pop", callable: true, doc: "D.pop(k[,d]) -> v, remove specified key and return the corresponding value" },
    { name: "popitem", callable: true, doc: "D.popitem() -> (k, v), remove and return some (key, value) pair" },
    { name: "setdefault", callable: true, doc: "D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D" },
    { name: "update", callable: true, doc: "D.update([E, ]**F) -> None -- update D from dict/iterable E and F" },
    { name: "values", callable: true, doc: "D.values() -> an object providing a view on D's values" },
  ],
  
  str: [
    { name: "capitalize", callable: true, doc: "S.capitalize() -> str" },
    { name: "casefold", callable: true, doc: "S.casefold() -> str" },
    { name: "center", callable: true, doc: "S.center(width[, fillchar]) -> str" },
    { name: "count", callable: true, doc: "S.count(sub[, start[, end]]) -> int" },
    { name: "encode", callable: true, doc: "S.encode(encoding='utf-8', errors='strict') -> bytes" },
    { name: "endswith", callable: true, doc: "S.endswith(suffix[, start[, end]]) -> bool" },
    { name: "find", callable: true, doc: "S.find(sub[, start[, end]]) -> int" },
    { name: "format", callable: true, doc: "S.format(*args, **kwargs) -> str" },
    { name: "index", callable: true, doc: "S.index(sub[, start[, end]]) -> int" },
    { name: "isalnum", callable: true, doc: "S.isalnum() -> bool" },
    { name: "isalpha", callable: true, doc: "S.isalpha() -> bool" },
    { name: "isdigit", callable: true, doc: "S.isdigit() -> bool" },
    { name: "islower", callable: true, doc: "S.islower() -> bool" },
    { name: "isspace", callable: true, doc: "S.isspace() -> bool" },
    { name: "isupper", callable: true, doc: "S.isupper() -> bool" },
    { name: "join", callable: true, doc: "S.join(iterable) -> str" },
    { name: "lower", callable: true, doc: "S.lower() -> str" },
    { name: "lstrip", callable: true, doc: "S.lstrip([chars]) -> str" },
    { name: "replace", callable: true, doc: "S.replace(old, new[, count]) -> str" },
    { name: "rfind", callable: true, doc: "S.rfind(sub[, start[, end]]) -> int" },
    { name: "rstrip", callable: true, doc: "S.rstrip([chars]) -> str" },
    { name: "split", callable: true, doc: "S.split(sep=None, maxsplit=-1) -> list of strings" },
    { name: "startswith", callable: true, doc: "S.startswith(prefix[, start[, end]]) -> bool" },
    { name: "strip", callable: true, doc: "S.strip([chars]) -> str" },
    { name: "upper", callable: true, doc: "S.upper() -> str" },
    { name: "zfill", callable: true, doc: "S.zfill(width) -> str" },
  ],
  
  set: [
    { name: "add", callable: true, doc: "Add an element to a set" },
    { name: "clear", callable: true, doc: "Remove all elements from this set" },
    { name: "copy", callable: true, doc: "Return a shallow copy of a set" },
    { name: "difference", callable: true, doc: "Return the difference of two or more sets as a new set" },
    { name: "discard", callable: true, doc: "Remove an element from a set if it is a member" },
    { name: "intersection", callable: true, doc: "Return the intersection of two sets as a new set" },
    { name: "issubset", callable: true, doc: "Report whether another set contains this set" },
    { name: "issuperset", callable: true, doc: "Report whether this set contains another set" },
    { name: "pop", callable: true, doc: "Remove and return an arbitrary set element" },
    { name: "remove", callable: true, doc: "Remove an element from a set; it must be a member" },
    { name: "union", callable: true, doc: "Return the union of sets as a new set" },
    { name: "update", callable: true, doc: "Update a set with the union of itself and others" },
  ],
  
  tuple: [
    { name: "count", callable: true, doc: "T.count(value) -> integer -- return number of occurrences of value" },
    { name: "index", callable: true, doc: "T.index(value) -> integer -- return first index of value" },
  ],

  int: [
    { name: "bit_length", callable: true, doc: "Number of bits necessary to represent self in binary" },
    { name: "to_bytes", callable: true, doc: "Return an array of bytes representing an integer" },
    { name: "from_bytes", callable: true, doc: "Return the integer represented by the given array of bytes" },
  ],

  float: [
    { name: "as_integer_ratio", callable: true, doc: "Return integer ratio" },
    { name: "is_integer", callable: true, doc: "Return True if the float is an integer" },
    { name: "hex", callable: true, doc: "Return a hexadecimal representation of a floating-point number" },
  ],
};

const PYTHON_BUILTINS = [
  { name: "abs", doc: "Return the absolute value of the argument" },
  { name: "all", doc: "Return True if bool(x) is True for all values x in the iterable" },
  { name: "any", doc: "Return True if bool(x) is True for any x in the iterable" },
  { name: "ascii", doc: "Return an ASCII-only representation of an object" },
  { name: "bin", doc: "Return the binary representation of an integer" },
  { name: "bool", doc: "bool(x) -> bool" },
  { name: "breakpoint", doc: "breakpoint(*args, **kws)" },
  { name: "bytearray", doc: "bytearray(iterable_of_ints) -> bytearray" },
  { name: "bytes", doc: "bytes(iterable_of_ints) -> bytes" },
  { name: "callable", doc: "Return whether the object is callable" },
  { name: "chr", doc: "Return a Unicode string of one character with ordinal i" },
  { name: "classmethod", doc: "classmethod(function) -> method" },
  { name: "compile", doc: "Compile source into a code object that can be executed" },
  { name: "complex", doc: "Create a complex number from a real part and an optional imaginary part" },
  { name: "delattr", doc: "Deletes the named attribute from the given object" },
  { name: "dict", doc: "dict() -> new empty dictionary" },
  { name: "dir", doc: "Return the list of names in the current local scope" },
  { name: "divmod", doc: "Return the tuple (x//y, x%y)" },
  { name: "enumerate", doc: "Return an enumerate object" },
  { name: "eval", doc: "Evaluate the given source in the context of globals and locals" },
  { name: "exec", doc: "Execute the given source in the context of globals and locals" },
  { name: "filter", doc: "filter(function or None, iterable) --> filter object" },
  { name: "float", doc: "Convert a string or number to a floating point number" },
  { name: "format", doc: "Return value.__format__(format_spec)" },
  { name: "frozenset", doc: "frozenset() -> empty frozenset object" },
  { name: "getattr", doc: "Get a named attribute from an object" },
  { name: "globals", doc: "Return the dictionary containing the current scope's global variables" },
  { name: "hasattr", doc: "Return whether the object has an attribute with the given name" },
  { name: "hash", doc: "Return the hash value for the given object" },
  { name: "help", doc: "Define the builtin 'help'" },
  { name: "hex", doc: "Return the hexadecimal representation of an integer" },
  { name: "id", doc: "Return the identity of an object" },
  { name: "input", doc: "Read a string from standard input" },
  { name: "int", doc: "int([x]) -> integer" },
  { name: "isinstance", doc: "Return whether an object is an instance of a class or of a subclass thereof" },
  { name: "issubclass", doc: "Return whether 'cls' is a derived from another class or is the same class" },
  { name: "iter", doc: "iter(iterable) -> iterator" },
  { name: "len", doc: "Return the length of an object" },
  { name: "list", doc: "Built-in mutable sequence" },
  { name: "locals", doc: "Return a dictionary containing the current scope's local variables" },
  { name: "map", doc: "map(func, *iterables) --> map object" },
  { name: "max", doc: "max(iterable, *[, default=obj, key=func]) -> value" },
  { name: "memoryview", doc: "Create a new memoryview object which references the given object" },
  { name: "min", doc: "min(iterable, *[, default=obj, key=func]) -> value" },
  { name: "next", doc: "next(iterator[, default])" },
  { name: "object", doc: "The base class of the class hierarchy" },
  { name: "oct", doc: "Return the octal representation of an integer" },
  { name: "open", doc: "Open file and return a stream" },
  { name: "ord", doc: "Return the Unicode code point for a one-character string" },
  { name: "pow", doc: "Equivalent to base**exp with 2 arguments or base**exp % mod with 3 arguments" },
  { name: "print", doc: "print(value, ..., sep=' ', end='\\n', file=sys.stdout, flush=False)" },
  { name: "property", doc: "Property attribute" },
  { name: "range", doc: "range(stop) -> range object" },
  { name: "repr", doc: "Return the canonical string representation of the object" },
  { name: "reversed", doc: "Return a reverse iterator" },
  { name: "round", doc: "Round a number to a given precision in decimal digits" },
  { name: "set", doc: "set() -> new empty set object" },
  { name: "setattr", doc: "Sets the named attribute on the given object to the specified value" },
  { name: "slice", doc: "slice(stop)" },
  { name: "sorted", doc: "Return a new list containing all items from the iterable in ascending order" },
  { name: "staticmethod", doc: "staticmethod(function) -> method" },
  { name: "str", doc: "str(object='') -> str" },
  { name: "sum", doc: "Return the sum of a 'start' value plus an iterable of numbers" },
  { name: "super", doc: "super() -> same as super(__class__, <first argument>)" },
  { name: "tuple", doc: "Built-in immutable sequence" },
  { name: "type", doc: "type(object) -> the object's type" },
  { name: "vars", doc: "Return the __dict__ attribute for a module, class, instance, or any other object" },
  { name: "zip", doc: "zip(*iterables) --> A zip object yielding tuples" },
];

const PYTHON_KEYWORDS = [
  "False", "None", "True", "and", "as", "assert", "async", "await",
  "break", "class", "continue", "def", "del", "elif", "else", "except",
  "finally", "for", "from", "global", "if", "import", "in", "is",
  "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
  "try", "while", "with", "yield"
];

export default function App() {
  const editorRef = useRef<any>(null);
  const [code, setCode] = useState(`# Python IDE with Auto-Complete
mylist = [1, 2, 3, 4, 5]
mydict = {"name": "John", "age": 30}
mystring = "Hello World"
myset = {1, 2, 3}
mytuple = (1, 2, 3)

# Try typing:
# mylist. (autocomplete appears automatically!)
# mydict.
# mystring.

print("Start typing to see autocomplete!")`);
  const [output, setOutput] = useState("");
  const [timings, setTimings] = useState<{ key: string; delta: number }[]>([]);
  const lastKeyTimeRef = useRef<number | null>(null);

  const inferType = (varName: string, code: string): string | null => {
    const patterns = [
      { regex: new RegExp(`${varName}\\s*=\\s*\\[`), type: 'list' },
      { regex: new RegExp(`${varName}\\s*=\\s*\\{[^}]*:[^}]*\\}`), type: 'dict' },
      { regex: new RegExp(`${varName}\\s*=\\s*\\{[^:}]*\\}`), type: 'set' },
      { regex: new RegExp(`${varName}\\s*=\\s*\\(`), type: 'tuple' },
      { regex: new RegExp(`${varName}\\s*=\\s*["'\`]`), type: 'str' },
      { regex: new RegExp(`${varName}\\s*=\\s*\\d+\\.\\d+`), type: 'float' },
      { regex: new RegExp(`${varName}\\s*=\\s*\\d+(?!\\.)\\s*($|\\n)`), type: 'int' },
      { regex: new RegExp(`${varName}\\s*=\\s*list\\(`), type: 'list' },
      { regex: new RegExp(`${varName}\\s*=\\s*dict\\(`), type: 'dict' },
      { regex: new RegExp(`${varName}\\s*=\\s*set\\(`), type: 'set' },
      { regex: new RegExp(`${varName}\\s*=\\s*str\\(`), type: 'str' },
      { regex: new RegExp(`${varName}\\s*=\\s*int\\(`), type: 'int' },
      { regex: new RegExp(`${varName}\\s*=\\s*float\\(`), type: 'float' },
    ];

    for (const pattern of patterns) {
      if (pattern.regex.test(code)) {
        return pattern.type;
      }
    }
    return null;
  };

  const handleEditorDidMount = (editor: any, monacoInstance: typeof monaco) => {
    editorRef.current = editor;

    editor.onKeyDown((e: any) => {
      const now = performance.now();
      const key = e.browserEvent.key;

      if (lastKeyTimeRef.current !== null) {
        const delta = now - lastKeyTimeRef.current;
        setTimings((prev) => [...prev, { key, delta }]);
      }
      lastKeyTimeRef.current = now;
    });

    monacoInstance.languages.registerCompletionItemProvider("python", {
      triggerCharacters: ["."],
      
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
          const objName = attributeMatch[1];
          const attrPrefix = attributeMatch[2] || "";
          
          const inferredType = inferType(objName, fullCode);

          if (inferredType && PYTHON_TYPE_COMPLETIONS[inferredType]) {
            const methods = PYTHON_TYPE_COMPLETIONS[inferredType];
            
            methods.forEach((method) => {
              if (method.name.toLowerCase().startsWith(attrPrefix.toLowerCase())) {
                suggestions.push({
                  label: method.name,
                  kind: method.callable
                    ? monacoInstance.languages.CompletionItemKind.Method
                    : monacoInstance.languages.CompletionItemKind.Property,
                  insertText: method.name,
                  range: range,
                  documentation: method.doc,
                  detail: `${inferredType}.${method.name}`,
                  sortText: `0${method.name}`,
                });
              }
            });
          }

        } else {
          PYTHON_BUILTINS.forEach((builtin) => {
            if (builtin.name.toLowerCase().startsWith(word.word.toLowerCase())) {
              suggestions.push({
                label: builtin.name,
                kind: monacoInstance.languages.CompletionItemKind.Function,
                insertText: builtin.name,
                range: range,
                documentation: builtin.doc,
                detail: "built-in function",
              });
            }
          });

          PYTHON_KEYWORDS.forEach((keyword) => {
            if (keyword.toLowerCase().startsWith(word.word.toLowerCase())) {
              suggestions.push({
                label: keyword,
                kind: monacoInstance.languages.CompletionItemKind.Keyword,
                insertText: keyword,
                range: range,
                detail: "keyword",
              });
            }
          });

          const varMatches = fullCode.matchAll(/(\w+)\s*=/g);
          const variables = new Set<string>();

          for (const match of varMatches) {
            variables.add(match[1]);
          }

          variables.forEach((varName) => {
            if (varName.toLowerCase().startsWith(word.word.toLowerCase())) {
              const varType = inferType(varName, fullCode);
              suggestions.push({
                label: varName,
                kind: monacoInstance.languages.CompletionItemKind.Variable,
                insertText: varName,
                range: range,
                detail: varType ? `variable (${varType})` : "variable",
              });
            }
          });

          const funcMatches = fullCode.matchAll(/def\s+(\w+)/g);
          for (const match of funcMatches) {
            const funcName = match[1];
            if (funcName.toLowerCase().startsWith(word.word.toLowerCase())) {
              suggestions.push({
                label: funcName,
                kind: monacoInstance.languages.CompletionItemKind.Function,
                insertText: funcName,
                range: range,
                detail: "function",
              });
            }
          }

          const classMatches = fullCode.matchAll(/class\s+(\w+)/g);
          for (const match of classMatches) {
            const className = match[1];
            if (className.toLowerCase().startsWith(word.word.toLowerCase())) {
              suggestions.push({
                label: className,
                kind: monacoInstance.languages.CompletionItemKind.Class,
                insertText: className,
                range: range,
                detail: "class",
              });
            }
          }
        }

        const uniqueSuggestions = suggestions.filter(
          (item, index, self) =>
            index === self.findIndex((t) => t.label === item.label)
        );

        return { suggestions: uniqueSuggestions };
      },
    });

    editor.onDidChangeModelContent(() => {
      const model = editor.getModel();
      const position = editor.getPosition();
      
      if (!model || !position) return;

      const textUntilPosition = model.getValueInRange({
        startLineNumber: position.lineNumber,
        startColumn: 1,
        endLineNumber: position.lineNumber,
        endColumn: position.column,
      });

      // Auto-trigger when user types "."
      if (textUntilPosition.endsWith('.')) {
        // Small delay to let Monaco process the character
        setTimeout(() => {
          editor.trigger('', 'editor.action.triggerSuggest', {});
        }, 50);
      }
    });
  };

  const runCode = () => {
    setOutput(" Code execution is disabled in this demo.\nThis version focuses on autocomplete functionality.");
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}> Python IDE - Auto-Complete</h1>
      
      <div style={styles.instructions}>
        <p> <strong>Auto-complete is enabled!</strong></p>
        <p> Type <code>mydict.</code> or <code>mylist.</code> and watch the suggestions appear automatically</p>
        <p> You can also press <kbd>Ctrl+Space</kbd> anywhere to trigger suggestions</p>
      </div>

      <div style={styles.editorContainer}>
        <Editor
          height="450px"
          defaultLanguage="python"
          theme="vs-dark"
          value={code}
          onChange={(value) => setCode(value || "")}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            automaticLayout: true,
            suggestOnTriggerCharacters: true,
            quickSuggestions: {
              other: true,
              comments: false,
              strings: false,
            },
            quickSuggestionsDelay: 100,

            acceptSuggestionOnEnter: "on",
            tabCompletion: "on",
            wordBasedSuggestions: "off", // Disable word-based to avoid duplicates
            parameterHints: { enabled: true },
            suggest: {
              showMethods: true,
              showFunctions: true,
              showConstructors: true,
              showFields: true,
              showVariables: true,
              showClasses: true,
              showKeywords: true,
              showWords: false, // Disable generic word suggestions
            },
            
            tabSize: 4,
            insertSpaces: true,
          }}
        />
      </div>

      <button style={styles.button} onClick={runCode}>
        ℹ Info
      </button>

      <div style={styles.outputContainer}>
        <h3> Tips:</h3>
        <pre style={styles.output}>
{`• Type "mylist." and autocomplete appears instantly!
- All Python built-in functions are available
- Type "pr" to see "print"
- Type "for" to see keyword completion
- Hover over suggestions to see documentation`}
        </pre>
      </div>

      <div style={styles.outputContainer}>
        <h3>⌨ Keystroke Dynamics (Last 15):</h3>
        <pre style={styles.output}>
          {timings.slice(-15).map((t, i) => 
            `${i + 1}. ${t.key.padEnd(15)} → ${t.delta.toFixed(1)} ms`
          ).join("\n") || "Start typing to see keystroke timing..."}
        </pre>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: 20,
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    maxWidth: 1100,
    margin: "0 auto",
    backgroundColor: "#1e1e1e",
    minHeight: "100vh",
    color: "#d4d4d4",
  },
  title: {
    textAlign: "center",
    marginBottom: 10,
    color: "#fff",
  },
  instructions: {
    textAlign: "center",
    marginBottom: 20,
    padding: 15,
    backgroundColor: "#2d2d30",
    borderRadius: 6,
    border: "1px solid #3c3c3c",
  },
  editorContainer: {
    border: "1px solid #3c3c3c",
    borderRadius: 8,
    overflow: "hidden",
    marginBottom: 15,
    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.3)",
  },
  button: {
    padding: "12px 24px",
    marginBottom: 20,
    backgroundColor: "#0e639c",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 16,
    fontWeight: "bold",
  },
  outputContainer: {
    marginTop: 15,
    padding: 15,
    backgroundColor: "#252526",
    borderRadius: 8,
    border: "1px solid #3c3c3c",
  },
  output: {
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    fontSize: 13,
    fontFamily: "'Consolas', 'Monaco', monospace",
    margin: 0,
    color: "#d4d4d4",
  },
};
