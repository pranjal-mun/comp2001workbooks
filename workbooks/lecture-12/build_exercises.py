"""Build workbooks/lecture-12/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-12/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-12

The questions follow the printed Lecture 12 workbook, numbered 1.1 to 9.2,
and the model answers are the ones in the solutions edition. The page was
first published with the ids below; questions added later get new ids, so
the old ones keep their meaning:

    1.1 q1                  1.2 q2, q2-why
    2.1 q3                  2.2 q4          2.3 q5-output, q5-why
    2.4 q6-literal, q6      2.5 q2-5-output, q2-5-why (added Oct 22)
    3.1 q7      3.2 q8      3.3 q9          3.4 q10     3.5 q11, q11-why
    4.1 q12                 4.2 q13-output, q13      4.3 q4-3 (added Oct 22)
    5.1 q14                 5.2 q15-output, q15
    5.3 q16, q16-header     5.4 q17, q17-why
    6.1 q18-values, q18     6.2 q19-output, q19-why
    6.3 q20, q20-result, q20-why 6.4 q21-values, q21
    7.1 q22-output          7.2 q23, q23-why         7.3 q7-3 (added Oct 22)
    8.1 q24, q24-why        8.2 q25-output, q25, q25-demo
    9.1 q26                 9.2 q27

Section 7 has one runnable example, weeklog-demo. Section 10 has two
complete programs, one box per class (ids p1-* and p2-*).

A box that asks for part of a class starts from the rest of that class, and a
small driver class on its classpath (the `files` list) calls the student's
code and prints what comes back; the runner uses that main when the editor's
class has none. The WeekLog, SeatRow and program classes are read from the
lecture folder's code/ directory, so the page and the PDF use the same files.
"""
import base64, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402

CODE_DIR = ROOT.parent / "output" / "L12_Chapter_7A_Arrays_For_Loop_v3" / "code"


def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()


def run(code, files=(), inputs=()):
    status, stdout, stderr, _ = run_java(code.rstrip("\n"), inputs, None, files)
    assert status == "ok", f"{status}\n{stderr}"
    return stdout.rstrip("\n")


def compiles(code, files=()):
    """True when the code compiles (it may still throw when it runs)."""
    status, stdout, stderr, message = run_java(code.rstrip("\n"), (), None, files)
    return status != "compile-error"


def throws(code, exception, files=()):
    status, stdout, stderr, message = run_java(code.rstrip("\n"), (), None, files)
    return status != "ok" and exception in (stdout or "") + (stderr or "") + (message or "")


def has(fragment, message):
    """A check line: the source contains `fragment`, ignoring whitespace."""
    compact = re.sub(r"\s+", "", fragment)
    return f'require(source.replaceAll("\\\\s+", "").contains({json.dumps(compact)}), {json.dumps(message)});'


def lacks(fragment, message):
    compact = re.sub(r"\s+", "", fragment)
    return f'require(!source.replaceAll("\\\\s+", "").contains({json.dumps(compact)}), {json.dumps(message)});'


def matches(regex, message):
    """A check line: the whitespace-stripped source matches `regex` (a Java regex, whole string)."""
    return f'require(source.replaceAll("\\\\s+", "").matches({json.dumps("(?s)" + regex)}), {json.dumps(message)});'


def file(name, content):
    return {"name": name, "content": content.rstrip("\n")}


def driver(name, body):
    """A hidden class whose main method exercises the student's class."""
    lines = "\n".join("        " + line if line else "" for line in body.strip("\n").splitlines())
    return [file(f"{name}.java", f"public class {name}\n{{\n    public static void main(String[] args)\n    {{\n{lines}\n    }}\n}}\n")]


def demo(name, body, imports=""):
    """A class whose main method holds `body`."""
    lines = "\n".join("        " + line if line else "" for line in body.strip("\n").splitlines())
    return f"{imports}{chr(10) if imports else ''}public class {name}\n{{\n    public static void main(String[] args)\n    {{\n{lines}\n    }}\n}}\n"


def code_forms(*forms, semicolon=True):
    """Accepted forms of a code blank: as written, without spaces around punctuation, and with or without a final semicolon.

    The page collapses runs of spaces to one but keeps them, so `names=new String[4]`
    needs its own form; the space in `new String` stays.
    """
    out = []
    for form in forms:
        for f in (form, form.rstrip(";") if form.endswith(";") else form + ";") if semicolon else (form,):
            for g in (f, re.sub(r"\s*([=;,()\[\]{}<>+\-*/!&|])\s*", r"\1", f)):
                if g not in out:
                    out.append(g)
    return out


def box(starter, answer, extra=12):
    """Editor height: the starter's lines plus room to write."""
    n = max(starter.count("\n"), answer.count("\n")) + 2
    return {"minLines": n, "maxLines": n + extra}


def code_box(eid, title, starter, answer, files, checks, xp=4, extra=12, name="Output of the checking program"):
    """A code exercise whose expected output comes from running the model answer."""
    E[eid] = {"type": "code", "xp": xp, "title": title, **box(starter, answer, extra),
              "starter": starter.rstrip("\n"),
              "cases": [{"name": name, "expected": run(answer, files)}],
              "check": "\n".join(checks),
              "answer": b64(answer), "files": list(files)}
    return E[eid]["cases"][0]["expected"]


