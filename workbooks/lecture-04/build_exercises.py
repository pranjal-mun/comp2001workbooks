"""Build workbooks/lecture-04/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-04/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-04

Most code boxes on this page ask for a method inside a class rather than a
program. Each of those boxes has a small driver class on its classpath (the
`files` list) whose main method calls the method and prints what comes back;
the runner uses that main when the editor's class has none.
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


def matches(regex, message):
    """A check line: the whitespace-stripped source matches `regex` (a Java regex, whole string)."""
    return f'require(source.replaceAll("\\\\s+", "").matches({json.dumps("(?s)" + regex)}), {json.dumps(message)});'


def file(name, content):
    return {"name": name, "content": content.rstrip("\n")}


def driver(name, body):
    """A hidden class whose main method exercises the student's class."""
    lines = "\n".join("        " + line for line in body.strip("\n").splitlines())
    return [file(f"{name}.java", f"public class {name}\n{{\n    public static void main(String[] args)\n    {{\n{lines}\n    }}\n}}\n")]


# The complete CampusCard of this lecture (Section 6).
CAMPUS_CARD = '''public class CampusCard
{
    private String owner;
    private int balance;
    private int totalSpent;

    public CampusCard(String owner, int openingBalance)
    {
        this.owner = owner;
        if(openingBalance >= 0) {
            balance = openingBalance;
        }
        else {
            balance = 0;
        }
        totalSpent = 0;
    }

    public String getOwner()
    {
        return owner;
    }

    public int getBalance()
    {
        return balance;
    }

    public int getTotalSpent()
    {
        return totalSpent;
    }

    public boolean topUp(int amount)
    {
        if(amount > 0) {
            balance = balance + amount;
            return true;
        }
        else {
            return false;
        }
    }

    public boolean pay(int amount)
    {
        if(amount > 0 && amount <= balance) {
            balance = balance - amount;
            totalSpent = totalSpent + amount;
            return true;
        }
        else {
            return false;
        }
    }

    public int refundBalance()
    {
        int amountToRefund = balance;
        balance = 0;
        return amountToRefund;
    }
}
'''
CARD = [file("CampusCard.java", CAMPUS_CARD)]

# The Section 1 starting point: fields and a constructor, no methods yet.
CARD_HEAD = '''public class CampusCard
{
    private String owner;
    private int balance;
    private int totalSpent;

    public CampusCard(String owner, int openingBalance)
    {
        this.owner = owner;
        balance = openingBalance;
        totalSpent = 0;
    }
'''

THERMOSTAT = '''public class Thermostat
{
    private double temperature;
    private double minimum;
    private double maximum;
    private double increment;

    public Thermostat(double minimum, double maximum,
                      double initialTemperature)
    {
        this.minimum = minimum;
        this.maximum = maximum;
        if(initialTemperature >= minimum && initialTemperature <= maximum) {
            temperature = initialTemperature;
        }
        else {
            temperature = minimum;
        }
        increment = 1.0;
    }

    public double getTemperature()
    {
        return temperature;
    }

    public boolean setIncrement(double increment)
    {
        if(increment > 0) {
            this.increment = increment;
            return true;
        }
        else {
            return false;
        }
    }

    public boolean warmer()
    {
        double proposed = temperature + increment;
        if(proposed <= maximum) {
            temperature = proposed;
            return true;
        }
        else {
            return false;
        }
    }

    public boolean cooler()
    {
        double proposed = temperature - increment;
        if(proposed >= minimum) {
            temperature = proposed;
            return true;
        }
        else {
            return false;
        }
    }
}
'''

THERMOSTAT_DEMO = '''public class ThermostatDemo
{
    public static void main(String[] args)
    {
        Thermostat room = new Thermostat(16.0, 24.0, 20.0);
        room.setIncrement(2.0);
        System.out.println("Start: " + room.getTemperature());
        System.out.println("Warmer: " + room.warmer());
        System.out.println("Warmer: " + room.warmer());
        System.out.println("Warmer at max: " + room.warmer());
        System.out.println("Final: " + room.getTemperature());
    }
}
'''

