// Checking: expected-output comparison, multi-case runs with rewrites and
// scripted input, instructor check scripts, and answer-cell matching.

import { runner } from "./runner.js";
import { buildProject, relocateMessages } from "./java.js";

/** Trailing whitespace per line and trailing blank lines are ignored. */
export function normalizeOutput(text) {
  return String(text ?? "")
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .map((line) => line.replace(/\s+$/, ""))
    .join("\n")
    .replace(/\n+$/, "");
}

/** Line-by-line comparison. Returns {pass, lines: [{expected, actual, ok}]}. */
export function compareOutput(expected, actual) {
  const want = normalizeOutput(expected).split("\n");
  const got = normalizeOutput(actual).split("\n");
  const count = Math.max(want.length, got.length);
  const lines = [];
  let pass = true;
  for (let i = 0; i < count; i++) {
    const ok = want[i] === got[i];
    if (!ok) pass = false;
    lines.push({ expected: want[i], actual: got[i], ok });
  }
  return { pass, lines };
}

/** Apply [from, to] literal rewrites to the student's source (case setup). */
export function applyRewrites(source, rewrites = []) {
  let result = source;
  for (const [from, to] of rewrites) {
    if (!result.includes(from)) {
      throw new Error(`This check expects the line \`${from}\` in your code so it can try a different starting value. Keep that line as given.`);
    }
    result = result.split(from).join(to);
  }
  return result;
}

/**
 * Run every case of a coding exercise. Each case: {name, inputs, expected,
 * rewrite, check}. A spec-level `check` (the body of a Java method that gets
 * the student's `source` and `stdout`) applies to every case.
 * Returns {pass, cases: [{name, pass, error, comparison, checkMessage, stdout, stderr, inputs}]}.
 */
export async function runCases(spec, source, files = []) {
  const cases = spec.cases?.length ? spec.cases : [{ name: "Program output", expected: spec.expected ?? "" }];
  const results = [];
  for (const testCase of cases) {
    const outcome = { name: testCase.name || "Case", pass: false, inputs: testCase.inputs ?? [] };
    try {
      const code = applyRewrites(source, testCase.rewrite);
      const project = buildProject(code, files);
      const check = [spec.check, testCase.check].filter(Boolean).join("\n\n") || null;
      const result = await runner.run({ files: project.files, entry: project.entry, inputs: outcome.inputs, echoInput: false, check });
      outcome.stdout = result.stdout;
      outcome.stderr = relocateMessages(result.stderr, project.studentFile, project.offset, project.files);
      outcome.studentFile = project.studentFile;
      outcome.offset = project.offset;
      if (result.status === "need-input") {
        outcome.error = "Your program asked for more input than this case provides.";
      } else if (result.status === "compile-error") {
        outcome.error = "Your program did not compile.";
      } else if (result.status === "error") {
        outcome.error = "Your program stopped with an error.";
      } else {
        if (testCase.expected != null) {
          outcome.comparison = compareOutput(testCase.expected, result.stdout);
        }
        if (result.check && !result.check.passed) outcome.checkMessage = result.check.message;
        outcome.pass = (outcome.comparison?.pass ?? true) && !outcome.checkMessage;
      }
    } catch (error) {
      outcome.error = error.message;
    }
    results.push(outcome);
  }
  return { pass: results.every((r) => r.pass), cases: results };
}

/** Normalize a typed answer for comparison with accepted answers. */
export function normalizeAnswer(text, { caseSensitive = false, preserveWhitespace = false } = {}) {
  let value = String(text ?? "").trim();
  if (!preserveWhitespace) value = value.replace(/\s+/g, " ");
  const classMatch = value.match(/^<class\s+['"]([^'"]+)['"]>$/i);
  if (classMatch) value = classMatch[1];
  if (!caseSensitive) value = value.toLowerCase();
  return value;
}

