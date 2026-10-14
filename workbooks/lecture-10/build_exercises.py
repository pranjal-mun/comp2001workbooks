"""Build workbooks/lecture-10/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-10/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-10

The questions follow the printed Lecture 10 workbook, numbered 1.1 to 9.1,
and the model answers are the ones in the solutions edition. The ids keep the
meaning they had on the first published page:

    1.1 q1      1.2 q2      1.3 q3-why, q3
    2.1 q4, q4-why          2.2 q5      2.3 q6
    3.1 q7      3.2 q8, q8-why          3.3 q9, q9-why
    3.4 q10-output, q10, q10-why        3.5 q11-clean, q11-message, q11-why
    5.1 q14, q14-why        5.2 q15, q15-die
    5.3 q16, q16-why        5.4 q17, q17-why
    6.1 q18-box, q18-why    6.2 q19, q19-why        6.3 q20-trace, q20-why
    7.1 q21-method, q21-class, q21-why  7.2 q22
    9.1 q25

New for the QEII Library parts: 4.1 q26, 4.2 q27 and q27-demo, 8.1 q28,
8.2 q29, q29-why and q29-demo. The clinic ids q12, q13, q13-why, q23, q23-why,
q24, q24-demo and q24-why are retired, as are q6-why, q15-why, q18, q18-types
and q20 and the old runnable examples; none of them is reused. Section 10 has
two complete programs, one box per class (ids p1-* and p2-*).

A box that asks for part of a class starts from the rest of that class, and a
small driver class on its classpath (the `files` list) calls the student's
code and prints what comes back; the runner uses that main when the editor's
class has none. The library and program classes are read from the lecture
folder's code/ directory, so the page and the PDF use the same files.
"""
import base64, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402

CODE_DIR = ROOT.parent / "output" / "L10_Chapter_6A_Library_Classes_v3" / "code"


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


def no_semi(accept):
    return [a for a in accept if not a.endswith(";")]


def list_forms(*names):
    joined = ", ".join(names)
    forms = [f"[{joined}]", joined, "[" + ",".join(names) + "]", ",".join(names), " ".join(names)]
    if len(names) == 2:
        forms.append(f"{names[0]} and {names[1]}")
    elif len(names) > 2:
        forms.append(", ".join(names[:-1]) + ", and " + names[-1])
        forms.append(", ".join(names[:-1]) + " and " + names[-1])
    return forms


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


SHORT = lambda answer, chars=20, rows=2, xp=2: {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}  # noqa: E731
CODE = {"caseSensitive": True, "width": "26rem"}
TEXT = {"caseSensitive": True, "preserveWhitespace": True, "width": "18rem", "placeholder": "text"}
NUM = {"placeholder": "number", "width": "7rem"}
YESNO = {"placeholder": "yes / no"}
NO = ["no", "No", "no."]
TYPE = {"caseSensitive": True, "placeholder": "type", "width": "8rem"}
E = {}

REPLIES = ["Can you describe that in more detail?", "Have you checked the course web page?",
           "That question comes up often. Let us look at it together.",
           "Please post that on the discussion board so others can see the answer."]
ONE_OF_FOUR = " || ".join(json.dumps(r) + ".equals(reply)" for r in REPLIES)

# ---------------------------------------------------------------- classes
BOOK = read("library/part1/Book.java")
assert BOOK == read("library/part2/Book.java")
CATALOGUE_1 = read("library/part1/Catalogue.java")
DEMO_1 = read("library/part1/LibraryDemo.java")
CATALOGUE_2 = read("library/part2/Catalogue.java")
DEMO_2 = read("library/part2/LibraryDemo.java")
BOOK_FILE = [file("Book.java", BOOK)]
PART1_FILES = BOOK_FILE + [file("Catalogue.java", CATALOGUE_1)]
PART2_FILES = BOOK_FILE + [file("Catalogue.java", CATALOGUE_2)]

FIVE = [("Objects First with Java", "David Barnes", "QA76.73 B37"), ("Head First Java", "Kathy Sierra", "QA76.73 S54"),
        ("The Colony of Unrequited Dreams", "Wayne Johnston", "PS8569 J64"), ("The Navigator of New York", "Wayne Johnston", "PS8569 J65"),
        ("A Brief History of Time", "Stephen Hawking", "QB981 H38")]


def add_five(target):
    return "".join(f'{target}.addBook(new Book("{t}", "{a}", "{n}"));\n' for t, a, n in FIVE)


# The finished HelpBot without its comments, as the workbook builds it.
HELPBOT = '''import java.util.ArrayList;
import java.util.Random;

public class HelpBot
{
    private ArrayList<String> generalReplies;
    private ArrayList<Integer> ratings;
    private Random randomGenerator;

    public HelpBot()
    {
        generalReplies = new ArrayList<>();
        ratings = new ArrayList<>();
        randomGenerator = new Random();
        fillGeneralReplies();
    }

    public String replyTo(String question)
    {
        String cleaned = clean(question);
        if(cleaned.isEmpty()) {
            return "Please type a question.";
        }
        return pickGeneralReply();
    }

    public String clean(String question)
    {
        return question.trim().toLowerCase();
    }

    public String pickGeneralReply()
    {
        int index = randomGenerator.nextInt(generalReplies.size());
        return generalReplies.get(index);
    }

    public void addRating(int rating)
    {
        if(rating >= 1 && rating <= 5) {
            ratings.add(rating);
        }
    }

    public int numberOfRatings()
    {
        return ratings.size();
    }

    public int averageRating()
    {
        if(ratings.isEmpty()) {
            return 0;
        }
        int total = 0;
        for(int rating : ratings) {
            total = total + rating;
        }
        return total / ratings.size();
    }

    private void fillGeneralReplies()
    {
''' + "".join(f"        generalReplies.add({json.dumps(r)});\n" for r in REPLIES) + '''    }
}
'''

# ---------------------------------------------------------------- 1. Library
E["q1"] = SHORT("For example, String holds text, ArrayList keeps an ordered list of objects, and System gives us System.out for printing. Before calling a method we need its name, the types of its parameters, its return type, what it does, and any limits on the arguments.", rows=3)