GAME_SCORE = '''public class GameScore
{
    private String player;
    private int score;
    private int bestScore;

    public GameScore(String player)
    {
        this.player = player;
        score = 0;
        bestScore = 0;
    }

    public String getPlayer()
    {
        return player;
    }

    public int getScore()
    {
        return score;
    }

    public int getBestScore()
    {
        return bestScore;
    }

    public boolean addPoints(int points)
    {
        if(points > 0) {
            score = score + points;
            if(score > bestScore) {
                bestScore = score;
            }
            return true;
        }
        else {
            return false;
        }
    }

    public int finishRound()
    {
        int completedScore = score;
        score = 0;
        return completedScore;
    }
}
'''

GAME_SCORE_DEMO = '''public class GameScoreDemo
{
    public static void main(String[] args)
    {
        GameScore score = new GameScore("Kai");
        score.addPoints(40);
        score.addPoints(25);
        System.out.println(score.getPlayer() + " finished with " +
                           score.finishRound());
        System.out.println("Current: " + score.getScore());
        System.out.println("Best: " + score.getBestScore());
    }
}
'''

SHORT = lambda answer, chars=20, rows=2, xp=2: {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}  # noqa: E731

E = {}

# ---------------------------------------------------------------- Section 1
E["p1-1"] = {"type": "table", "xp": 1, "blanks": {
    "vis": {"accept": ["public"], "placeholder": "part"},
    "ret": {"accept": ["boolean"], "placeholder": "part"},
    "name": {"accept": ["pay"], "caseSensitive": True, "placeholder": "part"},
    "ptype": {"accept": ["int"], "placeholder": "part"},
    "pname": {"accept": ["amount"], "caseSensitive": True, "placeholder": "part"}}}
E["p1-2"] = SHORT("Its header contains parentheses and is followed by a method-body block. A field declaration has no parameter parentheses and ends with a semicolon.")
E["p1-3"] = {"type": "table", "xp": 1, "blanks": {
    "part": {"accept": ["parameter list", "the parameter list", "parameters", "the parameters", "its parameters", "its parameter list", "parameter"],
             "placeholder": "which part of the header?", "show": "the parameter list", "width": "14rem"}}}
OWNER_DRIVER = driver("OwnerDemo", 'CampusCard card = new CampusCard("Mina", 1200);\nSystem.out.println("Owner: " + card.getOwner());')
p1_4 = CARD_HEAD + "\n    public String getOwner()\n    {\n        return owner;\n    }\n}\n"
E["p1-4"] = {"type": "code", "xp": 2, "minLines": 16, "maxLines": 22, "title": "CampusCard.java",
    "starter": CARD_HEAD + "\n    // Repair the header so the method publicly returns a String and takes no parameters.\n    String public getOwner\n    {\n        return owner;\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(p1_4, OWNER_DRIVER)}],
    "check": has("public String getOwner()", "The header is public String getOwner(): visibility, return type, name, then an empty parameter list."),
    "answer": b64(p1_4), "files": OWNER_DRIVER}

# ---------------------------------------------------------------- Section 2
E["ex-caller"] = example('CampusCard card = new CampusCard("Mina", 1200);\n\nint current = card.getBalance();\nSystem.out.println(current);\n\nint afterLunch = card.getBalance() - 500;\nSystem.out.println(afterLunch);\n', files=CARD)
SPENT_DRIVER = driver("TotalSpentDemo", 'CampusCard card = new CampusCard("Mina", 1200);\ncard.pay(450);\nSystem.out.println("Total spent: " + card.getTotalSpent());')
GETTER_HEAD = CARD_HEAD + '''
    public boolean pay(int amount)
    {
        if(amount > 0 && amount <= balance) {
            balance = balance - amount;
            totalSpent = totalSpent + amount;
            return true;
        }
        else {
            return false;
        }
    }
'''
p2_1 = GETTER_HEAD + "\n    public int getTotalSpent()\n    {\n        return totalSpent;\n    }\n}\n"
E["p2-1"] = {"type": "code", "xp": 2, "minLines": 26, "maxLines": 34, "title": "CampusCard.java",
    "starter": GETTER_HEAD + "\n    // Write the getter for totalSpent here.\n\n\n\n\n}\n",
    "cases": [{"name": "Program output", "expected": run(p2_1, SPENT_DRIVER)}],
    "check": "\n".join([
        has("public int getTotalSpent()", "The header is public int getTotalSpent(): the field is an int, so the getter returns an int."),
        has("return totalSpent;", "The body returns the field: return totalSpent;")]),
    "answer": b64(p2_1), "files": SPENT_DRIVER}
