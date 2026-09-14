"""Build workbooks/lecture-02/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-02/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-02
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


def lacks(fragment, message):
    compact = re.sub(r"\s+", "", fragment)
    return f'require(!source.replaceAll("\\\\s+", "").contains({json.dumps(compact)}), {json.dumps(message)});'


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

    public void turnOn()
    {
        on = true;
    }

    public void turnOff()
    {
        on = false;
    }

    public void setBrightness(int newBrightness)
    {
        brightness = newBrightness;
    }

    public void setColor(String newColor)
    {
        color = newColor;
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

GAME_CHARACTER = '''public class GameCharacter
{
    private String name;
    private int health;
    private int xPosition;

    public GameCharacter(String name, int health)
    {
        this.name = name;
        this.health = health;
        xPosition = 0;
    }

    public void move(int distance)
    {
        xPosition = xPosition + distance;
    }

    public void takeDamage(int amount)
    {
        health = health - amount;
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

    public void printState()
    {
        System.out.println(name + ": health=" + health
                           + ", xPosition=" + xPosition);
    }
}
'''

LAMP = [{"name": "SmartLamp.java", "content": SMART_LAMP.rstrip("\n")}]
GAME = [{"name": "GameCharacter.java", "content": GAME_CHARACTER.rstrip("\n")}]

E = {}

# ---------------------------------------------------------------- Section 1
E["p1-1"] = {"type": "table", "xp": 1, "blanks": {
    "c1": {"accept": ["class"], "placeholder": "class / object / reference name", "width": "15rem"},
    "c2": {"accept": ["object", "an object", "instance", "an instance"], "placeholder": "class / object / reference name", "width": "15rem", "show": "object"},
    "c3": {"accept": ["reference-variable name", "reference variable name", "reference variable", "reference-variable", "variable name", "variable", "reference"],
           "placeholder": "class / object / reference name", "width": "15rem", "show": "reference-variable name"}}}
E["p1-2"] = {"type": "short", "xp": 2, "minChars": 30, "answer": b64(
    "`SmartLamp` is the general description of the state and behavior available to smart lamps. "
    "One desk lamp is a concrete object, or instance, created from that class.")}
E["p1-3"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "Yes. Each object stores its own field values even though both objects use the same class definition.")}
E["p1-4"] = {"type": "short", "xp": 2, "minChars": 30, "rows": 4, "answer": b64(
    "One sample answer is class `GameCharacter`, an explorer object, health and position as state, and `move` as a behavior. "
    "Other coherent models are valid.")}
E["p1-5"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "State is the set of values stored in fields. Output is only one possible display of some or all of those values.")}

# ---------------------------------------------------------------- Section 2
E["ex-new"] = example('SmartLamp deskLamp = new SmartLamp("Desk");\n\n// Added so you can see the initial state:\ndeskLamp.printState();\n', files=LAMP)
E["ex-two"] = example(
    'SmartLamp deskLamp = new SmartLamp("Desk");\nSmartLamp readingLamp = new SmartLamp("Reading corner");\n\n'
    '// Added so you can see both states:\ndeskLamp.printState();\nreadingLamp.printState();\n', files=LAMP)
E["p2-1"] = {"type": "table", "xp": 1, "blanks": {
    "cls": {"accept": ["SmartLamp"], "caseSensitive": True, "placeholder": "class name"},
    "var": {"accept": ["deskLamp"], "caseSensitive": True, "placeholder": "variable name"},
    "ctor": {"accept": ['new SmartLamp("Desk")', 'SmartLamp("Desk")', 'new SmartLamp("Desk");'], "caseSensitive": True, "placeholder": "constructor call", "width": "14rem"},
    "arg": {"accept": ['"Desk"', 'Desk'], "caseSensitive": True, "placeholder": "argument", "show": '"Desk"'}}}
p2_2 = 'SmartLamp windowLamp = new SmartLamp("Window");\nwindowLamp.printState();\n'
E["p2-2"] = {"type": "code", "xp": 2, "minLines": 3,
    "starter": "// Create a lamp whose location is \"Window\" and store it in windowLamp.\n\n\nwindowLamp.printState();\n",
    "cases": [{"name": "Program output", "expected": run(p2_2, LAMP)}],
    "check": "\n".join([
        has('SmartLamp windowLamp', "Declare the variable with its type: SmartLamp windowLamp = ..."),
        has('new SmartLamp("Window")', 'Construct the lamp with new SmartLamp("Window").')]),
    "answer": b64(p2_2), "files": LAMP}
E["p2-3"] = {"type": "short", "xp": 2, "minChars": 20, "answer": b64(
    "No object is created. A constructor call using `new` is required:\n\n`windowLamp = new SmartLamp(\"Window\");`")}
E["p2-4"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "They create two distinct objects. Every evaluation of `new SmartLamp(...)` constructs a fresh instance.")}
E["p2-5"] = {"type": "short", "xp": 2, "minChars": 30, "answer": b64(
    "The variable stores a reference that lets the program find the object. "
    "The object has its own identity and fields separately from the variable that currently refers to it.")}

# ---------------------------------------------------------------- Section 3
E["ex-receivers"] = example(
    'SmartLamp deskLamp = new SmartLamp("Desk");\nSmartLamp readingLamp = new SmartLamp("Reading corner");\n\n'
    'deskLamp.turnOn();\nreadingLamp.turnOn();\n\n// Added so you can see both states:\ndeskLamp.printState();\nreadingLamp.printState();\n', files=LAMP)
E["p3-1"] = {"type": "table", "xp": 1, "blanks": {
    "recv": {"accept": ["readingLamp"], "caseSensitive": True, "placeholder": "receiver"},
    "meth": {"accept": ["turnOff", "turnOff()"], "caseSensitive": True, "placeholder": "method"},
    "nargs": {"accept": ["0", "zero", "none", "no arguments"], "placeholder": "how many?", "show": "0"}}}
E["p3-2"] = {"type": "table", "xp": 1, "blanks": {
    "desk": {"accept": ["off", "false", "on=false"], "placeholder": "on or off", "show": "off"},
    "reading": {"accept": ["on", "true", "on=true"], "placeholder": "on or off", "show": "on"}}}
p3_3 = 'SmartLamp deskLamp = new SmartLamp("Desk");\nSmartLamp readingLamp = new SmartLamp("Reading corner");\n\ndeskLamp.printState();\n'
E["p3-3"] = {"type": "code", "xp": 2, "minLines": 4,
    "starter": 'SmartLamp deskLamp = new SmartLamp("Desk");\nSmartLamp readingLamp = new SmartLamp("Reading corner");\n\n// Ask deskLamp to print its state.\n',
    "cases": [{"name": "Program output", "expected": run(p3_3, LAMP)}],
    "check": has("deskLamp.printState()", "Call printState on the receiver deskLamp: deskLamp.printState();"),
    "answer": b64(p3_3), "files": LAMP}
E["p3-4"] = {"type": "short", "xp": 2, "minChars": 30, "answer": b64(
    "`turnOn`, `turnOff`, `setBrightness`, and `setColor` change state. "
    "`getBrightness` returns state information and `printState` displays it.")}
E["p3-5"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "It omits the receiver before the dot, so the client code does not say which lamp object should receive the request.")}

# ---------------------------------------------------------------- Section 4
E["p4-1"] = {"type": "table", "xp": 1, "blanks": {
    "param": {"accept": ["newBrightness"], "caseSensitive": True, "placeholder": "parameter"},
    "arg": {"accept": ["70"], "placeholder": "argument"},
    "type": {"accept": ["int"], "placeholder": "type"}}}
E["p4-2"] = {"type": "table", "xp": 1, "blanks": {
    "t1": {"accept": ["int"]}, "t2": {"accept": ["String"]}, "t3": {"accept": ["boolean"]}, "t4": {"accept": ["String"]}}}
p4_3 = 'SmartLamp deskLamp = new SmartLamp("Desk");\n\ndeskLamp.turnOn();\ndeskLamp.setBrightness(70);\ndeskLamp.setColor("daylight");\ndeskLamp.turnOff();\n\ndeskLamp.printState();\n'
E["p4-3"] = {"type": "code", "xp": 5, "minLines": 8,
    "starter": 'SmartLamp deskLamp = new SmartLamp("Desk");\n\ndeskLamp.turnOn(1);\ndeskLamp.setBrightness("70");\ndeskLamp.setColor(daylight);\ndeskLamp.turnOff();\n\ndeskLamp.printState();\n',
    "cases": [{"name": "Program output", "expected": run(p4_3, LAMP)}],
    "check": "\n".join([
        has("deskLamp.turnOn()", "turnOn takes no arguments: deskLamp.turnOn();"),
        has("deskLamp.setBrightness(70)", "setBrightness takes an int, so pass 70 without quotes."),
        has('deskLamp.setColor("daylight")', 'setColor takes a String, so put daylight in double quotes: "daylight".'),
        has("deskLamp.turnOff()", "Keep the call deskLamp.turnOff(); it was already valid.")]),
    "answer": b64(p4_3), "files": LAMP}
E["p4-4"] = {"type": "short", "xp": 2, "minChars": 30, "answer": b64(
    "The signature is `setBrightness(int)`. Java defines a method signature using the method name and parameter types; "
    "the parameter name is local documentation and the return type does not distinguish overloads.")}
p4_5 = 'SmartLamp readingLamp = new SmartLamp("Reading corner");\n\nreadingLamp.turnOn();\nreadingLamp.setBrightness(35);\nreadingLamp.setColor("warm white");\n\nreadingLamp.printState();\n'
E["p4-5"] = {"type": "code", "xp": 5, "minLines": 7,
    "starter": 'SmartLamp readingLamp = new SmartLamp("Reading corner");\n\n// Turn the lamp on, set its brightness to 35, and set its color to "warm white".\n\n\n\nreadingLamp.printState();\n',
    "cases": [{"name": "Program output", "expected": run(p4_5, LAMP)}],
    "check": "\n".join([
        has("readingLamp.turnOn()", "Ask readingLamp to turn on: readingLamp.turnOn();"),
        has("readingLamp.setBrightness(35)", "Set the brightness with readingLamp.setBrightness(35);"),
        has('readingLamp.setColor("warm white")', 'Set the color with readingLamp.setColor("warm white");')]),
    "answer": b64(p4_5), "files": LAMP}

# ---------------------------------------------------------------- Section 5
E["ex-trace"] = example(
    'SmartLamp deskLamp = new SmartLamp("Desk");\nSmartLamp readingLamp = new SmartLamp("Reading corner");\n\n'
    'deskLamp.turnOn();\ndeskLamp.setBrightness(70);\ndeskLamp.setColor("daylight");\n\n'
    '// Added so you can see both states:\ndeskLamp.printState();\nreadingLamp.printState();\n', files=LAMP)
E["ex-query"] = example(
    'SmartLamp deskLamp = new SmartLamp("Desk");\ndeskLamp.turnOn();\ndeskLamp.setBrightness(70);\n\n'
    'int level = deskLamp.getBrightness();\n\n// Added so you can see the returned value:\nSystem.out.println("level is " + level);\n', files=LAMP)
E["p5-1"] = {"type": "table", "xp": 1, "blanks": {
    "don": {"accept": ["true", "on", "on=true"], "placeholder": "true / false", "show": "true"},
    "dbr": {"accept": ["0"], "placeholder": "brightness"},
    "ron": {"accept": ["false", "off", "on=false"], "placeholder": "true / false", "show": "false"},
    "rbr": {"accept": ["40"], "placeholder": "brightness"}}}
E["ex-p5-1"] = example(
    'SmartLamp deskLamp = new SmartLamp("Desk");\nSmartLamp readingLamp = new SmartLamp("Reading corner");\n\n'
    'deskLamp.turnOn();\nreadingLamp.setBrightness(40);\n\ndeskLamp.printState();\nreadingLamp.printState();\n', files=LAMP, output=False)
E["p5-2"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "They are distinct objects created by separate uses of `new`. Each instance stores its own field values.")}
E["p5-3"] = {"type": "table", "xp": 1, "blanks": {
    "val": {"accept": ["70"], "placeholder": "value"},
    "chg": {"accept": ["no", "false", "it does not", "does not", "no change", "unchanged"], "placeholder": "yes / no", "show": "no"}}}
E["p5-4"] = {"type": "short", "xp": 2, "minChars": 30, "answer": b64(
    "A returned value is passed back to the calling expression and can be stored or used. "
    "Printed output sends text to the terminal and is not automatically available as a value in the program.")}
E["p5-5"] = {"type": "table", "xp": 1, "blanks": {
    "on": {"accept": ["false", "on=false", "off"], "placeholder": "value", "show": "false"},
    "br": {"accept": ["55", "brightness=55"], "placeholder": "value", "show": "55"},
    "col": {"accept": ['"daylight"', "daylight", 'color="daylight"'], "placeholder": "value", "show": '"daylight"'}}}
E["p5-6"] = {"type": "short", "xp": 2, "minChars": 20, "rows": 2, "answer": b64(
    "Examples include calling query methods, printing a state report, using a debugger, or tracing field values in a table.")}

# ---------------------------------------------------------------- Section 6
demo_body = (
    'SmartLamp deskLamp = new SmartLamp("Desk");\nSmartLamp readingLamp = new SmartLamp("Reading corner");\n\n'
    'deskLamp.turnOn();\ndeskLamp.setBrightness(70);\ndeskLamp.setColor("daylight");\n\n'
    'readingLamp.turnOn();\nreadingLamp.setBrightness(35);\n\n'
    'deskLamp.printState();\nreadingLamp.printState();\n\n'
    'int level = deskLamp.getBrightness();\nSystem.out.println("Desk brightness returned: " + level);\n')
E["p6-rebuild"] = {"type": "code", "xp": 5, "minLines": 12,
    "starter": (
        'SmartLamp deskLamp = ______;\nSmartLamp readingLamp = ______;\n\n'
        'deskLamp.______();\ndeskLamp.______(70);\ndeskLamp.______("daylight");\n\n'
        'readingLamp.______();\nreadingLamp.______(35);\n\n'
        'deskLamp.printState();\nreadingLamp.printState();\n\n'
        'int level = ______;\nSystem.out.println("Desk brightness returned: " + level);\n'),
    "cases": [{"name": "Program output", "expected": run(demo_body, LAMP)}],
    "check": "\n".join([
        lacks("______", "Fill in every blank (______) before checking."),
        has('new SmartLamp("Desk")', 'Construct the desk lamp with new SmartLamp("Desk").'),
        has('new SmartLamp("Reading corner")', 'Construct the reading lamp with new SmartLamp("Reading corner").'),
        has("deskLamp.getBrightness()", "Store the returned value of deskLamp.getBrightness() in level.")]),
    "answer": b64(demo_body), "files": LAMP}
LAMP_DEMO = (
    'public class LampDemo\n{\n    public static void main(String[] args)\n    {\n'
    '        SmartLamp deskLamp = new SmartLamp("Desk");\n        SmartLamp readingLamp = new SmartLamp("Reading corner");\n\n'
    '        deskLamp.turnOn();\n        deskLamp.setBrightness(70);\n        deskLamp.setColor("daylight");\n\n'
    '        readingLamp.turnOn();\n        readingLamp.setBrightness(35);\n\n'
    '        deskLamp.printState();\n        readingLamp.printState();\n\n'
    '        int level = deskLamp.getBrightness();\n        System.out.println("Desk brightness returned: " + level);\n    }\n}\n')
E["ex-lampdemo"] = example(LAMP_DEMO, files=LAMP, title="LampDemo.java")
E["p6-1"] = {"type": "short", "xp": 2, "minChars": 30, "rows": 2, "answer": b64(
    "The construction expressions are `new SmartLamp(\"Desk\")` and `new SmartLamp(\"Reading corner\")`. "
    "Their references are stored in `deskLamp` and `readingLamp`.")}
E["p6-2"] = {"type": "table", "xp": 1, "blanks": {
    "don": {"accept": ["true", "on", "on=true"], "placeholder": "on?", "show": "true"},
    "dbr": {"accept": ["70"], "placeholder": "brightness"},
    "dcol": {"accept": ['"daylight"', "daylight"], "placeholder": "color", "show": '"daylight"'},
    "ron": {"accept": ["true", "on", "on=true"], "placeholder": "on?", "show": "true"},
    "rbr": {"accept": ["35"], "placeholder": "brightness"},
    "rcol": {"accept": ['"warm white"', "warm white"], "placeholder": "color", "show": '"warm white"'},
    "level": {"accept": ["70"], "placeholder": "value"}}}
p6_3 = demo_body.replace('readingLamp.setBrightness(35);\n', 'readingLamp.setBrightness(35);\nreadingLamp.setColor("blue");\n')
E["p6-3"] = {"type": "code", "xp": 2, "minLines": 12,
    "starter": demo_body,
    "cases": [{"name": "Program output", "expected": run(p6_3, LAMP)}],
    "check": "\n".join([
        has('readingLamp.setColor("blue")', 'Add the call readingLamp.setColor("blue"); to the reading-lamp configuration.'),
        lacks('deskLamp.setColor("blue")', "Do not change the receiver to deskLamp: only the reading lamp should turn blue.")]),
    "answer": b64(p6_3), "files": LAMP}
E["p6-4"] = {"type": "short", "xp": 2, "minChars": 30, "answer": b64(
    "The public interface states the available method names, parameter types, and return types. "
    "The class hides the implementation details behind that interface.")}

# ---------------------------------------------------------------- Section 7
E["p7-trace"] = {"type": "table", "xp": 1, "blanks": {
    "eh": {"accept": ["85"], "placeholder": "health"}, "ex": {"accept": ["8"], "placeholder": "x-position"},
    "gh": {"accept": ["120"], "placeholder": "health"}, "gx": {"accept": ["-3"], "placeholder": "x-position"}}}
GAME_DEMO = (
    'public class GameCharacterDemo\n{\n    public static void main(String[] args)\n    {\n'
    '        GameCharacter explorer = new GameCharacter("Explorer", 100);\n        GameCharacter guardian = new GameCharacter("Guardian", 120);\n\n'
    '        explorer.move(8);\n        explorer.takeDamage(15);\n        guardian.move(-3);\n\n'
    '        explorer.printState();\n        guardian.printState();\n\n'
    '        int remainingHealth = explorer.getHealth();\n        System.out.println("Explorer health returned: " + remainingHealth);\n    }\n}\n')
E["p7-demo"] = {"type": "code", "xp": 10, "minLines": 16, "maxLines": 30,
    "starter": 'public class GameCharacterDemo\n{\n    public static void main(String[] args)\n    {\n        // Your code here\n    }\n}\n',
    "cases": [{"name": "Program output", "expected": run(GAME_DEMO, GAME)}],
    "check": "\n".join([
        has('new GameCharacter("Explorer", 100)', 'Construct the explorer with new GameCharacter("Explorer", 100).'),
        has('new GameCharacter("Guardian", 120)', 'Construct the guardian with new GameCharacter("Guardian", 120).'),
        has("explorer.move(8)", "Move the explorer by 8: explorer.move(8);"),
        has("explorer.takeDamage(15)", "Apply 15 damage to the explorer: explorer.takeDamage(15);"),
        has("guardian.move(-3)", "Move the guardian by -3: guardian.move(-3);"),
        has("explorer.getHealth()", "Store the explorer's returned health in an int with explorer.getHealth()."),
        'require(source.matches("(?s).*int\\\\s+\\\\w+\\\\s*=\\\\s*explorer\\\\.getHealth\\\\(\\\\).*"), "Store the value returned by explorer.getHealth() in an int variable before printing it.");']),
    "answer": b64(GAME_DEMO), "files": GAME}
assert run(GAME_DEMO, GAME) == "Explorer: health=85, xPosition=8\nGuardian: health=120, xPosition=-3\nExplorer health returned: 85"
assert run(LAMP_DEMO, LAMP) == "Desk: on=true, brightness=70, color=daylight\nReading corner: on=true, brightness=35, color=warm white\nDesk brightness returned: 70"

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-02",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 2 Workbook",
    "subtitle": "Chapter 1: Objects have state and behavior",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
