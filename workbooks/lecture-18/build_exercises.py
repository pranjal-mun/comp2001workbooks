"""Build Lecture 18 exercises from the workbook and real Java runs.

Question N.M has the id qN-M; p1-* and p2-* are the classes of the two
complete programs. Multiple-choice questions take their options, the right one
(marked \\correct) and the explanation from the workbook. Every code case is computed by run(),
then pinned by an assert against the output the workbook prints. The classes
come from the lecture's code folder, where they were compiled and run.
"""
import base64, html, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402

LECTURES = ROOT.parent / "output"
CODE_DIR = LECTURES / "L18_Chapter_13_Dynamic_Method_Lookup_v4" / "code"
L17_CODE = LECTURES / "L17_Chapter_12B_Subtyping_Polymorphism_v4" / "code"


def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()


def run(code, files=(), inputs=()):
    status, stdout, stderr, _ = run_java(code.rstrip("\n"), inputs, None, files)
    assert status == "ok", f"{status}\n{stderr}"
    return stdout.rstrip("\n")


def attempt(code, files=()):
    """(status, stdout, stderr) without asserting success."""
    status, stdout, stderr, _ = run_java(code.rstrip("\n"), (), None, files)
    return status, stdout.rstrip("\n"), stderr


def compile_errors(code, files=()):
    """The compiler's messages, or '' when the code compiles."""
    status, stdout, stderr, message = run_java(code.rstrip("\n"), (), None, files)
    return stderr if status == "compile-error" else ""


def has(fragment, message):
    """A check line: the source contains `fragment`, ignoring whitespace."""
    compact = re.sub(r"\s+", "", fragment)
    return f'require(source.replaceAll("\\\\s+", "").contains({json.dumps(compact)}), {json.dumps(message)});'


def lacks(fragment, message):
    compact = re.sub(r"\s+", "", fragment)
    return f'require(!source.replaceAll("\\\\s+", "").contains({json.dumps(compact)}), {json.dumps(message)});'


def file(name, content):
    return {"name": name, "content": content.rstrip("\n")}


def demo(name, body, imports=""):
    """A class whose main method holds `body`."""
    lines = "\n".join("        " + line if line else "" for line in body.strip("\n").splitlines())
    return f"{imports}public class {name}\n{{\n    public static void main(String[] args)\n    {{\n{lines}\n    }}\n}}\n"


def driver(name, body, imports=""):
    """A hidden class whose main method exercises the student's class."""
    return file(f"{name}.java", demo(name, body, imports))


def box(starter, answer, extra=12):
    n = max(starter.count("\n"), answer.count("\n")) + 2
    return {"minLines": n, "maxLines": n + extra}


def code_box(eid, title, starter, answer, files, checks, xp=4, extra=12, name="Output of the checking program"):
    E[eid] = {"type": "code", "xp": xp, "title": title, **box(starter, answer, extra),
              "starter": starter.rstrip("\n"),
              "cases": [{"name": name, "expected": run(answer, files)}],
              "check": "\n".join(checks),
              "answer": b64(answer), "files": list(files)}
    return E[eid]["cases"][0]["expected"]


def checked(eid, title, starter, answer, files, expected, checks=(), xp=4):
    got = code_box(eid, title, starter, answer, files, checks, xp=xp)
    assert got == expected, (eid, got)
    # The starter alone must not already pass.
    status, out, _ = attempt(starter, files)
    assert not (status == "ok" and out == expected), (eid, "starter passes")


def read(path):
    return (CODE_DIR / path).read_text()


def files_at(folder, *names):
    return [file(name + '.java', read(folder + '/' + name + '.java')) for name in names]


def replaced(src, old, new):
    assert src.count(old) == 1, old
    return src.replace(old, new)


def without(src, header, note):
    """src with the @Override method `header` removed and a comment in its place."""
    lines = src.rstrip("\n").split("\n")
    i = lines.index("    " + header)
    assert lines[i - 1] == "    @Override", header
    j = lines.index("    }", i)
    return "\n".join(lines[:i - 1] + ["    // " + note] + lines[j + 1:]) + "\n"


def lines_table(eid, output, xp=2, width="20rem"):
    blanks = {}
    for i, line in enumerate(output.split("\n")):
        accept = [line] + ([f'"{line}"'] if not re.fullmatch(r"-?\d+|true|false|null", line) else [])
        blanks[str(i)] = {"accept": accept, "show": line, "caseSensitive": True, "placeholder": "printed", "width": width}
    E[eid] = {"type": "table", "xp": xp, "blanks": blanks}