E["p2-2"] = SHORT("`return` sends the value to the caller for further use. `println` displays text but does not return that value to the caller.", rows=3)
E["p2-3"] = {"type": "table", "xp": 1, "blanks": {
    "saved": {"accept": ["1200"], "placeholder": "value"},
    "printed": {"accept": ["nothing", "nothing is printed", "no output", "none", "nothing at all"], "placeholder": "what is printed?", "show": "nothing", "width": "12rem"}}}
VOID_CARD = [file("CampusCard.java", CARD_HEAD + '''
    public void printBalance()
    {
        System.out.println("Balance: " + balance);
    }
}
''')]
E["ex-void"] = example('// printBalance() has return type void.\n// Press Run to read the compiler\'s complaint about the assignment.\nCampusCard card = new CampusCard("Mina", 1200);\nint saved = card.printBalance();\n', files=VOID_CARD, output=False)
E["p2-4"] = SHORT("A `void` call produces no result value, so there is no integer to assign to `saved`.", rows=3)
BALANCE_DRIVER = driver("BalanceDemo", 'CampusCard card = new CampusCard("Mina", 1200);\nSystem.out.println("Balance: " + card.getBalance());')
p2_5 = CARD_HEAD + "\n    public int getBalance()\n    {\n        return balance;\n    }\n}\n"
E["p2-5"] = {"type": "code", "xp": 2, "minLines": 16, "maxLines": 22, "title": "CampusCard.java",
    "starter": CARD_HEAD + "\n    // Repair this method.\n    public void getBalance()\n    {\n        return balance;\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(p2_5, BALANCE_DRIVER)}],
    "check": "\n".join([
        has("public int getBalance()", "The field is an int, so the return type is int: public int getBalance()."),
        has("return balance;", "The body can stay as it was: return balance;")]),
    "answer": b64(p2_5), "files": BALANCE_DRIVER}

# ---------------------------------------------------------------- Section 3
E["ex-topup"] = example('CampusCard card = new CampusCard("Mina", 1200);\nSystem.out.println(card.getBalance());\n\ncard.topUp(300);\nSystem.out.println(card.getBalance());\n', files=CARD)
E["p3-1"] = {"type": "table", "xp": 1, "blanks": {
    "b1": {"accept": ["1000"], "placeholder": "balance"},
    "b2": {"accept": ["1050"], "placeholder": "balance"}}}
RECORD_DRIVER = driver("SpendingDemo", 'CampusCard card = new CampusCard("Mina", 1200);\ncard.recordSpending(200);\ncard.recordSpending(300);\nSystem.out.println("Total spent: " + card.getTotalSpent());')
RECORD_HEAD = CARD_HEAD + "\n    public int getTotalSpent()\n    {\n        return totalSpent;\n    }\n"
p3_2 = RECORD_HEAD + "\n    public void recordSpending(int amount)\n    {\n        totalSpent = totalSpent + amount;\n    }\n}\n"
E["p3-2"] = {"type": "code", "xp": 2, "minLines": 22, "maxLines": 28, "title": "CampusCard.java",
    "starter": RECORD_HEAD + "\n    // Repair the method so it adds the new amount to the previous total.\n    public void recordSpending(int amount)\n    {\n        totalSpent = amount;\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(p3_2, RECORD_DRIVER)}],
    "check": matches(r".*(totalSpent=totalSpent\+amount;|totalSpent=amount\+totalSpent;|totalSpent\+=amount;).*", "Add the amount to the old total: totalSpent = totalSpent + amount;"),
    "answer": b64(p3_2), "files": RECORD_DRIVER}
