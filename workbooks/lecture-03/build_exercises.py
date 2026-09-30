"""Build workbooks/lecture-03/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-03/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-03

Most code boxes on this page ask for a class rather than a program. Each of
those boxes has a small driver class on its classpath (the `files` list)
whose main method constructs objects and prints their state; the runner
uses that main when the editor's class has none.
"""
import base64, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402


def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()


def run(code, files=(), inputs=()):
    status, stdout, stderr, _ = run_java(code.rstrip("\n"), inputs, None, files)
    assert status == "ok", f"{status}\n{stderr}"
    return stdout.rstrip("\n")


def example(code, output=True, **kw):
    spec = {"type": "example", "code": code.rstrip("\n"), **kw}
    if output:
        spec["output"] = run(code, kw.get("files", ()))
    return spec


def has(fragment, message):
    """A check line: the source contains `fragment`, ignoring whitespace."""
    compact = re.sub(r"\s+", "", fragment)
    return f'require(source.replaceAll("\\\\s+", "").contains({json.dumps(compact)}), {json.dumps(message)});'


def has_field(fragment, message):
    """Like has(), but the first identifier (after an optional `return`) is a field, so `this.` may precede it."""
    compact = re.sub(r"\s+", "", fragment)
    m = re.fullmatch(r"(return)?([A-Za-z_]\w*)(.*)", compact)
    regex = re.escape(m.group(1) or "") + r"(this\.)?" + re.escape(m.group(2)) + re.escape(m.group(3))
    return f'require(source.replaceAll("\\\\s+", "").matches({json.dumps("(?s).*" + regex + ".*")}), {json.dumps(message)});'


def lacks(fragment, message):
    compact = re.sub(r"\s+", "", fragment)
    return f'require(!source.replaceAll("\\\\s+", "").contains({json.dumps(compact)}), {json.dumps(message)});'


def matches(regex, message):
    """A check line: the whitespace-stripped source matches `regex` (a Java regex, whole string)."""
    return f'require(source.replaceAll("\\\\s+", "").matches({json.dumps("(?s)" + regex)}), {json.dumps(message)});'


def file(name, content):
    return {"name": name, "content": content.rstrip("\n")}


# The complete SmartLamp of this lecture: fields, constructor, and the
# getters and printState (Lecture 4 explains how to write those).
SMART_LAMP = '''public class SmartLamp
{
    private String location;
    private boolean on;
    private int brightness;
    private String color;

    public SmartLamp(String location)
    {
        this.location = location;
        on = false;
        brightness = 0;
        color = "warm white";
    }

    public String getLocation()
    {
        return location;
    }

    public boolean isOn()
    {
        return on;
    }

    public int getBrightness()
    {
        return brightness;
    }

    public String getColor()
    {
        return color;
    }

    public void printState()
    {
        System.out.println(location + ": on=" + on
                           + ", brightness=" + brightness
                           + ", color=" + color);
    }
}
'''

BOOK = '''public class Book
{
    private String title;
    private String author;
    private int pages;
    private boolean referenceOnly;

    public Book(String title, String author, int pages)
    {
        this.title = title;
        this.author = author;
        this.pages = pages;
        referenceOnly = false;
    }

    public String getTitle()
    {
        return title;
    }

    public String getAuthor()
    {
        return author;
    }

    public int getPages()
    {
        return pages;
    }

    public boolean isReferenceOnly()
    {
        return referenceOnly;
    }

    public void printState()
    {
        System.out.println(title + " by " + author
                           + ": pages=" + pages
                           + ", referenceOnly=" + referenceOnly);
    }
}
'''

BOOK_DEMO = '''public class BookDemo
{
    public static void main(String[] args)
    {
        Book first = new Book("The Left Hand of Darkness",
                              "Ursula K. Le Guin", 304);
        Book second = new Book("Kindred", "Octavia E. Butler", 288);
        first.printState();
        second.printState();
    }
}
'''

