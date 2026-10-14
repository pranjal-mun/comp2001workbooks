"""Build workbooks/lecture-11/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-11/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-11

The questions follow the printed Lecture 11 workbook, numbered 1.1 to 9.1,
and the model answers are the ones in the solutions edition. The ids keep the
meaning they had on the first published page:

    1.1 q1, q1-why          1.2 q2      1.3 q3-output, q3-why
    1.4 q4, q4-why          1.5 q5-output, q5-why       1.6 q6
    2.1 q7, q7-why          2.2 q8, q8-why
    3.1 q9                  3.2 q10-output, q10-why, q10-loop
    5.1 q15                 6.1 q16-output, q16-why
    6.2 q17, q17-why        6.3 q18, q18-why            6.4 q19
    7.1 q20, q20-output, q20-why        7.2 q21, q21-why
    7.3 q22-output, q22-why             9.1 q25

q18 now asks about the final call number of Book instead of Appointment. New
for the QEII Library parts and the collections table: 4.1 q26-subject and
q26, 4.2 q27 and q27-output, 5.2 q30, 8.1 q28 and q28-constant, 8.2 q31,
8.3 q29 and q29-why. The clinic ids q11, q11-why, q12, q12-why, q13, q13-why,
q23, q23-why, q24 and q24-why are retired, as are q14 and the old runnable
examples (summary-example, starting-example, part11-example, part12-example,
main-example); none of them is reused. Section 10 has two complete programs,
one box per class (ids p1-* and p2-*).

A box that asks for part of a class starts from the rest of that class, and a
small driver class on its classpath (the `files` list) calls the student's
code and prints what comes back; the runner uses that main when the editor's
class has none. The HelpBot, library and program classes are read from the
lecture folder's code/ directory, so the page and the PDF use the same files.
"""
import base64, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402

CODE_DIR = ROOT.parent / "output" / "L11_Chapter_6B_Maps_Sets_Static_v3" / "code"


def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()


def run(code, files=(), inputs=()):
    status, stdout, stderr, _ = run_java(code.rstrip("\n"), inputs, None, files)
    assert status == "ok", f"{status}\n{stderr}"
    return stdout.rstrip("\n")


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


def code_forms(*forms):
    """Accepted forms of a code blank: as written, without spaces, and with or without a final semicolon."""
    out = []
    for form in forms:
        for f in (form, form.rstrip(";") if form.endswith(";") else form + ";"):
            for g in (f, re.sub(r"\s+", "", f)):
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


def lines_table(eid, output, xp=2, width="20rem", alts=None):
    """A table with one blank per printed line, named 0, 1, 2, ..."""
    blanks = {}
    for i, line in enumerate(output.split("\n")):
        accept = [line] + ([f'"{line}"'] if not re.fullmatch(r"-?\d+|true|false|null", line) else [])
        accept += (alts or {}).get(i, [])
        blanks[str(i)] = {"accept": accept, "show": line, "caseSensitive": True, "placeholder": "printed", "width": width}
    E[eid] = {"type": "table", "xp": xp, "blanks": blanks}


SHORT = lambda answer, chars=20, rows=2, xp=2: {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}  # noqa: E731
CODE = {"caseSensitive": True, "width": "26rem"}
NUM = {"placeholder": "number", "width": "7rem"}
YES = {"accept": ["yes", "Yes", "yes.", "compiles", "it compiles"], "show": "yes", "placeholder": "yes / no", "width": "8rem"}
NO = {"accept": ["no", "No", "no.", "does not compile", "it does not compile"], "show": "no", "placeholder": "yes / no", "width": "8rem"}
E = {}

# ---------------------------------------------------------------- classes
HELPBOT_FULL = read("final/HelpBot.java")
# The finished HelpBot without its comments, as the boxes show it.
HELPBOT = re.sub(r"\n[ \t]*/\*\*.*?\*/", "", HELPBOT_FULL, flags=re.S)
HELPBOT = HELPBOT.replace("import java.util.Random;\n\npublic class", "import java.util.Random;\n\npublic class")
assert "/**" not in HELPBOT and "public class HelpBot" in HELPBOT
assert run(read("final/HelpBotDemo.java"), [file("HelpBot.java", HELPBOT)]) == read("final/expected.txt").rstrip("\n")

REPLIES = {"submit": "Upload your .java files to the assignment page before the deadline.",
           "compile": "Read the first error message and check the line just above it.",
           "late": "Late work loses 10 percent per day.",
           "test": "Term Test 2 covers Chapters 1 to 9 and 12 to 13, mostly 6 to 9 and 12 to 13."}
for k, v in REPLIES.items():
    assert json.dumps(v) in HELPBOT, k
PUTS = "".join(f"replyMap.put({json.dumps(k)}, {json.dumps(v)});\n" for k, v in REPLIES.items())
BOT_FILE = [file("HelpBot.java", HELPBOT)]

BOOK_3, CATALOGUE_3, DEMO_3 = read("library/part3/Book.java"), read("library/part3/Catalogue.java"), read("library/part3/LibraryDemo.java")
BOOK_4, CATALOGUE_4, DEMO_4 = read("library/part4/Book.java"), read("library/part4/Catalogue.java"), read("library/part4/LibraryDemo.java")
PART3_FILES = [file("Book.java", BOOK_3), file("Catalogue.java", CATALOGUE_3)]
PART4_FILES = [file("Book.java", BOOK_4), file("Catalogue.java", CATALOGUE_4)]