E["p3-3"] = SHORT("No. A `void` method might only print or perform another action without changing any field. Mutation is determined by the body, not the return type alone.", rows=3)
E["p3-4"] = {"type": "table", "xp": 1, "blanks": {
    "field": {"accept": ["field", "the field", "the field owner", "field owner", "the current object's field", "the object's field"], "placeholder": "field / parameter", "show": "the field", "width": "12rem"},
    "param": {"accept": ["parameter", "the parameter", "the parameter owner", "parameter owner", "the method parameter"], "placeholder": "field / parameter", "show": "the parameter", "width": "12rem"}}}
CLEAR_DRIVER = driver("ClearDemo", 'CampusCard card = new CampusCard("Mina", 1200);\ncard.recordSpending(400);\nSystem.out.println("Before: " + card.getTotalSpent());\ncard.clearTotal();\nSystem.out.println("After: " + card.getTotalSpent());')
CLEAR_HEAD = p3_2[:-2]  # the repaired class without its closing brace
p3_5 = CLEAR_HEAD + "\n    public void clearTotal()\n    {\n        totalSpent = 0;\n    }\n}\n"
E["p3-5"] = {"type": "code", "xp": 2, "minLines": 28, "maxLines": 34, "title": "CampusCard.java",
    "starter": CLEAR_HEAD + "\n    // Write clearTotal() here.\n\n\n\n\n}\n",
    "cases": [{"name": "Program output", "expected": run(p3_5, CLEAR_DRIVER)}],
    "check": "\n".join([
        has("public void clearTotal()", "The header is public void clearTotal(): no value comes back and there are no parameters."),
        has("totalSpent = 0;", "The body sets the field to zero: totalSpent = 0;")]),
    "answer": b64(p3_5), "files": CLEAR_DRIVER}

# ---------------------------------------------------------------- Section 4
E["ex-boolean"] = example('CampusCard card = new CampusCard("Mina", 1200);\n\nSystem.out.println(card.topUp(300));\nSystem.out.println(card.topUp(-50));\nSystem.out.println(card.getBalance());\n', files=CARD)
E["p4-1"] = {"type": "table", "xp": 1, "blanks": {
    "e1": {"accept": ["true"], "placeholder": "true / false"},
    "e2": {"accept": ["false"], "placeholder": "true / false"},
    "e3": {"accept": ["true"], "placeholder": "true / false"}}}
E["p4-2"] = SHORT("A payment equal to the balance is valid and should leave a balance of zero. Using `<` would reject that exact-boundary case.", rows=3)
E["p4-3"] = {"type": "table", "xp": 1, "blanks": {
    "r1": {"accept": ["true"], "placeholder": "result"}, "b1": {"accept": ["300"], "placeholder": "balance"}, "t1": {"accept": ["200"], "placeholder": "total"},
    "r2": {"accept": ["false"], "placeholder": "result"}, "b2": {"accept": ["300"], "placeholder": "balance"}, "t2": {"accept": ["200"], "placeholder": "total"},
    "r3": {"accept": ["true"], "placeholder": "result"}, "b3": {"accept": ["0"], "placeholder": "balance"}, "t3": {"accept": ["500"], "placeholder": "total"}}}
