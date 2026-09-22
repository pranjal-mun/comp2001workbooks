"""Build workbooks/lecture-05/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-05/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-05

The boxes on this page work with two collaborating classes. A box that asks
for a method inside Flashlight has the finished Battery class and a small
driver class on its classpath (the `files` list); the driver's main method
calls the method and prints what comes back, and the runner uses that main
when the editor's class has none.
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


def driver(name, body):
    """A hidden class whose main method exercises the student's class."""
    lines = "\n".join("        " + line for line in body.strip("\n").splitlines())
    return [file(f"{name}.java", f"public class {name}\n{{\n    public static void main(String[] args)\n    {{\n{lines}\n    }}\n}}\n")]


# The complete Battery and Flashlight of this lecture (Section 6).
BATTERY = '''public class Battery
{
    private int capacity;
    private int charge;

    public Battery(int capacity)
    {
        this.capacity = capacity;
        charge = capacity;
    }

    public int getCharge()
    {
        return charge;
    }

    public boolean isEmpty()
    {
        return charge == 0;
    }

    public void drain(int amount)
    {
        if(amount > 0) {
            charge = charge - amount;
            if(charge < 0) {
                charge = 0;
            }
        }
    }

    public void recharge()
    {
        charge = capacity;
    }
}
'''

FLASHLIGHT = '''public class Flashlight
{
    private Battery battery;
    private boolean on;

    public Flashlight()
    {
        battery = new Battery(100);
        on = false;
    }

    public Flashlight(Battery battery)
    {
        this.battery = battery;
        on = false;
    }

    public void turnOn()
    {
        if(!battery.isEmpty()) {
            on = true;
        }
    }

    public void turnOff()
    {
        on = false;
    }

    public void useForOneMinute()
    {
        if(on) {
            battery.drain(1);
            updatePowerState();
        }
    }

    private void updatePowerState()
    {
        if(battery.isEmpty()) {
            on = false;
        }
    }

    public boolean isOn()
    {
        return on;
    }

    public int getBatteryCharge()
    {
        return battery.getCharge();
    }
}
'''
BATTERY_FILE = [file("Battery.java", BATTERY)]
FLASHLIGHT_FILES = BATTERY_FILE + [file("Flashlight.java", FLASHLIGHT)]

# Flashlight without its last method, so a box can ask for getBatteryCharge().
FLASHLIGHT_HEAD = FLASHLIGHT[:FLASHLIGHT.index("    public int getBatteryCharge()")]

FUEL_TANK = '''public class FuelTank
{
    private int capacity;
    private int fuel;

    public FuelTank(int capacity)
    {
        this.capacity = capacity;
        fuel = capacity;
    }

    public int getFuel()
    {
        return fuel;
    }

    public boolean isEmpty()
    {
        return fuel == 0;
    }

    public void consume(int amount)
    {
        if(amount > 0) {
            fuel = fuel - amount;
            if(fuel < 0) {
                fuel = 0;
            }
        }
    }

    public void refill()
    {
        fuel = capacity;
    }
}
'''

SCOOTER = '''public class Scooter
{
    private String name;
    private FuelTank tank;
    private boolean running;

    public Scooter(String name)
    {
        this.name = name;
        tank = new FuelTank(100);
        running = false;
    }

    public Scooter(String name, FuelTank tank)
    {
        this.name = name;
        this.tank = tank;
        running = false;
    }

    public void start()
    {
        if(!tank.isEmpty()) {
            running = true;
        }
    }

    public void stop()
    {
        running = false;
    }

    public void ride(int distance)
    {
        if(running && distance > 0) {
            tank.consume(distance);
            if(tank.isEmpty()) {
                running = false;
            }
        }
    }

    public int getFuel()
    {
        return tank.getFuel();
    }

    public boolean isRunning()
    {
        return running;
    }
}
'''

SCOOTER_DEMO = '''public class ScooterDemo
{
    public static void main(String[] args)
    {
        FuelTank tank = new FuelTank(5);
        Scooter scooter = new Scooter("Runabout", tank);

        scooter.start();

        scooter.ride(2);
        System.out.println("After first ride - fuel: " +
                            scooter.getFuel() + ", running: " +
                            scooter.isRunning());

        scooter.ride(4);
        System.out.println("After second ride - fuel: " +
                            scooter.getFuel() + ", running: " +
                            scooter.isRunning());
    }
}
'''

