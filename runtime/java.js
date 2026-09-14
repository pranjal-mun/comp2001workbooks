// How editor text becomes a Java project. A widget's code is either a whole
// class (or several) or a snippet: statements to run one after the other,
// the way a listing in the workbook shows them. Snippets are wrapped in a
// Main class before compiling, and line numbers in compiler messages and
// stack traces are shifted back so they match the editor.

const SNIPPET_PREFIX = ["public class Main {", "    public static void main(String[] args) throws Exception {"];
const SNIPPET_SUFFIX = ["    }", "}"];

/** The code with comments and string literals blanked out, for pattern tests. */
function skeleton(code) {
  return String(code)
    .replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, " "))
    .replace(/\/\/[^\n]*/g, "")
    .replace(/"(?:[^"\\\n]|\\.)*"/g, '""')
    .replace(/'(?:[^'\\\n]|\\.)*'/g, "''");
}

/** True when the code declares no type of its own, so it is a list of statements. */
export function isSnippet(code) {
  return !/\b(class|interface|enum)\s+[A-Za-z_$][\w$]*/.test(skeleton(code));
}

/** Wrap a snippet as the body of Main.main. Returns {source, offset}: editor line = source line - offset. */
export function wrapSnippet(code) {
  const body = String(code).split("\n").map((line) => (line ? "        " + line : line));
  return { source: [...SNIPPET_PREFIX, ...body, ...SNIPPET_SUFFIX].join("\n"), offset: SNIPPET_PREFIX.length };
}

/** Names of the top-level types declared in the code, in order, with whether each is public and has a main method. */
export function declaredTypes(code) {
  const text = skeleton(code);
  const pattern = /\b((?:public|final|abstract|static|strictfp)\s+)*(class|interface|enum)\s+([A-Za-z_$][\w$]*)/g;
  const found = [...text.matchAll(pattern)];
  return found.map((match, index) => {
    const start = match.index;
    const end = index + 1 < found.length ? found[index + 1].index : text.length;
    return {
      name: match[3],
      kind: match[2],
      isPublic: /\bpublic\b/.test(match[0]),
      hasMain: /\bstatic\s+void\s+main\s*\(/.test(text.slice(start, end)),
    };
  });
}

/** The class whose main method should run: the one that has main, else the public class, else the first type. */
export function mainClassOf(code) {
  const types = declaredTypes(code);
  return (types.find((t) => t.hasMain) ?? types.find((t) => t.isPublic) ?? types[0])?.name ?? "Main";
}

/** The file name a compilation unit must have: after its public class, else after the class that runs. */
export function fileNameOf(code) {
  const types = declaredTypes(code);
  return `${(types.find((t) => t.isPublic) ?? types.find((t) => t.hasMain) ?? types[0])?.name ?? "Main"}.java`;
}

/**
 * Build the project for a widget: {files, entry, studentFile, offset}. The
 * editor's code becomes the first file; `extra` files from the spec follow.
 */
export function buildProject(code, extra = []) {
  let source = String(code);
  let offset = 0;
  if (isSnippet(source)) ({ source, offset } = wrapSnippet(source));
  const studentFile = fileNameOf(source);
  const entry = mainClassOf(source);
  const files = [{ name: studentFile, content: source }, ...extra.filter((f) => f.name !== studentFile)];
  return { files, entry, studentFile, offset };
}

/** Rewrite line numbers in compiler messages and stack traces to editor lines, and hide the worker's paths. */
export function relocateMessages(text, studentFile, offset) {
  let result = String(text ?? "").replace(/\/str\//g, "").replace(/\/files\/workbook\/run\d+\/classes\//g, "");
  if (!offset) return result;
  const escaped = studentFile.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  result = result.replace(new RegExp(`(ERROR|WARNING) in ${escaped} \\(at line (\\d+)\\)`, "g"), (m, kind, line) => `${kind} in ${studentFile} (at line ${Math.max(1, Number(line) - offset)})`);
  result = result.replace(new RegExp(`\\(${escaped}:(\\d+)\\)`, "g"), (m, line) => `(${studentFile}:${Math.max(1, Number(line) - offset)})`);
  return result;
}

/** Editor line to highlight for a failed run: the first compiler error or innermost stack frame in the student's file, or null. */
export function errorLine(text, studentFile, offset = 0) {
  const escaped = studentFile.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const compile = String(text ?? "").match(new RegExp(`ERROR in (?:/str/)?${escaped} \\(at line (\\d+)\\)`));
  const frame = String(text ?? "").match(new RegExp(`\\(${escaped}:(\\d+)\\)`));
  const match = compile ?? frame;
  if (!match) return null;
  return Math.max(1, Number(match[1]) - offset);
}

/** True when the program reads from the keyboard. */
export function usesInput(code) {
  return /\bSystem\.in\b/.test(skeleton(code));
}

/**
 * One compilation unit for Python Tutor, which only takes a single file: the
 * student's code first (wrapped if it is a snippet), then the extra files
 * with `public` removed from their type declarations, imports hoisted to the
 * top.
 */
export function tutorSource(code, extra = []) {
  const { files } = buildProject(code, extra);
  const imports = new Set();
  const bodies = files.map((file, index) => {
    let body = file.content.replace(/^\s*import\s+[^;]+;\s*$/gm, (line) => { imports.add(line.trim()); return ""; });
    if (index > 0) body = body.replace(/\bpublic\s+((?:final\s+|abstract\s+)*(?:class|interface|enum)\s)/g, "$1");
    return body.replace(/^\n+/, "").replace(/\s+$/, "");
  });
  return [...imports].concat(bodies).join("\n\n").replace(/^\n+/, "");
}
