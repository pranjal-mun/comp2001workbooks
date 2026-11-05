"""Build Lecture 15 exercises from the workbook and real Java runs.

The page was rebuilt to follow the deck being taught. The old ids q1 to q28,
p1-* and p2-* meant other questions, so none is reused: r1 to r27 follow
questions 1.1 to 8.2 in order, with r-p1-item, r-p1-test, r-p2-test and
r-p2-fix for the two programs. Every code case is computed by run(), then
pinned by an assert. The real JUnit runs are in the lecture's code folder.
The site's runner has no JUnit jars, so each test box carries a small stand-in
with the same package names. Students write real JUnit test classes, and the
stand-in prints one line per test. No server is needed.
"""
import base64, html, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402

CODE_DIR = ROOT.parent / "output" / "L15_Chapter_9_Testing_Debugging_v3" / "code"


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
    return src.rstrip().rstrip("}").rstrip("\n") + "\n\n" + "\n".join("    " + line if line else "" for line in text.rstrip("\n").splitlines()) + "\n}\n"


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

# ------------------------------------------------ workbook and classes
sys.path.insert(0, str(ROOT.parent / 'scripts' / 'web_l15'))
from workbook import question_code, answer_code, QUESTION_RAW, SOURCE, listings, inline, group


def solution(n):
    m = re.search(r'\\solution\{', QUESTION_RAW[n])
    return html.unescape(re.sub('<[^>]+>', '', inline(group(QUESTION_RAW[n], m.end()-1)[0])))


def files_at(folder, *names):
    return [file(name+'.java', read(folder+'/'+name+'.java')) for name in names]


def output(n, eid, expected, files=(), imports='', why=True):
    value = run(demo('Prediction', question_code(n), imports), files)
    assert value == expected, (n, value)
    lines_table(eid, value)
    if why: E[eid+'-why'] = SHORT(solution(n))


def checked(eid, title, starter, answer, files, expected, checks=(), xp=4):
    assert code_box(eid, title, starter, answer, files, checks, xp=xp) == expected, eid



from workbook import QUESTION_SOURCE, STUDENT

# ------------------------------------------------ the JUnit stand-in
ANN = """package org.junit.jupiter.api;
import java.lang.annotation.*;
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface %s
{
}
"""
ASSERTIONS = """package org.junit.jupiter.api;
public final class Assertions
{
    public static void assertEquals(int expected, int actual)
    {
        if(expected != actual) {
            throw new AssertionError("expected: <" + expected + "> but was: <" + actual + ">");
        }
    }
    public static void assertEquals(Object expected, Object actual)
    {
        if(expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError("expected: <" + expected + "> but was: <" + actual + ">");
        }
    }
    public static void assertTrue(boolean condition)
    {
        if(!condition) {
            throw new AssertionError("expected: <true> but was: <false>");
        }
    }
    public static void assertFalse(boolean condition)
    {
        if(condition) {
            throw new AssertionError("expected: <false> but was: <true>");
        }
    }
}
"""
RUNNER = """import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
public class TestRun
{
    public static void all(Class<?> testClass) throws Exception
    {
        ArrayList<Method> tests = new ArrayList<>();
        for(Method m : testClass.getDeclaredMethods()) {
            if(m.isAnnotationPresent(Test.class)) {
                tests.add(m);
            }
        }
        Collections.sort(tests, Comparator.comparing(Method::getName));
        int errors = 0;
        int failures = 0;
        for(Method test : tests) {
            String result = runOne(testClass, test);
            System.out.println(result);
            if(result.startsWith("FAIL")) {
                failures++;
            }
            else if(result.startsWith("ERROR")) {
                errors++;
            }
        }
        System.out.println("Tests: " + tests.size() + "  Errors: " + errors + "  Failures: " + failures);
    }

    private static String runOne(Class<?> testClass, Method test) throws Exception
    {
        Object object = testClass.getDeclaredConstructor().newInstance();
        try {
            for(Method m : testClass.getDeclaredMethods()) {
                if(m.isAnnotationPresent(BeforeEach.class)) {
                    m.invoke(object);
                }
            }
            test.invoke(object);
            for(Method m : testClass.getDeclaredMethods()) {
                if(m.isAnnotationPresent(AfterEach.class)) {
                    m.invoke(object);
                }
            }
            return "PASS " + test.getName();
        }
        catch(InvocationTargetException e) {
            Throwable cause = e.getCause();
            if(cause instanceof AssertionError) {
                return "FAIL " + test.getName() + "  " + cause.getMessage();
            }
            return "ERROR " + test.getName() + "  " + cause;
        }
    }
}
"""
SHIM = [file('Test.java', ANN % 'Test'), file('BeforeEach.java', ANN % 'BeforeEach'),
        file('AfterEach.java', ANN % 'AfterEach'), file('Assertions.java', ASSERTIONS),
        file('TestRun.java', RUNNER)]