def read(path):
    return (CODE_DIR / path).read_text()


def strip_docs(src):
    """The class without its Javadoc comments, as the boxes show it."""
    src = re.sub(r"\A/\*\*.*?\*/\n", "", src, flags=re.S)
    return re.sub(r"\n[ \t]*/\*\*.*?\*/", "", src, flags=re.S)


def without_method(src, header):
    """src with one method (from its header to the closing brace at 4 spaces) removed."""
    start = src.index("    " + header)
    end = src.index("\n    }\n", start) + len("\n    }\n")
    return src[:start].rstrip("\n") + "\n" + src[end:].lstrip("\n") if src[end:].strip() != "}" else src[:start].rstrip("\n") + "\n}\n"


def add_before_end(src, text):
    """src with `text` added just before the class's closing brace."""
    return src.rstrip().rstrip("}").rstrip("\n") + "\n\n" + text.rstrip("\n") + "\n}\n"


def lines_table(eid, output, xp=2, width="20rem", alts=None):
    """A table with one blank per printed line, named 0, 1, 2, ..."""
    blanks = {}
    for i, line in enumerate(output.split("\n")):
        accept = [line] + ([f'"{line}"'] if not re.fullmatch(r"-?\d+|true|false|null", line) else [])
        accept += (alts or {}).get(i, [])
        blanks[str(i)] = {"accept": accept, "show": line, "caseSensitive": True, "placeholder": "printed", "width": width}
    E[eid] = {"type": "table", "xp": xp, "blanks": blanks}


def num(value):
    return {"accept": [str(value)], **NUM}


SHORT = lambda answer, chars=20, rows=2, xp=2: {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}  # noqa: E731
CODE = {"caseSensitive": True, "width": "26rem"}
NUM = {"placeholder": "number", "width": "7rem"}
YES = {"accept": ["yes", "Yes", "yes.", "compiles", "it compiles"], "show": "yes", "placeholder": "yes / no", "width": "8rem"}
NO = {"accept": ["no", "No", "no.", "does not compile", "it does not compile"], "show": "no", "placeholder": "yes / no", "width": "8rem"}
STOPS = {"accept": ["yes", "Yes", "yes.", "throws", "it throws"], "show": "yes", "placeholder": "yes / no", "width": "8rem"}
RUNS = {"accept": ["no", "No", "no.", "runs", "it runs"], "show": "no", "placeholder": "yes / no", "width": "8rem"}
E = {}

# ---------------------------------------------------------------- classes
WEEKLOG = strip_docs(read("weeklog/WeekLog.java"))
assert "/**" not in WEEKLOG and WEEKLOG.startswith("public class WeekLog")
WEEK_FILE = [file("WeekLog.java", WEEKLOG)]
WEEK = [45, 0, 90, 30, 0, 120, 60]
RECORD_WEEK = "".join(f"week.record({d}, {m});\n" for d, m in enumerate(WEEK) if m)
WEEK_ARRAY = "int[] minutes = {45, 0, 90, 30, 0, 120, 60};\n"

WEEK_DEMO = read("weeklog/WeekLogDemo.java")
WEEK_DEMO_OUT = run(WEEK_DEMO, WEEK_FILE)
assert WEEK_DEMO_OUT == ("No such day: 7\nMonday: 45\nTuesday: 0\nWednesday: 90\nThursday: 30\nFriday: 0\n"
                         "Saturday: 120\nSunday: 60\nTotal: 345\nDays studied: 5\nBusiest: Saturday (120)"), WEEK_DEMO_OUT

SEATS_1 = strip_docs(read("seats/part1/SeatRow.java"))
SEATS_2 = strip_docs(read("seats/part2/SeatRow.java"))
assert "countFree" not in SEATS_1 and "firstFree" in SEATS_2

# ---------------------------------------------------------------- 1. Fixed size
E["q1"] = SHORT("(a) An array of 24: a day always has 24 hours. (b) An ArrayList: students join and leave, so the number changes. (c) An array of 5: the number of assignments is known when the course starts and does not change.", rows=3)
DECLS = {"a": "ArrayList<int> a;", "b": "ArrayList<Integer> b;", "c": "int[] c;", "d": "Integer[] d;"}
for key, decl in DECLS.items():
    ok = compiles(demo("Decl", decl, "import java.util.ArrayList;\n"))
    assert ok == (key != "a"), (key, ok)
E["q2"] = {"type": "table", "xp": 2, "blanks": {"a": NO, "b": YES, "c": YES, "d": YES}}
E["q2-why"] = SHORT("A type argument of ArrayList must be a class, and int is a primitive type. An array can have a primitive base type, as in int[], or a class, as in Integer[].", rows=2)