PACKAGES = {"Random": "java.util", "ArrayList": "java.util", "String": "java.lang", "Integer": "java.lang"}
NONE_IMPORT = ["none", "no import", "not needed", "no", "nothing"]
q2 = {}
for name, pkg in PACKAGES.items():
    q2[f"{name}-name"] = {"accept": [f"{pkg}.{name}"], "show": f"{pkg}.{name}", "placeholder": "qualified name", **CODE, "width": "14rem"}
    if pkg == "java.util":
        q2[f"{name}-import"] = {"accept": code_forms(f"import {pkg}.{name};"), "show": f"import {pkg}.{name};", "placeholder": "import", **CODE, "width": "18rem"}
    else:
        q2[f"{name}-import"] = {"accept": NONE_IMPORT, "show": "none", "placeholder": "import", "width": "18rem"}
E["q2"] = {"type": "table", "xp": 3, "blanks": q2}

E["q3-why"] = SHORT("(a) Yes, Random is in java.util. (b) No. java.util.function is a separate package, and the wildcard does not reach into it.", rows=2)
Q3_STARTER = demo("QualifiedDemo", "// Create generator here, without an import.\n\nSystem.out.println(generator != null);")
Q3_ANSWER = demo("QualifiedDemo", "java.util.Random generator = new java.util.Random();\nSystem.out.println(generator != null);")
assert code_box("q3", "QualifiedDemo.java", Q3_STARTER, Q3_ANSWER, [], [
    has("java.util.Random generator = new java.util.Random()", "Use the qualified name twice: java.util.Random generator = new java.util.Random();"),
    lacks("import", "The file has no imports, so do not add one.")], xp=2, extra=4, name="Program output") == "true"

# ---------------------------------------------------------------- 2. Interfaces
DOC = {"accept": ["documentation", "the documentation", "docs", "interface", "public documentation"], "show": "documentation", "placeholder": "answer", "width": "13rem"}
IMPL = {"accept": ["implementation", "the implementation", "private implementation"], "show": "implementation", "placeholder": "answer", "width": "13rem"}
E["q4"] = {"type": "table", "xp": 2, "blanks": {"a": DOC, "b": DOC, "c": IMPL}}
E["q4-why"] = SHORT("The documentation tells us that get(0) returns the first element of a list that is not empty, and that is all a caller needs to know. How get finds the element is part of the implementation.", rows=2)

E["q5"] = {"type": "table", "xp": 3, "blanks": {
    "access": {"accept": ["public"], "show": "public", "placeholder": "modifier", **TYPE},
    "result": {"accept": ["int"], "show": "int", **TYPE},
    "name": {"accept": ["indexOf"], "show": "indexOf", "placeholder": "name", **TYPE, "width": "9rem"},
    "param": {"accept": ["String"], "show": "String", **TYPE},
    "signature": {"accept": ["indexOf(String)", "indexOf (String)"], "show": "indexOf(String)", "placeholder": "signature", **TYPE, "width": "12rem"},
    "caller": {"accept": NO + ["no, any String expression", "No; any String expression"], "show": "no", **YESNO}}}

E["q6"] = {"type": "table", "xp": 2, "blanks": {
    "add": {"accept": code_forms("boolean add(String e)", "public boolean add(String e)"), "show": "boolean add(String e)", "placeholder": "header", **CODE, "width": "18rem"},
    "get": {"accept": code_forms("String get(int index)", "public String get(int index)"), "show": "String get(int index)", "placeholder": "header", **CODE, "width": "18rem"},
    "integer": {"accept": ["Integer"], "show": "Integer", **TYPE}}}

# ---------------------------------------------------------------- 3. Strings
TYPED = "  When is the TEST?   "
SETUP = f'String typed = {json.dumps(TYPED)};\nString trimmed = typed.trim();\nString cleaned = trimmed.toLowerCase();\n'
LENGTHS = run(demo("Lengths", SETUP + 'System.out.println("[" + typed + "] " + typed.length());\nSystem.out.println("[" + trimmed + "] " + trimmed.length());\nSystem.out.println("[" + cleaned + "] " + cleaned.length());'))
assert LENGTHS == "[  When is the TEST?   ] 22\n[When is the TEST?] 17\n[when is the test?] 17"
q7 = {}
for line, var in zip(LENGTHS.split("\n"), ["typed", "trimmed", "cleaned"]):
    text, length = re.match(r"\[(.*)\] (\d+)$", line).groups()
    q7[f"{var}-text"] = {"accept": [f'"{text}"'], "show": f'"{text}"', **TEXT}
    q7[f"{var}-length"] = {"accept": [length], **NUM}
E["q7"] = {"type": "table", "xp": 3, "blanks": q7}

EXPR = ['typed.contains("test")', 'cleaned.contains("test")', 'cleaned.startsWith("when")', 'cleaned.indexOf("test")',
        'cleaned.indexOf("exam")', 'cleaned.substring(0, 4)', 'cleaned.isEmpty()']
TYPES = ["boolean", "boolean", "boolean", "int", "int", "String", "boolean"]
RESULTS = run(demo("Operations", SETUP + "".join(f"System.out.println({e});\n" for e in EXPR))).split("\n")
assert RESULTS == ["false", "true", "true", "12", "-1", "when", "false"]
q8 = {}
for i, (value, kind) in enumerate(zip(RESULTS, TYPES)):
    accept = [f'"{value}"', value] if kind == "String" else [value]
    q8[f"{i}-result"] = {"accept": accept, "show": f'"{value}"' if kind == "String" else value, "placeholder": "result", **CODE, "width": "8rem"}
    q8[f"{i}-type"] = {"accept": [kind], "show": kind, **TYPE}
E["q8"] = {"type": "table", "xp": 4, "blanks": q8}
E["q8-why"] = SHORT("contains is case sensitive. typed has TEST in capitals, so the small letters test are not in it; after toLowerCase they are.", rows=2)