def run_it(test_class, more=''):
    """The hidden main: run one test class, then any further checks."""
    extra = '\n'.join('        ' + line for line in more.strip('\n').splitlines())
    return file('RunIt.java', f"""public class RunIt
{{
    public static void main(String[] args) throws Exception
    {{
        TestRun.all({test_class}.class);
{extra}
    }}
}}
""")


def tests_on(test_class, *classes, more=''):
    return list(classes) + SHIM + [run_it(test_class, more)]


def results(test_source, *classes):
    """Run a whole test class through the stand-in; return the printed lines."""
    name = re.search(r'public class (\w+)', test_source)[1]
    return run(test_source, tests_on(name, *classes))


def replaced(src, old, new):
    assert src.count(old) == 1, old
    return src.replace(old, new)


# ------------------------------------------------ the cafe, as four versions
def cafe(folder):
    return files_at('tdd/' + folder, 'Customer', 'MenuItem', 'Order')


FIXED = cafe('3_fixed')
FIRST_TRY = cafe('2_first_try')
ORDER_TEST = read('tdd/3_fixed/OrderTest.java')


def order_with(body):
    """The cafe with another removeItem body, to pin what the workbook says about it."""
    source = read('tdd/1_stub/Order.java')
    old = '    public boolean removeItem(MenuItem item)\n    {\n        return false;\n    }\n'
    new = '    public boolean removeItem(MenuItem item)\n    {\n' + body + '    }\n'
    return files_at('tdd/1_stub', 'Customer', 'MenuItem') + [file('Order.java', replaced(source, old, new))]


def failing(output):
    return [line for line in output.split('\n') if line.startswith('FAIL')]


# Sections 5 and 7 of the workbook, against real runs of the eight tests.
assert results(ORDER_TEST, *cafe('1_stub')).endswith('Tests: 8  Errors: 0  Failures: 3')
assert sorted(x.split()[1] for x in failing(results(ORDER_TEST, *cafe('1_stub')))) == ['removeItemInOrder', 'removeOneOfTwoSame', 'removeOnlyItem']
assert failing(results(ORDER_TEST, *FIRST_TRY)) == ['FAIL removeOnlyItem  expected: <true> but was: <false>']
assert results(ORDER_TEST, *FIXED).endswith('Tests: 8  Errors: 0  Failures: 0')
assert results(ORDER_TEST, *cafe('4_refactored')).endswith('Tests: 8  Errors: 0  Failures: 0')
# 5.2: a stub that returns true and removes nothing fails all five removeItem tests.
TRUE_STUB = results(ORDER_TEST, *order_with('        return true;\n'))
assert sorted(x.split()[1] for x in failing(TRUE_STUB)) == sorted(['removeItemInOrder', 'removeItemNotInOrder', 'removeFromEmptyOrder', 'removeOnlyItem', 'removeOneOfTwoSame']), TRUE_STUB
# 3.5 and 7.1: finds the item and returns true, but never removes it.
NEVER_REMOVES = results(ORDER_TEST, *order_with('        return items.contains(item);\n'))
assert 'FAIL removeItemInOrder  expected: <425> but was: <750>' in NEVER_REMOVES, NEVER_REMOVES
assert 'FAIL removeOnlyItem  expected: <0> but was: <250>' in NEVER_REMOVES, NEVER_REMOVES


def order_case(items, remove, files=FIXED):
    adds = '\n'.join(f'order.addItem(MenuItem.{i});' for i in items)
    return run(demo('Case', f"""Order order = new Order(new Customer("Ada Lim", "555-0101"), new ArrayList<>());
{adds}
System.out.println(order.removeItem(MenuItem.{remove}));
System.out.println(order.getTotal());""", 'import java.util.ArrayList;'), files)