# ---------------------------------------------------------------- 2. Creation
assert compiles(demo("Make", "double[] rainfall = new double[12];\nString[] names;\nnames = new String[4];\nSystem.out.println(rainfall.length + names.length);"))
E["q3"] = {"type": "table", "xp": 2, "blanks": {
    "a": {"accept": code_forms("double[] rainfall = new double[12];"), "show": "double[] rainfall = new double[12];", **CODE},
    "b": {"accept": code_forms("names = new String[4];", "this.names = new String[4];"), "show": "names = new String[4];", **CODE}}}
for wrong in ("int[] a = new int(7);", "int[] b = new int[];", "int[] c;  c = {1, 2, 3};"):
    assert not compiles(demo("Wrong", wrong)), wrong
assert compiles(demo("Right", "int[] a = new int[7];\nint[] b = new int[5];\nint[] c = {1, 2, 3};\nint[] d;\nd = new int[] {1, 2, 3};"))
E["q4"] = SHORT("The size goes in square brackets: new int[7]. A new array needs a size: new int[5], for example. The short literal form works only in a declaration: int[] c = {1, 2, 3}; or c = new int[] {1, 2, 3};", rows=3)
DEFAULTS = "int[] counts = new int[3];\nboolean[] open = new boolean[2];\nString[] names = new String[2];\nSystem.out.println(counts[2]);\nSystem.out.println(open[1]);\nSystem.out.println(names[0]);\n"
Q5 = run(demo("Defaults", DEFAULTS))
assert Q5 == "0\nfalse\nnull", Q5
assert throws(demo("Defaults", DEFAULTS + "System.out.println(names[0].length());"), "NullPointerException")
lines_table("q5-output", Q5, width="8rem")
E["q5-why"] = SHORT("0, false and null are the default values. The last line calls length() through null, so the program stops with a NullPointerException.", rows=2)
MONTHS = "int[] monthDays = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};"
Q6 = run(demo("Months", MONTHS + "\nSystem.out.println(monthDays.length);\nSystem.out.println(monthDays[1]);\nSystem.out.println(monthDays[monthDays.length - 1]);"))
assert Q6 == "12\n28\n31", Q6
E["q6-literal"] = {"type": "table", "xp": 2, "blanks": {"literal": {"accept": code_forms(MONTHS, MONTHS.replace(", ", ",")), "show": MONTHS, **CODE, "width": "34rem"}}}
E["q6"] = {"type": "table", "xp": 3, "blanks": {k: num(v) for k, v in zip(("length", "feb", "last"), Q6.split("\n"))}}
Q2_5 = run(demo("TwoNames", 'int[] a = {1, 2, 3};\nint[] b = a;\nb[1] = 20;\na = new int[3];\nSystem.out.println(b[1] + " " + a[1]);'))
assert Q2_5 == "20 0", Q2_5
lines_table("q2-5-output", Q2_5, width="8rem")
E["q2-5-why"] = SHORT("b = a copies the reference, so b[1] = 20 changes the one array, which is now 1, 20, 3. Then a is given a new array of three zeros; b still refers to the first array.", rows=2)

# ---------------------------------------------------------------- 3. Positions
Q7 = run(demo("Readings", "int[] readings = new int[24];\nSystem.out.println(0);\nSystem.out.println(readings.length - 1);"))
assert Q7 == "0\n23"
E["q7"] = {"type": "table", "xp": 2, "blanks": {"first": num(0), "last": num(23),
    "expr": {"accept": code_forms("readings.length - 1", semicolon=False), "show": "readings.length - 1", **CODE, "width": "14rem"}}}
ACCESSES = ["a[0]", "a[5]", "a[a.length - 1]", "a[-1]", "a[a.length]", "a[2 + 2]"]
q8 = {}
for i, access in enumerate(ACCESSES):
    code = demo("Access", f"int[] a = new int[5];\nSystem.out.println({access});")
    assert compiles(code), access
    stops = throws(code, "ArrayIndexOutOfBoundsException")
    assert stops == (access in ("a[5]", "a[-1]", "a[a.length]")), access
    q8[f"c{i}"] = YES
    q8[f"s{i}"] = STOPS if stops else RUNS
E["q8"] = {"type": "table", "xp": 1, "blanks": q8}
Q9 = run(demo("Trace", "int[] a = new int[4];\na[1] = 3;\na[2] = a[1] * 2;\na[3] += a[2];\na[0] = a[3] - a[1];\nfor(int x : a) {\n    System.out.println(x);\n}"))
assert Q9 == "3\n3\n6\n6", Q9
E["q9"] = {"type": "table", "xp": 2, "blanks": {str(i): num(v) for i, v in enumerate(Q9.split("\n"))}}
LENGTHS = [("minutes.size()", "minutes.length"), ("name.length", "name.length()"), ("minutes.length", "minutes.length"), ("list.length()", "list.size()")]
SETUP = 'String name = "Ada";\nArrayList<String> list = new ArrayList<>();\nint[] minutes = new int[7];\n'
q10 = {}
for i, (expr, fixed) in enumerate(LENGTHS):
    ok = compiles(demo("Len", SETUP + f"System.out.println({expr});", "import java.util.ArrayList;\n"))
    assert ok == (expr == fixed), expr
    assert compiles(demo("Len", SETUP + f"System.out.println({fixed});", "import java.util.ArrayList;\n")), fixed
    q10[f"c{i}"] = YES if ok else NO
    accept = code_forms(fixed, semicolon=False) + (["correct", "already correct", "no change", "-"] if ok else [])
    q10[f"f{i}"] = {"accept": accept, "show": fixed, **CODE, "width": "12rem"}