E["ex-trace"] = example('CampusCard card = new CampusCard("Mina", 500);\n\nSystem.out.println(card.pay(200) + " " + card.getBalance() + " " + card.getTotalSpent());\nSystem.out.println(card.pay(400) + " " + card.getBalance() + " " + card.getTotalSpent());\nSystem.out.println(card.pay(300) + " " + card.getBalance() + " " + card.getTotalSpent());\n', files=CARD)
COND_DRIVER = driver("ConditionDemo", 'CampusCard card = new CampusCard("Mina", 1200);\ncard.topUp(0);\ncard.topUp(-5);\ncard.topUp(100);\nSystem.out.println("Balance: " + card.getBalance());')
COND_HEAD = CARD_HEAD + "\n    public int getBalance()\n    {\n        return balance;\n    }\n"
COND_TAIL = ' {\n            System.out.println("Amount rejected");\n        }\n        else {\n            balance = balance + amount;\n        }\n    }\n}\n'
p4_4 = COND_HEAD + "\n    public void topUp(int amount)\n    {\n        if(amount <= 0)" + COND_TAIL
E["p4-4"] = {"type": "code", "xp": 2, "minLines": 26, "maxLines": 32, "title": "CampusCard.java",
    "starter": COND_HEAD + "\n    public void topUp(int amount)\n    {\n        // Replace false with a condition that is true for zero and negative amounts.\n        if(false)" + COND_TAIL,
    "cases": [{"name": "Program output", "expected": run(p4_4, COND_DRIVER)}],
    "check": matches(r".*if\((amount<=0|amount<1|0>=amount|1>amount|!\(amount>0\)|!\(amount>=1\))\).*", "The error branch must run for zero and for negative values: if(amount <= 0)"),
    "answer": b64(p4_4), "files": COND_DRIVER}
E["p4-5"] = SHORT("Checking first prevents invalid state from being stored. Printing an error after a bad assignment would not undo the mutation.", rows=3)
AFFORD_DRIVER = driver("AffordDemo", 'CampusCard card = new CampusCard("Mina", 500);\nSystem.out.println("200: " + card.canAfford(200));\nSystem.out.println("500: " + card.canAfford(500));\nSystem.out.println("600: " + card.canAfford(600));\nSystem.out.println("0: " + card.canAfford(0));\nSystem.out.println("Balance is still " + card.getBalance());')
p4_6 = COND_HEAD + "\n    public boolean canAfford(int amount)\n    {\n        return amount > 0 && amount <= balance;\n    }\n}\n"
E["p4-6"] = {"type": "code", "xp": 3, "minLines": 22, "maxLines": 32, "title": "CampusCard.java",
    "starter": COND_HEAD + "\n    // Write canAfford(int amount) here.\n\n\n\n\n\n}\n",
    "cases": [{"name": "Program output", "expected": run(p4_6, AFFORD_DRIVER)}],
    "check": "\n".join([
        has("public boolean canAfford(int amount)", "The header is public boolean canAfford(int amount)."),
        matches(r".*canAfford\(intamount\)\{[^}]*&&[^}]*\}.*", "Both requirements must hold, so combine them with &&: amount > 0 && amount <= balance")]),
    "answer": b64(p4_6), "files": AFFORD_DRIVER}

# ---------------------------------------------------------------- Section 5
REFUND_DRIVER = driver("RefundDemo", 'CampusCard card = new CampusCard("Mina", 1200);\nSystem.out.println("Refunded: " + card.refundBalance());\nSystem.out.println("Balance now: " + card.getBalance());')
E["ex-refund-wrong"] = example(COND_HEAD + "\n    public int refundBalance()\n    {\n        balance = 0;\n        return balance; // Always returns 0.\n    }\n}\n", files=REFUND_DRIVER, title="CampusCard.java")
E["ex-unreachable"] = example(COND_HEAD + "\n    // Press Run to read the compiler's complaint.\n    public int refundBalance()\n    {\n        return balance;\n        balance = 0;\n    }\n}\n", files=REFUND_DRIVER, title="CampusCard.java", output=False)
E["ex-refund"] = example(COND_HEAD + "\n    public int refundBalance()\n    {\n        int amountToRefund = balance;\n        balance = 0;\n        return amountToRefund;\n    }\n}\n", files=REFUND_DRIVER, title="CampusCard.java")
E["p5-1"] = {"type": "table", "xp": 1, "blanks": {
    "bal": {"accept": ["field", "a field", "instance variable"], "placeholder": "field / parameter / local", "show": "field", "width": "12rem"},
    "amt": {"accept": ["parameter", "a parameter"], "placeholder": "field / parameter / local", "show": "parameter", "width": "12rem"},
    "ref": {"accept": ["local", "a local", "local variable", "a local variable"], "placeholder": "field / parameter / local", "show": "local", "width": "12rem"}}}