# 3.1, 5.3 and the case table.
assert order_case(['TEA', 'COOKIE'], 'TEA') == 'true\n175'
assert order_case(['TEA', 'COOKIE'], 'COFFEE') == 'false\n375'
assert order_case(['COFFEE', 'MUFFIN'], 'MUFFIN', FIRST_TRY) == 'false\n575'
for items, remove, expected in [(['COFFEE', 'MUFFIN', 'COOKIE'], 'MUFFIN', 'true\n425'), (['COFFEE', 'MUFFIN'], 'TEA', 'false\n575'), ([], 'COFFEE', 'false\n0'), (['COFFEE'], 'COFFEE', 'true\n0'), (['COFFEE', 'COFFEE'], 'COFFEE', 'true\n250')]:
    assert order_case(items, remove) == expected
# 3.4
assert run(demo('Count', """ArrayList<String> none = new ArrayList<>();
System.out.println(Collections.frequency(none, "coffee"));
System.out.println(Collections.frequency(Arrays.asList("coffee", "muffin"), "tea"));
System.out.println(Collections.frequency(Arrays.asList("coffee", "muffin"), "muffin"));
System.out.println(Collections.frequency(Arrays.asList("coffee", "tea", "coffee"), "coffee"));""", 'import java.util.*;')) == '0\n0\n1\n2'

# ------------------------------------------------ explanations
for i, n in enumerate((m for m in QUESTION_SOURCE if m not in ('3.6', '3.7')), 1):
    if n in ('1.1', '1.2', '2.1', '2.5', '3.2', '3.5', '5.1', '5.5', '7.1', '7.2', '8.1'):
        E[f'r{i}'] = SHORT(solution(n))
assert set(E) == {'r1', 'r2', 'r3', 'r7', 'r9', 'r12', 'r16', 'r20', 'r24', 'r25', 'r26'}, set(E)
E['r27-why'] = SHORT(solution('8.2'))
# 3.7, from the first try: the middle items act alike and the last item does not.
assert order_case(['COFFEE', 'MUFFIN', 'COOKIE'], 'MUFFIN', FIRST_TRY) == 'true\n425'
assert order_case(['COFFEE', 'TEA', 'COOKIE'], 'TEA', FIRST_TRY) == 'true\n425'
assert order_case(['COFFEE', 'MUFFIN', 'COOKIE'], 'COOKIE', FIRST_TRY) == 'false\n750'
E['r-alike'] = SHORT(solution('3.7'))

# ------------------------------------------------ tables
def word(*accept, width='9rem', placeholder='answer'):
    return {'accept': list(accept), 'show': accept[0], 'placeholder': placeholder, 'width': width}


def boolean(value):
    return word(value, width='7rem', placeholder='true / false')


def table_spec(eid, blanks, xp=2):
    E[eid] = {'type': 'table', 'xp': xp, 'blanks': blanks}


table_spec('r4', {'0': num(8), '1': num(0)})
table_spec('r5', {'code': {'accept': code_forms('assertEquals(500, order.getTotal());'), 'show': 'assertEquals(500, order.getTotal());', **CODE}})
table_spec('r8', {'0-0': boolean('true'), '0-1': num(175), '1-0': boolean('false'), '1-1': num(375)})
table_spec('r10', {'0': word('positive', 'positive test'), '1': word('negative', 'negative test'), '2': word('edge', 'edge case', 'edge test')})
table_spec('r11', {'0': num(0), '1': num(0), '2': num(1), '3': num(2)})
table_spec('r-limit', {'0-0': num(9), '0-1': num(11), '1-0': num(29), '1-1': num(31)})
table_spec('r13', {'0': word('Create Test Class', 'Create Test Class...', width='18rem', placeholder='command'),
                   '1': word('Test All', width='18rem', placeholder='command'),
                   '2': word('Run Tests', width='18rem', placeholder='command'),
                   '3': word('Object Bench to Test Fixture', width='18rem', placeholder='command')})