ACCOUNT = '''public class Account
{
    private int balance;

    public Account(int openingBalance)
    {
        balance = openingBalance;
    }

    public int getBalance()
    {
        return balance;
    }

    public boolean canAfford(int amount)
    {
        return amount > 0 && balance >= amount;
    }

    public boolean withdraw(int amount)
    {
        if(canAfford(amount)) {
            balance = balance - amount;
            return true;
        }
        else {
            return false;
        }
    }

    public void deposit(int amount)
    {
        if(amount > 0) {
            balance = balance + amount;
        }
    }
}
'''

PAYMENT_CARD = '''public class PaymentCard
{
    private String label;
    private Account account;

    public PaymentCard(String label, Account account)
    {
        this.label = label;
        this.account = account;
    }

    public boolean buy(int amount)
    {
        return account.withdraw(amount);
    }

    public int getBalance()
    {
        return account.getBalance();
    }

    public String getLabel()
    {
        return label;
    }
}
'''

SHARED_ACCOUNT_DEMO = '''public class SharedAccountDemo
{
    public static void main(String[] args)
    {
        Account account = new Account(100);
        PaymentCard cardA = new PaymentCard("Card A", account);
        PaymentCard cardB = new PaymentCard("Card B", account);

        cardA.buy(30);
        System.out.println("Card A balance: " + cardA.getBalance());
        System.out.println("Card B balance: " + cardB.getBalance());

        boolean secondPurchase = cardB.buy(80);
        System.out.println("Second purchase succeeded: " +
                            secondPurchase);
        System.out.println("Final balance: " + account.getBalance());
    }
}
'''

SHORT = lambda answer, chars=20, rows=2, xp=2: {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}  # noqa: E731


def owner(cls):
    return {"accept": [cls], "placeholder": "Flashlight / Battery", "show": cls}


E = {}

# ---------------------------------------------------------------- Section 1
E["p1-1"] = {"type": "table", "xp": 1, "blanks": {
    "on": owner("Flashlight"), "capacity": owner("Battery"), "charge": owner("Battery"),
    "turnOff": owner("Flashlight"), "drain": owner("Battery"), "recharge": owner("Battery")}}
E["p1-2"] = SHORT("The two values could disagree. There should be one authoritative charge value, owned by `Battery`; the `Flashlight` should ask for it instead of keeping its own copy.", rows=3)
E["p1-3"] = SHORT("A class boundary should represent a useful, separate responsibility. Moving every field into its own class adds complexity without necessarily making the design clearer or more reusable.", rows=3)
E["p1-4"] = {"type": "table", "xp": 1, "blanks": {
    "c0": {"accept": ["3"], "placeholder": "charge"},
    "c1": {"accept": ["2"], "placeholder": "charge"},
    "c2": {"accept": ["0"], "placeholder": "charge"},
    "c3": {"accept": ["3"], "placeholder": "charge"}}}
E["ex-battery-trace"] = example('Battery battery = new Battery(3);\nSystem.out.println(battery.getCharge());\n\nbattery.drain(1);\nSystem.out.println(battery.getCharge());\n\nbattery.drain(5);\nSystem.out.println(battery.getCharge());\n\nbattery.recharge();\nSystem.out.println(battery.getCharge());\n', files=BATTERY_FILE)
assert E["ex-battery-trace"]["output"] == "3\n2\n0\n3"
E["p1-5"] = SHORT("`Battery` owns the charge and the rule that keeps it valid. Enforcing the rule in one place protects every caller and avoids duplicated checks scattered across many device classes.", rows=3)

# ---------------------------------------------------------------- Section 2
E["p2-1"] = {"type": "table", "xp": 1, "blanks": {
    "decl": {"accept": ["private TemperatureSensor sensor;", "private TemperatureSensor sensor"], "caseSensitive": True,
             "placeholder": "the field declaration", "show": "private TemperatureSensor sensor;", "width": "18rem"}}}
E["p2-2"] = {"type": "table", "xp": 1, "blanks": {
    "mod": {"accept": ["private"], "caseSensitive": True, "placeholder": "part"},
    "type": {"accept": ["Battery"], "caseSensitive": True, "placeholder": "part"},
    "name": {"accept": ["battery"], "caseSensitive": True, "placeholder": "part"}}}
E["p2-3"] = {"type": "table", "xp": 1, "blanks": {
    "value": {"accept": ["null"], "placeholder": "value"},
    "count": {"accept": ["0", "zero", "none"], "placeholder": "how many?", "show": "zero"}}}
