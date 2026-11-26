"""Build Lecture 21 exercises from the workbook.

Question N.M has the id qN-M; p1 and p2 are the two complete programs.
JavaFX cannot run in the browser, so this page has no code boxes: questions
are multiple choice, one fill-in table (5.4) and written answers compared with
the model answer. Multiple-choice options, the right option (marked \\correct)
and the explanation come from the workbook; model code comes from the
lecture's code folder. Every JavaFX claim the answers make was checked by
running the real windows (code/verify/MakeWorkbook21.java, 17 checks); the
String facts behind 5.5 and 5.7 are checked again here with plain Java.
"""
import base64, html, json, re, sys, pathlib, textwrap

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402

LECTURE = ROOT.parent / "output" / "L21_Chapter_17A_Building_A_GUI_v2"
CODE = LECTURE / "code"


def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()


def run(code, files=()):
    status, stdout, stderr, _ = run_java(code.rstrip("\n"), (), None, files)
    assert status == "ok", f"{status}\n{stderr}"
    return stdout.rstrip("\n")


def demo(name, body):
    lines = "\n".join("        " + line for line in body.strip("\n").splitlines())
    return f"public class {name}\n{{\n    public static void main(String[] args)\n    {{\n{lines}\n    }}\n}}\n"


def as_code(src):
    """Model code for a <wb-short> answer: each line in backticks, indented with en spaces.
    A blank line becomes a paragraph break, which the page shows as a small gap."""
    out = []
    for line in src.rstrip("\n").split("\n"):
        stripped = line.lstrip(" ")
        out.append("\u2002" * (len(line) - len(stripped)) + "`" + stripped + "`" if stripped else "")
    return "\n".join(out)


def lines_of(path, first=1, last=None):
    lines = (CODE / path).read_text().rstrip("\n").split("\n")
    return textwrap.dedent("\n".join(lines[first - 1:last]))


def short(answer, chars=20, rows=2, xp=2, placeholder=None):
    spec = {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}
    if placeholder:
        spec["placeholder"] = placeholder
    return spec


E = {}

# ------------------------------------------------ workbook
sys.path.insert(0, str(ROOT.parent / "scripts" / "web_l21"))
from workbook import QUESTION_RAW, QUESTION_SOURCE, inline, group  # noqa: E402

ID = {n: "q" + n.replace(".", "-") for n in QUESTION_SOURCE}
assert len(ID) == 45, len(ID)

CHOICES = re.compile(r"\\begin\{choices\}(.*?)\\end\{choices\}", re.S)
MCQS = [n for n in QUESTION_SOURCE if CHOICES.search(QUESTION_RAW[n])]
assert len(MCQS) == 24, MCQS


def solution(n):
    m = re.search(r"\\solution\{", QUESTION_RAW[n])
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", inline(group(QUESTION_RAW[n], m.end() - 1)[0]))
    return html.unescape(re.sub("<[^>]+>", "", text))


for n in MCQS:
    raw = QUESTION_RAW[n]
    opts = re.split(r"\\item\b", CHOICES.search(raw)[1])[1:]
    right = [i for i, o in enumerate(opts) if r"\correct" in o]
    assert len(opts) == 4 and len(right) == 1, n
    text = solution(n)
    head = f'{"ABCD"[right[0]]}. '
    assert text.startswith(head), (n, text[:40])
    E[ID[n]] = {"type": "choice", "xp": 1, "options": 4, "answer": right[0], "explain": b64(text[len(head):])}

# Written answers: the workbook's \solution text.
CODE_ANSWERS = {
    "3.1": lines_of("workbook/welcome/WelcomeWindow.java", 8, 16),
    "4.1": lines_of("workbook/bye/ByeHandler.java"),
    "4.2": "byeButton.setOnAction(new ByeHandler(message));",
    "5.1": lines_of("workbook/morning/MorningHandlerFirst.java", 17, 22),
    "5.2": lines_of("workbook/morning/MorningHandler.java", 17, 27),
    "6.2": lines_of("workbook/notes/SaveWindow.java", 20, 27),
    "7.2": lines_of("greeter/ClearHandler.java"),
}
assert "byeButton.setOnAction(new ByeHandler(message));" in lines_of("workbook/bye/ByeWindow.java")