E["q10"] = {"type": "table", "xp": 1, "blanks": q10}
assert run(demo("Names", 'System.out.println(WeekLog.dayName(5));'), WEEK_FILE) == "Saturday"
assert throws(demo("Names", 'System.out.println(WeekLog.dayName(7));'), "ArrayIndexOutOfBoundsException", WEEK_FILE)
E["q11"] = {"type": "table", "xp": 2, "blanks": {"five": {"accept": ['"Saturday"', "Saturday"], "show": '"Saturday"', "caseSensitive": True, "width": "10rem"}}}
E["q11-why"] = SHORT("dayName does not check its parameter, so DAY_NAMES[7] throws an ArrayIndexOutOfBoundsException.", rows=2)

# ---------------------------------------------------------------- 4. Seats Part 1
SEAT_SIZE = '''public class SeatRow
{
    private boolean[] booked;

    public SeatRow(int size)
    {
        booked = new boolean[size];
    }

    public int getSize()
    {
        return booked.length;
    }
}
'''
assert without_method(without_method(SEATS_1, "public boolean isBooked(int seat)"), "public boolean book(int seat)") == SEAT_SIZE
Q12_STARTER = '''public class SeatRow
{
    // The field goes here.

    public SeatRow(int size)
    {
        // Create the array, one element for each seat.
    }

    public int getSize()
    {
        // The number of seats.
        return 0;
    }
}
'''
assert code_box("q12", "SeatRow.java", Q12_STARTER, SEAT_SIZE, driver("SizeCheck", "System.out.println(new SeatRow(10).getSize());\nSystem.out.println(new SeatRow(0).getSize());"), [
    has("private boolean[] booked;", "Declare the field private boolean[] booked;"),
    has("booked = new boolean[size];", "Create the array in the constructor: booked = new boolean[size];"),
    has("return booked.length;", "getSize returns booked.length.")], xp=3, extra=4) == "10\n0"

SEAT_DEMO_1 = read("seats/part1/SeatDemo.java")
Q13 = run(SEAT_DEMO_1, [file("SeatRow.java", SEATS_1)])
assert Q13 == "Seats: 10\nBook 3: true\nBook 3 again: false\nBook 10: false\nSeat 3 booked: true\nSeat 4 booked: false", Q13
lines_table("q13-output", Q13, xp=3, width="16rem")
Q13_STARTER = SEAT_SIZE.rstrip().rstrip("}") + "\n    // Write isBooked and book here.\n\n\n}\n"
assert code_box("q13", "SeatRow.java", Q13_STARTER, SEATS_1, driver("BookCheck", '''SeatRow row = new SeatRow(5);
System.out.println("Book -1: " + row.book(-1));
System.out.println("Book 0: " + row.book(0));
System.out.println("Book 0 again: " + row.book(0));
System.out.println("Book 4: " + row.book(4));
System.out.println("Book 5: " + row.book(5));
System.out.println("Seat 0 booked: " + row.isBooked(0));
System.out.println("Seat 1 booked: " + row.isBooked(1));'''), [
    has("public boolean isBooked(int seat)", "Include public boolean isBooked(int seat)."),
    has("public boolean book(int seat)", "Include public boolean book(int seat)."),
    has("booked[seat] = true;", "Book the seat with booked[seat] = true;")], xp=5) == (
    "Book -1: false\nBook 0: true\nBook 0 again: false\nBook 4: true\nBook 5: false\nSeat 0 booked: true\nSeat 1 booked: false")

assert compiles("public class Theatre\n{\n    private double price;\n\n    public int countBooked(int from, int to)\n    {\n        return to - from;\n    }\n}\n")
E["q4-3"] = {"type": "table", "xp": 2, "blanks": {
    "a": {"accept": code_forms("private double price;"), "show": "private double price;", **CODE},
    "b": {"accept": code_forms("public int countBooked(int from, int to)", semicolon=False), "show": "public int countBooked(int from, int to)", **CODE}}}

# ---------------------------------------------------------------- 5. For loops
Q14 = run(demo("Passes", "SeatRow row = new SeatRow(10);\nint passes = 0;\nfor(int seat = row.getSize() - 1; seat >= 0; seat--) {\n    System.out.println(seat);\n    passes++;\n}\nSystem.out.println(passes);"), [file("SeatRow.java", SEATS_1)]).split("\n")
assert (Q14[0], Q14[-2], Q14[-1]) == ("9", "0", "10"), Q14
E["q14"] = {"type": "table", "xp": 1, "blanks": {
    "init": {"accept": code_forms("int seat = row.getSize() - 1", semicolon=False), "show": "int seat = row.getSize() - 1", **CODE, "width": "18rem"},
    "cond": {"accept": code_forms("seat >= 0", semicolon=False), "show": "seat >= 0", **CODE, "width": "10rem"},
    "upd": {"accept": code_forms("seat--", "seat -= 1", "seat = seat - 1", "--seat", semicolon=False), "show": "seat--", **CODE, "width": "10rem"},
    "first": num(Q14[0]), "last": num(Q14[-2]), "passes": num(Q14[-1])}}