E["p5-2"] = SHORT("The assignment replaces the old field value before the return expression is evaluated, so the method returns zero.", rows=3)
E["p5-3"] = SHORT("Executing `return` ends the method, so the later assignment can never be reached.", rows=3)
E["p5-4"] = SHORT("No. It is needed only during one refund call and is not part of the card's persistent state. A local gives it the narrow scope and lifetime its job requires.", rows=3)
E["p5-5"] = SHORT("Scope is the source-code region where a name may be used. Lifetime is the period during execution when the variable exists.", rows=3)
DOUBLE_DRIVER = driver("DoubleDemo", 'CampusCard card = new CampusCard("Mina", 1200);\nSystem.out.println("Doubled: " + card.doubleBalance());')
p5_6 = COND_HEAD + "\n    public int doubleBalance()\n    {\n        int doubled = balance * 2;\n        return doubled;\n    }\n}\n"
E["p5-6"] = {"type": "code", "xp": 2, "minLines": 22, "maxLines": 28, "title": "CampusCard.java",
    "starter": COND_HEAD + "\n    // Repair this method by declaring and initializing the local before it is used.\n    public int doubleBalance()\n    {\n        int doubled;\n        return doubled;\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(p5_6, DOUBLE_DRIVER)}],
    "check": "\n".join([
        matches(r".*intdoubled=(balance\*2|2\*balance|balance\+balance);.*", "Give the local a value when it is declared: int doubled = balance * 2;"),
        has("return doubled;", "Return the local: return doubled;")]),
    "answer": b64(p5_6), "files": DOUBLE_DRIVER}

# ---------------------------------------------------------------- Section 6
E["p6-1"] = SHORT("Accessors: `getOwner`, `getBalance`, and `getTotalSpent`. State-changing methods: `topUp`, `pay`, and `refundBalance`.", rows=3)
E["p6-2"] = SHORT("Yes. `pay` and `topUp` mutate state on successful calls and return a boolean result. `refundBalance` also mutates and returns the old balance.", rows=3)
E["p6-3"] = {"type": "table", "xp": 1, "blanks": {
    "inv": {"accept": ["balance >= 0", "balance>=0", "the balance is never negative", "balance is never negative", "balance is not negative", "the balance is not negative", "balance is at least 0", "balance is at least zero", "0 <= balance", "balance never goes below zero", "the balance never goes below zero"],
            "placeholder": "condition", "show": "balance >= 0", "width": "14rem"}}}
PREDICT = 'CampusCard card = new CampusCard("Mina", 1200);\nSystem.out.println(card.topUp(300));\nSystem.out.println(card.pay(450));\nSystem.out.println(card.pay(2000));\nSystem.out.println(card.getBalance());\nSystem.out.println(card.getTotalSpent());\nSystem.out.println(card.refundBalance());\nSystem.out.println(card.getBalance());\n'
E["p6-4"] = {"type": "table", "xp": 1, "blanks": {
    "l1": {"accept": ["true"], "placeholder": "output"}, "l2": {"accept": ["true"], "placeholder": "output"}, "l3": {"accept": ["false"], "placeholder": "output"},
    "l4": {"accept": ["1050"], "placeholder": "output"}, "l5": {"accept": ["450"], "placeholder": "output"}, "l6": {"accept": ["1050"], "placeholder": "output"}, "l7": {"accept": ["0"], "placeholder": "output"}}}
E["ex-predict"] = example(PREDICT, files=CARD)
assert E["ex-predict"]["output"] == "true\ntrue\nfalse\n1050\n450\n1050\n0"