FIVE = [("Objects First with Java", "David Barnes", "QA76.73 B37"), ("Head First Java", "Kathy Sierra", "QA76.73 S54"),
        ("The Colony of Unrequited Dreams", "Wayne Johnston", "PS8569 J64"), ("The Navigator of New York", "Wayne Johnston", "PS8569 J65"),
        ("A Brief History of Time", "Stephen Hawking", "QB981 H38")]


def add_five(target):
    return "".join(f'{target}.addBook(new Book("{t}", "{a}", "{n}"));\n' for t, a, n in FIVE)


def without_method(src, header):
    """src with one method (from its header to the closing brace at 4 spaces) removed."""
    start = src.index("    " + header)
    end = src.index("\n    }\n", start) + len("\n    }\n")
    return src[:start].rstrip("\n") + "\n" + src[end:].lstrip("\n") if src[end:].strip() != "}" else src[:start].rstrip("\n") + "\n}\n"


def strip_docs(src):
    return re.sub(r"\n[ \t]*/\*\*.*?\*/", "", src, flags=re.S).replace("\n\n\npublic class", "\n\npublic class")


# ---------------------------------------------------------------- 1. Maps
COURSES = '''import java.util.HashMap;

public class CourseList
{
    private HashMap<String, Integer> enrolment;

    public CourseList()
    {
        enrolment = new HashMap<>();
    }

    public void enrol(String course, int students)
    {
        enrolment.put(course, students);
    }

    public int studentsIn(String course)
    {
        return enrolment.getOrDefault(course, 0);
    }
}
'''
COURSES_STARTER = (COURSES.replace("import java.util.HashMap;\n", "// 1. The import goes here.\n")
                   .replace("    private HashMap<String, Integer> enrolment;\n", "    // 2. The field enrolment goes here.\n")
                   .replace("        enrolment = new HashMap<>();\n", "        // 3. Create the map here.\n"))
COURSES_DRIVER = driver("CourseCheck", 'CourseList list = new CourseList();\nlist.enrol("COMP2001", 120);\nlist.enrol("COMP1001", 300);\nSystem.out.println("COMP2001: " + list.studentsIn("COMP2001"));\nSystem.out.println("COMP3754: " + list.studentsIn("COMP3754"));')
assert code_box("q1", "CourseList.java", COURSES_STARTER, COURSES, COURSES_DRIVER, [
    has("import java.util.HashMap;", "Import the class: import java.util.HashMap;"),
    has("private HashMap<String, Integer> enrolment;", "Declare the field: private HashMap<String, Integer> enrolment;"),
    has("enrolment = new HashMap<>();", "Create the map in the constructor: enrolment = new HashMap<>();"),
    lacks("HashMap<String,int>", "A type argument must be a class: use Integer, not int."),
    lacks("HashMap<String, Integer> enrolment = new", "Assign the field in the constructor; do not declare a new local variable.")], xp=3, extra=4) == "COMP2001: 120\nCOMP3754: 0"
E["q1-why"] = SHORT("A type argument must be a class, and int is a primitive type, so the map uses the wrapper class Integer. Java boxes and unboxes the numbers for us.", rows=2)
E["q2"] = SHORT("Both are String. No: a key appears at most once, and a second put with the key submit replaces its reply. Yes: two keys can have equal values.", rows=3)

MAP_SETUP = "HashMap<String, String> replyMap = new HashMap<>();\n" + PUTS
Q3 = run(demo("MapReads", MAP_SETUP + 'System.out.println(replyMap.get("test"));\nSystem.out.println(replyMap.size());\nSystem.out.println(replyMap.containsKey("room"));\nSystem.out.println(replyMap.get("room"));\nSystem.out.println(replyMap.getOrDefault("room",\n    "I do not have an answer for that yet."));\nSystem.out.println(replyMap.size());', "import java.util.HashMap;\n"))
assert Q3 == REPLIES["test"] + "\n4\nfalse\nnull\nI do not have an answer for that yet.\n4", Q3
lines_table("q3-output", "\n".join(Q3.split("\n")[:5]), xp=3, width="34rem")
E["q3-why"] = SHORT("println prints the text null for a null reference and calls no method on it. reply.length() calls a method through null, which throws a NullPointerException.", rows=2)

LOOKUP = '''import java.util.HashMap;

public class ReplyLookup
{
    private HashMap<String, String> replyMap;

    public ReplyLookup()
    {
        replyMap = new HashMap<>();
''' + "".join(f"        {line}\n" for line in PUTS.strip().split("\n")) + '''    }

    public void printLength(String keyword)
    {
        if(replyMap.containsKey(keyword)) {
            System.out.println(replyMap.get(keyword).length());
        }
        else {
            System.out.println("Unknown keyword");
        }
    }
}
'''
LOOKUP_BODY = LOOKUP[LOOKUP.index("        if(replyMap.containsKey"):LOOKUP.rindex("    }\n}")]
LOOKUP_STARTER = LOOKUP.replace(LOOKUP_BODY, "        String reply = replyMap.get(keyword);\n        System.out.println(reply.length());\n")
assert code_box("q4", "ReplyLookup.java", LOOKUP_STARTER, LOOKUP, driver("LookupCheck", 'ReplyLookup lookup = new ReplyLookup();\nlookup.printLength("test");\nlookup.printLength("room");'), [
    has("containsKey(keyword)", "Check the key first with replyMap.containsKey(keyword)."),
    has('"Unknown keyword"', 'Print "Unknown keyword" when the key has no reply.')], xp=3, extra=6) == "76\nUnknown keyword"