IMMUTABLE = run(demo("Immutable", 'String original = "  compile  ";\nString cleaned = original.trim();\nSystem.out.println("[" + original + "] " + original.length());\nSystem.out.println("[" + cleaned + "] " + cleaned.length());'))
assert IMMUTABLE == "[  compile  ] 11\n[compile] 7"
E["q9"] = {"type": "table", "xp": 2, "blanks": {
    "original-text": {"accept": ['"  compile  "'], "show": '"  compile  "', **TEXT},
    "original-length": {"accept": ["11"], **NUM},
    "cleaned-text": {"accept": ['"compile"', "compile"], "show": '"compile"', **TEXT},
    "cleaned-length": {"accept": ["7"], **NUM}}}
E["q9-why"] = SHORT("Yes, the variable original can be assigned another string. No: the first object keeps its 11 characters. Immutable describes the object, not the variable.", rows=2)

DISCARD = 'String name = "  help desk  ";\nname.trim();\nSystem.out.println(name.length());\nname = name.trim();\nSystem.out.println(name.length());'
assert run(demo("DiscardDemo", DISCARD)) == "13\n9"
E["q10-output"] = {"type": "table", "xp": 2, "blanks": {"first": {"accept": ["13"], **NUM}, "second": {"accept": ["9"], **NUM}}}
assert code_box("q10", "DiscardDemo.java", demo("DiscardDemo", DISCARD), demo("DiscardDemo", DISCARD.replace("name.trim();\nSystem", "name = name.trim();\nSystem", 1)), [], [
    matches(r"(.*name=name\.trim\(\);){2}.*", "Keep the result of the first call too: name = name.trim();"),
    lacks("name.length() - 4", "Fix the trim call; do not change the printed numbers.")], xp=2, extra=4, name="Program output") == "9\n9"
E["q10-why"] = SHORT("The first call to trim builds the trimmed string, but nothing keeps it, so name still refers to the string with spaces. The space between help and desk stays, so the trimmed length is 9, not 8.", rows=2)

TIDY_ANSWER = '''public class NameFormatter
{
    public String tidy(String name)
    {
        return name.trim().toUpperCase();
    }
}
'''
TIDY_STARTER = '''public class NameFormatter
{
    public String tidy(String name)
    {
        // One chained expression.
        return name;
    }
}
'''
TIDY_DRIVER = driver("TidyCheck", 'NameFormatter formatter = new NameFormatter();\nSystem.out.println("[" + formatter.tidy("  ada lovelace ") + "]");\nSystem.out.println("[" + formatter.tidy("   ") + "]");')
assert code_box("q11-clean", "NameFormatter.java", TIDY_STARTER, TIDY_ANSWER, TIDY_DRIVER, [
    has(".trim().toUpperCase()", "Chain the two calls: return name.trim().toUpperCase();")], xp=3, extra=4) == "[ADA LOVELACE]\n[]"
MESSAGE_ANSWER = demo("MessageDemo", 'String message = "Your question was received.\\n"\n    + "A reply will follow.";\nSystem.out.println(message);')
MESSAGE_STARTER = demo("MessageDemo", "// Assign the two-line message here.\n\nSystem.out.println(message);")
assert code_box("q11-message", "MessageDemo.java", MESSAGE_STARTER, MESSAGE_ANSWER, [], [
    has("\\n", "Put the line break \\n inside the first string."),
    lacks("println(\"A reply", "Build one message and print it once.")], xp=2, extra=4, name="Program output") == "Your question was received.\nA reply will follow."
E["q11-why"] = SHORT("trim returns a String, so toUpperCase can be called on its result. The newline must be inside the first string; splitting the line of code does not start a new output line.", rows=2)

# ---------------------------------------------------------------- 4. Library Part 1
assert CATALOGUE_1.count("public void printMatches(String query)") == 1
CATALOGUE_HEAD = CATALOGUE_1[:CATALOGUE_1.index("    public void printMatches")]
Q26_STARTER = CATALOGUE_HEAD + "    public void printMatches(String query)\n    {\n        // Clean the query once; refuse an empty one; then a for-each loop and a found flag.\n\n\n\n\n\n\n\n\n\n    }\n}\n"
Q26_DRIVER = driver("SearchCheck", '''Catalogue empty = new Catalogue();
System.out.println("Empty catalogue:");
empty.printMatches("java");
Catalogue catalogue = new Catalogue();
''' + add_five("catalogue") + '''System.out.println("Five books:");
catalogue.printMatches("  JAVA  ");
catalogue.printMatches("UNREQUITED");
catalogue.printMatches(" Python");
catalogue.printMatches("   ");
System.out.println("Books: " + catalogue.getCount());''')
Q26_OUT = code_box("q26", "Catalogue.java", Q26_STARTER, CATALOGUE_1, BOOK_FILE + Q26_DRIVER, [
    has("public void printMatches(String query)", "Keep the header public void printMatches(String query)."),
    has(".trim().toLowerCase()", "Clean the query with query.trim().toLowerCase()."),
    has(".isEmpty()", "Refuse an empty query with isEmpty()."),
    has("for(Book", "Visit the books with a for-each loop: for(Book book : books)."),
    has(".getTitle().toLowerCase().contains(", "Compare the lower-case title with contains."),
    has("boolean ", "Record whether anything matched in a boolean variable.")], xp=6)
assert Q26_OUT == ('Empty catalogue:\nNo titles match "java".\nFive books:\nObjects First with Java (QA76.73 B37)\nHead First Java (QA76.73 S54)\n'
                   'The Colony of Unrequited Dreams (PS8569 J64)\nNo titles match "python".\nPlease type a word to search for.\nBooks: 5')

DEMO1_OUT = run(DEMO_1, PART1_FILES)
assert DEMO1_OUT == ('Books: 5\nSearch for "  JAVA  ":\nObjects First with Java (QA76.73 B37)\nHead First Java (QA76.73 S54)\n'
                     'Search for "first":\nObjects First with Java (QA76.73 B37)\nHead First Java (QA76.73 S54)\n'
                     'Search for "New York":\nThe Navigator of New York (PS8569 J65)\nSearch for "python":\nNo titles match "python".\n'
                     'Search for "   ":\nPlease type a word to search for.')
