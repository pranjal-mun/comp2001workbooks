// Web Worker that compiles and runs Java in the browser with CheerpJ (a Java
// 8 runtime compiled to WebAssembly) and the Eclipse Compiler for Java. The
// heavy lifting is done by workbook.Runner (tools/runner/workbook/Runner.java,
// shipped as java/workbook-runner.jar): it compiles the project with ECJ,
// runs the main class with scripted keyboard input, and runs the instructor's
// check. It reports back through the native emit function below.
//
// Messages in:  {type: "run", id, files: [{name, content}], entry, inputs,
//                echoInput, check}
// Messages out: {type: "ready"} once, {type: "fatal", error} if the runtime
//               cannot load, {type: "phase", id, phase: "running"} when the
//               program starts, and {type: "result", id, status, stdout,
//               stderr, check} for every run. status is one of ok, error,
//               compile-error, need-input.

"use strict";

importScripts("https://cjrtnc.leaningtech.com/4.3/loader.js");

const RUNTIME_DIRECTORY = new URL("./", self.location.href);
// CheerpJ mounts the web origin at /app, so the jars are addressed by URL path.
const JAVA_PATH = `/app${RUNTIME_DIRECTORY.pathname.replace(/\/+$/, "")}/java`;
const CLASS_PATH = `${JAVA_PATH}/workbook-runner.jar:${JAVA_PATH}/ecj.jar`;
const CHECK_CLASS = "WorkbookCheck";

let active = null;
const ready = initialize();

self.addEventListener("message", async (event) => {
  if (event.data?.type !== "run") return;
  const request = event.data;
  try {
    await ready;
    postMessage({ type: "result", id: request.id, ...(await run(request)) });
  } catch (error) {
    postMessage({ type: "result", id: request.id, status: "error", stdout: active?.stdout ?? "", stderr: `The Java runtime failed: ${error?.message ?? error}`, check: null });
  } finally {
    active = null;
  }
});

async function initialize() {
  try {
    await cheerpjInit({
      version: 8,
      status: "none",
      overrideDocumentBase: RUNTIME_DIRECTORY.href,
      natives: { Java_workbook_Runner_emitNative },
    });
    postMessage({ type: "ready" });
  } catch (error) {
    postMessage({ type: "fatal", error: `Could not load the Java runtime: ${error?.message ?? error}` });
    throw error;
  }
}

async function run(request) {
  const files = [...request.files];
  if (request.check) files.push({ name: `${CHECK_CLASS}.java`, content: checkSource(request.check) });
  const runId = `run${request.id}`;
  active = { id: request.id, stdout: "", stderr: "", compiler: "", compileResult: null, programResult: null, check: null, runner: "" };

  for (const file of files) {
    const path = `/str/${file.name}`;
    try { cheerpOSRemoveStringFile(path); } catch { /* nothing to remove on the first run */ }
    cheerpOSAddStringFile(path, file.content);
  }
  const answers = request.inputs ?? [];
  await cheerpjRunMain(
    "workbook.Runner",
    CLASS_PATH,
    runId,
    request.entry,
    String(answers.length),
    encodeBase64(answers.join("\n")),
    request.echoInput ? "1" : "0",
    request.check ? CHECK_CLASS : "-",
    `/files/workbook/${runId}`,
    ...files.map((file) => `/str/${file.name}`),
  );
  for (const file of files) {
    try { cheerpOSRemoveStringFile(`/str/${file.name}`); } catch { /* already gone */ }
  }

  const result = active;
  if (result.runner) return { status: "error", stdout: result.stdout, stderr: result.runner, check: null };
  if (result.compileResult !== "success") return { status: "compile-error", stdout: "", stderr: result.compiler, check: null };
  if (result.programResult === "need-input") return { status: "need-input", stdout: result.stdout, stderr: "", check: null };
  const status = result.programResult === "success" ? "ok" : "error";
  let check = null;
  if (status === "ok" && request.check) {
    check = result.check === "pass" ? { passed: true, message: "" } : { passed: false, message: result.check ?? "The check did not run." };
  }
  return { status, stdout: result.stdout, stderr: result.stderr, check };
}

// Called from Java (workbook.Runner.emit) for every piece of output.
function Java_workbook_Runner_emitNative(_library, channel, value) {
  if (!active) return;
  const text = String(value);
  switch (String(channel)) {
    case "program": active.stdout += text; break;
    case "program-error": active.stderr += text; break;
    case "compiler":
    case "compiler-error": active.compiler += text; break;
    case "compile-result":
      active.compileResult = text;
      if (text === "success") postMessage({ type: "phase", id: active.id, phase: "running" });
      break;
    case "program-result": active.programResult = text; break;
    case "check-result": active.check = text; break;
    case "runner": active.runner += text; break;
  }
}

// The spec's check is the body of a static method; the student's source and
// output are its parameters. Mirrored in tools/check_workbook.py.
function checkSource(body) {
  return [
    "import java.util.*;",
    `public class ${CHECK_CLASS} {`,
    "    static void require(boolean ok, String message) { if (!ok) throw new AssertionError(message); }",
    "    public static void check(String source, String stdout) throws Exception {",
    body,
    "    }",
    "}",
  ].join("\n");
}

function encodeBase64(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}