E["q4-why"] = SHORT("For a missing key, get returns null, and calling length through null throws a NullPointerException. With the check, length is called only when the key has a reply.", rows=2)

Q5 = run(demo("LearnDemo", 'HelpBot bot = new HelpBot();\nbot.learn("room", "Ask at the front desk.");\nbot.learn("submit", "Use the upload page.");\nSystem.out.println(bot.numberOfKeywords());\nSystem.out.println(bot.replyFor("room"));'), BOT_FILE)
assert Q5 == "5\nAsk at the front desk."
lines_table("q5-output", Q5, width="20rem")
E["q5-why"] = SHORT("numberOfKeywords returns replyMap.size(). room is a new key, so the first call adds a fifth entry. submit is already a key, so the second call replaces its reply and the size stays 5.", rows=2)

Q6 = run(demo("RouteDemo", 'HelpBot bot = new HelpBot();\nSystem.out.println(bot.replyTo("Can I relate this to Lecture 9?"));\nSystem.out.println(bot.replyTo("  "));\nSystem.out.println(bot.hasBeenAsked("submit"));'), BOT_FILE)
assert Q6 == REPLIES["late"] + "\nPlease type a question.\nfalse"
E["q6"] = SHORT("(a) The late reply: relate contains late, so the bot matches it even though the question is not about late work. (b) Please type a question. (c) A general reply, because no keyword appears in it. (d) It contains submit and test. The loop returns at the first keyword it visits, and a HashMap does not promise an order, so either reply could come back.", rows=4)

# ---------------------------------------------------------------- 2. Counts
Q7 = run(demo("CountDemo", 'HelpBot bot = new HelpBot();\nbot.replyTo("Is my work late?");\nbot.replyTo("Why will it not compile?");\nbot.replyTo("How late is too late?");\nbot.replyTo("Can I hand it in late?");\nSystem.out.println(bot.timesAsked("late"));\nSystem.out.println(bot.timesAsked("compile"));\nSystem.out.println(bot.timesAsked("test"));\nSystem.out.println(bot.timesAsked("submit"));\nSystem.out.println(bot.numberOfTopicsAsked());'), BOT_FILE)
assert Q7 == "3\n1\n0\n0\n2", Q7
E["q7"] = {"type": "table", "xp": 3, "blanks": {str(i): {"accept": [v], **NUM} for i, v in enumerate(Q7.split("\n"))}}
E["q7-why"] = SHORT("Only the late count changes, to 4. late already has an entry, so the size of the count map stays 2. A question counts once, even when it contains late twice.", rows=2)

RECORDER = '''import java.util.HashMap;

public class KeywordRecorder
{
    private HashMap<String, Integer> keywordCounts;

    public KeywordRecorder()
    {
        keywordCounts = new HashMap<>();
    }

    public void ask(String keyword)
    {
        recordKeyword(keyword);
    }

    public int timesAsked(String keyword)
    {
        return keywordCounts.getOrDefault(keyword, 0);
    }

    public int numberCounted()
    {
        return keywordCounts.size();
    }

    private void recordKeyword(String keyword)
    {
        int count = keywordCounts.getOrDefault(keyword, 0);
        keywordCounts.put(keyword, count + 1);
    }
}
'''
RECORD_BODY = "        int count = keywordCounts.getOrDefault(keyword, 0);\n        keywordCounts.put(keyword, count + 1);\n"
assert RECORD_BODY in RECORDER
RECORDER_STARTER = RECORDER.replace(RECORD_BODY, "        // Add 1 to the keyword's count.\n\n\n")
assert code_box("q8", "KeywordRecorder.java", RECORDER_STARTER, RECORDER, driver("RecordCheck", 'KeywordRecorder recorder = new KeywordRecorder();\nrecorder.ask("late");\nrecorder.ask("compile");\nrecorder.ask("late");\nSystem.out.println("late: " + recorder.timesAsked("late"));\nSystem.out.println("compile: " + recorder.timesAsked("compile"));\nSystem.out.println("test: " + recorder.timesAsked("test"));\nSystem.out.println("Keywords counted: " + recorder.numberCounted());'), [
    has("getOrDefault(keyword, 0)", "Read the count with getOrDefault(keyword, 0), so a new keyword starts from 0."),
    has("keywordCounts.put(keyword,", "Store the new count with keywordCounts.put(keyword, ...)."),
    lacks("keywordCounts.get(keyword) + 1", "get returns null for a new keyword; use getOrDefault.")], xp=3, extra=4) == "late: 2\ncompile: 1\ntest: 0\nKeywords counted: 2"
NPE = run_java(demo("FirstCount", 'java.util.HashMap<String, Integer> counts = new java.util.HashMap<>();\nint count = counts.get("late") + 1;\nSystem.out.println(count);'), (), None, [])
assert NPE[0] != "ok" and "NullPointerException" in NPE[1] + NPE[2], NPE
E["q8-why"] = SHORT("The first time, the keyword has no entry, so get returns null. Java tries to unbox null into an int to add 1, and the program stops with a NullPointerException. getOrDefault gives 0 instead.", rows=2)

# ---------------------------------------------------------------- 3. Sets
Q9 = run(demo("ListSet", 'ArrayList<String> list = new ArrayList<>();\nHashSet<String> set = new HashSet<>();\nlist.add("late"); list.add("test"); list.add("late"); list.add("late");\nset.add("late"); set.add("test"); set.add("late"); set.add("late");\nSystem.out.println(list.size() + " " + set.size());', "import java.util.ArrayList;\nimport java.util.HashSet;\n"))
assert Q9 == "4 2"
E["q9"] = SHORT("The list has size 4 and the set size 2. Only the list knows that late was added three times; the set only knows that it was added. No: a HashSet promises no order.", rows=3)