SQUARES_FOR = 'for(int i = 1; i <= 5; i++) {\n    System.out.print(i * i + " ");\n}'
SQUARES_WHILE = 'int i = 1;\nwhile(i <= 5) {\n    System.out.print(i * i + " ");\n    i++;\n}'
Q15 = run(demo("Squares", SQUARES_FOR))
assert Q15.rstrip() == "1 4 9 16 25", Q15
E["q15-output"] = {"type": "table", "xp": 2, "blanks": {"0": {"accept": ["1 4 9 16 25", "1 4 9 16 25 ", "1, 4, 9, 16, 25"], "show": "1 4 9 16 25", "placeholder": "printed", "width": "14rem"}}}
assert code_box("q15", "Squares.java", demo("Squares", SQUARES_FOR), demo("Squares", SQUARES_WHILE), [], [
    lacks("for(", "Rewrite the loop with while; no for is left."),
    has("while(", "Use a while loop."),
    has("i++", "Update i inside the body, as the last statement.")], xp=3, extra=4, name="Program output") == Q15
BUGGY = WEEK_ARRAY + "int sum = 0;\nfor(int day = 1; day <= minutes.length; day++) {\n    sum += minutes[day];\n}\nSystem.out.println(sum);"
assert throws(demo("Bug", BUGGY), "ArrayIndexOutOfBoundsException")
assert run(demo("Fixed", WEEK_ARRAY + "int sum = 0;\nfor(int day = 0; day < minutes.length; day++) {\n    sum += minutes[day];\n}\nSystem.out.println(sum);")) == "345"
E["q16"] = SHORT("It starts at day 1, so Monday's 45 is never added, and the test <= lets day reach 7, so minutes[7] throws an ArrayIndexOutOfBoundsException after days 1 to 6 have been added.", rows=2)
HEADER = "for(int day = 0; day < minutes.length; day++)"
E["q16-header"] = {"type": "table", "xp": 2, "blanks": {"header": {"accept": code_forms(HEADER, HEADER.replace("for(", "for ("), HEADER + " {", HEADER.replace("for(", "for (") + " {", semicolon=False), "show": HEADER, **CODE, "width": "30rem"}}}
Q17 = run(demo("Steps", WEEK_ARRAY + "int sum = 0;\nfor(int i = 0; i < 6; i += 2) {\n    sum += minutes[i];\n    System.out.println(i + \" \" + sum);\n}"))
assert Q17 == "0 45\n2 135\n4 135", Q17
E["q17"] = {"type": "table", "xp": 1, "blanks": {**{f"i{k}": num(row.split()[0]) for k, row in enumerate(Q17.split("\n"))},
                                                 **{f"s{k}": num(row.split()[1]) for k, row in enumerate(Q17.split("\n"))}}}
E["q17-why"] = SHORT("After the third pass, i becomes 6 and 6 < 6 is false. Days 0, 2 and 4 were added: 45 + 90 + 0 = 135.", rows=2)

# ---------------------------------------------------------------- 6. Reports
DAYS_OVER = "    public int daysOver(int limit)\n    {\n        int count = 0;\n        for(int mins : minutes) {\n            if(mins > limit) {\n                count++;\n            }\n        }\n        return count;\n    }\n"
Q18_OUT = code_box("q18", "WeekLog.java", add_before_end(WEEKLOG, "    // Write daysOver(int limit) here."), add_before_end(WEEKLOG, DAYS_OVER),
                   driver("OverCheck", "WeekLog week = new WeekLog();\n" + RECORD_WEEK + "System.out.println(week.daysOver(60));\nSystem.out.println(week.daysOver(0));\nSystem.out.println(week.daysOver(200));\nSystem.out.println(new WeekLog().daysOver(0));"), [
    has("public int daysOver(int limit)", "Include public int daysOver(int limit)."),
    has("> limit", "Count the days with more than limit minutes: mins > limit.")], xp=4, extra=8)