/** True if `answer` matches any of the accepted forms. */
export function matchAnswer(answer, accepted, options = {}) {
  const given = normalizeAnswer(answer, options);
  if (!given) return false;
  if (accepted.some((form) => normalizeAnswer(form, options) === given)) return true;
  // A code answer may differ from every listed form only in layout:
  // spacing, an extra semicolon, the lambda parameter's name, a flipped
  // comparison, or the order of the two sides of &&.
  if (options.preserveWhitespace) return false;
  return accepted.some((form) => looksLikeCode(form) && codeKey(answer, form, options) === codeKey(form, form, options));
}

const CODE_HINT = /[;{}\[\]]|->|::|&&|\|\||\+\+|--|[<>=!]=|\w\(/;
const TOKEN = /"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[A-Za-z_$][\w$]*|\d+(?:\.\d+)?|->|::|\+\+|--|&&|\|\||[<>=!+\-*\/%]=|\S/g;
const FLIP = { ">": "<", ">=": "<=" };

function looksLikeCode(form) {
  return CODE_HINT.test(String(form));
}

/** A layout-free key for a code answer, compared with the key of `form`. */
function codeKey(text, form, { caseSensitive = false } = {}) {
  let tokens = String(text ?? "").match(TOKEN) ?? [];
  if (tokens.at(-1) === ";" && !String(form).trim().endsWith(";")) tokens = tokens.slice(0, -1);
  if (!caseSensitive) tokens = tokens.map((t) => (t.startsWith('"') || t.startsWith("'") ? t : t.toLowerCase()));
  tokens = renameLambdaParameters(tokens);
  const parts = splitTopLevel(tokens, "&&").map(canonicalComparison);
  if (parts.length > 1 && !splitTopLevel(tokens, "||").slice(1).length) parts.sort();
  return parts.join(" && ");
}

/** `t -> t.x()` and `track -> track.x()` both become `$0 -> $0 . x ( )`. Brackets around the parameters stay. */
function renameLambdaParameters(tokens) {
  let names = [];
  let rest = null;
  let bracketed = false;
  if (tokens[1] === "->" && /^[A-Za-z_$]/.test(tokens[0])) {
    names = [tokens[0]];
    rest = tokens.slice(2);
  } else if (tokens[0] === "(") {
    const close = tokens.indexOf(")");
    const inside = tokens.slice(1, close);
    if (close > 0 && tokens[close + 1] === "->" && inside.every((t, i) => (i % 2 ? t === "," : /^[A-Za-z_$]/.test(t)))) {
      names = inside.filter((t, i) => i % 2 === 0);
      rest = tokens.slice(close + 2);
      bracketed = true;
    }
  }
  if (!rest) return tokens;
  const renamed = rest.map((t, i) => (names.includes(t) && rest[i - 1] !== "." ? `$${names.indexOf(t)}` : t));
  const params = names.map((_, i) => `$${i}`).join(" , ").split(" ");
  return [...(bracketed ? ["(", ...params, ")"] : params), "->", ...renamed];
}

/** Split at `op` outside brackets; returns token lists. */
function splitTopLevel(tokens, op) {
  const parts = [[]];
  let depth = 0;
  for (const t of tokens) {
    if ("([{".includes(t)) depth++;
    if (")]}".includes(t)) depth--;
    if (t === op && depth === 0) parts.push([]);
    else parts.at(-1).push(t);
  }
  return parts;
}

/** `a > b` becomes `b < a`, so both ways of writing a comparison agree. */
function canonicalComparison(tokens) {
  let depth = 0;
  let at = -1;
  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];
    if ("([{".includes(t)) depth++;
    if (")]}".includes(t)) depth--;
    if (depth === 0 && ["<", ">", "<=", ">="].includes(t)) {
      if (at >= 0) return tokens.join(" ");
      at = i;
    }
  }
  if (at <= 0 || !(tokens[at] in FLIP)) return tokens.join(" ");
  return [...tokens.slice(at + 1), FLIP[tokens[at]], ...tokens.slice(0, at)].join(" ");
}