JAVA_BOOKS = list_forms("Objects First with Java", "Head First Java") + list_forms("Objects First with Java (QA76.73 B37)", "Head First Java (QA76.73 S54)")
SEARCH = {"placeholder": "what it prints", "width": "24rem"}
E["q27"] = {"type": "table", "xp": 3, "blanks": {
    "java": {"accept": JAVA_BOOKS, "show": "Objects First with Java (QA76.73 B37), Head First Java (QA76.73 S54)", **SEARCH},
    "first": {"accept": JAVA_BOOKS + ["the same two books", "same two books", "the same two", "same as above"], "show": "the same two books", **SEARCH},
    "york": {"accept": ["The Navigator of New York", "The Navigator of New York (PS8569 J65)"], "show": "The Navigator of New York (PS8569 J65)", **SEARCH},
    "python": {"accept": ['No titles match "python".', 'No titles match "python"', "No titles match python."], "show": 'No titles match "python".', **SEARCH},
    "empty": {"accept": ["Please type a word to search for.", "Please type a word to search for"], "show": "Please type a word to search for.", **SEARCH}}}
Q27_STARTER = demo("LibraryDemo", 'Catalogue catalogue = new Catalogue();\n// Add the five books, print "Books: " and the count,\n// then the five searches, each after its "Search for" line.\n' + "\n" * 14)
assert code_box("q27-demo", "LibraryDemo.java", Q27_STARTER, DEMO_1, PART1_FILES, [
    has("catalogue.addBook(new Book(", "Add each book as an anonymous object: catalogue.addBook(new Book(...));"),
    has('printMatches("  JAVA  ")', 'Search for "  JAVA  " with its spaces.'),
    has('printMatches("   ")', 'End with the empty search printMatches("   ").'),
    has(".getCount()", "Print the count with getCount().")], xp=4, extra=8, name="Program output") == DEMO1_OUT

# ---------------------------------------------------------------- 5. Random
COIN = '''import java.util.Random;

public class Coin
{
    private Random generator;

    public Coin()
    {
        generator = new Random();
    }

    public String flip()
    {
        if(generator.nextInt(2) == 0) {
            return "heads";
        }
        return "tails";
    }
}
'''
COIN_STARTER = '''// 1. The import goes here.

public class Coin
{
    // 2. The field goes here.

    public Coin()
    {
        // 3. Create the generator here.
    }

    public String flip()
    {
        if(generator.nextInt(2) == 0) {
            return "heads";
        }
        return "tails";
    }
}
'''
COIN_DRIVER = driver("CoinCheck", '''Coin coin = new Coin();
boolean valid = true;
boolean heads = false;
boolean tails = false;
for(int i = 0; i < 100; i++) {
    String side = coin.flip();
    if(side.equals("heads")) {
        heads = true;
    }
    else if(side.equals("tails")) {
        tails = true;
    }
    else {
        valid = false;
    }
}
System.out.println("All flips valid: " + valid);
System.out.println("Saw heads: " + heads);
System.out.println("Saw tails: " + tails);''')
assert code_box("q14", "Coin.java", COIN_STARTER, COIN, COIN_DRIVER, [
    has("import java.util.Random;", "Import the class above it: import java.util.Random;"),
    has("private Random generator;", "Declare the field with the others: private Random generator;"),
    matches(r".*publicCoin\(\)\{generator=newRandom\(\);\}.*", "Create the generator in the constructor: generator = new Random();"),
    lacks("Random generator = new Random()", "Assign the field in the constructor; do not declare a new local variable.")], xp=3, extra=4) == "All flips valid: true\nSaw heads: true\nSaw tails: true"
E["q14-why"] = SHORT("One generator should produce the whole sequence of flips. A new generator in every call is wasteful, and with a fixed seed it would restart the same sequence each time, giving the same flip again and again.", rows=2)

ZERO = run_java(demo("ZeroBound", "System.out.println(new java.util.Random().nextInt(0));"), (), None, [])
assert ZERO[0] != "ok" and "IllegalArgumentException" in ZERO[1] + ZERO[2], ZERO
E["q15"] = {"type": "table", "xp": 3, "blanks": {
    "four": {"accept": list_forms("0", "1", "2", "3") + ["0 to 3", "0 through 3", "0-3", "0, 1, 2 or 3", "0, 1, 2, or 3"], "show": "0, 1, 2, 3", "placeholder": "results", "width": "14rem"},
    "one": {"accept": ["0", "only 0", "always 0", "just 0"], "show": "only 0", "placeholder": "results", "width": "14rem"},
    "zero": {"accept": ["error", "an error", "IllegalArgumentException", "an IllegalArgumentException", "error: the bound must be positive",
                        "an error: the bound must be positive", "the bound must be positive", "bound must be positive", "an error, the bound must be positive"],
             "show": "an error: the bound must be positive", "placeholder": "results or error", "width": "20rem"}}}
MONTHS = '''import java.util.Random;

public class Months
{
    private Random randomGenerator;

    public Months()
    {
        randomGenerator = new Random();
    }

    public int randomMonth()
    {
        int month = 1 + randomGenerator.nextInt(12);
        return month;
    }
}
'''
MONTH_DRIVER = driver("MonthCheck", '''Months months = new Months();
int smallest = 100;
int largest = -100;
for(int i = 0; i < 2000; i++) {
    int month = months.randomMonth();
    smallest = Math.min(smallest, month);
    largest = Math.max(largest, month);
}
System.out.println("Smallest: " + smallest);
System.out.println("Largest: " + largest);''')
assert code_box("q15-die", "Months.java", MONTHS.replace("1 + randomGenerator.nextInt(12)", "0"), MONTHS, MONTH_DRIVER, [
    has("nextInt(12)", "Twelve possible months need the bound 12: nextInt(12)."),
    has("+", "Add 1 so the months run from 1 to 12, not 0 to 11.")], xp=2, extra=4) == "Smallest: 1\nLargest: 12"