E["p2-4"] = SHORT("The first call has no `Battery` object as its receiver, because the field is still `null`. The collaborator must be created or assigned before its methods are called.", rows=3)
DIAGRAM = {"accept": ["class diagram", "class", "the class diagram"], "placeholder": "class / object diagram", "show": "class diagram", "width": "12rem"}
OBJECT_DIAGRAM = {"accept": ["object diagram", "object", "the object diagram"], "placeholder": "class / object diagram", "show": "object diagram", "width": "12rem"}
E["p2-5"] = {"type": "table", "xp": 1, "blanks": {"a": DIAGRAM, "b": OBJECT_DIAGRAM, "c": dict(OBJECT_DIAGRAM)}}

# ---------------------------------------------------------------- Section 3
E["p3-1"] = {"type": "table", "xp": 1, "blanks": {
    "count": {"accept": ["2", "two"], "placeholder": "how many?", "show": "two"},
    "classes": {"accept": ["Flashlight and Battery", "Battery and Flashlight", "Flashlight, Battery", "Battery, Flashlight", "a Flashlight and a Battery", "one Flashlight and one Battery"],
                "placeholder": "their classes", "show": "Flashlight and Battery", "width": "14rem"}}}
E["p3-2"] = {"type": "table", "xp": 1, "blanks": {
    "f": {"accept": ["2", "two"], "placeholder": "how many?", "show": "two"},
    "b": {"accept": ["2", "two"], "placeholder": "how many?", "show": "two"},
    "share": {"accept": ["no", "no, each has its own", "they do not share"], "placeholder": "yes / no", "show": "no"}}}
KIND = lambda show: {"accept": [show], "placeholder": "declaration / construction / assignment / method call", "show": show, "width": "18rem"}  # noqa: E731
E["p3-3"] = {"type": "table", "xp": 1, "blanks": {
    "k1": KIND("declaration"), "k2": KIND("construction"),
    "k3": {"accept": ["assignment", "assignment containing a construction", "assignment and construction", "construction and assignment", "assignment with a construction"],
           "placeholder": "declaration / construction / assignment / method call", "show": "assignment (containing a construction)", "width": "18rem"},
    "k4": {"accept": ["method call", "call", "a method call"], "placeholder": "declaration / construction / assignment / method call", "show": "method call", "width": "18rem"}}}
E["p3-4"] = SHORT("Both names are `battery`. `this.battery` identifies the field of the new flashlight; the unqualified `battery` identifies the constructor parameter. The assignment stores the supplied reference in the field.", rows=3)
E["p3-5"] = SHORT("One `Battery` and one `Flashlight`. `testBattery` and `testLight`'s `battery` field both refer to the same battery object.", rows=3)
CTOR = {"placeholder": "no-argument / Battery-parameter", "width": "14rem"}
E["p3-6"] = {"type": "table", "xp": 1, "blanks": {
    "c1": {"accept": ["no-argument", "no-argument constructor", "Flashlight()", "the no-argument constructor", "no argument", "default"], "show": "no-argument", **CTOR},
    "n1": {"accept": ["yes"], "placeholder": "yes / no"},
    "c2": {"accept": ["Battery-parameter", "Battery-parameter constructor", "Flashlight(Battery)", "Flashlight(Battery battery)", "the Battery-parameter constructor", "Battery parameter"], "show": "Battery-parameter", **CTOR},
    "n2": {"accept": ["no"], "placeholder": "yes / no"}}}
E["ex-two-lights"] = example('Flashlight first = new Flashlight();\nFlashlight second = new Flashlight();\n\nfirst.turnOn();\nfirst.useForOneMinute();\nSystem.out.println("first: " + first.getBatteryCharge());\nSystem.out.println("second: " + second.getBatteryCharge());\n', files=FLASHLIGHT_FILES)
assert E["ex-two-lights"]["output"] == "first: 99\nsecond: 100"
E["ex-receive"] = example('Battery testBattery = new Battery(3);\nFlashlight testLight = new Flashlight(testBattery);\n\ntestLight.turnOn();\ntestLight.useForOneMinute();\nSystem.out.println("through the flashlight: " + testLight.getBatteryCharge());\nSystem.out.println("through testBattery: " + testBattery.getCharge());\n', files=FLASHLIGHT_FILES)
assert E["ex-receive"]["output"] == "through the flashlight: 2\nthrough testBattery: 2"