GAME_CHARACTER = '''public class GameCharacter
{
    private String name;
    private int health;
    private int xPosition;
    private boolean active;

    public GameCharacter(String name, int health, int xPosition)
    {
        this.name = name;
        this.health = health;
        this.xPosition = xPosition;
        active = true;
    }

    public String getName()
    {
        return name;
    }

    public int getHealth()
    {
        return health;
    }

    public int getXPosition()
    {
        return xPosition;
    }

    public boolean isActive()
    {
        return active;
    }

    public void printState()
    {
        System.out.println(name + ": health=" + health
                           + ", xPosition=" + xPosition
                           + ", active=" + active);
    }
}
'''

GAME_DEMO = '''public class GameCharacterDemo
{
    public static void main(String[] args)
    {
        GameCharacter explorer = new GameCharacter("Explorer", 85, 8);
        GameCharacter guardian = new GameCharacter("Guardian", 120, -3);
        explorer.printState();
        guardian.printState();
    }
}
'''

LAMP = [file("SmartLamp.java", SMART_LAMP)]

E = {}

# ---------------------------------------------------------------- Section 1
E["p1-1"] = {"type": "table", "xp": 1, "blanks": {
    "kw1": {"accept": ["public"], "placeholder": "keyword"},
    "kw2": {"accept": ["class"], "placeholder": "keyword"},
    "name": {"accept": ["SmartLamp"], "caseSensitive": True, "placeholder": "class name"},
    "body": {"accept": ["braces", "curly braces", "curly brackets", "the braces", "the outer braces", "outer braces", "{ }", "{}", "brackets", "a pair of braces", "the curly braces", "the curly brackets"],
             "placeholder": "what encloses it?", "show": "the outer braces { }", "width": "12rem"}}}
BOOK_DRIVER = [file("BookWrapperDemo.java",
    'public class BookWrapperDemo\n{\n    public static void main(String[] args)\n    {\n'
    '        Book b = new Book();\n        System.out.println("The Book class compiled: " + (b != null));\n    }\n}\n')]
p1_2 = "public class Book\n{\n}\n"
E["p1-2"] = {"type": "code", "xp": 2, "minLines": 4, "title": "Book.java",
    "starter": "// Write the empty outer wrapper of a public class named Book.\n\n\n\n",
    "cases": [{"name": "Program output", "expected": run(p1_2, BOOK_DRIVER)}],
    "check": "\n".join([
        has("public class Book", "The header is public class Book, in that order."),
        matches(r".*publicclassBook\{\}.*", "The class body is an empty pair of braces: public class Book { }")]),
    "answer": b64(p1_2), "files": BOOK_DRIVER}
E["p1-3"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "Java's grammar requires the access modifier before the `class` keyword. Keywords cannot be reordered freely.")}
E["p1-4"] = {"type": "table", "xp": 1, "blanks": {
    "end": {"accept": ["opening brace", "an opening brace", "brace", "{", "opening curly bracket", "curly bracket", "opening curly brace", "curly brace", "a brace", "an opening curly brace", "an opening curly bracket", "the opening brace"],
            "placeholder": "semicolon or opening brace?", "show": "an opening brace", "width": "14rem"}}}

# ---------------------------------------------------------------- Section 2
FIELD_LISTER = [file("FieldList.java",
    'import java.lang.reflect.Field;\nimport java.lang.reflect.Modifier;\nimport java.util.Arrays;\n\n'
    'public class FieldList\n{\n    public static void main(String[] args)\n    {\n'
    '        Field[] fields = Book.class.getDeclaredFields();\n'
    '        Arrays.sort(fields, (a, b) -> a.getName().compareTo(b.getName()));\n'
    '        System.out.println("Book declares " + fields.length + " field(s):");\n'
    '        for (Field f : fields) {\n'
    '            System.out.println("  " + Modifier.toString(f.getModifiers()) + " " + f.getType().getSimpleName() + " " + f.getName());\n'
    '        }\n    }\n}\n')]