PICKER = '''import java.util.ArrayList;
import java.util.Random;

public class ReplyPicker
{
    private Random randomGenerator;

    public ReplyPicker()
    {
        randomGenerator = new Random();
    }

    public String randomReply(ArrayList<String> replies)
    {
        if(replies.isEmpty()) {
            return null;
        }
        int index = randomGenerator.nextInt(replies.size());
        return replies.get(index);
    }
}
'''
PICKER_STARTER = PICKER[:PICKER.index("    public String randomReply")] + "    public String randomReply(ArrayList<String> replies)\n    {\n        // null for an empty list; otherwise a random valid index.\n\n\n\n\n\n    }\n}\n"
PICKER_DRIVER = driver("PickerCheck", '''ReplyPicker picker = new ReplyPicker();
System.out.println("Empty list: " + picker.randomReply(new java.util.ArrayList<String>()));
java.util.ArrayList<String> replies = new java.util.ArrayList<>();
''' + "".join(f"replies.add({json.dumps(r)});\n" for r in REPLIES) + '''boolean valid = true;
java.util.ArrayList<String> seen = new java.util.ArrayList<>();
for(int i = 0; i < 400; i++) {
    String reply = picker.randomReply(replies);
    if(!replies.contains(reply)) {
        valid = false;
    }
    else if(!seen.contains(reply)) {
        seen.add(reply);
    }
}
System.out.println("Always one of the four: " + valid);
System.out.println("All four came up: " + (seen.size() == 4));
System.out.println("Still " + replies.size() + " replies");''')
assert code_box("q16", "ReplyPicker.java", PICKER_STARTER, PICKER, PICKER_DRIVER, [
    has("public String randomReply(ArrayList<String> replies)", "Keep the header public String randomReply(ArrayList<String> replies)."),
    has("nextInt(replies.size())", "Use the list size as the bound: nextInt(replies.size())."),
    lacks("replies.size() + 1", "The bound is the size itself; size() + 1 can give an index past the end."),
    lacks(".remove(", "Leave the reply in the list.")], xp=4) == "Empty list: null\nAlways one of the four: true\nAll four came up: true\nStill 4 replies"
E["q16-why"] = SHORT("With four replies, nextInt(5) can return 4, and get(4) is past the end of the list. The empty check comes first, so nextInt is never called with a bound of 0.", rows=2)

REPLY_BODY = '''        String cleaned = clean(question);
        if(cleaned.isEmpty()) {
            return "Please type a question.";
        }
        return pickGeneralReply();
'''
assert REPLY_BODY in HELPBOT
REPLY_STARTER = HELPBOT.replace(REPLY_BODY, "        // Clean the question; an empty one gets \"Please type a question.\";\n        // otherwise return a general reply.\n        return \"\";\n")
REPLY_DRIVER = driver("ReplyCheck", f'''HelpBot bot = new HelpBot();
System.out.println(bot.replyTo("   "));
String reply = bot.replyTo("   How do I SUBMIT my work?  ");
System.out.println("One of the four general replies: " + ({ONE_OF_FOUR}));''')
assert code_box("q17", "HelpBot.java", REPLY_STARTER, HELPBOT, REPLY_DRIVER, [
    has("clean(question)", "Reuse the clean method: clean(question)."),
    has("isEmpty()", "Check the cleaned text with isEmpty()."),
    has("return pickGeneralReply();", "End with return pickGeneralReply();")], xp=3, extra=6) == "Please type a question.\nOne of the four general replies: true"
E["q17-why"] = SHORT("For \"   \" the cleaned text is empty, so it returns \"Please type a question.\" For the submit question it returns any one of the four general replies. We cannot say which, because the generator was created with new Random(), not with a fixed seed. The reply still ignores what the question asks.", rows=3)

# ---------------------------------------------------------------- 6. Ratings
BOXING = run(demo("Boxing", "ArrayList<Integer> scores = new ArrayList<>();\nscores.add(7);\nscores.add(2);\nint last = scores.get(1);\nint sum = scores.get(0) + last;\nSystem.out.println(last);\nSystem.out.println(sum);", "import java.util.ArrayList;\n"))
assert BOXING == "2\n9"
BOX = {"accept": ["boxes", "box", "boxing", "autoboxing", "autoboxes", "boxes the int", "boxes 7", "boxes 2"], "show": "boxes", "placeholder": "boxes / unboxes / neither", "width": "13rem"}
UNBOX = {"accept": ["unboxes", "unbox", "unboxing", "unboxes the Integer"], "show": "unboxes", "placeholder": "boxes / unboxes / neither", "width": "13rem"}
E["q18-box"] = {"type": "table", "xp": 3, "blanks": {"a": BOX, "b": BOX, "c": UNBOX, "d": UNBOX,
                                                    "last": {"accept": ["2"], **NUM}, "sum": {"accept": ["9"], **NUM}}}
E["q18-why"] = SHORT("The type in the angle brackets must be a class, and int is a primitive type. Integer is the wrapper class for int, so the list holds Integer objects and Java boxes and unboxes the values for us.", rows=2)

QUIZ = '''import java.util.ArrayList;

public class Quiz
{
    private ArrayList<Integer> scores;

    public Quiz()
    {
        scores = new ArrayList<>();
    }

    public void addScore(int score)
    {
        if(score >= 0 && score <= 10) {
            scores.add(score);
        }
    }

    public int numberOfScores()
    {
        return scores.size();
    }
}
'''
QUIZ_STARTER = QUIZ[:QUIZ.index("    public void addScore")] + "    // Write addScore(int score) and numberOfScores() here.\n\n\n\n\n\n\n\n\n\n\n}\n"
QUIZ_DRIVER = driver("QuizCheck", '''Quiz quiz = new Quiz();
System.out.println("New quiz: " + quiz.numberOfScores());
quiz.addScore(7);
quiz.addScore(11);
quiz.addScore(0);
quiz.addScore(-1);
quiz.addScore(10);
System.out.println("After the five calls: " + quiz.numberOfScores());
Quiz edges = new Quiz();
edges.addScore(0);
edges.addScore(10);
System.out.println("Edges kept: " + edges.numberOfScores());''')
assert code_box("q19", "Quiz.java", QUIZ_STARTER, QUIZ, QUIZ_DRIVER, [
    has("public void addScore(int score)", "Include public void addScore(int score)."),
    has("public int numberOfScores()", "Include public int numberOfScores()."),
    has("scores.size()", "Return scores.size(); the list already knows how many it holds."),
    lacks("count++", "No separate counter is needed.")], xp=4) == "New quiz: 0\nAfter the five calls: 3\nEdges kept: 2"