SHORT = lambda answer, chars=20, rows=2, xp=2: {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}  # noqa: E731
YES = {"accept": ["yes", "Yes", "yes.", "overrides", "it overrides"], "show": "yes", "placeholder": "yes / no", "width": "8rem"}
NO = {"accept": ["no", "No", "no.", "does not override", "it does not override"], "show": "no", "placeholder": "yes / no", "width": "8rem"}
E = {}

# ------------------------------------------------ workbook
sys.path.insert(0, str(ROOT.parent / 'scripts' / 'web_l18'))
from hl import unsplit  # noqa: E402
from workbook import question_code, answer_code, QUESTION_RAW, QUESTION_SOURCE, SOURCE, STUDENT, listings, inline, group  # noqa: E402

ID = {n: 'q' + n.replace('.', '-') for n in QUESTION_SOURCE}
assert len(ID) == 42, len(ID)


def solution(n):
    m = re.search(r'\\solution\{', QUESTION_RAW[n])
    return html.unescape(re.sub('<[^>]+>', '', inline(group(QUESTION_RAW[n], m.end()-1)[0])))


def solution_output(n):
    """The output listing the solutions edition prints for question n."""
    raw = QUESTION_RAW[n]
    m = re.search(r'\\begin\{lstlisting\}\[style=output[^\]]*\]\n(.*?)\\end\{lstlisting\}', raw[raw.index(r'\ifsolutions'):], re.S)
    return m[1].rstrip('\n')


def word(*accept, width='10rem', placeholder='answer'):
    forms = []
    for a in accept:
        for f in (a, a.lower(), a.capitalize()):
            if f not in forms:
                forms.append(f)
    return {'accept': forms, 'show': accept[0], 'placeholder': placeholder, 'width': width}


def inside(member, src):
    """The workbook's member, indented as in the class, is part of src."""
    return '\n'.join('    ' + x if x else x for x in member.split('\n')) in src


def table_spec(eid, blanks, xp=2):
    E[eid] = {'type': 'table', 'xp': xp, 'blanks': blanks}


TABULAR = re.compile(r'\\begin\{tabular\}\{[^}]+\}(.*?)\\end\{tabular\}', re.S)


def fillins(n):
    """Rows of the question's table as (cells, answers); blank ids match page.py."""
    text = re.sub(r'\\(?:toprule|midrule|bottomrule)', '', TABULAR.search(QUESTION_RAW[n])[1])
    rows = [[x.strip() for x in row.split('&')] for row in text.split(r'\\') if row.strip()][1:]
    out = []
    for i, row in enumerate(rows):
        values = [group(x, len(r'\fillin'))[0] for x in row if x.startswith(r'\fillin')]
        codes = [re.findall(r'\\texttt\{(.*?)\}', x) for x in row if not x.startswith(r'\fillin')]
        ids = [str(i)] if len(values) == 1 else [f'{i}-{j}' for j in range(len(values))]
        out.append((codes, dict(zip(ids, values))))
    return out


def auto_spec(eid, n, make):
    blanks = {}
    for _, values in fillins(n):
        for k, v in values.items():
            blanks[k] = make(v)
    table_spec(eid, blanks)


def code_lines(n):
    """The code of each row, in table order (the last texttt of the row)."""
    return [codes[-1][-1] if codes[-1] else None for codes, _ in fillins(n)]


def answers_of(n):
    return [list(values.values()) for _, values in fillins(n)]


YN = lambda v: YES if v == 'yes' else NO  # noqa: E731
TF = lambda v: word(v, width='7rem', placeholder='true / false')  # noqa: E731
CLASS = lambda v: word(v, width='11rem', placeholder='class')  # noqa: E731


def same(listing, path):
    """The workbook prints the class exactly as it is in the code folder."""
    assert listing.strip() == read(path).strip(), path


def tex_unescape(s):
    return s.replace('\\ ', ' ').replace(r'\{', '{').replace(r'\}', '}').replace(r'\_', '_')


NAMES = ('Notice', 'TextNotice', 'EventNotice', 'JobNotice', 'NoticeBoard')
OVERRIDE = files_at('notices/override', *NAMES)
SUPER = files_at('notices/super', *NAMES)
TOSTRING = files_at('notices/tostring', *NAMES)
HASH = files_at('notices/hash', 'Notice', 'TextNotice')
EQUALS = files_at('notices/equals', 'Notice', 'TextNotice')