table_spec('r17', {str(i): word('fail', 'fails', 'failed', width='7rem', placeholder='pass / fail') for i in range(5)})
table_spec('r18', {'limit0': num(1), 'cond0': boolean('true'), 'limit1': num(1), 'cond1': boolean('false')})
table_spec('r18-return', {'value': boolean('false')}, xp=1)

CARD = read('cards/starter/TransitCard.java')
CARD_TEST = read('practice_junit/TransitCardTest.java')
assert CARD_TEST.strip() == answer_code('6.1').strip()
# 6.2, from the supplied class
assert run(demo('Trace', """TransitCard exact = new TransitCard(250);
exact.tapOn();
System.out.println(exact.getBalance() + " " + exact.getTrips());
TransitCard month = new TransitCard(500);
month.tapOn();
System.out.println(month.getBalance() + " " + month.getTrips());
month.newMonth();
System.out.println(month.getBalance() + " " + month.getTrips());"""), [file('TransitCard.java', CARD)]) == '250 0\n250 1\n250 1'
table_spec('r22', {'0-0': num(250), '0-1': num(0), '1-0': num(250), '1-1': num(1), '2-0': num(250), '2-1': num(1)})

BOARD_FAULTY = without_method(strip_docs(read('programB/ScoreBoard.java')), 'public void reportState()')
BOARD_FIXED = replaced(BOARD_FAULTY, '        points = 0;\n    }\n\n    public int getPoints', '        points = 0;\n        rounds = 0;\n    }\n\n    public int getPoints')
# 8.2, from the supplied class
assert run(demo('Trace', """ScoreBoard b = new ScoreBoard();
b.recordRound(7);
System.out.println(b.getPoints() + " " + b.getRounds());
b.recordRound(5);
System.out.println(b.getPoints() + " " + b.getRounds());
b.reset();
System.out.println(b.getPoints() + " " + b.getRounds());
b.recordRound(3);
System.out.println(b.getPoints() + " " + b.getRounds());"""), [file('ScoreBoard.java', BOARD_FAULTY)]) == '7 1\n12 2\n0 2\n3 3'
table_spec('r27', {f'{i}-{j}': num(v) for i, row in enumerate([[7, 1], [12, 2], [0, 2], [3, 3]]) for j, v in enumerate(row)})

# ------------------------------------------------ code boxes
IMPORTS = """import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
"""
ORDER_FRAME = IMPORTS + """import java.util.ArrayList;

public class OrderTest
{
    private Customer ada;
    private Order order;

    @BeforeEach
    public void setUp()
    {
        ada = new Customer("Ada Lim", "555-0101");
        order = new Order(ada, new ArrayList<>());
    }

    // WRITE
}
"""


def in_frame(frame, comment, method):
    block = '\n'.join('    ' + line if line else '' for line in method.strip('\n').splitlines())
    return replaced(frame, '    // WRITE', block), replaced(frame, '    // WRITE', '    // ' + comment)


# 2.4
answer, starter = in_frame(ORDER_FRAME, 'Write totalOfThreeItems here.', answer_code('2.4'))
checked('r6', 'OrderTest.java', starter, answer, tests_on('OrderTest', *FIXED),
        'PASS totalOfThreeItems\nTests: 1  Errors: 0  Failures: 0',
        [has('@Test', 'Mark the method with @Test.'),
         has('order.addItem(MenuItem.COOKIE)', 'Add the cookie to the order.'),
         has('assertEquals(750,order.getTotal())', 'Check the total with assertEquals, with the expected value first.')])

# 4.2
CUSTOMER_TEST = read('tdd/suite/CustomerTest.java')
assert CUSTOMER_TEST.strip() == answer_code('4.2').strip()
checked('r14', 'CustomerTest.java', """// Write the imports here.

public class CustomerTest
{
    // Write nameIsKept and phoneIsKept here.
}
""", CUSTOMER_TEST, tests_on('CustomerTest', file('Customer.java', read('tdd/3_fixed/Customer.java'))),
        'PASS nameIsKept\nPASS phoneIsKept\nTests: 2  Errors: 0  Failures: 0',
        [matches(r'.*assertEquals\("AdaLim",\w+\.getName\(\)\).*', 'In nameIsKept, compare "Ada Lim" with getName(), with the expected value first.'),
         matches(r'.*assertEquals\("555-0101",\w+\.getPhone\(\)\).*', 'In phoneIsKept, compare "555-0101" with getPhone(), with the expected value first.')])