TOPICS = 'HashSet<String> topics = new HashSet<>();\nSystem.out.println(topics.isEmpty());\nSystem.out.println(topics.add("submit"));\nSystem.out.println(topics.add("submit"));\nSystem.out.println(topics.contains("compile"));\nSystem.out.println(topics.remove("late"));\nSystem.out.println(topics.size());\n'
Q10 = run(demo("TopicDemo", TOPICS, "import java.util.HashSet;\n"))
assert Q10 == "true\ntrue\nfalse\nfalse\nfalse\n1"
lines_table("q10-output", Q10, width="8rem")
E["q10-why"] = SHORT("The second add returns false because submit is already there. remove returns false because late was never added. One element is left, submit.", rows=2)
assert code_box("q10-loop", "TopicDemo.java", demo("TopicDemo", TOPICS + "\n// Print every element still in topics.\n\n\n", "import java.util.HashSet;\n"),
                demo("TopicDemo", TOPICS + "\nfor(String topic : topics) {\n    System.out.println(topic);\n}", "import java.util.HashSet;\n"), [], [
    matches(r".*for\(Stringtopic:topics\)\{System\.out\.println\(topic\);\}.*", "Visit the set with for(String topic : topics) and print topic.")], xp=2, extra=4, name="Program output") == Q10 + "\nsubmit"

# ---------------------------------------------------------------- 4. Library Part 3
BOOK_2 = without_method(BOOK_3, "public String getSubjectCode()")
assert "getSubjectCode" not in BOOK_2
SUBJECT_STARTER = BOOK_2.rstrip().rstrip("}") + "\n    public String getSubjectCode()\n    {\n        // The first two letters of the call number.\n        return \"\";\n    }\n}\n"
assert code_box("q26-subject", "Book.java", SUBJECT_STARTER, BOOK_3, driver("SubjectCheck", add_five("").replace(".addBook(new Book(", "System.out.println(new Book(").replace("));", ").getSubjectCode());")), [
    has("callNumber.substring(0, 2)", "Return callNumber.substring(0, 2).")], xp=2, extra=4) == "QA\nQA\nPS\nPS\nQB"

CAT_NO_COUNT = without_method(CATALOGUE_3, "public HashMap<String, Integer> countBySubject()")
CAT_NO_COUNT = re.sub(r"\n[ \t]*/\*\*(?:(?!\*/).)*?Count the books.*?\*/", "", CAT_NO_COUNT, flags=re.S)
Q26_STARTER = strip_docs(CAT_NO_COUNT).replace("    public HashSet<String> getAuthors()", "    public HashMap<String, Integer> countBySubject()\n    {\n        // A new map; for each book, getOrDefault then put.\n        return null;\n    }\n\n    public HashSet<String> getAuthors()")
Q26_DRIVER = driver("CountCheck", 'Catalogue empty = new Catalogue();\nSystem.out.println("Empty: " + empty.countBySubject().size());\nCatalogue catalogue = new Catalogue();\n' + add_five("catalogue") + 'java.util.HashMap<String, Integer> counts = catalogue.countBySubject();\nSystem.out.println("Subjects: " + counts.size());\nSystem.out.println("QA: " + counts.get("QA"));\nSystem.out.println("PS: " + counts.get("PS"));\nSystem.out.println("QB: " + counts.get("QB"));\nSystem.out.println("Books: " + catalogue.getCount());')
assert code_box("q26", "Catalogue.java", Q26_STARTER, strip_docs(CATALOGUE_3), [file("Book.java", BOOK_3)] + Q26_DRIVER, [
    has("public HashMap<String, Integer> countBySubject()", "Keep the header public HashMap<String, Integer> countBySubject()."),
    has("new HashMap<>()", "Build a new map each time: new HashMap<>()."),
    has("getSubjectCode()", "Use each book's getSubjectCode()."),
    has("getOrDefault(", "Count with getOrDefault, then put."),
    has(".put(", "Store each new count with put.")], xp=5) == "Empty: 0\nSubjects: 3\nQA: 2\nPS: 2\nQB: 1\nBooks: 5"

CAT_NO_AUTHORS = without_method(CATALOGUE_3, "public HashSet<String> getAuthors()")
Q27_STARTER = strip_docs(CAT_NO_AUTHORS).rstrip().rstrip("}").rstrip() + "\n\n    public HashSet<String> getAuthors()\n    {\n        // A new set; add each book's author.\n        return null;\n    }\n}\n"
Q27_DRIVER = driver("AuthorCheck", 'Catalogue catalogue = new Catalogue();\n' + add_five("catalogue") + 'java.util.HashSet<String> authors = catalogue.getAuthors();\nSystem.out.println("Authors: " + authors.size());\nSystem.out.println("Wayne Johnston? " + authors.contains("Wayne Johnston"));\nSystem.out.println("Kathy Sierra? " + authors.contains("Kathy Sierra"));\nSystem.out.println("Margaret Atwood? " + authors.contains("Margaret Atwood"));\nSystem.out.println("Books: " + catalogue.getCount());')
assert code_box("q27", "Catalogue.java", Q27_STARTER, strip_docs(CATALOGUE_3), [file("Book.java", BOOK_3)] + Q27_DRIVER, [
    has("public HashSet<String> getAuthors()", "Keep the header public HashSet<String> getAuthors()."),
    has("new HashSet<>()", "Build a new set each time: new HashSet<>()."),
    has(".add(book.getAuthor())", "Add each author with add(book.getAuthor()).")], xp=4) == "Authors: 4\nWayne Johnston? true\nKathy Sierra? true\nMargaret Atwood? false\nBooks: 5"