TREE = as_code("""Scene
  VBox
    Label "New note"
    HBox
      TextField
      Button "Add"
    Label "0 notes\"""") + "\n\nThe VBox holds three children from top to bottom; the HBox holds the text field and the button side by side."

for n in QUESTION_SOURCE:
    if n in MCQS or n == "5.4":
        continue
    if n in CODE_ANSWERS:
        code = CODE_ANSWERS[n]
        E[ID[n]] = short(as_code(code), chars=30, rows=min(8, max(3, code.count("\n") + 2)), xp=3,
                         placeholder="Write your code here…")
    elif n == "6.1":
        E[ID[n]] = short(TREE, chars=30, rows=8, xp=3, placeholder="Write the tree, one object per line, indented under its parent…")
    elif n == "2.1":
        E[ID[n]] = short("The three steps are: wait for the next event; run the code for that event; redraw what changed. "
                         "The loop stops when the window is closed.", chars=30, rows=3)
    else:
        E[ID[n]] = short(solution(n), chars=20, rows=3)

# 5.4: the label after each action, from the workbook's table.
TABULAR = re.compile(r"\\begin\{tabular\}\{(?:[^{}]|\{[^}]*\})+\}(.*?)\\end\{tabular\}", re.S)
rows = [r for r in re.sub(r"\\(?:toprule|midrule|bottomrule)", "", TABULAR.search(QUESTION_RAW["5.4"])[1]).split(r"\\") if r.strip()][1:]
blanks = {}
for i, row in enumerate(rows):
    cell = row.split("&")[1].strip()
    value = re.sub(r"\\texttt\{(.*?)\}", r"\1", group(cell, len(r"\fillin"))[0])
    blanks[str(i)] = {"accept": [value, f'"{value}"'], "show": value, "caseSensitive": True,
                      "placeholder": "label text", "width": "17rem"}
assert [b["show"] for b in blanks.values()] == ["Hello, Ben!", "Please type your name first.",
                                               "Please type your name first.", "Hello, Cy!"]
E[ID["5.4"]] = {"type": "table", "xp": 2, "blanks": blanks}

# The two complete programs: the model code of all four classes.
def program(folder, names):
    return "\n\n".join(as_code((CODE / folder / f"{c}.java").read_text()) for c in names)


E["p1"] = short(program("workbook/programA", ["Counter", "AddHandler", "ResetHandler", "CounterApp"]),
                chars=200, rows=10, xp=6, placeholder="Paste your four classes here…")
E["p2"] = short(program("workbook/programB", ["ShoppingList", "AddItemHandler", "ClearListHandler", "ShoppingApp"]),
                chars=200, rows=10, xp=6, placeholder="Paste your four classes here…")

# 5.5 and 5.7 rest on String facts; check them with plain Java.
assert run(demo("Empty", 'String s = "";\nSystem.out.println(s.isEmpty() + " " + s.length());')) == "true 0"
assert run(demo("Spaces", 'String name = "  ";\nSystem.out.println(name.isEmpty());\nSystem.out.println("[" + "Hello, " + name + "!" + "]");')) == "false\n[Hello,   !]"
assert E["q5-5"]["answer"] == 1 and E["q5-7"]["answer"] == 1

assert len(E) == 47, len(E)
data = {"id": "lecture-21", "course": "COMP 2001: Object-Oriented Programming",
        "title": "Lecture 21 Workbook", "subtitle": "Chapter 17, Part 1: Building a GUI", "exercises": E}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {out} with {len(E)} specs")