p2_1 = "public class Book\n{\n    private String title;\n    private String author;\n    private int pages;\n    private boolean referenceOnly;\n}\n"
E["p2-1"] = {"type": "code", "xp": 2, "minLines": 7, "title": "Book.java",
    "starter": "public class Book\n{\n    // Declare the four private fields here.\n\n\n\n\n}\n",
    "cases": [{"name": "Declared fields", "expected": run(p2_1, FIELD_LISTER)}],
    "check": "\n".join([
        has("private String title;", "Declare the title as private String title;"),
        has("private String author;", "Declare the author as private String author;"),
        has("private int pages;", "The page count is a whole number: private int pages;"),
        has("private boolean referenceOnly;", "The reference-only status is true or false: private boolean referenceOnly;")]),
    "answer": b64(p2_1), "files": FIELD_LISTER}
E["p2-2"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "The field should use `int` so Java treats the value as a whole number and rejects text assignments.")}
E["p2-3"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "No. The declaration introduces a field name and type. It does not construct a string or choose the intended starting location.")}
E["p2-4"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "No. Each object has its own field. The two separate fields happen to contain equal values.")}

# ---------------------------------------------------------------- Section 3
E["ex-window"] = example('SmartLamp windowLamp = new SmartLamp("Window");\n\n// Added so you can see the four field values:\nwindowLamp.printState();\n', files=LAMP)
E["p3-1"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "A constructor has the same name as the class and has no return type. It runs as part of object construction.")}
E["p3-2"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "The `void` return type makes it a method. A constructor has no return type.")}
E["p3-3"] = {"type": "table", "xp": 1, "blanks": {
    "loc": {"accept": ['"Window"', "Window"], "caseSensitive": True, "placeholder": "value", "show": '"Window"'},
    "on": {"accept": ["false"], "placeholder": "value"},
    "br": {"accept": ["0"], "placeholder": "value"},
    "col": {"accept": ['"warm white"', "warm white"], "placeholder": "value", "show": '"warm white"'}}}
E["p3-4"] = {"type": "table", "xp": 1, "blanks": {
    "loc": {"accept": ["caller", "the caller"], "placeholder": "caller / class", "show": "caller"},
    "on": {"accept": ["class", "the class"], "placeholder": "caller / class", "show": "class"},
    "br": {"accept": ["class", "the class"], "placeholder": "caller / class", "show": "class"},
    "col": {"accept": ["class", "the class"], "placeholder": "caller / class", "show": "class"}}}
E["p3-5"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "It records that 0 is the intended starting brightness and that the field was not accidentally omitted from initialization.")}

# ---------------------------------------------------------------- Section 4
BOOK_FILE = [file("Book.java", BOOK)]
E["p4-1"] = {"type": "table", "xp": 1, "blanks": {
    "param": {"accept": ["lampLocation", "String lampLocation"], "caseSensitive": True, "placeholder": "parameter"},
    "arg": {"accept": ['"Desk"', "Desk"], "caseSensitive": True, "placeholder": "argument", "show": '"Desk"'}}}
E["p4-2"] = {"type": "table", "xp": 1, "blanks": {
    "title": {"accept": ['"Kindred"', "Kindred"], "caseSensitive": True, "placeholder": "value", "show": '"Kindred"'},
    "author": {"accept": ['"Octavia E. Butler"', "Octavia E. Butler"], "caseSensitive": True, "placeholder": "value", "show": '"Octavia E. Butler"', "width": "13rem"},
    "pages": {"accept": ["288"], "placeholder": "value"}}}
E["ex-book-wrong"] = example(
    '// The Book constructor is Book(String title, String author, int pages).\n'
    '// Press Run to read the compiler\'s complaint about this call.\nBook novel = new Book(288, "Kindred", "Octavia E. Butler");\n', files=BOOK_FILE, output=False)