E["q19-why"] = SHORT("It returns 3: the list holds 7, 0 and 10. 0 and 10 are inside the range, so they are kept; 11 and -1 are ignored.", rows=2)

TRACE = run(demo("Trace", "int total = 0;\nint[] ratings = {4, 5, 2, 5};\nfor(int rating : ratings) {\n    total = total + rating;\n    System.out.println(total);\n}\nSystem.out.println(total / 4);\nSystem.out.println((5 + 4) / 2);"))
assert TRACE == "4\n9\n11\n16\n4\n4"
TRACE = TRACE.split("\n")
E["q20-trace"] = {"type": "table", "xp": 3, "blanks": {**{f"{i}-total": {"accept": [TRACE[i]], **NUM} for i in range(4)},
                                                     "main": {"accept": [TRACE[4]], **NUM}, "separate": {"accept": [TRACE[5]], **NUM}}}
E["q20-why"] = SHORT("16 / 4 = 4. For 5 and 4 it returns 9 / 2 = 4, because dividing one int by another gives a whole number and drops the 0.5.", rows=2)

# ---------------------------------------------------------------- 7. Documentation
ADD_RATING = "    public void addRating(int rating)\n"
assert HELPBOT.count(ADD_RATING) == 1
RATING_DOC = '''    /**
     * Record a rating for a reply. Ratings outside 1 to 5 are ignored.
     * @param rating The rating to record, from 1 to 5.
     */
'''
DOC_DRIVER = driver("DocCheck", "HelpBot bot = new HelpBot();\nbot.addRating(5);\nbot.addRating(9);\nbot.addRating(3);\nSystem.out.println(\"Ratings: \" + bot.numberOfRatings());")
assert code_box("q21-method", "HelpBot.java", HELPBOT.replace(ADD_RATING, "    // Write the Javadoc comment for addRating on the lines above its header.\n" + ADD_RATING),
                HELPBOT.replace(ADD_RATING, RATING_DOC + ADD_RATING), DOC_DRIVER, [
    matches(r".*/\*\*[^/]*@paramrating[^/]*\*/publicvoidaddRating\(intrating\).*", "Put a /** ... */ comment with an @param rating tag just above addRating."),
    matches(r".*/\*\*[^/]*(1to5|1and5|1-5|1through5|onetofive)[^/]*\*/publicvoidaddRating.*", "Say which ratings are kept, for example \"Ratings outside 1 to 5 are ignored.\""),
    lacks("@return", "addRating is void, so it has no @return tag.")], xp=3, extra=6) == "Ratings: 2"
BOOK_DOC = '''/**
 * A book in the library catalogue, with its title, author and
 * call number.
 * @author Pranjal Patra
 * @version 1.0
 */
'''
assert BOOK.startswith("public class Book")
assert code_box("q21-class", "Book.java", "// Write the class comment on the lines above the class header.\n" + BOOK, BOOK_DOC + BOOK,
                driver("BookCheck", 'Book book = new Book("Head First Java", "Kathy Sierra", "QA76.73 S54");\nSystem.out.println(book.getTitle() + " (" + book.getCallNumber() + ")");'), [
    matches(r".*/\*\*.*@author.*@version1\.0.*\*/publicclassBook.*", "Put a /** ... */ comment with @author and @version 1.0 just above public class Book."),
    lacks("@return", "A class comment has no @return tag.")], xp=3, extra=6) == "Head First Java (QA76.73 S54)"
E["q21-why"] = SHORT("Only a comment that starts with /** is a documentation comment. A comment that starts with /* is ignored when the documentation is made. The method comment has no @return tag because addRating is void.", rows=2)
E["q22"] = SHORT("It could add any number, such as bot.ratings.add(99), and skip the range check. Other classes should call addRating. No: fillGeneralReplies is a step in building a bot, not something other classes should call, so it stays private, and we can change it later without breaking them.", rows=4)

# ---------------------------------------------------------------- 8. Library Part 2
PICK_DRIVER = driver("PickCheck", '''Catalogue empty = new Catalogue();
System.out.println("Empty: " + empty.pickRandom());
Catalogue catalogue = new Catalogue();
''' + add_five("catalogue") + '''for(int i = 0; i < 5; i++) {
    System.out.println("Pick: " + catalogue.pickRandom().getTitle());
}
System.out.println("Books: " + catalogue.getCount());''')
Q28_STARTER = CATALOGUE_1.replace("import java.util.ArrayList;\n", "import java.util.ArrayList;\n// Import Random here.\n").replace(
    "    private ArrayList<Book> books;\n", "    private ArrayList<Book> books;\n    // The generator field goes here.\n").replace(
    "        books = new ArrayList<>();\n", "        books = new ArrayList<>();\n        // Create the generator with the seed 42.\n").rstrip().rstrip("}") + "\n    // Write pickRandom() with its Javadoc comment here.\n\n\n\n\n\n\n\n\n\n\n}\n"