# ---------------------------------------------------------------- Section 4
CHARGE_DRIVER = driver("ChargeDemo", 'Flashlight light = new Flashlight(new Battery(3));\nSystem.out.println("Charge: " + light.getBatteryCharge());')
p4_1 = FLASHLIGHT_HEAD + "    public int getBatteryCharge()\n    {\n        return battery.getCharge();\n    }\n}\n"
E["p4-1"] = {"type": "code", "xp": 2, "minLines": 40, "maxLines": 56, "title": "Flashlight.java",
    "starter": FLASHLIGHT_HEAD + "    // Repair the call so it has an object as its receiver.\n    public int getBatteryCharge()\n    {\n        return Battery.getCharge();\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(p4_1, BATTERY_FILE + CHARGE_DRIVER)}],
    "check": "\n".join([
        lacks("Battery.getCharge()", "Battery names the class, not an object, so Battery.getCharge() has no receiver."),
        has_field("battery.getCharge()", "Call the method on the field that refers to the battery object: battery.getCharge().")]),
    "answer": b64(p4_1), "files": BATTERY_FILE + CHARGE_DRIVER}
E["p4-1-why"] = SHORT("`Battery` names the class, not a particular battery object, and `getCharge` is an instance method, so it needs an object to run on. Fix: `battery.getCharge();`. (`static` methods come later.)", rows=3)
E["p4-2"] = {"type": "table", "xp": 1, "blanks": {
    "empty": {"accept": ["false"], "placeholder": "true / false"},
    "not": {"accept": ["true"], "placeholder": "true / false"},
    "on": {"accept": ["true"], "placeholder": "true / false"},
    "charge": {"accept": ["2"], "placeholder": "charge"}}}
E["p4-3"] = {"type": "table", "xp": 1, "blanks": {
    "empty": {"accept": ["true"], "placeholder": "true / false"},
    "not": {"accept": ["false"], "placeholder": "true / false"},
    "on": {"accept": ["false"], "placeholder": "true / false"}}}
E["ex-turn-on"] = example('Battery low = new Battery(2);\nFlashlight light = new Flashlight(low);\nlight.turnOn();\nSystem.out.println("on: " + light.isOn() + ", charge: " + light.getBatteryCharge());\n\nBattery flat = new Battery(2);\nflat.drain(2);\nFlashlight dark = new Flashlight(flat);\ndark.turnOn();\nSystem.out.println("on: " + dark.isOn() + ", charge: " + dark.getBatteryCharge());\n', files=FLASHLIGHT_FILES)
assert E["ex-turn-on"]["output"] == "on: true, charge: 2\non: false, charge: 0"
KIND_CALL = {"placeholder": "internal / external", "width": "9rem"}
RECEIVER_BATTERY = {"accept": ["battery", "the battery", "the battery field", "battery field"], "placeholder": "receiver", "show": "battery", "width": "14rem"}
E["p4-4"] = {"type": "table", "xp": 1, "blanks": {
    "ka": {"accept": ["external"], "show": "external", **KIND_CALL}, "ra": dict(RECEIVER_BATTERY),
    "kb": {"accept": ["internal"], "show": "internal", **KIND_CALL},
    "rb": {"accept": ["this", "the current object", "the current Flashlight object", "the current flashlight", "this flashlight", "the flashlight", "the Flashlight object", "the same object", "this object", "the flashlight itself"],
           "placeholder": "receiver", "show": "the current Flashlight object", "width": "14rem"},
    "kc": {"accept": ["external"], "show": "external", **KIND_CALL}, "rc": dict(RECEIVER_BATTERY)}}
E["p4-5"] = SHORT("`private` prevents access from outside the defining class. Methods of that same class, such as another instance method, may still call the private helper internally.", rows=3)
DELEGATE_DRIVER = driver("DelegateDemo", 'Battery small = new Battery(3);\nFlashlight light = new Flashlight(small);\nSystem.out.println("Charge: " + light.getBatteryCharge());\nlight.turnOn();\nlight.useForOneMinute();\nSystem.out.println("Charge: " + light.getBatteryCharge());\nsmall.recharge();\nSystem.out.println("Charge: " + light.getBatteryCharge());')
E["p4-6"] = {"type": "code", "xp": 2, "minLines": 40, "maxLines": 56, "title": "Flashlight.java",
    "starter": FLASHLIGHT_HEAD + "    // Write getBatteryCharge() here. Ask the battery; do not add a charge field.\n\n\n\n\n}\n",
    "cases": [{"name": "Program output", "expected": run(p4_1, BATTERY_FILE + DELEGATE_DRIVER)}],
    "check": "\n".join([
        has("public int getBatteryCharge()", "The header is public int getBatteryCharge(): the charge is an int and no parameters are needed."),
        has_field("return battery.getCharge();", "Delegate to the collaborator: return battery.getCharge();"),
        lacks("private int charge", "Do not add a charge field to Flashlight; the battery already owns that value.")]),
    "answer": b64(p4_1), "files": BATTERY_FILE + DELEGATE_DRIVER}