DEMO3_OUT = run(DEMO_3, PART3_FILES)
assert DEMO3_OUT == read("library/part3/expected.txt").rstrip("\n")
assert DEMO3_OUT == "Subjects: 3\nQA books: 2\nPS books: 2\nQB books: 1\nPR books: 0\nBooks: 5\nAuthors: 4\nWayne Johnston? true\nMargaret Atwood? false"
lines_table("q27-output", DEMO3_OUT, xp=3, width="16rem")

# ---------------------------------------------------------------- 5. Collections
E["q15"] = SHORT("(a) private ArrayList<String> questions; (b) private HashSet<String> students; (c) private HashMap<String, Integer> questionsPerStudent; (d) private HashMap<String, String> replyMap; Order and repeats call for a list, distinct values for a set, and a value attached to each key for a map.", rows=4)
LIST = {"accept": ["list", "List", "ArrayList", "an ArrayList", "a list"], "show": "list", "placeholder": "list / set / map", "width": "10rem"}
SET = {"accept": ["set", "Set", "HashSet", "a HashSet", "a set"], "show": "set", "placeholder": "list / set / map", "width": "10rem"}
MAP = {"accept": ["map", "Map", "HashMap", "a HashMap", "a map"], "show": "map", "placeholder": "list / set / map", "width": "10rem"}
E["q30"] = {"type": "table", "xp": 3, "blanks": {"shelf": LIST, "authors": SET, "subjects": MAP, "borrowed": LIST, "titles": MAP}}
E["q30-why"] = SHORT("Shelf: order matters, so a list. Authors: each author once, so a set. Subjects: a count for each code, so a map. Borrowed today: order and repeats, because the same book can be borrowed twice in a day, so a list. Titles: a value for each call number, so a map.", rows=3)

# ---------------------------------------------------------------- 6. Fields
Q16 = run(demo("SharedDemo", 'System.out.println(HelpBot.numberOfBots());\nHelpBot a = new HelpBot();\nHelpBot b = new HelpBot();\nHelpBot c = new HelpBot();\na.replyTo("submit");\nSystem.out.println(HelpBot.numberOfBots());\nSystem.out.println(a.timesAsked("submit"));\nSystem.out.println(b.timesAsked("submit"));'), BOT_FILE)
assert Q16 == "0\n3\n1\n0"
E["q16-output"] = {"type": "table", "xp": 3, "blanks": {str(i): {"accept": [v], **NUM} for i, v in enumerate(Q16.split("\n"))}}
NULLED = run(demo("NullDemo", 'HelpBot a = new HelpBot();\nHelpBot b = new HelpBot();\nHelpBot c = new HelpBot();\nb = null;\nSystem.out.println(HelpBot.numberOfBots());'), BOT_FILE)
assert NULLED == "3"
E["q16-why"] = SHORT("botsCreated is a class variable, shared by all bots, so it counts all three. keywordCounts is an instance variable: the question went to a, so only a's count changed. After b = null the count is still 3, because it counts the bots created.", rows=3)

CONSTANTS = "    public static final int MIN_RATING = 1;\n    public static final int MAX_RATING = 5;\n"
RANGE = "        if(rating >= MIN_RATING && rating <= MAX_RATING) {\n"
assert CONSTANTS in HELPBOT and RANGE in HELPBOT
Q17_STARTER = HELPBOT.replace(CONSTANTS, "    // The two rating constants go here.\n").replace(RANGE, "        if(rating >= 1 && rating <= 5) {\n")
Q17_DRIVER = driver("RatingCheck", 'System.out.println("Scale: " + HelpBot.MIN_RATING + " to " + HelpBot.MAX_RATING);\nHelpBot bot = new HelpBot();\nbot.addRating(5);\nbot.addRating(0);\nbot.addRating(1);\nbot.addRating(6);\nSystem.out.println("Ratings: " + bot.numberOfRatings());')
assert code_box("q17", "HelpBot.java", Q17_STARTER, HELPBOT, Q17_DRIVER, [
    has("public static final int MIN_RATING = 1;", "Declare public static final int MIN_RATING = 1;"),
    has("public static final int MAX_RATING = 5;", "Declare public static final int MAX_RATING = 5;"),
    has("rating >= MIN_RATING && rating <= MAX_RATING", "Use the constants in the test: rating >= MIN_RATING && rating <= MAX_RATING.")], xp=3, extra=4) == "Scale: 1 to 5\nRatings: 2"
E["q17-why"] = SHORT("Only the value of MAX_RATING changes, to 10. addRating and any other code that uses the constant stay as they are.", rows=2)

SETTER = "    public void setCallNumber(String number)\n    {\n        callNumber = number;\n    }\n"
Q18_STARTER = BOOK_3.rstrip().rstrip("}") + "\n" + SETTER + "}\n"
assert code_box("q18", "Book.java", Q18_STARTER, BOOK_3.replace("    private String callNumber;", "    private final String callNumber;"),
                driver("FinalCheck", 'Book book = new Book("Head First Java", "Kathy Sierra", "QA76.73 S54");\nSystem.out.println(book.getCallNumber());\nSystem.out.println(book.getSubjectCode());'), [
    has("private final String callNumber;", "Make the field final: private final String callNumber;"),
    lacks("setCallNumber", "A final field cannot be assigned outside the constructor, so remove setCallNumber.")], xp=3, extra=4) == "QA76.73 S54\nQA"