# ---------------------------------------------------------------- Section 7
THERMOSTAT_CHECK = driver("ThermostatCheck", '''Thermostat room = new Thermostat(16.0, 24.0, 20.0);
System.out.println("Start: " + room.getTemperature());
System.out.println("Increment 2.0: " + room.setIncrement(2.0));
System.out.println("Increment -1.0: " + room.setIncrement(-1.0));
System.out.println("Warmer: " + room.warmer());
System.out.println("Warmer: " + room.warmer());
System.out.println("Warmer at max: " + room.warmer());
System.out.println("Final: " + room.getTemperature());
Thermostat cold = new Thermostat(16.0, 24.0, 30.0);
System.out.println("Out of range start: " + cold.getTemperature());
System.out.println("Cooler at min: " + cold.cooler());
System.out.println("Still: " + cold.getTemperature());''')
THERMOSTAT_FILE = [file("Thermostat.java", THERMOSTAT)]
THERMOSTAT_DEMO_FILE = [file("ThermostatDemo.java", THERMOSTAT_DEMO)]
E["p7a-thermostat"] = {"type": "code", "xp": 10, "minLines": 30, "maxLines": 60, "title": "Thermostat.java",
    "starter": "public class Thermostat\n{\n    // fields\n\n\n\n\n\n    // constructor\n\n\n\n\n\n\n\n\n    // getTemperature, setIncrement, warmer, cooler\n\n\n\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(THERMOSTAT, THERMOSTAT_CHECK)}],
    "check": "\n".join([
        has("private double temperature;", "Declare private double temperature;"),
        has("private double minimum;", "Declare private double minimum;"),
        has("private double maximum;", "Declare private double maximum;"),
        has("private double increment;", "Declare private double increment;"),
        matches(r".*publicThermostat\(double\w+,double\w+,double\w+\).*", "The constructor header takes three double parameters: public Thermostat(double minimum, double maximum, double initialTemperature)."),
        has("public double getTemperature()", "Include the accessor public double getTemperature()."),
        matches(r".*publicbooleansetIncrement\(double\w+\).*", "Include public boolean setIncrement(double increment)."),
        has("public boolean warmer()", "Include public boolean warmer()."),
        has("public boolean cooler()", "Include public boolean cooler()."),
        matches(r".*publicbooleanwarmer\(\)\{double\w+=.*", "warmer() starts by storing the proposed temperature in a local double variable."),
        matches(r".*publicbooleancooler\(\)\{double\w+=.*", "cooler() starts by storing the proposed temperature in a local double variable.")]),
    "answer": b64(THERMOSTAT), "files": THERMOSTAT_CHECK}
E["p7a-demo"] = {"type": "code", "xp": 3, "minLines": 12, "maxLines": 20, "title": "ThermostatDemo.java",
    "starter": "public class ThermostatDemo\n{\n    public static void main(String[] args)\n    {\n        // Construct the thermostat, set the increment, then warm it past the maximum.\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(THERMOSTAT_DEMO, THERMOSTAT_FILE)}],
    "check": "\n".join([
        has("new Thermostat(16.0, 24.0, 20.0)", "Construct the thermostat with new Thermostat(16.0, 24.0, 20.0)."),
        has(".setIncrement(2.0)", "Set the increment to 2.0 with setIncrement(2.0)."),
        matches(r".*\.warmer\(\).*\.warmer\(\).*\.warmer\(\).*", "Call warmer() three times: the third call is the rejected one.")]),
    "answer": b64(THERMOSTAT_DEMO), "files": THERMOSTAT_FILE}