# 4.3
answer, starter = in_frame(ORDER_FRAME, 'Write removeOneOfTwoTeas here.', answer_code('4.3'))
checked('r15', 'OrderTest.java', starter, answer, tests_on('OrderTest', *FIXED),
        'PASS removeOneOfTwoTeas\nTests: 1  Errors: 0  Failures: 0',
        [has('order.addItem(MenuItem.COOKIE)', 'Start with tea, tea and a cookie.'),
         has('assertTrue(order.removeItem(MenuItem.TEA))', 'Check the return value with assertTrue.'),
         has('assertEquals(375,order.getTotal())', 'Check the total after the call.')])

# 5.4
answer, starter = in_frame(ORDER_FRAME, 'Write removeLastItem here.', answer_code('5.4'))
checked('r19', 'OrderTest.java', starter, answer, tests_on('OrderTest', *FIRST_TRY),
        'FAIL removeLastItem  expected: <true> but was: <false>\nTests: 1  Errors: 0  Failures: 1',
        [has('assertTrue(order.removeItem(MenuItem.MUFFIN))', 'Check the return value with assertTrue.'),
         has('assertEquals(250,order.getTotal())', 'Check the total after the call.')])

# 6.1
checked('r21', 'TransitCardTest.java', """import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;

public class TransitCardTest
{
    // Write the six tests here.
}
""", CARD_TEST, tests_on('TransitCardTest', file('TransitCard.java', CARD)),
        """FAIL newMonthResetsTrips  expected: <0> but was: <1>
PASS tapWithEnoughCredit
FAIL tapWithExactFare  expected: <true> but was: <false>
PASS tapWithTooLittleCredit
PASS topUpNegativeAmount
PASS topUpPositiveAmount
Tests: 6  Errors: 0  Failures: 2""",
        [has('topUp(-100)', 'Test a negative top-up of -100.'),
         has('newMonth()', 'Call newMonth in newMonthResetsTrips.')], xp=6)

# 6.3
CARD_FIXED = replaced(replaced(CARD, 'balance > FARE', 'balance >= FARE'), '        // Keep the credit for the new month.\n', '        trips = 0;\n')
CARD_MORE = """TransitCard low = new TransitCard(249);
System.out.println(low.tapOn() + " " + low.getBalance() + " " + low.getTrips());
TransitCard high = new TransitCard(251);
System.out.println(high.tapOn() + " " + high.getBalance() + " " + high.getTrips());
System.out.println(high.topUp(0) + " " + high.getBalance());
TransitCard month = new TransitCard(500);
month.tapOn();
month.newMonth();
month.newMonth();
System.out.println(month.tapOn() + " " + month.getBalance() + " " + month.getTrips());"""
checked('r23', 'TransitCard.java', CARD, CARD_FIXED,
        tests_on('TransitCardTest', file('TransitCardTest.java', CARD_TEST), more=CARD_MORE),
        """PASS newMonthResetsTrips
PASS tapWithEnoughCredit
PASS tapWithExactFare
PASS tapWithTooLittleCredit
PASS topUpNegativeAmount
PASS topUpPositiveAmount
Tests: 6  Errors: 0  Failures: 0
false 249 0
true 1 1
false 1
true 0 1""",
        [has('balance>=FARE', 'Accept an exact fare with >=.')])