def swap(files, name, content):
    return [file(name + '.java', content) if f['name'] == name + '.java' else f for f in files]


# The workbook prints these classes as they are in the code folder.
for path in ('notices/nooverride/TextNotice.java', 'notices/super/TextNotice.java'):
    assert any(x.strip() == read(path).strip() for x in listings(SOURCE)), path

# ------------------------------------------------ 1. Overriding
E[ID['1.1']] = SHORT(solution('1.1'))
# 1.2: which headers, written with @Override in TextNotice, compile.
TEXT = read('notices/override/TextNotice.java')
for header, (want,) in zip(code_lines('1.2'), answers_of('1.2')):
    src = replaced(TEXT, 'public void printSummary()', tex_unescape(header))
    ok = not compile_errors(src, swap(OVERRIDE, 'TextNotice', src))
    assert ok == (want == 'yes'), header
auto_spec('q1-2', '1.2', YN)

# ------------------------------------------------ 2. Lookup
# 2.1: the class where the lookup finds each method.
DECLS = question_code('2.1') + '\n'
for call, (want,) in zip(code_lines('2.1'), answers_of('2.1')):
    var, method = re.fullmatch(r'(\w+)\.(\w+)\(\)', call).groups()
    found = run(demo('Where', DECLS + f'try {{ System.out.println({var}.getClass().getMethod("{method}").getDeclaringClass().getSimpleName()); }}\ncatch(NoSuchMethodException e) {{ }}'), OVERRIDE)
    assert found == want, (call, found)
auto_spec('q2-1', '2.1', CLASS)

# 2.2: EventNotice without printSummary().
NO_EVENT = without(read('notices/override/EventNotice.java'), 'public void printSummary()', 'No printSummary() here.')
got = run(demo('Bo', 'Notice n = new EventNotice("bo", "Hackathon", 12);\nn.pin();\nn.printSummary();'), swap(OVERRIDE, 'EventNotice', NO_EVENT))
assert got == solution_output('2.2') == 'bo  pins: 1', got
lines_table('q2-2', got)
E['q2-2-why'] = SHORT(solution('2.2'))
E[ID['2.3']] = SHORT(solution('2.3'))

# ------------------------------------------------ 3. Super
got = run(demo('Gil', question_code('3.1')), SUPER)
assert got == solution_output('3.1') == 'gil  pins: 2\n  Chess club, day 3', got
lines_table('q3-1', got)

JOB_SUPER = read('notices/super/JobNotice.java')
assert inside(answer_code('3.2'), JOB_SUPER.replace('System.out.println("  job at " + employer);', 'System.out.println("  job at " + employer);'))
checked('q3-2', 'JobNotice.java', without(JOB_SUPER, 'public void printSummary()', 'Add printSummary() here.'), JOB_SUPER,
        files_at('notices/super', 'Notice') + [driver('JobCheck', 'Notice n = new JobNotice("dara", "Campus Bookstore");\nn.printSummary();')],
        'dara  pins: 0\n  job at Campus Bookstore',
        [has('super.printSummary()', 'Use super.printSummary() for the first line.')])

# ------------------------------------------------ 4. toString
got = run(demo('Found', question_code('4.1')), TOSTRING)
assert got == solution_output('4.1') == 'bo [pins: 1] Hackathon, day 12\nFound: hal [pins: 0] Lost keys.', got
lines_table('q4-1', got)

JOB_TOSTRING = read('notices/tostring/JobNotice.java')
assert inside(answer_code('4.2'), JOB_TOSTRING)
checked('q4-2', 'JobNotice.java', without(JOB_TOSTRING, 'public String toString()', 'Add toString() here.'), JOB_TOSTRING,
        files_at('notices/tostring', 'Notice') + [driver('JobCheck', 'Notice n = new JobNotice("dara", "Campus Bookstore");\nSystem.out.println(n);\nn.pin();\nSystem.out.println("Board: " + n);')],
        'dara [pins: 0] job at Campus Bookstore\nBoard: dara [pins: 1] job at Campus Bookstore',
        [has('super.toString()', 'Use super.toString() for the author and the pins.'),
         lacks('System.out.', 'Return the text; do not print it.')])