assert Q18_OUT == "2\n5\n0\n0", Q18_OUT
E["q18-values"] = {"type": "table", "xp": 2, "blanks": {"sixty": num(2), "zero": num(5)}}
Q19 = run(demo("Copies", WEEK_ARRAY + "int total = 0;\nfor(int mins : minutes) {\n    mins += 10;\n    total += mins;\n}\nSystem.out.println(total);\nSystem.out.println(minutes[1]);"))
assert Q19 == "415\n0", Q19
lines_table("q19-output", Q19, width="8rem")
E["q19-why"] = SHORT("mins holds a copy of each element. Each copy is 10 more than its element, so the total is 345 + 70, but the array itself does not change, so Tuesday is still 0.", rows=2)
TRACE = "int[] minutes = {30, 60, 60, 0, 90, 90, 10};\nint best = 0;\nfor(int day = 1; day < minutes.length; day++) {\n    if(minutes[day] OP minutes[best]) {\n        best = day;\n    }\n    System.out.println(best);\n}"
Q20 = run(demo("Busy", TRACE.replace("OP", ">"))).split("\n")
Q20GE = run(demo("Busy", TRACE.replace("OP", ">="))).split("\n")
assert Q20 == ["1", "1", "1", "4", "4", "4"] and Q20GE[-1] == "5", (Q20, Q20GE)
E["q20"] = {"type": "table", "xp": 1, "blanks": {f"b{i + 1}": num(v) for i, v in enumerate(Q20)}}
E["q20-result"] = {"type": "table", "xp": 2, "blanks": {"gt": num(Q20[-1]), "ge": num(Q20GE[-1])}}
E["q20-why"] = SHORT("busiestDay always returns a day from 0 to 6, so dayName never gets a bad index.", rows=2)
QUIETEST = "    public int quietestStudiedDay()\n    {\n        int best = -1;\n        for(int day = 0; day < minutes.length; day++) {\n            if(minutes[day] > 0) {\n                if(best == -1 || minutes[day] < minutes[best]) {\n                    best = day;\n                }\n            }\n        }\n        return best;\n    }\n"
Q21_OUT = code_box("q21", "WeekLog.java", add_before_end(WEEKLOG, "    // Write quietestStudiedDay() here."), add_before_end(WEEKLOG, QUIETEST),
                   driver("QuietCheck", "WeekLog week = new WeekLog();\n" + RECORD_WEEK + "System.out.println(week.quietestStudiedDay());\nSystem.out.println(new WeekLog().quietestStudiedDay());\nWeekLog two = new WeekLog();\ntwo.record(2, 50);\ntwo.record(4, 50);\nSystem.out.println(two.quietestStudiedDay());"), [
    has("public int quietestStudiedDay()", "Include public int quietestStudiedDay()."),
    has("-1", "Start with no best day, -1, and return it when no day has any study.")], xp=5, extra=8)
assert Q21_OUT == "3\n-1\n2", Q21_OUT
E["q21-values"] = {"type": "table", "xp": 2, "blanks": {"week": num(3), "empty": num(-1)}}

# ---------------------------------------------------------------- 7. One week
E["weeklog-demo"] = {"type": "example", "title": "WeekLogDemo.java", "code": WEEK_DEMO.rstrip("\n"), "output": WEEK_DEMO_OUT,
                     "files": WEEK_FILE, "maxLines": 30}
SECOND = demo("SecondWeekDemo", '''WeekLog week = new WeekLog();
week.record(1, 30);
week.record(1, 60);
week.record(4, 60);
week.record(-1, 20);
week.record(6, 15);
week.printWeek();
System.out.println("Total: " + week.total());
System.out.println("Days studied: " + week.daysStudied());
int best = week.busiestDay();
System.out.println("Busiest: " + WeekLog.dayName(best)
    + " (" + week.getMinutes(best) + ")");''')
Q22 = run(SECOND, WEEK_FILE)
assert Q22 == ("No such day: -1\nMonday: 0\nTuesday: 60\nWednesday: 0\nThursday: 0\nFriday: 60\nSaturday: 0\n"
               "Sunday: 15\nTotal: 135\nDays studied: 3\nBusiest: Tuesday (60)"), Q22
lines_table("q22-output", Q22, xp=4, width="16rem")
FOREACH = {"accept": ["for-each", "For-each", "for each", "For each", "foreach", "enhanced for"], "show": "for-each", "placeholder": "loop", "width": "9rem"}
FOR = {"accept": ["for", "For", "for loop", "a for loop"], "show": "for", "placeholder": "loop", "width": "9rem"}
WHILE = {"accept": ["while", "While", "while loop", "a while loop"], "show": "while", "placeholder": "loop", "width": "9rem"}
E["q23"] = {"type": "table", "xp": 1, "blanks": {"a": FOREACH, "b": FOR, "c": FOR, "d": WHILE}}
E["q23-why"] = SHORT("(a) for-each: every reading is added and its hour does not matter. (b) for: the seat number is printed, so the index is needed. (c) for: changing an element needs its index. (d) while: the loop runs until a condition on the number is false; it does not count through an array, and the number of passes is not obvious when the loop starts.", rows=3)

E["q7-3"] = SHORT("DAY_NAMES and dayName are static; the class diagram underlines them. dayName is a class method, so the demo calls it on the class, WeekLog.dayName(best), not on the object week.", rows=3)