GAME_SCORE_CHECK = driver("GameScoreCheck", '''GameScore score = new GameScore("Kai");
System.out.println("Player: " + score.getPlayer());
System.out.println("Add -5: " + score.addPoints(-5));
System.out.println("Add 40: " + score.addPoints(40));
System.out.println("Add 25: " + score.addPoints(25));
System.out.println("Score: " + score.getScore() + ", best: " + score.getBestScore());
System.out.println("Round: " + score.finishRound());
System.out.println("Score: " + score.getScore() + ", best: " + score.getBestScore());
score.addPoints(30);
System.out.println("Score: " + score.getScore() + ", best: " + score.getBestScore());
System.out.println("Round: " + score.finishRound());''')
GAME_SCORE_FILE = [file("GameScore.java", GAME_SCORE)]
E["p7b-gamescore"] = {"type": "code", "xp": 10, "minLines": 30, "maxLines": 60, "title": "GameScore.java",
    "starter": "public class GameScore\n{\n    // fields\n\n\n\n\n    // constructor\n\n\n\n\n\n\n    // getters\n\n\n\n\n\n\n\n    // addPoints and finishRound\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(GAME_SCORE, GAME_SCORE_CHECK)}],
    "check": "\n".join([
        has("private String player;", "Declare private String player;"),
        has("private int score;", "Declare private int score;"),
        has("private int bestScore;", "Declare private int bestScore;"),
        matches(r".*publicGameScore\(String\w+\).*", "The constructor header is public GameScore(String player)."),
        has("public String getPlayer()", "Include the getter public String getPlayer()."),
        has("public int getScore()", "Include the getter public int getScore()."),
        has("public int getBestScore()", "Include the getter public int getBestScore()."),
        matches(r".*publicbooleanaddPoints\(int\w+\).*", "Include public boolean addPoints(int points)."),
        has("public int finishRound()", "Include public int finishRound()."),
        matches(r".*publicintfinishRound\(\)\{int\w+=score;.*", "finishRound() starts by remembering the score in a local int variable."),
        matches(r".*publicintfinishRound\(\)\{((?!bestScore=)[^}])*\}.*", "finishRound() must not assign to bestScore.")]),
    "answer": b64(GAME_SCORE), "files": GAME_SCORE_CHECK}
E["p7b-demo"] = {"type": "code", "xp": 3, "minLines": 12, "maxLines": 20, "title": "GameScoreDemo.java",
    "starter": "public class GameScoreDemo\n{\n    public static void main(String[] args)\n    {\n        // Add points, finish a round, and print the round score, current score, and best score.\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(GAME_SCORE_DEMO, GAME_SCORE_FILE)}],
    "check": "\n".join([
        has('new GameScore("Kai")', 'Construct the score with new GameScore("Kai").'),
        has(".addPoints(40)", "Add 40 points with addPoints(40)."),
        has(".addPoints(25)", "Add 25 points with addPoints(25)."),
        has(".finishRound()", "Finish the round with finishRound() and print what it returns.")]),
    "answer": b64(GAME_SCORE_DEMO), "files": GAME_SCORE_FILE}
E["p7-1"] = {"type": "table", "xp": 1, "blanks": {
    "t": {"accept": ["16.0", "16"], "placeholder": "temperature"},
    "w": {"accept": ["true"], "placeholder": "true / false"},
    "c": {"accept": ["false"], "placeholder": "true / false"}}}
E["p7-2"] = SHORT("The proposed temperature is needed only while one warmer() or cooler() call decides whether to accept it. It is not part of the thermostat's persistent state, so a local variable with that one-call lifetime is the right choice.", chars=30, rows=3)
E["p7-3"] = {"type": "table", "xp": 1, "blanks": {
    "round": {"accept": ["65"], "placeholder": "value"},
    "score": {"accept": ["0"], "placeholder": "value"},
    "best": {"accept": ["65"], "placeholder": "value"}}}
E["p7-4"] = SHORT("`finishRound()` clears `score` but never assigns to `bestScore`, so the best score survives the round. `addPoints` only raises `bestScore` when the new score is higher.", chars=30, rows=3)

assert run(THERMOSTAT, THERMOSTAT_DEMO_FILE) == "Start: 20.0\nWarmer: true\nWarmer: true\nWarmer at max: false\nFinal: 24.0"
assert run(GAME_SCORE, [file("GameScoreDemo.java", GAME_SCORE_DEMO)]) == "Kai finished with 65\nCurrent: 0\nBest: 65"

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-04",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 4 Workbook",
    "subtitle": "Chapter 2, Part 2: Methods make state useful",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
