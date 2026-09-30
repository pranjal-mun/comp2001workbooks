#!/usr/bin/env python3
"""Verify a workbook's exercises.json against a real Java runtime.

    python3 tools/check_workbook.py workbooks/lecture-02

For every example with an `output`, compiles and runs its code and compares.
For every code exercise with a model `answer`, runs the answer through each
case (inputs, rewrite, expected, check) exactly as the browser grader does
and reports any case the model answer would fail. Exit status 1 on failure.

The code runs through the same workbook.Runner class the page uses in the
browser (runtime/java/workbook-runner.jar, compiled with the Eclipse compiler
in runtime/java/ecj.jar), on the desktop JVM. Needs `java` on the PATH.
"""
import base64
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLASS_PATH = [str(ROOT / "runtime" / "java" / "workbook-runner.jar"), str(ROOT / "runtime" / "java" / "ecj.jar")]
CHECK_CLASS = "WorkbookCheck"
SNIPPET_PREFIX = ["public class Main {", "    public static void main(String[] args) throws Exception {"]
SNIPPET_SUFFIX = ["    }", "}"]
RECORD = re.compile("\x00([a-z-]+)\x01(.*?)\x02", re.S)


def decode(text):
    return base64.b64decode("".join(text.split())).decode("utf-8")


def normalize(text):
    lines = [line.rstrip() for line in str(text or "").replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


# --- mirror of runtime/java.js ---------------------------------------------

def skeleton(code):
    code = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), code, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    code = re.sub(r'"(?:[^"\\\n]|\\.)*"', '""', code)
    code = re.sub(r"'(?:[^'\\\n]|\\.)*'", "''", code)
    return code


def is_snippet(code):
    return re.search(r"\b(class|interface|enum)\s+[A-Za-z_$][\w$]*", skeleton(code)) is None


def wrap_snippet(code):
    body = [("        " + line) if line else line for line in code.split("\n")]
    return "\n".join(SNIPPET_PREFIX + body + SNIPPET_SUFFIX)


def declared_types(code):
    text = skeleton(code)
    pattern = re.compile(r"\b((?:public|final|abstract|static|strictfp)\s+)*(class|interface|enum)\s+([A-Za-z_$][\w$]*)")
    found = list(pattern.finditer(text))
    types = []
    for index, match in enumerate(found):
        end = found[index + 1].start() if index + 1 < len(found) else len(text)
        types.append({
            "name": match.group(3),
            "public": "public" in match.group(0).split(),
            "main": re.search(r"\bstatic\s+void\s+main\s*\(", text[match.start():end]) is not None,
        })
    return types


def main_class_of(code, extra=()):
    types = declared_types(code)
    if not any(t["main"] for t in types):
        for f in extra:
            for t in declared_types(f["content"]):
                if t["main"]:
                    return t["name"]
    for pick in (lambda t: t["main"], lambda t: t["public"], lambda t: True):
        for t in types:
            if pick(t):
                return t["name"]
    return "Main"


def file_name_of(code):
    types = declared_types(code)
    for pick in (lambda t: t["public"], lambda t: t["main"], lambda t: True):
        for t in types:
            if pick(t):
                return t["name"] + ".java"
    return "Main.java"


def build_project(code, extra=()):
    source = wrap_snippet(code) if is_snippet(code) else code
    student_file = file_name_of(source)
    files = [(student_file, source)] + [(f["name"], f["content"]) for f in extra if f["name"] != student_file]
    return files, main_class_of(source, extra)


# --- mirror of runtime/java-worker.js -------------------------------------

def check_source(body):
    return "\n".join([
        "import java.util.*;",
        f"public class {CHECK_CLASS} {{",
        "    static void require(boolean ok, String message) { if (!ok) throw new AssertionError(message); }",
        "    public static void check(String source, String stdout) throws Exception {",
        body,
        "    }",
        "}",
    ])


def run(code, inputs=(), check=None, extra=()):
    """Compile and run through workbook.Runner. Returns (status, stdout, stderr, check_message)."""
    files, entry = build_project(code, extra)
    if check:
        files.append((CHECK_CLASS + ".java", check_source(check)))
    answers = list(inputs)
    with tempfile.TemporaryDirectory(prefix="workbook-") as folder:
        folder = pathlib.Path(folder)
        paths = []
        for name, content in files:
            (folder / name).write_text(content, encoding="utf-8")
            paths.append(str(folder / name))
        command = [
            "java", "-Dworkbook.desktop=true", "-cp", ":".join(CLASS_PATH), "workbook.Runner",
            "run1", entry, str(len(answers)),
            base64.b64encode("\n".join(answers).encode("utf-8")).decode("ascii"),
            "0", CHECK_CLASS if check else "-", str(folder / "run" / "run1"), *paths,
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
    channels = {}
    for channel, value in RECORD.findall(completed.stdout):
        channels[channel] = channels.get(channel, "") + value
    if completed.returncode != 0 and not channels:
        return "error", "", completed.stderr, None
    if channels.get("runner"):
        return "error", "", channels["runner"], None
    if channels.get("compile-result") != "success":
        return "compile-error", "", channels.get("compiler", "") + channels.get("compiler-error", ""), None
    result = channels.get("program-result")
    status = {"success": "ok", "need-input": "need-input"}.get(result, "error")
    stdout = channels.get("program", "")
    stderr = channels.get("program-error", "")
    message = None
    if check and status == "ok":
        verdict = channels.get("check-result", "The check did not run.")
        message = None if verdict == "pass" else verdict
    return status, stdout, stderr, message


def apply_rewrites(source, rewrites):
    for old, new in rewrites or []:
        if old not in source:
            raise ValueError(f"rewrite target not found: {old!r}")
        source = source.replace(old, new)
    return source


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    path = pathlib.Path(argv[0])
    if path.is_dir():
        path = path / "exercises.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    failures = 0
    checked = 0
    for eid, spec in data["exercises"].items():
        kind = spec.get("type")
        if kind == "example" and spec.get("output") is not None:
            checked += 1
            status, stdout, stderr, _ = run(spec["code"], extra=spec.get("files", ()))
            if status != "ok" or normalize(stdout) != normalize(spec["output"]):
                failures += 1
                print(f"FAIL example {eid}: status={status}\n--- expected\n{spec['output']}\n--- actual\n{stdout}{stderr}")
        elif kind == "code" and spec.get("answer"):
            answer = decode(spec["answer"])
            cases = spec.get("cases") or [{"name": "Program output", "expected": spec.get("expected", "")}]
            for case in cases:
                checked += 1
                try:
                    source = apply_rewrites(answer, case.get("rewrite"))
                except ValueError as error:
                    failures += 1
                    print(f"FAIL {eid} / {case.get('name')}: {error}")
                    continue
                check = "\n\n".join(filter(None, [spec.get("check"), case.get("check")])) or None
                status, stdout, stderr, message = run(source, case.get("inputs", ()), check, spec.get("files", ()))
                ok = status == "ok" and not message
                if ok and case.get("expected") is not None:
                    ok = normalize(stdout) == normalize(case["expected"])
                if not ok:
                    failures += 1
                    print(f"FAIL {eid} / {case.get('name')}: status={status} check={message!r}\n--- expected\n{case.get('expected')}\n--- actual\n{stdout}{stderr}")
    print(f"{checked} checks, {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