E["p4-3"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "The first parameter requires a `String`, but the call supplies an `int`. The remaining values are also in the wrong positions.")}
GC_DRIVER = [file("CharacterDemo.java",
    'public class CharacterDemo\n{\n    public static void main(String[] args)\n    {\n'
    '        GameCharacter explorer = new GameCharacter("Explorer", 85, 8);\n        explorer.printState();\n    }\n}\n')]
GC_TAIL = (
    '    {\n        this.name = name;\n        this.health = health;\n        this.xPosition = xPosition;\n    }\n\n'
    '    // Supplied so the demo can show the state. Lecture 4 explains how to write it.\n'
    '    public void printState()\n    {\n        System.out.println(name + ": health=" + health + ", xPosition=" + xPosition);\n    }\n}\n')
GC_HEAD = 'public class GameCharacter\n{\n    private String name;\n    private int health;\n    private int xPosition;\n\n'
p4_4 = GC_HEAD + '    public GameCharacter(String name, int health, int xPosition)\n' + GC_TAIL
E["p4-4"] = {"type": "code", "xp": 2, "minLines": 18, "maxLines": 24, "title": "GameCharacter.java",
    "starter": GC_HEAD + '    // Write the constructor header on the next line. Its body is already written.\n\n' + GC_TAIL,
    "cases": [{"name": "Program output", "expected": run(p4_4, GC_DRIVER)}],
    "check": "\n".join([
        has("public GameCharacter(String name, int health, int xPosition)", "The header is public GameCharacter(String name, int health, int xPosition): the class name, no return type, three typed parameters."),
        lacks("void GameCharacter", "A constructor has no return type, not even void.")]),
    "answer": b64(p4_4), "files": GC_DRIVER}
E["p4-5"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "Parameters disappear when the constructor finishes. Fields remain with the object, so they preserve values the object needs later.")}

# ---------------------------------------------------------------- Section 5
E["ex-assign"] = example('int brightness = 0;\nSystem.out.println(brightness);\n\nbrightness = 25;\nSystem.out.println(brightness);\n')
E["p5-1"] = {"type": "table", "xp": 1, "blanks": {
    "val": {"accept": ["25"], "placeholder": "value"}}}
E["p5-2"] = {"type": "table", "xp": 1, "blanks": {
    "read": {"accept": ["lampLocation", "the parameter lampLocation", "parameter lampLocation", "the parameter"], "caseSensitive": True, "placeholder": "variable", "show": "lampLocation"},
    "chg": {"accept": ["location", "the field location", "field location", "the field", "this.location"], "caseSensitive": True, "placeholder": "variable", "show": "location"}}}
E["p5-3"] = {"type": "short", "xp": 2, "minChars": 30, "rows": 3, "answer": b64(
    "The parameter declaration is closer, so both unqualified names mean the parameter. The statement assigns the parameter to itself and never selects the field.")}
BOOK_REPAIR_DRIVER = [file("BookRepairDemo.java",
    'public class BookRepairDemo\n{\n    public static void main(String[] args)\n    {\n'
    '        Book novel = new Book("Kindred", "Octavia E. Butler", 288);\n        novel.printState();\n    }\n}\n')]
BOOK_REPAIR_HEAD = 'public class Book\n{\n    private String title;\n    private String author;\n    private int pages;\n\n    public Book(String title, String author, int pages)\n    {\n'
BOOK_REPAIR_TAIL = (
    '    }\n\n    // Supplied so the demo can show the state. Lecture 4 explains how to write it.\n'
    '    public void printState()\n    {\n        System.out.println(title + " by " + author + ": pages=" + pages);\n    }\n}\n')