# ---------------------------------------------------------------- 8. Seats Part 2
COUNT_FREE = SEATS_2[SEATS_2.index("    public int countFree()"):SEATS_2.index("    public int firstFree()")].rstrip("\n") + "\n"
SEATS_COUNT = add_before_end(SEATS_1, COUNT_FREE)
assert code_box("q24", "SeatRow.java", add_before_end(SEATS_1, "    // Write countFree() here, with a for-each loop."), SEATS_COUNT,
                driver("FreeCheck", "SeatRow row = new SeatRow(4);\nSystem.out.println(row.countFree());\nrow.book(1);\nrow.book(3);\nSystem.out.println(row.countFree());"), [
    has("public int countFree()", "Include public int countFree()."),
    matches(r".*for\(boolean\w+:booked\).*", "Visit the seats with a for-each loop: for(boolean taken : booked).")], xp=4, extra=8) == "4\n2"
E["q24-why"] = SHORT("Every seat is checked, and the answer is a count, so the seat numbers are not needed.", rows=2)
SEAT_DEMO_2 = read("seats/part2/SeatDemo.java")
Q25 = run(SEAT_DEMO_2, [file("SeatRow.java", SEATS_2)])
assert Q25 == "Free: 10\nFree: 7\nFirst free: 2\nFree: 0\nFirst free: -1", Q25
lines_table("q25-output", Q25, xp=3, width="14rem")
assert code_box("q25", "SeatRow.java", add_before_end(SEATS_COUNT, "    // Write firstFree() here, with a for loop."), SEATS_2,
                driver("FirstCheck", "SeatRow row = new SeatRow(3);\nSystem.out.println(row.firstFree());\nrow.book(0);\nSystem.out.println(row.firstFree());\nrow.book(1);\nrow.book(2);\nSystem.out.println(row.firstFree());"), [
    has("public int firstFree()", "Include public int firstFree()."),
    has("for(int", "Visit the seats by number with a for loop."),
    has("return -1;", "Return -1 after the loop, when no seat is free.")], xp=4, extra=8) == "0\n1\n-1"
Q25_DEMO_STARTER = demo("SeatDemo", "SeatRow row = new SeatRow(10);\n// 1. Print the free count, as \"Free: 10\".\n// 2. Book seats 0, 1 and 3; print the free count and the first free seat, as \"First free: 2\".\n// 3. Book every seat with a for loop; print both again.\n")
assert code_box("q25-demo", "SeatDemo.java", Q25_DEMO_STARTER, SEAT_DEMO_2, [file("SeatRow.java", SEATS_2)], [
    has("row.countFree()", "Print the free count with row.countFree()."),
    has("row.firstFree()", "Print the first free seat with row.firstFree()."),
    has("for(int", "Book every seat with a for loop.")], xp=3, extra=8, name="Program output") == Q25

# ---------------------------------------------------------------- 9. Review
E["q26"] = SHORT("(a) The indices are 0 to 6. (b) It holds seven zeros, the default value of int. (c) length is a field: minutes.length, with no round brackets. (d) The variable holds a copy; changing an element needs an index. (e) final fixes the reference; the elements can still change.", rows=5)
FOUR = "WeekLog ada = new WeekLog();\nWeekLog bo = new WeekLog();\nWeekLog chen = new WeekLog();\nWeekLog dev = new WeekLog();\nSystem.out.println(ada.total() + bo.total() + chen.total() + dev.total());"
assert run(demo("Four", FOUR), WEEK_FILE) == "0"
E["q27"] = SHORT(FOUR + "\nFor 40 students: 40 variables and a sum of 40 calls. Nothing ties the logs into one collection that a loop could visit. Lecture 13 does that with an array whose elements are WeekLog objects.", rows=5)

# ---------------------------------------------------------------- 10. Programs
TEMP = strip_docs(read("programA/TemperatureLog.java"))
TEMP_DEMO = read("programA/TemperatureDemo.java")
TEMP_FILE = [file("TemperatureLog.java", TEMP)]
TEMP_OUT = run(TEMP_DEMO, TEMP_FILE)
assert TEMP_OUT == "Bad hour stored: false\nAverage: 4\nWarmest hour: 14\nHours below zero: 2", TEMP_OUT
TEMP_STARTER = '''public class TemperatureLog
{
    public static final int HOURS = 24;
    private int[] readings;

    public TemperatureLog()
    {
        // Create the array with HOURS elements.
    }

    public boolean record(int hour, int degrees)
    {
        // Refuse a bad hour; otherwise store.
        return false;
    }

    public int average()
    {
        // for-each: add up, then divide.
        return 0;
    }

    public int warmestHour()
    {
        // for: keep the index of the best.
        return 0;
    }

    public int hoursBelowZero()
    {
        // for-each: count readings below 0.
        return 0;
    }
}
'''
assert code_box("p1-log", "TemperatureLog.java", TEMP_STARTER, TEMP, driver("LogCheck", '''System.out.println("Hours: " + TemperatureLog.HOURS);
TemperatureLog flat = new TemperatureLog();
System.out.println("Average: " + flat.average());
System.out.println("Warmest: " + flat.warmestHour());
System.out.println("Below zero: " + flat.hoursBelowZero());
TemperatureLog day = new TemperatureLog();
System.out.println(day.record(0, -4));
System.out.println(day.record(3, 6));
System.out.println(day.record(7, 6));
System.out.println(day.record(23, -2));
System.out.println(day.record(-1, 9));
System.out.println(day.record(24, 9));
System.out.println("Average: " + day.average());
System.out.println("Warmest: " + day.warmestHour());
System.out.println("Below zero: " + day.hoursBelowZero());'''), [
    has("new int[HOURS]", "Create the array with the constant: new int[HOURS]."),
    has("readings.length", "Use readings.length in the range test and the average."),
    has("for(int", "warmestHour needs the hour, so it uses a for loop.")], xp=6) == (
    "Hours: 24\nAverage: 0\nWarmest: 0\nBelow zero: 0\ntrue\ntrue\ntrue\ntrue\nfalse\nfalse\nAverage: 0\nWarmest: 3\nBelow zero: 2")