# ---------------------------------------------------------------- Section 5
E["p5-1"] = {"type": "table", "xp": 1, "blanks": {"b": {"accept": ["3"], "placeholder": "value"}}}
E["p5-1-why"] = SHORT("Primitive assignment copied the value of `a` before `a` changed; the two variables are independent after that.", rows=2)
E["p5-2"] = {"type": "table", "xp": 1, "blanks": {"c": {"accept": ["2"], "placeholder": "value"}}}
E["p5-2-why"] = SHORT("`second = first` copied the reference, not the object. Both variables reach the same battery, which was changed through `first`.", rows=3)
E["ex-copies"] = example('int a = 3;\nint b = a;\na = 2;\nSystem.out.println("a = " + a + ", b = " + b);\n\nBattery first = new Battery(3);\nBattery second = first;\nfirst.drain(1);\nSystem.out.println("first: " + first.getCharge() + ", second: " + second.getCharge());\n', files=BATTERY_FILE)
assert E["ex-copies"]["output"] == "a = 2, b = 3\nfirst: 2, second: 2"
E["p5-3"] = {"type": "table", "xp": 1, "blanks": {
    "ctor": {"accept": ["no"], "placeholder": "yes / no"},
    "obj": {"accept": ["no"], "placeholder": "yes / no"}}}
E["p5-4"] = {"type": "table", "xp": 1, "blanks": {"v": {"accept": ["1"], "placeholder": "value"}}}
E["ex-shared"] = example('Battery small = new Battery(2);\nFlashlight light = new Flashlight(small);\nsmall.drain(1);\nSystem.out.println(light.getBatteryCharge());\n', files=FLASHLIGHT_FILES)
assert E["ex-shared"]["output"] == "1"
E["p5-5"] = {"type": "table", "xp": 1, "blanks": {
    "n": {"accept": ["2", "two"], "placeholder": "how many?", "show": "two"},
    "a": {"accept": ["5"], "placeholder": "value"},
    "b": {"accept": ["10"], "placeholder": "value"}}}
E["ex-reassign"] = example('Battery a = new Battery(5);\nBattery b = a;\nb = new Battery(10);\nSystem.out.println("a: " + a.getCharge() + ", b: " + b.getCharge());\n', files=BATTERY_FILE)
assert E["ex-reassign"]["output"] == "a: 5, b: 10"
E["p5-6"] = SHORT("A method such as `drain` changes fields inside the existing object. Assignment changes which object a variable refers to; it does not rewrite or move the former object, which may still be reachable through another reference.", rows=3)

# ---------------------------------------------------------------- Section 6
E["p6-1"] = SHORT("`charge` is private and belongs to `Battery`. `Flashlight` should use the public `drain` method so that battery rules stay centralized in one place.", rows=3)
E["p6-2"] = SHORT("`Flashlight` depends on the public behaviour of `drain`, not its implementation. That is abstraction across the class boundary: the caller can ignore the collaborator's internal details.", rows=3)
REFERENCE_DRIVER = driver("FlashlightDemo", 'Flashlight light = new Flashlight();\nlight.turnOn();\nlight.useForOneMinute();\nlight.useForOneMinute();\nSystem.out.println("on: " + light.isOn() + ", charge: " + light.getBatteryCharge());\nlight.turnOff();\nlight.useForOneMinute();\nSystem.out.println("on: " + light.isOn() + ", charge: " + light.getBatteryCharge());')
E["ex-flashlight"] = example(FLASHLIGHT, files=BATTERY_FILE + REFERENCE_DRIVER, title="Flashlight.java")
assert E["ex-flashlight"]["output"] == "on: true, charge: 98\non: false, charge: 98"
CALL = {"placeholder": "the call", "width": "14rem"}
E["p6-3"] = {"type": "table", "xp": 1, "blanks": {
    "e1": {"accept": ["battery.drain(1)", "battery.drain(1);"], "show": "battery.drain(1)", **CALL},
    "e2": {"accept": ["battery.isEmpty()", "battery.isEmpty();"], "show": "battery.isEmpty()", **CALL},
    "i": {"accept": ["updatePowerState()", "updatePowerState();"], "show": "updatePowerState()", **CALL}}}