p5_4 = BOOK_REPAIR_HEAD + '        this.title = title;\n        this.author = author;\n        this.pages = pages;\n' + BOOK_REPAIR_TAIL
E["p5-4"] = {"type": "code", "xp": 3, "minLines": 18, "maxLines": 24, "title": "Book.java",
    "starter": BOOK_REPAIR_HEAD + '        title = title;\n        author = author;\n        pages = pages;\n' + BOOK_REPAIR_TAIL,
    "cases": [{"name": "Program output", "expected": run(p5_4, BOOK_REPAIR_DRIVER)}],
    "check": "\n".join([
        has("this.title = title;", "Store the parameter in the field: this.title = title;"),
        has("this.author = author;", "Store the parameter in the field: this.author = author;"),
        has("this.pages = pages;", "Store the parameter in the field: this.pages = pages;")]),
    "answer": b64(p5_4), "files": BOOK_REPAIR_DRIVER}
E["p5-5"] = {"type": "short", "xp": 2, "minChars": 30, "rows": 3, "answer": b64(
    "`this.pages` is the field of the current object; `=` stores the right-side value into that field; the right-side `pages` is the constructor parameter.")}

# ---------------------------------------------------------------- Section 6
E["ex-two"] = example('SmartLamp deskLamp = new SmartLamp("Desk");\nSmartLamp readingLamp = new SmartLamp("Reading corner");\n\ndeskLamp.printState();\nreadingLamp.printState();\n', files=LAMP)
LAMP_DRIVER = [file("LampDemo.java",
    'public class LampDemo\n{\n    public static void main(String[] args)\n    {\n'
    '        SmartLamp deskLamp = new SmartLamp("Desk");\n        SmartLamp readingLamp = new SmartLamp("Reading corner");\n'
    '        deskLamp.printState();\n        readingLamp.printState();\n    }\n}\n')]
LAMP_TAIL = (
    '    // Supplied so the demo can show the state. Lecture 4 explains how to write it.\n'
    '    public void printState()\n    {\n        System.out.println(location + ": on=" + on\n'
    '                           + ", brightness=" + brightness\n                           + ", color=" + color);\n    }\n}\n')
p6_1 = ('public class SmartLamp\n{\n    private String location;\n    private boolean on;\n    private int brightness;\n    private String color;\n\n'
        '    public SmartLamp(String location)\n    {\n        this.location = location;\n        on = false;\n        brightness = 0;\n        color = "warm white";\n    }\n\n' + LAMP_TAIL)
E["p6-1"] = {"type": "code", "xp": 5, "minLines": 20, "maxLines": 30, "title": "SmartLamp.java",
    "starter": 'public class SmartLamp\n{\n    // Declare the four fields.\n\n\n\n\n    // Write the constructor.\n\n\n\n\n\n\n\n' + LAMP_TAIL,
    "cases": [{"name": "Program output", "expected": run(p6_1, LAMP_DRIVER)}],
    "check": "\n".join([
        has("private String location;", "Declare the location field: private String location;"),
        has("private boolean on;", "Declare the on field: private boolean on;"),
        has("private int brightness;", "Declare the brightness field: private int brightness;"),
        has("private String color;", "Declare the color field: private String color;"),
        matches(r".*publicSmartLamp\(String\w+\)\{.*", "The constructor header is public SmartLamp(String location): the class name, no return type, one String parameter."),
        lacks("void SmartLamp", "A constructor has no return type, not even void."),
        has_field("on = false;", "Give on a fixed starting value: on = false;"),
        has_field("brightness = 0;", "Give brightness a fixed starting value: brightness = 0;"),
        has('color = "warm white";', 'Give color a fixed starting value: color = "warm white";')]),
    "answer": b64(p6_1), "files": LAMP_DRIVER}
E["p6-2"] = {"type": "table", "xp": 1, "blanks": {
    "loc": {"accept": ["argument", "an argument", "the argument"], "placeholder": "argument / fixed value", "show": "argument", "width": "12rem"},
    "on": {"accept": ["fixed value", "fixed", "a fixed value"], "placeholder": "argument / fixed value", "show": "fixed value", "width": "12rem"},
    "br": {"accept": ["fixed value", "fixed", "a fixed value"], "placeholder": "argument / fixed value", "show": "fixed value", "width": "12rem"},
    "col": {"accept": ["fixed value", "fixed", "a fixed value"], "placeholder": "argument / fixed value", "show": "fixed value", "width": "12rem"}}}