# ------------------------------------------------ 5. Equality
DECLS = question_code('5.1') + '\n'
for expr, (want,) in zip(code_lines('5.1'), answers_of('5.1')):
    assert run(demo('Same', DECLS + f'System.out.println({expr});'), HASH) == want, expr
auto_spec('q5-1', '5.1', TF)

EVENT = read('notices/tostring/EventNotice.java')
EVENT_START = 'import java.util.Objects;\n' + replaced(EVENT, '\n}', '\n    // Add equals and hashCode here.\n}')
EVENT_ANSWER = 'import java.util.Objects;\n' + replaced(EVENT, '\n}', '\n' + '\n'.join('    ' + x if x else x for x in answer_code('5.2').split('\n')) + '\n}')
checked('q5-2', 'EventNotice.java', EVENT_START, EVENT_ANSWER,
        files_at('notices/tostring', 'Notice') + [driver('EventCheck', '''EventNotice a = new EventNotice("bo", "Hackathon", 12);
EventNotice b = new EventNotice("bo", "Hackathon", 12);
EventNotice c = new EventNotice("bo", "Hackathon", 13);
b.pin();
System.out.println(a == b);
System.out.println(a.equals(b));
System.out.println(a.equals(c));
System.out.println(a.equals("Hackathon"));
HashSet<EventNotice> set = new HashSet<>();
set.add(a);
set.add(b);
set.add(c);
System.out.println(set.size());''', 'import java.util.HashSet;\n')],
        'false\ntrue\nfalse\nfalse\n2',
        [has('instanceofEventNotice', 'Check obj instanceof EventNotice before the cast.'),
         has('Objects.hash(', 'Build the hash code with Objects.hash(...).')], xp=6)
E[ID['5.3']] = SHORT(solution('5.3'))

# ------------------------------------------------ 6. Reuse
E[ID['6.1']] = SHORT(solution('6.1'))
assert run(read('notices/reuse/ListBoardDemo.java'), files_at('notices/reuse', 'Notice', 'TextNotice', 'ListBoard')) == read('notices/reuse/ListBoardDemo.output.txt').rstrip('\n') == '0'

# ------------------------------------------------ 7. Whole program
PHOTO = read('workbook/photo/PhotoNotice.java')
same(answer_code('7.1'), 'workbook/photo/PhotoNotice.java')
for cls in NAMES:
    assert read(f'workbook/photo/{cls}.java') == read(f'notices/tostring/{cls}.java'), cls
checked('q7-1', 'PhotoNotice.java', 'public class PhotoNotice extends Notice\n{\n    // Add the field, the constructor and toString().\n}\n', PHOTO,
        files_at('workbook/photo', *NAMES, 'PhotoDemo'), read('workbook/photo/PhotoDemo.output.txt').rstrip('\n'),
        [has('super.toString()', 'Use super.toString() for the author and the pins.')], xp=6)
assert E['q7-1']['cases'][0]['expected'] == 'eli [pins: 0] Room 2 is free.\nfay [pins: 1] photo: Campus at dawn'

# ------------------------------------------------ 8. Bikes
STARTER, PART1, PART2 = 'bikes/starter', 'bikes/part1', 'bikes/part2'
for part in (STARTER, PART1, PART2):
    for cls in ('Bike', 'EBike'):
        assert any(x.strip() == read(f'{part}/{cls}.java').strip() for x in listings(SOURCE)) or part != STARTER, (part, cls)
assert run(read(PART1 + '/BikeDemo.java'), files_at(PART1, 'Bike', 'EBike')) == read(PART1 + '/BikeDemo.output.txt').rstrip('\n')
assert run(read(PART2 + '/BikeDemo.java'), files_at(PART2, 'Bike', 'EBike')) == read(PART2 + '/BikeDemo.output.txt').rstrip('\n')
starter_out = run(read(STARTER + '/BikeDemo.java'), files_at(STARTER, 'Bike', 'EBike'))
assert re.fullmatch(r'Bike@[0-9a-f]+: 3 hours, \$12\nBike@[0-9a-f]+: 3 hours, \$15\nEBike@[0-9a-f]+: 3 hours, \$18', starter_out), starter_out