Q28_OUT = code_box("q28", "Catalogue.java", Q28_STARTER, CATALOGUE_2, BOOK_FILE + PICK_DRIVER, [
    has("import java.util.Random;", "Import the class: import java.util.Random;"),
    has("private Random generator;", "Add the field private Random generator;"),
    has("generator = new Random(42);", "Create the generator once, in the constructor: generator = new Random(42);"),
    has("public Book pickRandom()", "Include public Book pickRandom()."),
    matches(r".*publicBookpickRandom\(\)\{if\(books\.isEmpty\(\)\)\{returnnull;\}.*", "Return null for an empty catalogue before calling nextInt."),
    has("generator.nextInt(books.size())", "Use the number of books as the bound: generator.nextInt(books.size())."),
    matches(r".*/\*\*[^/]*@return[^/]*\*/publicBookpickRandom\(\).*", "Put a /** ... */ comment with an @return tag just above pickRandom."),
    lacks(".remove(", "The picked book stays in the catalogue.")], xp=6)
assert Q28_OUT == ("Empty: null\nPick: Objects First with Java\nPick: The Navigator of New York\nPick: The Navigator of New York\n"
                   "Pick: A Brief History of Time\nPick: Objects First with Java\nBooks: 5"), Q28_OUT

DEMO2_OUT = run(DEMO_2, PART2_FILES)
assert DEMO2_OUT == ("Pick from an empty catalogue: null\nPick 1: Objects First with Java\nPick 2: The Navigator of New York\n"
                     "Pick 3: The Navigator of New York\nBooks: 5")
E["q29"] = {"type": "table", "xp": 2, "blanks": {
    "empty": {"accept": ["Pick from an empty catalogue: null", "null"], "show": "Pick from an empty catalogue: null", "placeholder": "first line", "width": "20rem"},
    "could": {"accept": ["any of the five", "any of the five titles", "any of the five books", "any title", "any book", "any of them", "all five",
                         "any one of the five", "any of the 5", "any of 5"], "show": "any of the five titles, each time", "placeholder": "titles", "width": "20rem"},
    "count": {"accept": ["Books: 5", "5"], "show": "Books: 5", "placeholder": "last line", "width": "10rem"}}}
E["q29-why"] = SHORT("The result is null, and calling a method through null stops the program. A pick does not remove the book, so the same title can come up twice, as it does with the seed 42.", rows=2)
Q29_STARTER = demo("LibraryDemo", 'Catalogue empty = new Catalogue();\n// Print the pick from the empty catalogue.\n\nCatalogue catalogue = new Catalogue();\n// Add the five books, print three picks, then "Books: " and the count.\n' + "\n" * 12)
assert code_box("q29-demo", "LibraryDemo.java", Q29_STARTER, DEMO_2, PART2_FILES, [
    has("empty.pickRandom()", "Print the pick from the empty catalogue: empty.pickRandom()."),
    has("catalogue.addBook(new Book(", "Add each book as an anonymous object: catalogue.addBook(new Book(...));"),
    matches(r".*pickRandom\(\).*pickRandom\(\).*pickRandom\(\).*pickRandom\(\).*", "Pick once from the empty catalogue and three times from the full one."),
    has(".getCount()", "Print the count with getCount().")], xp=4, extra=8, name="Program output") == DEMO2_OUT

# ---------------------------------------------------------------- 9. Review
E["q25"] = SHORT("(a) No: the result is thrown away. Write title = title.toUpperCase(); (b) No: the results are 0 to 3. (c) Use ArrayList<Integer>. (d) No: the query is empty after cleaning, so it prints the request to type a word. (e) No: it chooses a general reply at random. Lecture 11 uses a map to connect a word such as submit to its own reply.", rows=5)

# ---------------------------------------------------------------- 10. Complete Java Programs
CONTACT, CONTACT_LIST, CONTACT_DEMO = read("programA/Contact.java"), read("programA/ContactList.java"), read("programA/ContactDemo.java")
TIP, TIP_JAR, TIP_DEMO = read("programB/Tip.java"), read("programB/TipJar.java"), read("programB/TipDemo.java")

CONTACT_STARTER = '''public class Contact
{
    private String name;
    private String email;

    public Contact(String name, String email)
    {
        // Assign the two fields.
    }

    public String getName()
    {
    }

    public String getEmail()
    {
    }

    public String getInitials()
    {
        // indexOf(" "), then two substrings.
    }
}
'''
CONTACT_LIST_STARTER = '''import java.util.ArrayList;

public class ContactList
{
    private ArrayList<Contact> contacts;

    public ContactList()
    {
        contacts = new ArrayList<>();
    }

    public void addContact(String name, String email)
    {
        // trim both; email in lower case.
    }

    public void printAll()
    {
        // initials, name, <email>.
    }

    public void printSearch(String text)
    {
        // clean once; contains; a found flag.
    }

    public int countEmailsAt(String domain)
    {
        // endsWith("@" + domain).
    }
}
'''
CONTACT_DEMO_STARTER = '''public class ContactDemo
{
    public static void main(String[] args)
    {
        ContactList list = new ContactList();
        // 1. Add the three contacts.
        // 2. Print "All contacts:" and call printAll.
        // 3. Search for "  a", "TUR" and "xyz", each after a heading.
        // 4. Print "At mun.ca: " and the count.
    }
}
'''
TIP_STARTER = '''public class Tip
{
    private String text;
    private String topic;

    public Tip(String text, String topic)
    {
        // Assign the two fields.
    }

    public String getText()
    {
    }

    public String getTopic()
    {
    }
}
'''
TIP_JAR_STARTER = '''import java.util.ArrayList;
import java.util.Random;

public class TipJar
{
    private ArrayList<Tip> tips;
    private ArrayList<Integer> ratings;
    private Random generator;

    public TipJar()
    {
        // Two empty lists; new Random(7).
    }

    public void addTip(Tip tip)
    {
    }

    public Tip pickTip()
    {
        // null if empty; else nextInt(tips.size()).
    }

    public void addRating(int rating)
    {
        // Keep 1 to 5 only.
    }

    public int numberOfRatings()
    {
    }

    public int averageRating()
    {
        // 0 if empty; else a for-each total / size.
    }
}
'''
TIP_DEMO_STARTER = '''public class TipDemo
{
    public static void main(String[] args)
    {
        TipJar jar = new TipJar();
        // 1. Print the empty pick and the average with no ratings.
        // 2. Add the three tips in order.
        // 3. Pick and print two tips.
        // 4. Add the ratings 4, 5, 2, 9.
        // 5. Print the number of ratings and the average.
    }
}
'''

