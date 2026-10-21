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

/**
 * The class whose main method should run: the one that has main, else the
 * public class, else the first type. When the code declares no main at all
 * (a class-writing exercise) and one of the supplied `extra` files does,
 * that file's class runs instead.
 */
export function mainClassOf(code, extra = []) {
  const types = declaredTypes(code);
  if (!types.some((t) => t.hasMain)) {
    for (const file of extra) {
      const driver = declaredTypes(file.content).find((t) => t.hasMain);
      if (driver) return driver.name;
    }
  }
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
  const entry = mainClassOf(source, extra);
  const files = [{ name: studentFile, content: source }, ...extra.filter((f) => f.name !== studentFile)];
  return { files, entry, studentFile, offset };
}

/**
 * Rewrite line numbers in compiler messages and stack traces to editor lines,
 * and hide the worker's paths. `files` (the project's files) lets stack frames
 * that CheerpJ prints as "(Unknown Source)" get their line from the source.
 */
export function relocateMessages(text, studentFile, offset, files = []) {
  let result = String(text ?? "").replace(/\/str\//g, "").replace(/\/files\/workbook\/run\d+\/classes\//g, "");
  if (offset) {
    const escaped = studentFile.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    result = result.replace(new RegExp(`(ERROR|WARNING) in ${escaped} \\(at line (\\d+)\\)`, "g"), (m, kind, line) => `${kind} in ${studentFile} (at line ${Math.max(1, Number(line) - offset)})`);
    result = result.replace(new RegExp(`\\(${escaped}:(\\d+)\\)`, "g"), (m, line) => `(${studentFile}:${Math.max(1, Number(line) - offset)})`);
  }
  return files.length ? locateFrames(result, files, studentFile, offset) : result;
}

// CheerpJ runs the compiled classes without their line tables, so a stack
// trace names each method but says "(Unknown Source)". For a frame in one of
// the project's classes the line can usually be found from the source: inside
// that method's body, the line that calls the method of the frame above it
// (get, for example), or for the innermost frame the line that can throw the
// exception (a division for ArithmeticException). One such line gives
// (File.java:N), as java prints it; a few give "line N or M"; more give the
// method's lines.

const FRAME = /^(\s*at\s+)([\w$.]+)\.([\w$<>]+)\(Unknown Source\)/;
const RAISES = {
  ArithmeticException: /[/%]/,
  ArrayIndexOutOfBoundsException: /\[\s*[^\s\]]/,
  NegativeArraySizeException: /\bnew\s+[\w.]+\s*\[/,
  ClassCastException: /\(\s*[A-Z][\w.]*(?:<[^()]*>)?\s*\)\s*[\w(]/,
  NullPointerException: /[\w)\]]\s*(?:\.\s*[A-Za-z_$]|\[)/,
};

function locateFrames(text, files, studentFile, offset) {
  const sources = files.map((file) => ({ name: file.name, lines: skeleton(file.content).split("\n") }));
  let exception = "";
  let callee = null;
  return text.split("\n").map((line) => {
    const header = line.match(/^(?:Exception in thread "[^"]*"|Caused by:)\s+([\w$.]+)/);
    if (header) {
      exception = header[1].split(".").pop();
      callee = null;
      return line;
    }
    const frame = line.match(FRAME);
    if (!frame) return line;
    const [, lead, owner, method] = frame;
    const here = { owner, method };
    const outer = owner.split("$")[0];
    const file = sources.find((s) => findType(s.lines.join("\n"), outer) != null);
    let place = null;
    if (file) {
      const { found, span } = candidateLines(file.lines, owner, method, callee, exception);
      const shift = (n) => Math.max(1, n - (file.name === studentFile ? offset : 0));
      place = describePlace(file.name, found.map(shift), span.map(shift));
    }
    callee = here;
    return place ? line.replace("(Unknown Source)", place) : line;
  }).join("\n");
}

function describePlace(fileName, found, span) {
  if (found.length === 1) return `(${fileName}:${found[0]})`;
  if (found.length > 1 && found.length <= 3) return `(${fileName}, line ${found.slice(0, -1).join(", ")} or ${found[found.length - 1]})`;
  if (!span.length) return null;
  return `(${fileName}, lines ${span[0]}-${span[span.length - 1]})`;
}

/** Source lines (1-based) where the frame's method could have stopped (`found`), and all the lines of the method (`span`). */
function candidateLines(lines, owner, method, callee, exception) {
  const text = lines.join("\n");
  const names = owner.split("$");
  let range = findType(text, names[0]);
  for (const inner of names.slice(1)) {
    if (/^\d+$/.test(inner) || !range) break;
    range = findType(text, inner, range[0] + 1, range[1]) ?? range;
  }
  if (!range) return { found: [], span: [] };
  const simple = names[names.length - 1].replace(/^\d+$/, "");
  const bodies = method.startsWith("lambda$") || method === "<clinit>" ? [range]
    : methodBodies(text, range, method === "<init>" ? simple : method);
  if (!bodies.length) return { found: [], span: [] };
  const lineOf = (index) => text.slice(0, index).split("\n").length;
  const span = [];
  for (const [open, close] of bodies) for (let n = lineOf(open); n <= lineOf(close); n++) span.push(n);
  const matching = (pattern) => span.filter((n) => pattern.test(lines[n - 1]));
  let found = [];
  if (callee) {
    const target = callee.method === "<init>" ? callee.owner.split(/[.$]/).pop() : callee.method;
    if (!target.startsWith("lambda$") && !target.startsWith("<")) {
      found = matching(callee.method === "<init>" ? new RegExp(`\\bnew\\s+${escapeName(target)}\\b|\\b(?:this|super)\\s*\\(`) : new RegExp(`\\b${escapeName(target)}\\s*\\(`));
      // A for-each loop calls iterator(), hasNext() and next() without naming them.
      if (!found.length && ["next", "hasNext", "iterator", "forEachRemaining"].includes(target)) found = matching(/\bfor\s*\([^;]*:/);
    }
  } else {
    found = matching(new RegExp(`\\bthrow\\s+new\\s+${escapeName(exception)}\\b`));
    if (!found.length && RAISES[exception]) found = matching(RAISES[exception]);
    if (!found.length) found = matching(/\bthrow\b/);
  }
  // A lambda's frame covers the whole class; prefer the lines with an arrow.
  if (method.startsWith("lambda$") && found.some((n) => lines[n - 1].includes("->"))) found = found.filter((n) => lines[n - 1].includes("->"));
  return { found, span };
}

function escapeName(name) {
  return name.replace(/\$/g, "\\$");
}

/** [open, close] indexes of the braces of a type's body, searching within [from, to), or null. */
function findType(text, name, from = 0, to = text.length) {
  const pattern = new RegExp(`\\b(?:class|interface|enum)\\s+${escapeName(name)}\\b`, "g");
  pattern.lastIndex = from;
  const match = pattern.exec(text);
  if (!match || match.index >= to) return null;
  const open = text.indexOf("{", match.index);
  return open < 0 ? null : [open, matchingBrace(text, open)];
}

/** Brace ranges of the bodies of methods (or constructors) called `name` declared directly in the type body `range`. */
function methodBodies(text, range, name) {
  const pattern = new RegExp(`\\b${escapeName(name)}\\s*\\(`, "g");
  const bodies = [];
  pattern.lastIndex = range[0];
  for (let match; (match = pattern.exec(text)) && match.index < range[1];) {
    if (depthAt(text, range[0], match.index) !== 1) continue;
    const before = text.slice(range[0], match.index).replace(/\s+$/, "");
    if (/[.=(,]$/.test(before) || /\bnew$/.test(before) || /\breturn$/.test(before)) continue;
    const close = matchingParen(text, match.index + match[0].length - 1);
    const after = text.slice(close + 1).match(/^\s*(?:throws\s+[\w$.,\s<>]+?)?\s*\{/);
    if (!after) continue;
    const open = close + after[0].length;
    bodies.push([open - 1, matchingBrace(text, open - 1)]);
  }
  return bodies;
}

function depthAt(text, start, index) {
  let depth = 0;
  for (let i = start; i < index; i++) {
    if (text[i] === "{") depth++;
    else if (text[i] === "}") depth--;
  }
  return depth;
}

function matchingBrace(text, open) {
  return matchingPair(text, open, "{", "}");
}

function matchingParen(text, open) {
  return matchingPair(text, open, "(", ")");
}

function matchingPair(text, open, left, right) {
  let depth = 0;
  for (let i = open; i < text.length; i++) {
    if (text[i] === left) depth++;
    else if (text[i] === right && --depth === 0) return i;
  }
  return text.length - 1;
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