BIKE0, BIKE1, BIKE2 = read(STARTER + '/Bike.java'), read(PART1 + '/Bike.java'), read(PART2 + '/Bike.java')
assert inside(answer_code('8.1'), BIKE1) and without(BIKE1, 'public String toString()', 'x') == replaced(BIKE0, '\n}', '\n    // x\n}')
checked('q8-1', 'Bike.java', replaced(BIKE0, '\n}', '\n    // Add toString() here.\n}'), BIKE1,
        files_at(STARTER, 'EBike', 'BikeDemo'), 'B1 ($4/h): 3 hours, $12\nB2 ($5/h): 3 hours, $15\nE1 ($6/h): 3 hours, $18')
same(answer_code('8.2'), PART1 + '/EBike.java')
checked('q8-2', 'EBike.java', replaced(read(STARTER + '/EBike.java'), '\n}', '\n    // Add cost and toString here.\n}'), read(PART1 + '/EBike.java'),
        files_at(PART1, 'Bike', 'BikeDemo'), read(PART1 + '/BikeDemo.output.txt').rstrip('\n'),
        [has('super.cost(hours)', 'Use super.cost(hours) for the bike price.'),
         has('super.toString()', 'Use super.toString() for the id and the rate.')])
assert read(PART2 + '/EBike.java') == read(PART1 + '/EBike.java')
assert inside(answer_code('8.3'), BIKE2)
checked('q8-3', 'Bike.java', 'import java.util.Objects;\n' + replaced(BIKE1, '\n}', '\n    // Add equals and hashCode here.\n}'), BIKE2,
        files_at(PART2, 'EBike', 'BikeDemo'), read(PART2 + '/BikeDemo.output.txt').rstrip('\n'),
        [has('Objects.hash(id)', 'Build the hash code from the id, as equals uses only the id.')], xp=6)
assert E['q8-3']['cases'][0]['expected'].endswith('true\nBikes out: 2')

# 8.4: cost without super calls itself.
LOOP = replaced(read(PART1 + '/EBike.java'), 'return super.cost(hours) + 5;', 'return cost(hours) + 5;')
status, out, err = attempt(read(PART1 + '/BikeDemo.java'), files_at(PART1, 'Bike') + [file('EBike.java', LOOP)])
assert status == 'error' and 'StackOverflowError' in err, (status, err[:300])
E[ID['8.4']] = SHORT(solution('8.4'))

# ------------------------------------------------ 9. Review
auto_spec('q9-1', '9.1', TF)
BROKEN = unsplit('\n'.join(x.rstrip() for x in listings(QUESTION_SOURCE['9.3'])))
assert BROKEN.startswith('public class TextNotice') and BROKEN.endswith('\n}'), BROKEN
NOTICE = files_at('notices/super', 'Notice')
CHECK93 = driver('Review', 'TextNotice t = new TextNotice("eli", "Room 2 is free.");\nSystem.out.println(t);\nt.printSummary();')
errors = compile_errors(BROKEN, NOTICE + [CHECK93])
assert 'must override or implement a supertype method' in errors and 'This method must return a result of type String' in errors, errors
FIXED = replaced(replaced(replaced(BROKEN, 'public void printSummary(String prefix)', 'public void printSummary()'),
                          'System.out.println(prefix + message);', 'System.out.println(getAuthor() + ": " + message);'),
                 'System.out.println(getAuthor() + ": " + message);\n    }\n}', 'return getAuthor() + ": " + message;\n    }\n}')
assert 'public void printSummary()' in solution('9.3') and 'return getAuthor() + ": " + message;' in solution('9.3')
E['q9-3'] = SHORT(solution('9.3'))
checked('q9-3-fix', 'TextNotice.java', BROKEN, FIXED, NOTICE + [CHECK93], 'eli: Room 2 is free.\neli: Room 2 is free.',
        [has('publicvoidprintSummary()', 'printSummary() takes no parameter, like the one in Notice.'),
         has('return', 'toString() must return the text.')])

# ------------------------------------------------ Complete Java Programs
def skeleton(first):
    return next(x for x in listings(STUDENT) if x.startswith(first)).rstrip()


A, B = 'workbook/programA', 'workbook/programB'
for name in ('Vehicle', 'Truck', 'Fleet', 'FleetDemo'):
    assert any(x.strip() == read(f'{A}/{name}.java').strip() for x in listings(SOURCE)), name
for name in ('Ticket', 'StudentTicket', 'Show', 'ShowDemo'):
    assert any(x.strip() == read(f'{B}/{name}.java').strip() for x in listings(SOURCE)), name