E["p6-4"] = {"type": "table", "xp": 1, "blanks": {
    "n": {"accept": ["2", "two"], "placeholder": "how many?", "show": "two"},
    "charge": {"accept": ["0"], "placeholder": "charge"},
    "on": {"accept": ["false", "off"], "placeholder": "true / false", "show": "false"}}}
E["ex-trace"] = example('Battery small = new Battery(2);\nFlashlight light = new Flashlight(small);\nlight.turnOn();\nlight.useForOneMinute();\nlight.useForOneMinute();\nSystem.out.println("charge: " + light.getBatteryCharge() + ", on: " + light.isOn());\n', files=FLASHLIGHT_FILES)
assert E["ex-trace"]["output"] == "charge: 0, on: false"
RECHARGE_DRIVER = driver("RechargeDemo", 'Battery small = new Battery(2);\nFlashlight light = new Flashlight(small);\nlight.turnOn();\nlight.useForOneMinute();\nSystem.out.println("on: " + light.isOn() + ", charge: " + light.getBatteryCharge());\nlight.rechargeBattery();\nSystem.out.println("on: " + light.isOn() + ", charge: " + light.getBatteryCharge());')
p6_5 = FLASHLIGHT[:-2] + "\n    public void rechargeBattery()\n    {\n        battery.recharge();\n        on = false;\n    }\n}\n"
E["p6-5"] = {"type": "code", "xp": 3, "minLines": 44, "maxLines": 62, "title": "Flashlight.java",
    "starter": FLASHLIGHT[:-2] + "\n    // Write rechargeBattery() here.\n\n\n\n\n\n}\n",
    "cases": [{"name": "Program output", "expected": run(p6_5, BATTERY_FILE + RECHARGE_DRIVER)}],
    "check": "\n".join([
        has("public void rechargeBattery()", "The header is public void rechargeBattery()."),
        has_field("battery.recharge();", "Delegate the recharge to the battery: battery.recharge();"),
        matches(r".*publicvoidrechargeBattery\(\)\{[^}]*(this\.)?(on=false;|turnOff\(\);)[^}]*\}.*", "Leave the flashlight off: on = false; (or the internal call turnOff();)")]),
    "answer": b64(p6_5), "files": BATTERY_FILE + RECHARGE_DRIVER}

# ---------------------------------------------------------------- Section 7
FUEL_TANK_CHECK = driver("FuelTankCheck", '''FuelTank tank = new FuelTank(5);
System.out.println("Start: " + tank.getFuel() + ", empty: " + tank.isEmpty());
tank.consume(2);
System.out.println("After consume(2): " + tank.getFuel());
tank.consume(-3);
System.out.println("After consume(-3): " + tank.getFuel());
tank.consume(9);
System.out.println("After consume(9): " + tank.getFuel() + ", empty: " + tank.isEmpty());
tank.refill();
System.out.println("After refill(): " + tank.getFuel());''')
E["p7-1"] = {"type": "code", "xp": 8, "minLines": 26, "maxLines": 50, "title": "FuelTank.java",
    "starter": "public class FuelTank\n{\n    // fields\n\n\n\n    // constructor\n\n\n\n\n\n    // getFuel, isEmpty, consume, refill\n\n\n\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(FUEL_TANK, FUEL_TANK_CHECK)}],
    "check": "\n".join([
        has("private int capacity;", "Declare private int capacity;"),
        has("private int fuel;", "Declare private int fuel;"),
        matches(r".*publicFuelTank\(int\w+\).*", "The constructor header takes one int parameter: public FuelTank(int capacity)."),
        has("public int getFuel()", "Include public int getFuel()."),
        has("public boolean isEmpty()", "Include public boolean isEmpty()."),
        matches(r".*publicvoidconsume\(int\w+\).*", "Include public void consume(int amount)."),
        has("public void refill()", "Include public void refill().")]),
    "answer": b64(FUEL_TANK), "files": FUEL_TANK_CHECK}