TEMP_DEMO_STARTER = '''public class TemperatureDemo
{
    public static void main(String[] args)
    {
        int[] day = {2, 1, 1, 0, 0, -1, -1, 0, 2, 4, 6, 8,
                     10, 11, 12, 12, 11, 9, 7, 5, 4, 3, 3, 2};
        TemperatureLog log = new TemperatureLog();
        // 1. Record each reading with a for loop.
        // 2. Try hour 24 and print the result.
        // 3. Print the average, the warmest hour
        //    and the hours below zero.
    }
}
'''
assert TEMP_DEMO_STARTER.split("TemperatureLog log")[0] in TEMP_DEMO
assert code_box("p1-demo", "TemperatureDemo.java", TEMP_DEMO_STARTER, TEMP_DEMO, TEMP_FILE, [
    has("log.record(hour, day[hour])", "Record each reading: log.record(hour, day[hour]) inside a for loop."),
    has("log.record(24, 5)", "Try the bad hour with log.record(24, 5).")], xp=4, extra=8, name="Program output") == TEMP_OUT

GOLF = strip_docs(read("programB/GolfCard.java"))
GOLF_DEMO = read("programB/GolfDemo.java")
GOLF_FILE = [file("GolfCard.java", GOLF)]
GOLF_OUT = run(GOLF_DEMO, GOLF_FILE)
assert GOLF_OUT == "Player: Maya\nTotal: 38\nHoles under par: 2\nBest hole: 2", GOLF_OUT
GOLF_STARTER = '''public class GolfCard
{
    private static final int[] PAR = {4, 3, 5, 4, 4, 3, 4, 5, 4};
    private String player;
    private int[] strokes;

    public GolfCard(String player)
    {
        // Store the name; create strokes.
    }

    public String getPlayer()
    {
        return "";
    }

    public void record(int hole, int count)
    {
        // Ignore a bad hole; otherwise store.
    }

    public int total()
    {
        // for-each: add up the strokes.
        return 0;
    }

    public int holesUnderPar()
    {
        // for: compare strokes[hole] with PAR[hole].
        return 0;
    }

    public int bestHole()
    {
        // for: smallest strokes minus par.
        return 0;
    }
}
'''
PAR = [4, 3, 5, 4, 4, 3, 4, 5, 4]
assert "{" + ", ".join(map(str, PAR)) + "}" in GOLF
assert code_box("p2-card", "GolfCard.java", GOLF_STARTER, GOLF, driver("CardCheck", '''GolfCard empty = new GolfCard("Sam");
System.out.println(empty.getPlayer() + " " + empty.total());
GolfCard card = new GolfCard("Lee");
int[] par = {4, 3, 5, 4, 4, 3, 4, 5, 4};
for(int hole = 0; hole < par.length; hole++) {
    card.record(hole, par[hole]);
}
card.record(1, 2);
card.record(6, 6);
card.record(-1, 1);
card.record(9, 1);
System.out.println("Total: " + card.total());
System.out.println("Under par: " + card.holesUnderPar());
System.out.println("Best hole: " + card.bestHole());'''), [
    has("new int[PAR.length]", "Create strokes with PAR.length elements."),
    has("PAR[hole]", "Compare each hole with its own par, PAR[hole]."),
    has("for(int", "holesUnderPar and bestHole need the hole number, so they use a for loop.")], xp=6) == (
    "Sam 0\nTotal: 37\nUnder par: 1\nBest hole: 1")
GOLF_DEMO_STARTER = '''public class GolfDemo
{
    public static void main(String[] args)
    {
        GolfCard card = new GolfCard("Maya");
        int[] round = {5, 3, 4, 4, 6, 2, 4, 5, 5};
        // 1. Record each hole with a for loop.
        // 2. Record 3 strokes for hole 9.
        // 3. Print the player, the total, the
        //    holes under par and the best hole.
    }
}
'''
assert code_box("p2-demo", "GolfDemo.java", GOLF_DEMO_STARTER, GOLF_DEMO, GOLF_FILE, [
    has("card.record(hole, round[hole])", "Record each hole: card.record(hole, round[hole]) inside a for loop."),
    has("card.record(9, 3)", "Record 3 strokes for hole 9: card.record(9, 3).")], xp=4, extra=8, name="Program output") == GOLF_OUT

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-12",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 12 Workbook",
    "subtitle": "Chapter 7, Part 1: Arrays and the for Loop",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