# Program A
THERMO = strip_docs(read('programA/Thermostat.java'))
THERMO_TEST = read('programA/junit/ThermostatTest.java')
student_listings = listings(STUDENT.split(r'\section{8. Complete Java Programs}')[1])
THERMO_START = next(x for x in student_listings if 'public class Thermostat\n' in x)
THERMO_TEST_START = next(x for x in student_listings if 'public class ThermostatTest' in x)
# 3.6, from the real class.
assert run(demo('Limits', """for(int t : new int[] {9, 10, 11, 29, 30, 31}) {
    System.out.println(new Thermostat().setTarget(t));
}"""), (file('Thermostat.java', THERMO),)) == 'false\ntrue\ntrue\ntrue\ntrue\nfalse'
THERMO_MORE = """Thermostat more = new Thermostat();
System.out.println(more.setTarget(11) + " " + more.getTarget());
System.out.println(more.setTarget(29) + " " + more.getTarget());
System.out.println(more.setTarget(5) + " " + more.getTarget());"""
checked('r-p1-item', 'Thermostat.java', THERMO_START, THERMO,
        tests_on('ThermostatTest', file('ThermostatTest.java', THERMO_TEST), more=THERMO_MORE),
        """PASS aboveRange
PASS belowRange
PASS lowerLimit
PASS normalTarget
PASS startsAtTwenty
PASS upperLimit
Tests: 6  Errors: 0  Failures: 0
true 11
true 29
false 29""", xp=4)
checked('r-p1-test', 'ThermostatTest.java', THERMO_TEST_START, THERMO_TEST,
        tests_on('ThermostatTest', file('Thermostat.java', THERMO)),
        """PASS aboveRange
PASS belowRange
PASS lowerLimit
PASS normalTarget
PASS startsAtTwenty
PASS upperLimit
Tests: 6  Errors: 0  Failures: 0""",
        [has('heat=newThermostat()', 'Make a new thermostat in setUp.')]
        + [has(f'heat.setTarget({v})', f'Test the request at {v}.') for v in (22, 10, 30, 9, 31)]
        + [has('assertFalse(heat.setTarget(31))', 'Check that 31 is refused with assertFalse.'),
           has('assertEquals(20,heat.getTarget())', 'Check that a refused target leaves the old one.')], xp=6)
# 8.1
BUGGY_THERMO = replaced(THERMO, """        if(target < 10 || target > 30) {
            return false;
        }
        this.target = target;
        return true;""", """        this.target = target;
        return target >= 10 && target <= 30;""")
assert 'FAIL aboveRange  expected: <20> but was: <31>' in results(THERMO_TEST, file('Thermostat.java', BUGGY_THERMO))

# Program B
BOARD_TEST = read('programB/junit/ScoreBoardTest.java')
assert BOARD_TEST.strip() == next(x for x in listings(SOURCE) if 'public class ScoreBoardTest' in x).strip()
BOARD_TEST_START = IMPORTS + """
public class ScoreBoardTest
{
    private ScoreBoard board;

    @BeforeEach
    public void setUp()
    {
        // Make a new scoreboard.
    }

    // Write the four tests here.
}
"""
checked('r-p2-test', 'ScoreBoardTest.java', BOARD_TEST_START, BOARD_TEST,
        tests_on('ScoreBoardTest', file('ScoreBoard.java', BOARD_FAULTY)),
        """PASS freshBoard
FAIL newGameAfterReset  expected: <1> but was: <3>
FAIL resetClearsBoth  expected: <0> but was: <2>
PASS twoRounds
Tests: 4  Errors: 0  Failures: 2""",
        [has('board=newScoreBoard()', 'Make a new scoreboard in setUp.'),
         has('board.reset()', 'Call reset in the two reset tests.')], xp=6)
assert results(BOARD_TEST, file('ScoreBoard.java', BOARD_FIXED)).endswith('Tests: 4  Errors: 0  Failures: 0')
BOARD_MORE = """ScoreBoard more = new ScoreBoard();
more.reset();
System.out.println(more.getPoints() + " " + more.getRounds());
more.recordRound(0);
System.out.println(more.getPoints() + " " + more.getRounds());
more.reset();
more.reset();
System.out.println(more.getPoints() + " " + more.getRounds());"""
checked('r-p2-fix', 'ScoreBoard.java', BOARD_FAULTY, BOARD_FIXED,
        tests_on('ScoreBoardTest', file('ScoreBoardTest.java', BOARD_TEST), more=BOARD_MORE),
        """PASS freshBoard
PASS newGameAfterReset
PASS resetClearsBoth
PASS twoRounds
Tests: 4  Errors: 0  Failures: 0
0 0
0 1
0 0""")

data = {'id': 'lecture-15', 'course': 'COMP 2001: Object-Oriented Programming',
        'title': 'Lecture 15 Workbook', 'subtitle': 'Chapter 9: Testing and Debugging', 'exercises': E}
out = pathlib.Path(__file__).with_name('exercises.json')
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
print(f'wrote {out} with {len(E)} specs')