FUEL_TANK_FILE = [file("FuelTank.java", FUEL_TANK)]
SCOOTER_CHECK = driver("ScooterCheck", '''Scooter fresh = new Scooter("Commuter");
System.out.println("Default tank: " + fresh.getFuel() + ", running: " + fresh.isRunning());
fresh.ride(10);
System.out.println("Ride while stopped: " + fresh.getFuel());
FuelTank tank = new FuelTank(5);
Scooter scooter = new Scooter("Runabout", tank);
scooter.start();
System.out.println("Started: " + scooter.isRunning());
scooter.ride(2);
System.out.println("After ride(2): " + scooter.getFuel() + ", running: " + scooter.isRunning());
scooter.ride(-1);
System.out.println("After ride(-1): " + scooter.getFuel());
scooter.stop();
scooter.ride(1);
System.out.println("Ride after stop(): " + scooter.getFuel());
scooter.start();
scooter.ride(4);
System.out.println("After ride(4): " + scooter.getFuel() + ", running: " + scooter.isRunning());
System.out.println("Shared tank: " + tank.getFuel());
scooter.start();
System.out.println("Start when empty: " + scooter.isRunning());''')
E["p7-2"] = {"type": "code", "xp": 10, "minLines": 40, "maxLines": 70, "title": "Scooter.java",
    "starter": "public class Scooter\n{\n    // fields\n\n\n\n\n    // constructors\n\n\n\n\n\n\n\n\n\n\n\n\n    // start, stop, ride, getFuel, isRunning\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(SCOOTER, FUEL_TANK_FILE + SCOOTER_CHECK)}],
    "check": "\n".join([
        has("private String name;", "Declare private String name;"),
        has("private FuelTank tank;", "Declare private FuelTank tank;"),
        has("private boolean running;", "Declare private boolean running;"),
        lacks("private int fuel", "Do not add a separate fuel field to Scooter; the tank owns the fuel."),
        matches(r".*publicScooter\(String\w+\)\{.*", "Include the constructor public Scooter(String name)."),
        has("new FuelTank(100)", "The one-parameter constructor creates a default tank of capacity 100: new FuelTank(100)."),
        matches(r".*publicScooter\(String\w+,FuelTank\w+\).*", "Include the constructor public Scooter(String name, FuelTank tank)."),
        matches(r".*publicScooter\(String\w+,FuelTank(\w+)\)\{[^}]*this\.tank=\1;.*", "The two-parameter constructor stores the tank it receives: this.tank = tank;"),
        has("public void start()", "Include public void start()."),
        has("public void stop()", "Include public void stop()."),
        matches(r".*publicvoidride\(int\w+\).*", "Include public void ride(int distance)."),
        has("public int getFuel()", "Include public int getFuel()."),
        has("public boolean isRunning()", "Include public boolean isRunning()."),
        has_field("return tank.getFuel();", "getFuel() delegates to the tank: return tank.getFuel();")]),
    "answer": b64(SCOOTER), "files": FUEL_TANK_FILE + SCOOTER_CHECK}
SCOOTER_FILES = FUEL_TANK_FILE + [file("Scooter.java", SCOOTER)]
E["p7-3"] = {"type": "code", "xp": 3, "minLines": 14, "maxLines": 24, "title": "ScooterDemo.java",
    "starter": "public class ScooterDemo\n{\n    public static void main(String[] args)\n    {\n        // Create a tank of capacity 5, pass it to a scooter, start it, ride 2, then ride 4.\n\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(SCOOTER_DEMO, SCOOTER_FILES)}],
    "check": "\n".join([
        has("new FuelTank(5)", "Create the tank with new FuelTank(5)."),
        matches(r".*newScooter\(\"[^\"]*\",\w+\).*", "Pass the tank to the scooter's two-parameter constructor: new Scooter(\"Runabout\", tank)."),
        has(".start()", "Start the scooter with start()."),
        has(".ride(2)", "Ride 2 with ride(2)."),
        has(".ride(4)", "Ride 4 with ride(4).")]),
    "answer": b64(SCOOTER_DEMO), "files": SCOOTER_FILES}
E["p7-3-refs"] = SHORT("The local variable `tank` in `main` and the scooter's `tank` field both refer to the same `FuelTank` object.", rows=2)