E["p6-3"] = {"type": "short", "xp": 2, "minChars": 30, "rows": 3, "answer": b64(
    "The first statement declares a field and its type. The second assignment stores a constructor parameter value in that field of the current object.")}

# ---------------------------------------------------------------- Section 7
BOOK_DEMO_FILE = [file("BookDemo.java", BOOK_DEMO)]
E["p7a-book"] = {"type": "code", "xp": 10, "minLines": 24, "maxLines": 44, "title": "Book.java",
    "starter": "public class Book\n{\n    // fields\n\n\n\n\n    // constructor\n\n\n\n\n\n\n    // getters and printState, written like the ones in SmartLamp\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of BookDemo", "expected": run(BOOK, BOOK_DEMO_FILE)}],
    "check": "\n".join([
        has("private String title;", "Declare private String title;"),
        has("private String author;", "Declare private String author;"),
        has("private int pages;", "Declare private int pages;"),
        has("private boolean referenceOnly;", "Declare private boolean referenceOnly;"),
        has("public Book(String title, String author, int pages)", "The constructor header is public Book(String title, String author, int pages)."),
        has("this.title = title;", "Use this to store the parameter in the same-named field: this.title = title;"),
        has("this.author = author;", "Use this to store the parameter in the same-named field: this.author = author;"),
        has("this.pages = pages;", "Use this to store the parameter in the same-named field: this.pages = pages;"),
        has_field("referenceOnly = false;", "Give referenceOnly the fixed starting value false."),
        has("String getTitle()", "Include the getter String getTitle()."),
        has("String getAuthor()", "Include the getter String getAuthor()."),
        has("int getPages()", "Include the getter int getPages()."),
        has("boolean isReferenceOnly()", "Include the getter boolean isReferenceOnly().")]),
    "answer": b64(BOOK), "files": BOOK_DEMO_FILE}
E["p7a-demo"] = {"type": "code", "xp": 3, "minLines": 10, "maxLines": 20, "title": "BookDemo.java",
    "starter": "public class BookDemo\n{\n    public static void main(String[] args)\n    {\n        // Construct the two books and print their state.\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(BOOK_DEMO, BOOK_FILE)}],
    "check": "\n".join([
        has('new Book("The Left Hand of Darkness", "Ursula K. Le Guin", 304)', 'Construct the first book with new Book("The Left Hand of Darkness", "Ursula K. Le Guin", 304).'),
        has('new Book("Kindred", "Octavia E. Butler", 288)', 'Construct the second book with new Book("Kindred", "Octavia E. Butler", 288).'),
        matches(r".*\.printState\(\);.*\.printState\(\);.*", "Ask each book to print its state with printState().")]),
    "answer": b64(BOOK_DEMO), "files": BOOK_FILE}