assert run(read(A + '/FleetDemo.java'), files_at(A, 'Vehicle', 'Truck', 'Fleet')) == read(A + '/FleetDemo.output.txt').rstrip('\n')
assert run(read(B + '/ShowDemo.java'), files_at(B, 'Ticket', 'StudentTicket', 'Show')) == read(B + '/ShowDemo.output.txt').rstrip('\n')

# The Lecture 17 classes, before this lecture's methods.
VEHICLE17 = (L17_CODE / A / 'Vehicle.java').read_text()
assert without(read(A + '/Vehicle.java'), 'public String toString()', 'x') == replaced(VEHICLE17, '\n}', '\n    // x\n}')
checked('p1-vehicle', 'Vehicle.java', replaced(VEHICLE17, '\n}', '\n    // Add toString() here.\n}'), read(A + '/Vehicle.java'),
        [driver('VehicleCheck', 'Vehicle v = new Vehicle("CAR-9");\nv.drive(12);\nSystem.out.println(v);\nSystem.out.println("Fleet: " + v);')],
        'CAR-9: 12 km\nFleet: CAR-9: 12 km')
checked('p1-truck', 'Truck.java', without(read(A + '/Truck.java'), 'public String toString()', 'Add toString() here.'), read(A + '/Truck.java'),
        files_at(A, 'Vehicle') + [driver('TruckCheck', 'Vehicle t = new Truck("TRK-8", 500);\nt.drive(70);\nSystem.out.println(t);')],
        'TRK-8: 70 km, max load 500 kg',
        [has('super.toString()', 'Use super.toString() for the plate and the km.')])
checked('p1-fleet', 'Fleet.java', skeleton('import java.util.ArrayList;\npublic class Fleet'), read(A + '/Fleet.java'),
        files_at(A, 'Vehicle', 'Truck', 'FleetDemo'), read(A + '/FleetDemo.output.txt').rstrip('\n'),
        [has('ArrayList<Vehicle>', 'Keep one ArrayList<Vehicle>.')], xp=6)

TICKET17 = (L17_CODE / B / 'Ticket.java').read_text()
assert read(B + '/Ticket.java').startswith('import java.util.Objects;\n' + TICKET17.rstrip()[:-1])
checked('p2-ticket', 'Ticket.java', 'import java.util.Objects;\n' + replaced(TICKET17, '\n}', '\n    // Add toString, equals and hashCode here.\n}'), read(B + '/Ticket.java'),
        [driver('TicketCheck', '''Ticket a = new Ticket("A3", 20);
Ticket b = new Ticket("A3", 30);
Ticket c = new Ticket("C5", 25);
System.out.println(a);
System.out.println(a.equals(b));
System.out.println(a.equals(c));
System.out.println(a.hashCode() == b.hashCode());''')],
        'A3: 20 dollars\ntrue\nfalse\ntrue',
        [has('instanceofTicket', 'Check obj instanceof Ticket before the cast.')], xp=6)
checked('p2-student', 'StudentTicket.java', without(read(B + '/StudentTicket.java'), 'public String toString()', 'Add toString() here.'), read(B + '/StudentTicket.java'),
        files_at(B, 'Ticket') + [driver('StudentCheck', 'Ticket t = new StudentTicket("B12", 15, "2001234");\nSystem.out.println(t);')],
        'B12: 15 dollars, student 2001234',
        [has('super.toString()', 'Use super.toString() for the seat and the price.')])
checked('p2-show', 'Show.java', skeleton('import java.util.ArrayList;\npublic class Show'), read(B + '/Show.java'),
        files_at(B, 'Ticket', 'StudentTicket', 'ShowDemo'), read(B + '/ShowDemo.output.txt').rstrip('\n'),
        [has('ArrayList<Ticket>', 'Keep one ArrayList<Ticket>.'), has('.contains(', 'Use the list\'s contains to find a sold seat.')], xp=6)

# ------------------------------------------------ multiple choice
CHOICES = re.compile(r'\\begin\{choices\}(.*?)\\end\{choices\}', re.S)
MCQS = [n for n in QUESTION_SOURCE if CHOICES.search(QUESTION_RAW[n])]
assert len(MCQS) == 22, MCQS
for n in MCQS:
    raw = QUESTION_RAW[n]
    opts = re.split(r'\\item\b', CHOICES.search(raw)[1])[1:]
    right = [i for i, o in enumerate(opts) if r'\correct' in o]
    assert len(opts) == 4 and len(right) == 1, n
    m = re.search(r'\\solution\{', raw)
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', inline(group(raw, m.end() - 1)[0]))
    text = html.unescape(re.sub('<[^>]+>', '', text))
    head = f'{"ABCD"[right[0]]}. '
    assert text.startswith(head), (n, text[:40])
    E[ID[n]] = {'type': 'choice', 'xp': 1, 'options': len(opts), 'answer': right[0], 'explain': b64(text[len(head):])}