E["p8-1"] = SHORT("Three objects: one `Account` object, and two `PaymentCard` objects whose `account` fields both point to that one `Account` object. The local `account` variable in `main` also points to the same object.", chars=30, rows=3)
ACCOUNT_CHECK = driver("AccountCheck", '''Account account = new Account(100);
System.out.println("Balance: " + account.getBalance());
System.out.println("Can afford 100: " + account.canAfford(100));
System.out.println("Can afford 101: " + account.canAfford(101));
System.out.println("Withdraw 30: " + account.withdraw(30));
System.out.println("Withdraw 80: " + account.withdraw(80));
System.out.println("Balance: " + account.getBalance());
account.deposit(50);
System.out.println("After deposit(50): " + account.getBalance());''')
E["p8-2-account"] = {"type": "code", "xp": 8, "minLines": 28, "maxLines": 50, "title": "Account.java",
    "starter": "public class Account\n{\n    // field\n\n\n    // constructor\n\n\n\n\n    // getBalance, canAfford, withdraw, deposit\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(ACCOUNT, ACCOUNT_CHECK)}],
    "check": "\n".join([
        has("private int balance;", "Declare private int balance;"),
        matches(r".*publicAccount\(int\w+\).*", "The constructor receives the opening balance: public Account(int openingBalance)."),
        has("public int getBalance()", "Include public int getBalance()."),
        matches(r".*publicbooleancanAfford\(int\w+\).*", "Include public boolean canAfford(int amount)."),
        matches(r".*publicbooleanwithdraw\(int\w+\).*", "withdraw returns a boolean: public boolean withdraw(int amount)."),
        matches(r".*publicvoiddeposit\(int\w+\).*", "Include public void deposit(int amount).")]),
    "answer": b64(ACCOUNT), "files": ACCOUNT_CHECK}
ACCOUNT_FILE = [file("Account.java", ACCOUNT)]
CARD_CHECK = driver("PaymentCardCheck", '''Account account = new Account(100);
PaymentCard cardA = new PaymentCard("Card A", account);
PaymentCard cardB = new PaymentCard("Card B", account);
System.out.println(cardA.getLabel() + " sees " + cardA.getBalance());
System.out.println("Buy 30 with " + cardA.getLabel() + ": " + cardA.buy(30));
System.out.println(cardB.getLabel() + " sees " + cardB.getBalance());
System.out.println("Buy 80 with " + cardB.getLabel() + ": " + cardB.buy(80));
account.deposit(10);
System.out.println(cardA.getLabel() + " sees " + cardA.getBalance());''')
E["p8-2-card"] = {"type": "code", "xp": 8, "minLines": 24, "maxLines": 40, "title": "PaymentCard.java",
    "starter": "public class PaymentCard\n{\n    // fields\n\n\n\n    // constructor\n\n\n\n\n\n    // buy, getBalance, getLabel\n\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(PAYMENT_CARD, ACCOUNT_FILE + CARD_CHECK)}],
    "check": "\n".join([
        has("private String label;", "Declare private String label;"),
        has("private Account account;", "Declare private Account account;"),
        lacks("private int balance", "Do not store a balance in PaymentCard; the account owns it."),
        matches(r".*publicPaymentCard\(String\w+,Account\w+\).*", "The constructor receives a label and an existing Account: public PaymentCard(String label, Account account)."),
        lacks("new Account(", "The card receives an existing account; it must not construct one."),
        matches(r".*publicbooleanbuy\(int\w+\).*", "Include public boolean buy(int amount)."),
        matches(r".*returnaccount\.withdraw\(\w+\);.*", "buy delegates to the account: return account.withdraw(amount);"),
        has_field("return account.getBalance();", "getBalance() delegates: return account.getBalance();"),
        has("public String getLabel()", "Include public String getLabel().")]),
    "answer": b64(PAYMENT_CARD), "files": ACCOUNT_FILE + CARD_CHECK}
CARD_FILES = ACCOUNT_FILE + [file("PaymentCard.java", PAYMENT_CARD)]
E["p8-3"] = {"type": "code", "xp": 3, "minLines": 14, "maxLines": 26, "title": "SharedAccountDemo.java",
    "starter": "public class SharedAccountDemo\n{\n    public static void main(String[] args)\n    {\n        // One account with balance 100, two cards that both receive it.\n\n\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(SHARED_ACCOUNT_DEMO, CARD_FILES)}],
    "check": "\n".join([
        has("new Account(100)", "Create the account with new Account(100)."),
        matches(r".*newPaymentCard\(\"[^\"]*\",(\w+)\).*newPaymentCard\(\"[^\"]*\",\1\).*", "Both cards receive the same account variable."),
        has(".buy(30)", "Buy for 30 through the first card with buy(30)."),
        has(".buy(80)", "Attempt the purchase of 80 through the second card with buy(80).")]),
    "answer": b64(SHARED_ACCOUNT_DEMO), "files": CARD_FILES}

assert run(SCOOTER_DEMO, SCOOTER_FILES) == "After first ride - fuel: 3, running: true\nAfter second ride - fuel: 0, running: false"
assert run(SHARED_ACCOUNT_DEMO, CARD_FILES) == "Card A balance: 70\nCard B balance: 70\nSecond purchase succeeded: false\nFinal balance: 70"

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-05",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 5 Workbook",
    "subtitle": "Chapter 3: Objects collaborate",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
