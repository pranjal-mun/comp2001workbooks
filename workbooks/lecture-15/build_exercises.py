"""Build Lecture 15 exercises from the approved workbook and real Java runs.

New page: q1 to q28 follow questions 1.1 to 11.4 in order. Suffixes
identify classes, state tables or explanations in the same question.
Program classes use p1-* and p2-* as in Lecture 14. Every code case is
computed by run(), then pinned by an assert. Hidden drivers test boundaries,
refusals, repeated resets and later operations. No server is needed.
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



from workbook import QUESTION_SOURCE
RUNS = json.loads((CODE_DIR.parent/'validation/step2_runs.json').read_text())
OLD_RUNS = json.loads((CODE_DIR.parent/'_scratch/runs.json').read_text())
for i,n in enumerate(QUESTION_SOURCE,1):
    if n not in ['2.2','4.1','5.3','8.1','9.1','11.1','11.3','11.4']:
        E['q'+str(i)] = SHORT(solution(n))

def assertion(eid,code):
    E[eid]={'type':'table','xp':2,'blanks':{'code':{'accept':code_forms(code),'show':code,**CODE}}}
assertion('q4','assertEquals("two coffees", 500, order.getTotal());')
assertion('q18','assertEquals("day total kept", 575, till.getDayTotal());')
CARD1 = read('cards/part1/TransitCard.java')
CARD2 = read('cards/part2/TransitCard.java')
TEST1 = read('cards/part1/TransitCardTest.java')
TEST2 = read('cards/part2/TransitCardTest.java')
CARD_DEMO = read('cards/part2/TransitCardDemo.java')
CARD_EDGES = driver('CardEdges','''TransitCard low = new TransitCard(249);
System.out.println(low.tapOn());
System.out.println(low.getBalance());
System.out.println(low.getTrips());
TransitCard exact = new TransitCard(250);
System.out.println(exact.tapOn());
System.out.println(exact.getBalance());
System.out.println(exact.getTrips());
System.out.println(exact.tapOn());
System.out.println(exact.getBalance());
System.out.println(exact.getTrips());
TransitCard above = new TransitCard(251);
System.out.println(above.tapOn());
System.out.println(above.getBalance());
System.out.println(above.getTrips());
System.out.println(above.topUp(0));
System.out.println(above.topUp(-100));
System.out.println(above.getBalance());
System.out.println(above.getTrips());
System.out.println(above.topUp(100));
System.out.println(above.getBalance());
System.out.println(above.getTrips());''')
checked('q9-card','TransitCard.java',read('cards/starter/TransitCard.java'),CARD1,CARD_EDGES,
 'false\n249\n0\ntrue\n0\n1\nfalse\n0\n1\ntrue\n1\n1\nfalse\nfalse\n1\n1\ntrue\n101\n1')
TEST_START = '''public class TransitCardTest
{
    private static int failures = 0;

    public static void main(String[] args)
    {
        // Run testTaps and report the failure count.
    }

    // Add testTaps and the two assertion helpers.
}'''
TEST_CHECKS = [has('assertEquals(String label, int expected, int actual)', 'Include the integer assertion helper with a label.'),
 has('assertTrue(String label, boolean condition)', 'Include the boolean assertion helper with a label.'),
 has('failures++', 'Count failed checks and keep going.'),
 has('if(failures == 0)', 'Print the success message only when no check failed.'),
 has('testTaps();', 'Run the tap tests from main.'),
 matches(r'.*\.topUp\(-100\).*', 'Keep the negative top-up check.'),
 matches(r'.*\.tapOn\(\).*\.tapOn\(\).*\.tapOn\(\).*', 'Test the first tap, exact fare and third refused tap.')]
checked('q9-test','TransitCardTest.java',TEST_START,TEST1,[file('TransitCard.java',CARD1)],
 RUNS['card-part1/TransitCardTest'].strip(),TEST_CHECKS)
REPORT_START = '''public class Report
{
    private static int failures = 0;

    private static void report()
    {
        // Print success only for zero failures; otherwise print the count.
    }

    public static void main(String[] args)
    {
        report();
        failures = 2;
        report();
    }
}'''
REPORT = REPORT_START.replace('        // Print success only for zero failures; otherwise print the count.', '''        if(failures == 0) {
            System.out.println("All tests passed");
        }
        else {
            System.out.println("Failures: " + failures);
        }''')
checked('q12','Report.java',REPORT_START,REPORT,[], 'All tests passed\nFailures: 2',
 [has('if(failures == 0)', 'Compare the failure count with zero before reporting success.')])
E['q15-state']={'type':'table','xp':3,'blanks':{f'{i}-{j}':num(v) for i,row in enumerate([[0,0,0],[250,1,0],[250,1,250],[0,1,250],[175,2,250]]) for j,v in enumerate(row)}}
MONTH_EDGES = driver('MonthEdges','''TransitCard card = new TransitCard(500);
card.newMonth();
card.reportState();
System.out.println(card.tapOn());
card.reportState();
card.newMonth();
card.reportState();
card.newMonth();
card.reportState();
System.out.println(card.tapOn());
card.reportState();
System.out.println(card.tapOn());
card.reportState();
System.out.println(card.topUp(0));
System.out.println(card.topUp(-100));
card.reportState();
System.out.println(card.topUp(100));
card.reportState();
TransitCard low = new TransitCard(249);
System.out.println(low.tapOn());
low.reportState();
TransitCard above = new TransitCard(251);
System.out.println(above.tapOn());
above.reportState();''')
checked('q20-card','TransitCard.java',CARD1,CARD2,MONTH_EDGES,
 'balance=500 trips=0\ntrue\nbalance=250 trips=1\nbalance=250 trips=0\nbalance=250 trips=0\ntrue\nbalance=0 trips=1\nfalse\nbalance=0 trips=1\nfalse\nfalse\nbalance=0 trips=1\ntrue\nbalance=100 trips=1\nfalse\nbalance=249 trips=0\ntrue\nbalance=1 trips=1')
checked('q20-test','TransitCardTest.java',TEST1,TEST2,[file('TransitCard.java',CARD2)],
 RUNS['card-part2/TransitCardTest'].strip(),TEST_CHECKS+[
 has('testNewMonth();', 'Call the new month regression test from main.'),
 matches(r'.*\.newMonth\(\);.*', 'Exercise the month reset.'),
 matches(r'.*assertEquals\("[^"]*",0,[A-Za-z_$][\w$]*\.getTrips\(\)\);.*', 'Check that the month reset clears trips.'),
 matches(r'.*assertEquals\("[^"]*",250,[A-Za-z_$][\w$]*\.getBalance\(\)\);.*', 'Check that the month reset preserves credit.')])
checked('q20-demo','TransitCardDemo.java',demo('TransitCardDemo','// Report a fresh 500-cent card, three taps and the month reset.'),CARD_DEMO,[file('TransitCard.java',CARD2)],RUNS['card-part2/TransitCardDemo'].strip())
THERMO=read('programA/Thermostat.java');THERMO_TEST=read('programA/ThermostatTest.java')
checked('p1-item','Thermostat.java','''public class Thermostat
{
    // Add target, the constructor, setTarget and getTarget.
}''',THERMO,driver('ThermostatEdges','''Thermostat t = new Thermostat();
System.out.println(t.getTarget());
System.out.println(t.setTarget(22));
System.out.println(t.getTarget());
System.out.println(t.setTarget(9));
System.out.println(t.getTarget());
System.out.println(t.setTarget(10));
System.out.println(t.getTarget());
System.out.println(t.setTarget(30));
System.out.println(t.getTarget());
System.out.println(t.setTarget(31));
System.out.println(t.getTarget());
System.out.println(t.setTarget(10));
System.out.println(t.getTarget());'''),
 '20\ntrue\n22\nfalse\n22\ntrue\n10\ntrue\n30\nfalse\n30\ntrue\n10')
THERMO_CHECKS = [has('assertEquals(String label, int expected, int actual)', 'Include the integer assertion helper.'),
 has('assertTrue(String label, boolean condition)', 'Include the boolean assertion helper.'),
 has('failures++', 'Count failures and keep going.'),
 has('if(failures == 0)', 'Report success only when all checks pass.'),
 has('testTargets();', 'Run testTargets from main.')]
for value in [22,9,10,30,31]: THERMO_CHECKS.append(matches(r'.*\.setTarget\('+str(value)+r'\).*', f'Test the request at {value}.'))
checked('p1-test','ThermostatTest.java',demo('ThermostatTest','// Write testTargets, the assertion helpers and the final report.'),THERMO_TEST,[file('Thermostat.java',THERMO)],RUNS['programA/ThermostatTest'].strip(),THERMO_CHECKS)
checked('q25','ThermostatTest.java',THERMO_TEST,read('programA/extension/ThermostatTest.java'),[file('Thermostat.java',THERMO)],RUNS['programA-extension/ThermostatTest'].strip(),THERMO_CHECKS+[
 has('testReturnToLowerBound();','Call the new boundary test from main.'),
 has('private static void testReturnToLowerBound()', 'Add the separate boundary test with a fresh fixture.')])
BOARD=read('programB/fixed/ScoreBoard.java');FAULTY=read('programB/ScoreBoard.java');BOARD_DEMO=read('programB/ScoreBoardDemo.java')
checked('p2-demo','ScoreBoardDemo.java',demo('ScoreBoardDemo','// Report a fresh scoreboard, rounds 7 and 5, a reset and round 3.'),BOARD_DEMO,[file('ScoreBoard.java',FAULTY)],RUNS['programB/ScoreBoardDemo'].strip())
checked('q27','ScoreBoard.java',FAULTY,BOARD,driver('ScoreBoardEdges','''ScoreBoard s = new ScoreBoard();
s.reset();
s.reportState();
s.recordRound(7);
s.reportState();
s.recordRound(5);
s.reportState();
s.reset();
s.reportState();
s.reset();
s.reportState();
s.recordRound(0);
s.reportState();
s.recordRound(3);
s.reportState();
System.out.println(s.getPoints());
System.out.println(s.getRounds());'''),
 'points=0 rounds=0\npoints=7 rounds=1\npoints=12 rounds=2\npoints=0 rounds=0\npoints=0 rounds=0\npoints=0 rounds=1\npoints=3 rounds=2\n3\n2')
E['q27-state']={'type':'table','xp':2,'blanks':{f'{i}-{j}':num(v) for i,row in enumerate([[0,0],[7,1],[12,2],[0,0],[3,1]]) for j,v in enumerate(row)}}
BOARD_TEST=read('programB/fixed/ScoreBoardTest.java')
BOARD_CHECKS=[has('testFreshGame();','Run the new-game regression test from main.'),
 has('failures++','Count each failed check and keep going.'),
 has('if(failures == 0)','Report success only when all checks pass.')]
for fragment in ['board.recordRound(7)','board.recordRound(5)','board.reset()','board.recordRound(3)','board.getPoints()','board.getRounds()']:
    BOARD_CHECKS.append(has(fragment.replace('board.',''),'Keep the two-round first game, reset and checks for both fields.'))
checked('q28','ScoreBoardTest.java',demo('ScoreBoardTest','// Add testFreshGame, the assertion helpers and the final report.'),BOARD_TEST,[file('ScoreBoard.java',BOARD)],RUNS['programB-fixed/ScoreBoardTest'].strip(),BOARD_CHECKS)

data={'id':'lecture-15','course':'COMP 2001: Object-Oriented Programming',
      'title':'Lecture 15 Workbook','subtitle':'Chapter 9: Testing and Debugging','exercises':E}
out=pathlib.Path(__file__).with_name('exercises.json')
out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print(f'wrote {out} with {len(E)} specs')