FINAL_SET = run_java(BOOK_3.replace("    private String callNumber;", "    private final String callNumber;").rstrip().rstrip("}") + "\n" + SETTER + "}\n", (), None, [])
assert FINAL_SET[0] != "ok", FINAL_SET
E["q18-why"] = SHORT("(a) Yes: the constructor assigns it once. (b) No: a final field cannot be assigned outside the constructor. (c) No: a final field must be assigned in every constructor. (d) Yes: reading a final field is always allowed, and substring makes a new string without changing the field.", rows=3)
E["q19"] = SHORT("Yes: ratings.add changes the list, not the field, so it still works. final stops any second assignment to the field, such as ratings = new ArrayList<>(); in a method that tries to clear the ratings.", rows=3)

# ---------------------------------------------------------------- 7. Methods
BOTS = "    public static int numberOfBots()\n    {\n        return botsCreated;\n    }\n"
assert BOTS in HELPBOT
Q20_STARTER = HELPBOT.replace(BOTS, "    // Write the class method numberOfBots() here.\n\n\n\n\n")
assert code_box("q20", "HelpBot.java", Q20_STARTER, HELPBOT, driver("BotCount", 'System.out.println("Before: " + HelpBot.numberOfBots());\nHelpBot first = new HelpBot();\nHelpBot second = new HelpBot();\nSystem.out.println("After two: " + HelpBot.numberOfBots());'), [
    has("public static int numberOfBots()", "Include public static int numberOfBots()."),
    has("return botsCreated;", "Return the class variable botsCreated.")], xp=3, extra=4) == "Before: 0\nAfter two: 2"
Q20 = run(demo("ClassCalls", 'System.out.println(HelpBot.numberOfBots());\nSystem.out.println(Math.min(3, 7));'), BOT_FILE)
assert Q20 == "0\n3"
E["q20-output"] = {"type": "table", "xp": 2, "blanks": {str(i): {"accept": [v], **NUM} for i, v in enumerate(Q20.split("\n"))}}
E["q20-why"] = SHORT("Both are class methods, called with the class name. numberOfBots reads only the class variable, and min uses only its parameters, so neither needs an object.", rows=2)

KEPT = "    public static int ratingsKept(HelpBot bot)\n    {\n        return bot.numberOfRatings();\n    }\n"
HELPBOT_KEPT = HELPBOT.replace(BOTS, BOTS + "\n" + KEPT)
assert code_box("q21", "HelpBot.java", HELPBOT.replace(BOTS, BOTS + "\n    // Write the class method ratingsKept(HelpBot bot) here.\n\n\n\n\n"), HELPBOT_KEPT,
                driver("KeptCheck", 'HelpBot bot = new HelpBot();\nbot.addRating(5);\nbot.addRating(0);\nbot.addRating(4);\nSystem.out.println("Kept: " + HelpBot.ratingsKept(bot));\nSystem.out.println("New bot: " + HelpBot.ratingsKept(new HelpBot()));'), [
    has("public static int ratingsKept(HelpBot bot)", "Include public static int ratingsKept(HelpBot bot)."),
    has("bot.numberOfRatings()", "Ask the given bot: bot.numberOfRatings()."),
    lacks("ratingsKept(HelpBotbot){returnratings.size()", "A class method has no this; use the bot it is given.")], xp=3, extra=4) == "Kept: 2\nNew bot: 0"
STATIC_FAIL = run_java(HELPBOT.replace("    public int numberOfKeywords()", "    public static int numberOfKeywords()"), (), None, [])
assert STATIC_FAIL[0] != "ok" and any(w in STATIC_FAIL[1] + STATIC_FAIL[2] + (STATIC_FAIL[3] or "") for w in ("static context", "static reference")), STATIC_FAIL
E["q21-why"] = SHORT("It returns 2, because 0 is outside 1 to 5 and is not kept. ratingsKept says which bot it means. The static numberOfKeywords uses replyMap with no object, and a class method has no this, so the compiler cannot tell which bot's map to use.", rows=3)

Q22 = run(demo("TwoBots", 'HelpBot first = new HelpBot();\nHelpBot second = new HelpBot();\nSystem.out.println(HelpBot.numberOfBots());\nSystem.out.println(second.replyTo("Is it too LATE?"));'), BOT_FILE)
assert Q22 == "2\n" + REPLIES["late"]
lines_table("q22-output", Q22, width="22rem")
E["q22-why"] = SHORT("numberOfBots is a class method, called on the class. replyTo is an instance method, called on the object second, and it uses second's own reply map and counts.", rows=2)