GAME_DEMO_FILE = [file("GameCharacterDemo.java", GAME_DEMO)]
GAME_FILE = [file("GameCharacter.java", GAME_CHARACTER)]
E["p7b-character"] = {"type": "code", "xp": 10, "minLines": 24, "maxLines": 44, "title": "GameCharacter.java",
    "starter": "public class GameCharacter\n{\n    // fields\n\n\n\n\n    // constructor\n\n\n\n\n\n\n    // getters and printState\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of GameCharacterDemo", "expected": run(GAME_CHARACTER, GAME_DEMO_FILE)}],
    "check": "\n".join([
        has("private String name;", "Declare private String name;"),
        has("private int health;", "Declare private int health;"),
        has("private int xPosition;", "Declare private int xPosition;"),
        has("private boolean active;", "Declare private boolean active;"),
        has("public GameCharacter(String name, int health, int xPosition)", "The constructor header is public GameCharacter(String name, int health, int xPosition)."),
        has("this.name = name;", "Use this to store the parameter in the same-named field: this.name = name;"),
        has("this.health = health;", "Use this to store the parameter in the same-named field: this.health = health;"),
        has("this.xPosition = xPosition;", "Use this to store the parameter in the same-named field: this.xPosition = xPosition;"),
        has_field("active = true;", "Give active the fixed starting value true."),
        has("String getName()", "Include the getter String getName()."),
        has("int getHealth()", "Include the getter int getHealth()."),
        has("int getXPosition()", "Include the getter int getXPosition()."),
        has("boolean isActive()", "Include the getter boolean isActive().")]),
    "answer": b64(GAME_CHARACTER), "files": GAME_DEMO_FILE}
E["p7b-demo"] = {"type": "code", "xp": 3, "minLines": 10, "maxLines": 20, "title": "GameCharacterDemo.java",
    "starter": "public class GameCharacterDemo\n{\n    public static void main(String[] args)\n    {\n        // Construct the two characters and print their state.\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(GAME_DEMO, GAME_FILE)}],
    "check": "\n".join([
        has('new GameCharacter("Explorer", 85, 8)', 'Construct the explorer with new GameCharacter("Explorer", 85, 8).'),
        has('new GameCharacter("Guardian", 120, -3)', 'Construct the guardian with new GameCharacter("Guardian", 120, -3).'),
        matches(r".*\.printState\(\);.*\.printState\(\);.*", "Ask each character to print its state with printState().")]),
    "answer": b64(GAME_DEMO), "files": GAME_FILE}
E["p7-1"] = {"type": "table", "xp": 1, "blanks": {
    "title": {"accept": ["argument", "an argument", "the argument", "argument value"], "placeholder": "argument / fixed value", "show": "argument", "width": "12rem"},
    "author": {"accept": ["argument", "an argument", "the argument", "argument value"], "placeholder": "argument / fixed value", "show": "argument", "width": "12rem"},
    "pages": {"accept": ["argument", "an argument", "the argument", "argument value"], "placeholder": "argument / fixed value", "show": "argument", "width": "12rem"},
    "ref": {"accept": ["fixed value", "fixed", "a fixed value", "false", "fixed value false", "the fixed value false"], "placeholder": "argument / fixed value", "show": "fixed value (false)", "width": "12rem"}}}
E["p7-2"] = {"type": "short", "xp": 2, "minChars": 30, "rows": 3, "answer": b64(
    "The parameters hide fields with the same names, so `this` selects those fields. There is no parameter named `referenceOnly`, so the unqualified name already means the field.")}
E["p7-3"] = {"type": "table", "xp": 1, "blanks": {
    "name": {"accept": ['"Guardian"', "Guardian"], "caseSensitive": True, "placeholder": "value", "show": '"Guardian"'},
    "health": {"accept": ["120"], "placeholder": "value"},
    "x": {"accept": ["-3"], "placeholder": "value"},
    "active": {"accept": ["true"], "placeholder": "value"}}}
E["p7-4"] = {"type": "short", "xp": 2, "minChars": 30, "rows": 3, "answer": b64(
    "The printed objects retain their different constructor-supplied titles/names, page counts, health, or positions. Each result matches its own constructor call.")}

assert run(BOOK, BOOK_DEMO_FILE) == "The Left Hand of Darkness by Ursula K. Le Guin: pages=304, referenceOnly=false\nKindred by Octavia E. Butler: pages=288, referenceOnly=false"
assert run(GAME_CHARACTER, GAME_DEMO_FILE) == "Explorer: health=85, xPosition=8, active=true\nGuardian: health=120, xPosition=-3, active=true"

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-03",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 3 Workbook",
    "subtitle": "Chapter 2, Part 1: A class defines an object's state",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