def answer_index(n):
    return E[ID[n]]['answer']


# 1.4: the misspelled method without @Override is a new method, so Notice's runs.
TYPO = replaced(TEXT, '    @Override\n    public void printSummary()', '    public void printsummary()')
got = run(read('notices/override/NoticeBoardDemo.java'), swap(OVERRIDE, 'TextNotice', TYPO))
assert 'chen  pins: 0' in got and 'Lost calculator.' not in got, got
assert answer_index('1.4') == 2
# 3.3: printSummary() instead of super.printSummary() calls itself.
LOOP = replaced(read('notices/super/TextNotice.java'), 'super.printSummary();', 'printSummary();')
status, out, err = attempt(read('notices/super/NoticeBoardDemo.java'), swap(SUPER, 'TextNotice', LOOP))
assert status == 'error' and 'StackOverflowError' in err and answer_index('3.3') == 2, (status, err[:200])
# 3.4: author is private in Notice.
PRIV = replaced(read('notices/super/TextNotice.java'), 'super.printSummary();', 'System.out.println(author);')
assert 'not visible' in compile_errors(PRIV, swap(SUPER, 'TextNotice', PRIV)) and answer_index('3.4') == 2
# 4.4: Object's toString: class name, @ and a number.
assert re.fullmatch(r'Room@[0-9a-f]+', run(demo('Print', 'System.out.println(new Room());'), [file('Room.java', 'public class Room\n{\n}')]))
assert answer_index('4.4') == 2
# 5.6: equals without hashCode lets the set keep both.
assert 'hashCode' not in read('notices/equals/TextNotice.java')
assert run(read('notices/equals/EqualsDemo.java'), EQUALS).split('\n')[-1] == '2' and answer_index('5.6') == 2
assert run(read('notices/hash/EqualsDemo.java'), HASH).split('\n')[-1] == '1'
# 6.3: a final TextNotice can be used, but not extended.
FINAL = files_at('notices/final', 'Notice', 'TextNotice')
assert 'public final class TextNotice' in FINAL[1]['content']
assert run(demo('Use', 'Notice n = new TextNotice("ada", "Hi");\nTextNotice t = new TextNotice("bo", "Hi");\nSystem.out.println(n + " / " + t);'), FINAL) == 'ada [pins: 0] Hi / bo [pins: 0] Hi'
assert 'cannot subclass the final class TextNotice' in compile_errors(read('notices/final/UrgentNotice.java'), FINAL)
assert not compile_errors('public class PhotoNotice extends Notice\n{\n    public PhotoNotice(String author)\n    {\n        super(author);\n    }\n}', FINAL)
assert answer_index('6.3') == 1
# 7.2: the board is the same class with and without PhotoNotice.
assert answer_index('7.2') == 3
# 8.5: E1 costs 6 * 3 + 5.
assert '$23' in read(PART1 + '/BikeDemo.output.txt') and answer_index('8.5') == 1
# 8.6: equal ids, different rates.
assert run(demo('Same', 'System.out.println(new Bike("B1", 4).equals(new Bike("B1", 6)));'), files_at(PART2, 'Bike')) == 'true'
assert answer_index('8.6') == 0

# The web page has room for each println on one line; the PDF splits some.
from hl import unsplit  # noqa: E402
for spec in E.values():
    if spec.get('type') != 'code':
        continue
    spec['starter'] = unsplit(spec['starter'])
    spec['answer'] = b64(unsplit(base64.b64decode(spec['answer']).decode()))
    for f in spec['files']:
        f['content'] = unsplit(f['content'])

data = {'id': 'lecture-18', 'course': 'COMP 2001: Object-Oriented Programming',
        'title': 'Lecture 18 Workbook', 'subtitle': 'Chapter 13: Overriding and method lookup', 'exercises': E}
out = pathlib.Path(__file__).with_name('exercises.json')
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
print(f'wrote {out} with {len(E)} specs')