# ---------------------------------------------------------------- 8. Library Part 4
assert code_box("q28", "Book.java", BOOK_3.replace("    private String callNumber;\n", "    private String callNumber;\n    // The class variable booksCreated goes here.\n").rstrip().rstrip("}") + "\n    // Write getBooksCreated() here.\n}\n", BOOK_4,
                driver("BookCount", 'System.out.println("Before: " + Book.getBooksCreated());\nBook a = new Book("Head First Java", "Kathy Sierra", "QA76.73 S54");\nBook b = new Book("Random Passage", "Bernice Morgan", "PS8576 M67");\nSystem.out.println("After two: " + Book.getBooksCreated());\nSystem.out.println(b.getCallNumber() + " " + b.getSubjectCode());'), [
    has("private final String callNumber;", "Make the call number final: private final String callNumber;"),
    has("private static int booksCreated = 0;", "Declare private static int booksCreated = 0;"),
    matches(r".*publicBook\(Stringtitle,Stringauthor,StringcallNumber\)\{[^}]*booksCreated(\+\+|=booksCreated\+1|\+=1);[^}]*\}.*", "Add 1 to booksCreated in the constructor."),
    has("public static int getBooksCreated()", "Include public static int getBooksCreated().")], xp=5, extra=6) == "Before: 0\nAfter two: 2\nPS8576 M67 PS"
E["q28-constant"] = {"type": "table", "xp": 1, "blanks": {"constant": {
    "accept": code_forms('public static final String LIBRARY_NAME = "QEII Library";'), "show": 'public static final String LIBRARY_NAME = "QEII Library";',
    "placeholder": "declaration", **CODE, "width": "30rem"}}}
assert 'public static final String LIBRARY_NAME = "QEII Library";' in CATALOGUE_4
DEMO4_OUT = run(DEMO_4, PART4_FILES)
assert DEMO4_OUT == read("library/part4/expected.txt").rstrip("\n")
assert DEMO4_OUT == "QEII Library\nBooks created: 0\nBooks created: 5\nIn the catalogue: 5\nBooks created: 6\nIn the donations: 1"
lines_table("q31", DEMO4_OUT, xp=3, width="16rem")

BODIES = {"count": ("return booksCreated;", True), "title": ("return title.length();", False),
          "create": ('Book b = new Book("A", "B", "QA1"); return b.getTitle().length();', True),
          "this": ("return this.callNumber.length();", False), "constant": ("return Catalogue.LIBRARY_NAME.length();", True)}
q29 = {}
for key, (body, ok) in BODIES.items():
    trial = BOOK_4.replace("    public static int getBooksCreated()\n    {\n        return booksCreated;", f"    public static int getBooksCreated()\n    {{\n        {body}")
    assert trial.count(body) == 1 and "getBooksCreated()\n    {\n        " + body in trial
    status = run_java(trial, (), None, [file("Catalogue.java", CATALOGUE_4)])[0]
    assert (status != "compile-error" if ok else status == "compile-error"), (key, status)
    q29[key] = YES if ok else NO
E["q29"] = {"type": "table", "xp": 3, "blanks": q29}
E["q29-why"] = SHORT("A class method has no this, so it can use class variables, constants and its own local variables, but an instance field only through an object it names. The third body compiles, but it is a bad idea: it creates a book, so the count goes up by one each time the method is called.", rows=3)

# ---------------------------------------------------------------- 9. Review
E["q25"] = SHORT("(a) No: get returns null and the map does not change. (b) No: a HashSet keeps no order. (c) No: static means one copy shared by the class; final means it cannot change. (d) No: final fixes the reference, and the list can still change. (e) No: it can use an object it is given or creates, such as bot in ratingsKept. What it cannot do is use this.", rows=5)

# ---------------------------------------------------------------- 10. Complete Java Programs
ORDER, ORDER_LOG, ORDER_DEMO = read("programA/Order.java"), read("programA/OrderLog.java"), read("programA/OrderDemo.java")
TICKET, BOOTH, TICKET_DEMO = read("programB/Ticket.java"), read("programB/TicketBooth.java"), read("programB/TicketDemo.java")

ORDER_STARTER = '''public class Order
{
    private String customer;
    private String drink;

    public Order(String customer, String drink)
    {
        // Assign the two fields.
    }

    public String getCustomer()
    {
    }

    public String getDrink()
    {
    }
}
'''
ORDER_LOG_STARTER = '''import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;

public class OrderLog
{
    private ArrayList<Order> orders;

    public OrderLog()
    {
        orders = new ArrayList<>();
    }

    public void addOrder(String customer, String drink)
    {
        // trim both; drink in lower case.
    }

    public int getCount()
    {
    }

    public HashMap<String, Integer> countByDrink()
    {
        // A new map; getOrDefault, then put.
    }

    public HashSet<String> getCustomers()
    {
        // A new set; add each customer.
    }
}
'''
ORDER_DEMO_STARTER = '''import java.util.HashMap;
import java.util.HashSet;

public class OrderDemo
{
    public static void main(String[] args)
    {
        OrderLog log = new OrderLog();
        // 1. Add the six orders in order.
        // 2. Get the map from countByDrink and print the six lines.
        // 3. Get the set from getCustomers and print the three lines.
    }
}
'''
TICKET_STARTER = '''public class Ticket
{
    private static int nextNumber = 1;

    private final int number;
    private final String event;

    public Ticket(String event)
    {
        // Set both; add 1 to nextNumber.
    }

    public int getNumber()
    {
    }

    public String getEvent()
    {
    }

    public static int ticketsIssued()
    {
    }
}
'''
BOOTH_STARTER = '''import java.util.ArrayList;

public class TicketBooth
{
    public static final int PRICE = 12;

    private ArrayList<Ticket> sold;

    public TicketBooth()
    {
        sold = new ArrayList<>();
    }

    public Ticket sell(String event)
    {
        // New ticket, add it, return it.
    }

    public int getTakings()
    {
        // Use priceFor.
    }

    public static int priceFor(int count)
    {
    }
}
'''
TICKET_DEMO_STARTER = '''public class TicketDemo
{
    public static void main(String[] args)
    {
        // 1. Print the price, the price for 3 and the number issued.
        // 2. Create front and side; sell the three tickets; print each one.
        // 3. Print the number issued and the takings of each booth.
    }
}
'''
ORDER_FILE = [file("Order.java", ORDER)]
ORDER_FILES = ORDER_FILE + [file("OrderLog.java", ORDER_LOG)]
TICKET_FILE = [file("Ticket.java", TICKET)]
TICKET_FILES = TICKET_FILE + [file("TicketBooth.java", BOOTH)]