CONTACT_FILE = [file("Contact.java", CONTACT)]
CONTACT_FILES = CONTACT_FILE + [file("ContactList.java", CONTACT_LIST)]
TIP_FILE = [file("Tip.java", TIP)]
TIP_FILES = TIP_FILE + [file("TipJar.java", TIP_JAR)]

assert code_box("p1-item", "Contact.java", CONTACT_STARTER, CONTACT, driver("ContactCheck", '''Contact ada = new Contact("Ada Lovelace", "ada@example.com");
System.out.println(ada.getName());
System.out.println(ada.getEmail());
System.out.println(ada.getInitials());
Contact alan = new Contact("Alan Turing", "alan@mun.ca");
System.out.println(alan.getInitials());'''), [
    has("public Contact(String name, String email)", "Keep the constructor header Contact(String name, String email)."),
    has("indexOf(\" \")", "Find the space with indexOf(\" \")."),
    has(".substring(", "Take the two letters with substring.")], xp=3) == "Ada Lovelace\nada@example.com\nAL\nAT"

assert code_box("p1-collection", "ContactList.java", CONTACT_LIST_STARTER, CONTACT_LIST, CONTACT_FILE + driver("ContactListCheck", '''ContactList empty = new ContactList();
System.out.println("Empty list:");
empty.printAll();
empty.printSearch("a");
System.out.println("At mun.ca: " + empty.countEmailsAt("mun.ca"));
ContactList list = new ContactList();
list.addContact(" Mary Shelley  ", " Mary@MUN.CA");
list.addContact("Percy Shelley", "percy@example.com ");
System.out.println("Two contacts:");
list.printAll();
list.printSearch(" SHELLEY ");
list.printSearch("mary");
list.printSearch("byron");
System.out.println("At mun.ca: " + list.countEmailsAt("mun.ca"));
System.out.println("At example.com: " + list.countEmailsAt("example.com"));'''), [
    has(".trim().toLowerCase()", "Clean the email and the search text with trim() and toLowerCase()."),
    has(".contains(", "Search the names with contains."),
    has(".endsWith(\"@\" + domain)", "Count with endsWith(\"@\" + domain).")], xp=6) == (
    "Empty list:\nNo contacts match\nAt mun.ca: 0\nTwo contacts:\nMS Mary Shelley <mary@mun.ca>\nPS Percy Shelley <percy@example.com>\n"
    "Mary Shelley\nPercy Shelley\nMary Shelley\nNo contacts match\nAt mun.ca: 1\nAt example.com: 1")

assert code_box("p1-demo", "ContactDemo.java", CONTACT_DEMO_STARTER, CONTACT_DEMO, CONTACT_FILES, [
    has('list.addContact("  Ada Lovelace "', 'Add "  Ada Lovelace " with its spaces.'),
    has('printSearch("  a")', 'Search for "  a".'),
    has('countEmailsAt("mun.ca")', 'Count the emails with countEmailsAt("mun.ca").')], xp=4, extra=10, name="Program output") == (
    'All contacts:\nAL Ada Lovelace <ada@example.com>\nAT Alan Turing <alan@mun.ca>\nGH Grace Hopper <grace@mun.ca>\nSearch "  a":\n'
    'Ada Lovelace\nAlan Turing\nGrace Hopper\nSearch "TUR":\nAlan Turing\nSearch "xyz":\nNo contacts match\nAt mun.ca: 2')

assert code_box("p2-item", "Tip.java", TIP_STARTER, TIP, driver("TipCheck", '''Tip tip = new Tip("Sleep before a test.", "planning");
System.out.println(tip.getText());
System.out.println(tip.getTopic());'''), [
    has("public Tip(String text, String topic)", "Keep the constructor header Tip(String text, String topic).")], xp=2) == "Sleep before a test.\nplanning"

assert code_box("p2-collection", "TipJar.java", TIP_JAR_STARTER, TIP_JAR, TIP_FILE + driver("TipJarCheck", '''TipJar empty = new TipJar();
System.out.println("Empty jar: " + empty.pickTip());
System.out.println("Empty average: " + empty.averageRating());
TipJar jar = new TipJar();
jar.addTip(new Tip("Sleep before a test.", "planning"));
jar.addTip(new Tip("Print the values.", "debugging"));
boolean valid = true;
for(int i = 0; i < 50; i++) {
    Tip tip = jar.pickTip();
    if(tip == null) {
        valid = false;
    }
}
System.out.println("Picks are tips: " + valid);
jar.addRating(5);
jar.addRating(0);
jar.addRating(4);
jar.addRating(6);
System.out.println("Ratings: " + jar.numberOfRatings());
System.out.println("Average: " + jar.averageRating());'''), [
    has("new Random(7)", "Create the generator with new Random(7)."),
    has("nextInt(tips.size())", "Use the number of tips as the bound: nextInt(tips.size())."),
    has("rating >= 1 && rating <= 5", "Keep only the ratings from 1 to 5."),
    has("ratings.isEmpty()", "Return 0 for no ratings before dividing.")], xp=6) == (
    "Empty jar: null\nEmpty average: 0\nPicks are tips: true\nRatings: 2\nAverage: 4")

assert code_box("p2-demo", "TipDemo.java", TIP_DEMO_STARTER, TIP_DEMO, TIP_FILES, [
    has("jar.addTip(new Tip(", "Add each tip as an anonymous object: jar.addTip(new Tip(...));"),
    has("jar.addRating(9)", "Add the rating 9 too; the jar ignores it.")], xp=4, extra=12, name="Program output") == (
    "Empty jar: null\nAverage with no ratings: 0\nTip: Start the assignment the day it is posted. (planning)\n"
    "Tip: Explain your code out loud to a friend. (debugging)\nRatings: 3\nAverage: 3")

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-10",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 10 Workbook",
    "subtitle": "Chapter 6, Part 1: Learning and Using Library Classes",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