assert code_box("p1-item", "Order.java", ORDER_STARTER, ORDER, driver("OrderCheck", 'Order order = new Order("Ana", "latte");\nSystem.out.println(order.getCustomer());\nSystem.out.println(order.getDrink());'), [
    has("public Order(String customer, String drink)", "Keep the constructor header Order(String customer, String drink).")], xp=2) == "Ana\nlatte"

assert code_box("p1-collection", "OrderLog.java", ORDER_LOG_STARTER, ORDER_LOG, ORDER_FILE + driver("OrderLogCheck", '''OrderLog empty = new OrderLog();
System.out.println("Empty: " + empty.getCount() + " " + empty.countByDrink().size() + " " + empty.getCustomers().size());
OrderLog log = new OrderLog();
log.addOrder(" Kim ", " Cocoa");
log.addOrder("Lee", "cocoa ");
log.addOrder("Kim", "TEA");
java.util.HashMap<String, Integer> counts = log.countByDrink();
System.out.println("Orders: " + log.getCount());
System.out.println("cocoa: " + counts.get("cocoa"));
System.out.println("tea: " + counts.get("tea"));
System.out.println("Drinks: " + counts.size());
System.out.println("Customers: " + log.getCustomers().size());
System.out.println("Kim? " + log.getCustomers().contains("Kim"));'''), [
    has(".trim().toLowerCase()", "Clean the drink with trim() and toLowerCase()."),
    has("getOrDefault(", "Count the drinks with getOrDefault, then put."),
    has("new HashSet<>()", "Collect the customers in a new HashSet.")], xp=6) == "Empty: 0 0 0\nOrders: 3\ncocoa: 2\ntea: 1\nDrinks: 2\nCustomers: 2\nKim? true"

ORDER_OUT = run(ORDER_DEMO, ORDER_FILES)
assert ORDER_OUT == read("programA/expected.txt").rstrip("\n")
assert code_box("p1-demo", "OrderDemo.java", ORDER_DEMO_STARTER, ORDER_DEMO, ORDER_FILES, [
    has('log.addOrder("Ana", " LATTE ")', 'Add Ana\'s second order " LATTE " with its spaces.'),
    has('getOrDefault("espresso", 0)', 'Print the espresso count with getOrDefault("espresso", 0).'),
    has('contains("Eve")', 'Check whether Eve is a customer with contains("Eve").')], xp=4, extra=10, name="Program output") == ORDER_OUT

assert code_box("p2-item", "Ticket.java", TICKET_STARTER, TICKET, driver("TicketCheck", '''System.out.println("Issued: " + Ticket.ticketsIssued());
Ticket a = new Ticket("Choir");
Ticket b = new Ticket("Play");
System.out.println(a.getNumber() + " " + a.getEvent());
System.out.println(b.getNumber() + " " + b.getEvent());
System.out.println("Issued: " + Ticket.ticketsIssued());'''), [
    has("number = nextNumber;", "Give the ticket the next number: number = nextNumber;"),
    has("return nextNumber - 1;", "Tickets issued is nextNumber - 1.")], xp=3) == "Issued: 0\n1 Choir\n2 Play\nIssued: 2"

assert code_box("p2-collection", "TicketBooth.java", BOOTH_STARTER, BOOTH, TICKET_FILE + driver("BoothCheck", '''System.out.println("Price for 0: " + TicketBooth.priceFor(0));
System.out.println("Price for 5: " + TicketBooth.priceFor(5));
TicketBooth booth = new TicketBooth();
System.out.println("Takings: " + booth.getTakings());
Ticket t = booth.sell("Choir");
booth.sell("Choir");
System.out.println(t.getNumber() + " " + t.getEvent());
System.out.println("Takings: " + booth.getTakings());'''), [
    has("return count * PRICE;", "priceFor multiplies by the constant: return count * PRICE;"),
    has("priceFor(sold.size())", "getTakings uses priceFor(sold.size())."),
    has("sold.add(", "Keep each ticket sold in the list.")], xp=5) == "Price for 0: 0\nPrice for 5: 60\nTakings: 0\n1 Choir\nTakings: 24"

TICKET_OUT = run(TICKET_DEMO, TICKET_FILES)
assert TICKET_OUT == read("programB/expected.txt").rstrip("\n")
assert code_box("p2-demo", "TicketDemo.java", TICKET_DEMO_STARTER, TICKET_DEMO, TICKET_FILES, [
    has("TicketBooth.PRICE", "Print the constant with TicketBooth.PRICE."),
    has("TicketBooth.priceFor(3)", "Print the price for 3 with TicketBooth.priceFor(3)."),
    has("Ticket.ticketsIssued()", "Print the number issued with Ticket.ticketsIssued().")], xp=4, extra=12, name="Program output") == TICKET_OUT

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-11",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 11 Workbook",
    "subtitle": "Chapter 6, Part 2: Maps, Sets and Class Members",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
