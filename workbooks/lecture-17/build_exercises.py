"""Build Lecture 17 exercises from the workbook and real Java runs.

Question N.M has the id qN-M; p1-* and p2-* are the two new classes of each
complete program. Multiple-choice questions take their options, the right one
(marked \\correct) and the explanation from the workbook. Every code case is computed by run(),
then pinned by an assert against the output the workbook prints. The classes
come from the lecture's code folder, where they were compiled and run.
"""
import base64, html, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402

CODE_DIR = ROOT.parent / "output" / "L17_Chapter_12B_Subtyping_Polymorphism_v4" / "code"


def b64(text):
    return base64.b64encode(text.rstrip("\n").encode()).decode()


def run(code, files=(), inputs=()):
    status, stdout, stderr, _ = run_java(code.rstrip("\n"), inputs, None, files)
    assert status == "ok", f"{status}\n{stderr}"
    return stdout.rstrip("\n")


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


def demo(name, body):
    """A class whose main method holds `body`."""
    lines = "\n".join("        " + line if line else "" for line in body.strip("\n").splitlines())
    return f"public class {name}\n{{\n    public static void main(String[] args)\n    {{\n{lines}\n    }}\n}}\n"


def driver(name, body):
    """A hidden class whose main method exercises the student's class."""
    return file(f"{name}.java", demo(name, body))


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


def read(path):
    return (CODE_DIR / path).read_text()


def files_at(folder, *names):
    return [file(name + '.java', read(folder + '/' + name + '.java')) for name in names]


def replaced(src, old, new):
    assert src.count(old) == 1, old
    return src.replace(old, new)


def lines_table(eid, output, xp=2, width="20rem"):
    blanks = {}
    for i, line in enumerate(output.split("\n")):
        accept = [line] + ([f'"{line}"'] if not re.fullmatch(r"-?\d+|true|false|null", line) else [])
        blanks[str(i)] = {"accept": accept, "show": line, "caseSensitive": True, "placeholder": "printed", "width": width}
    E[eid] = {"type": "table", "xp": xp, "blanks": blanks}


SHORT = lambda answer, chars=20, rows=2, xp=2: {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}  # noqa: E731
YES = {"accept": ["yes", "Yes", "yes.", "compiles", "it compiles"], "show": "yes", "placeholder": "yes / no", "width": "8rem"}
NO = {"accept": ["no", "No", "no.", "does not compile", "it does not compile"], "show": "no", "placeholder": "yes / no", "width": "8rem"}
E = {}

# ------------------------------------------------ workbook
sys.path.insert(0, str(ROOT.parent / 'scripts' / 'web_l17'))
from workbook import question_code, answer_code, QUESTION_RAW, QUESTION_SOURCE, SOURCE, STUDENT, listings, inline, group  # noqa: E402

ID = {n: 'q' + n.replace('.', '-') for n in QUESTION_SOURCE}
assert len(ID) == 42, len(ID)


def solution(n):
    m = re.search(r'\\solution\{', QUESTION_RAW[n])
    return html.unescape(re.sub('<[^>]+>', '', inline(group(QUESTION_RAW[n], m.end()-1)[0])))


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
    return [codes[-1][-1] for codes, _ in fillins(n)]


def answers_of(n):
    return [list(values.values()) for _, values in fillins(n)]


YN = lambda v: YES if v == 'yes' else NO  # noqa: E731
RESULT = lambda v: word(v, *( ('ok', 'compiles', 'runs') if v == 'fine' else ('compile-time error', 'compiler error') if v == 'compile error' else ('runtime error', 'run time error', 'ClassCastException')), width='11rem', placeholder='fine / compile / run-time')  # noqa: E731
TF = lambda v: word(v, width='7rem', placeholder='true / false')  # noqa: E731
TYPE = lambda v: word(v, v.replace('ArrayList<', '').rstrip('>') if v.startswith('ArrayList<') else v, width='12rem', placeholder='type')  # noqa: E731


def same(listing, path):
    """The workbook prints the class exactly as it is in the code folder."""
    assert listing.strip() == read(path).strip(), path


ONELIST = files_at('notices/onelist', 'Notice', 'TextNotice', 'EventNotice', 'JobNotice', 'NoticeBoard')
MAMMALS = files_at('check', 'Animal', 'Mammal', 'Cat', 'Dog')
MAMMAL_DECLS = question_code('3.3') + '\n'
assert MAMMAL_DECLS.startswith('ArrayList<Mammal> mammals')
PART1, PART2 = 'shelter/part1', 'shelter/part2'
ANIMALS1 = files_at(PART1, 'Animal', 'Dog', 'Cat', 'Rabbit')
ANIMALS2 = files_at(PART2, 'Animal', 'Dog', 'Cat', 'Rabbit')
same(next(x for x in listings(STUDENT) if x.startswith('import java.util.ArrayList;\npublic class NoticeBoard\n{\n    private ArrayList<Notice> notices;')),
     'notices/onelist/NoticeBoard.java')


def outcome(body, files, imports=False):
    """fine, compile error or run-time error for a main method holding body."""
    code = ('import java.util.ArrayList;\n' if imports else '') + demo('Try', body)
    status, _, stderr, _ = run_java(code, (), None, files)
    return {'ok': 'fine', 'compile-error': 'compile error'}.get(status, 'run-time error')


# ------------------------------------------------ written answers
for n in ('1.1', '2.2', '8.4'):
    E[ID[n]] = SHORT(solution(n))
E['q3-2'] = SHORT('ArrayList<Mammal> mammals = new ArrayList<>();\n' + solution('3.2'))
E['q9-1'] = SHORT(solution('9.1'))
E['q8-5-why'] = SHORT(solution('8.5'))

# 2.1: substitution, one line at a time.
for line, (want,) in zip(code_lines('2.1'), answers_of('2.1')):
    assert (outcome(line, ONELIST) == 'fine') == (want == 'yes'), line
auto_spec('q2-1', '2.1', YN)

# 3.1: the new board prints in the order added, with later pins.
ORDER = files_at('workbook/order', 'Notice', 'TextNotice', 'EventNotice', 'JobNotice', 'NoticeBoard')
got = run(demo('Prediction', question_code('3.1')), ORDER)
assert got == read('workbook/order/OrderDemo.output.txt').rstrip('\n') == 'eli  pins: 1\nfay  pins: 2\ngil  pins: 0', got
lines_table('q3-1', got)
E['q3-1-why'] = SHORT(solution('3.1'))

# 3.2: the mammal list takes cats and dogs.
assert run('import java.util.ArrayList;\n' + demo('Mammals', answer_code('3.2') + '\nmammals.add(new Cat("Tom"));\nmammals.add(new Dog("Rex"));\nSystem.out.println(mammals.size());'), MAMMALS) == '2'

# 3.3: which lines compile after the declarations.
for line, (want,) in zip(code_lines('3.3'), answers_of('3.3')):
    assert (outcome(MAMMAL_DECLS + line, MAMMALS, imports=True) == 'fine') == (want == 'yes'), line
auto_spec('q3-3', '3.3', YN)

# 4.1: declared and actual types, shown by getClass().
for (codes, values) in fillins('4.1'):
    decl = codes[0][0]
    name = re.match(r'\w+ (\w+) =', decl)[1]
    files = MAMMALS if 'Animal' in decl or 'Mammal' in decl else ONELIST
    assert run(demo('Types', decl + f'\nSystem.out.println({name}.getClass().getSimpleName());'), files) == values[list(values)[1]], decl
    assert decl.startswith(values[list(values)[0]] + ' '), decl
auto_spec('q4-1', '4.1', TYPE)

# 4.2: only Notice methods compile on a Notice variable.
N42 = 'Notice n = new EventNotice("bo", "Hackathon", 12);\n'
for line, (want,) in zip(code_lines('4.2'), answers_of('4.2')):
    assert (outcome(N42 + line, ONELIST) == 'fine') == (want == 'yes'), line
auto_spec('q4-2', '4.2', YN)

# 5.1: cast back to EventNotice.
CAST_START = question_code('5.1') + '\n// Write the two lines here.\n'
CAST_ANSWER = question_code('5.1') + '\n' + answer_code('5.1') + '\n'
checked('q5-1', 'Main.java', CAST_START, CAST_ANSWER, files_at('notices/onelist', 'Notice', 'EventNotice'),
        'bo: Hackathon, day 12\n  pins: 1',
        [has('(EventNotice)', 'Cast n to EventNotice before calling printSummary().')])

# 5.2: the mammal casts, each line on its own.
M52 = question_code('5.2') + '\n'
for line, (want,) in zip(code_lines('5.2'), answers_of('5.2')):
    assert outcome(M52 + line, MAMMALS) == want, line
auto_spec('q5-2', '5.2', RESULT)

# 5.3: casts of a job notice.
N53 = 'Notice n = new JobNotice("dara", "Campus Bookstore");\n'
for line, (want,) in zip(code_lines('5.3'), answers_of('5.3')):
    assert outcome(N53 + line, ONELIST) == want, line
auto_spec('q5-3', '5.3', RESULT)

# 6.1: the most specific list type; each list takes what the row says.
for (codes, values), adds, refused in zip(fillins('6.1'), [
        ['new TextNotice("ada", "Hi")', 'new JobNotice("dara", "Library")'],
        ['new Cat("Tom")'],
        ['new Cat("Tom")', 'new Dog("Rex")'],
        ['new TextNotice("ada", "Hi")', '"Lost keys"']],
        ['"Lost keys"', 'new Dog("Rex")', 'new Animal("Nemo")', None]):
    t = list(values.values())[0]
    body = f'{t} list = new ArrayList<>();\n' + '\n'.join(f'list.add({a});' for a in adds)
    files = ONELIST + MAMMALS
    assert outcome(body, files, imports=True) == 'fine', t
    if refused:
        assert outcome(body + f'\nlist.add({refused});', files, imports=True) == 'compile error', t
auto_spec('q6-1', '6.1', TYPE)

# 7.1: totalPins.
TOTAL = read('workbook/total/NoticeBoard.java')
assert inside(answer_code('7.1'), TOTAL)
BOARD_START = replaced(read('workbook/order/NoticeBoard.java'), '\n}', '\n    // Add totalPins() here.\n}')
checked('q7-1', 'NoticeBoard.java', BOARD_START, TOTAL,
        files_at('workbook/total', 'Notice', 'TextNotice', 'EventNotice', 'JobNotice', 'TotalDemo'), 'Total pins: 3',
        [has('getPins()', 'Add up getPins() of each notice.')])

# ------------------------------------------------ the shelter
SHELTER1, SHELTER2 = read(PART1 + '/Shelter.java'), read(PART2 + '/Shelter.java')
assert answer_code('8.1').strip() == SHELTER1.strip()
assert SHELTER2.startswith(SHELTER1.rstrip()[:-1]) and inside(answer_code('8.2'), SHELTER2)
assert run(read(PART1 + '/ShelterDemo.java'), ANIMALS1 + [file('Shelter.java', SHELTER1)]) == read(PART1 + '/output.txt').rstrip('\n')
assert run(read(PART2 + '/ShelterDemo.java'), ANIMALS2 + [file('Shelter.java', SHELTER2)]) == read(PART2 + '/output.txt').rstrip('\n')
SHELTER_START = """import java.util.ArrayList;
public class Shelter
{
    private ArrayList<Animal> animals;
    // The constructor, add, printAll and countAdopted.
}
"""
checked('q8-1', 'Shelter.java', SHELTER_START, SHELTER1, ANIMALS1 + files_at(PART1, 'ShelterDemo'),
        'Rex, age 3\nMia, age 2\nBiscuit, age 5\nClover, age 1\nAdopted: 1',
        [has('ArrayList<Animal>', 'Keep one ArrayList<Animal>.')], xp=6)
DEMO2 = read(PART2 + '/ShelterDemo.java')
DEMO2_BODY = '\n'.join(x[8:] for x in DEMO2.split('\n')[4:-3])
assert DEMO2_BODY.startswith('Dog rex') and DEMO2_BODY.endswith('}'), DEMO2_BODY[-40:]
checked('q8-2', 'Shelter.java', replaced(SHELTER1, '\n}', '\n    // Add findByName and oldest here.\n}'), SHELTER2,
        ANIMALS2 + [driver('ShelterCheck', DEMO2_BODY + '\nSystem.out.println("Empty: " + new Shelter().oldest());')],
        read(PART2 + '/output.txt').rstrip('\n') + '\nEmpty: null', xp=6)
FILL = DEMO2_BODY[:DEMO2_BODY.index('shelter.printAll();')].rstrip('\n')
assert answer_code('8.3') in DEMO2_BODY
checked('q8-3', 'Main.java', FILL + '\n// Find Rex and print his breed.\n', FILL + '\n' + answer_code('8.3') + '\n',
        ANIMALS2 + [file('Shelter.java', SHELTER2)], 'Rex breed: Beagle',
        [has('(Dog)', 'Cast the animal to Dog before calling getBreed().'), has('!=null', 'Check for null before the cast.')])

# 8.4: a cat cast to Dog.
status, _, stderr, _ = run_java(FILL + '\n' + question_code('8.4'), (), None, ANIMALS2 + [file('Shelter.java', SHELTER2)])
assert status == 'error' and 'ClassCastException' in stderr and 'Cat cannot be cast to class Dog' in stderr, stderr

# 8.5: the declared type is Animal.
A85 = 'Animal a = new Dog("Rex", 3, "Beagle");\n'
for line, (want,) in zip(code_lines('8.5'), answers_of('8.5')):
    assert (outcome(A85 + line, ANIMALS2) == 'fine') == (want == 'yes'), line
auto_spec('q8-5', '8.5', YN)

# ------------------------------------------------ review
BROKEN = 'import java.util.ArrayList;\n' + demo('Review', question_code('9.1'))
errors = compile_errors(BROKEN, ONELIST)
assert '2 problems (2 errors)' in errors and 'not applicable for the arguments (String)' in errors and 'printSummary() is undefined for the type Notice' in errors, errors
FIXED = replaced(replaced(BROKEN, 'notices.add("Lost keys");', 'notices.add(new TextNotice("hal", "Lost keys."));'),
                 'notice.printSummary();', 'System.out.println(notice.getAuthor());')
assert 'notices.add(new TextNotice("hal", "Lost keys."));' in solution('9.1') and 'System.out.println(notice.getAuthor());' in solution('9.1')
checked('q9-1-fix', 'Review.java', BROKEN, FIXED, ONELIST, 'eli\nhal',
        [lacks('printSummary', 'Notice has no printSummary(): call a Notice method instead.')])
auto_spec('q9-2', '9.2', TF)
assert outcome('Notice n = new JobNotice("dara", "Library");\nTextNotice t = (TextNotice) n;', ONELIST) == 'run-time error'

# ------------------------------------------------ Complete Java Programs
def skeleton(first):
    return next(x for x in listings(STUDENT) if x.startswith(first)).rstrip()


A, B = 'workbook/programA', 'workbook/programB'
for name in ('Fleet', 'FleetDemo'):
    assert any(x.strip() == read(f'{A}/{name}.java').strip() for x in listings(SOURCE)), name
for name in ('Show', 'ShowDemo'):
    assert any(x.strip() == read(f'{B}/{name}.java').strip() for x in listings(SOURCE)), name
for name in ('Vehicle', 'Truck'):
    assert read(f'{A}/{name}.java') == (CODE_DIR.parents[1] / 'L16_Chapter_12A_Inheritance_v4/code' / A / f'{name}.java').read_text(), name
for name in ('Ticket', 'StudentTicket'):
    assert read(f'{B}/{name}.java') == (CODE_DIR.parents[1] / 'L16_Chapter_12A_Inheritance_v4/code' / B / f'{name}.java').read_text(), name

checked('p1-list', 'Fleet.java', skeleton('import java.util.ArrayList;\npublic class Fleet'), read(A + '/Fleet.java'),
        files_at(A, 'Vehicle', 'Truck') + [driver('FleetCheck', """Vehicle car = new Vehicle("CAR-1");
car.drive(10);
Truck truck = new Truck("TRK-5", 300);
truck.drive(40);
Fleet fleet = new Fleet();
fleet.add(car);
fleet.add(truck);
fleet.printAll();
System.out.println("Total: " + fleet.totalKm());
System.out.println(fleet.get(1).getPlate());""")],
        'CAR-1: 10 km\nTRK-5: 40 km\nTotal: 50\nTRK-5',
        [has('ArrayList<Vehicle>', 'Keep one ArrayList<Vehicle>.')], xp=6)
checked('p1-demo', 'FleetDemo.java', skeleton('public class FleetDemo'), read(A + '/FleetDemo.java'), files_at(A, 'Vehicle', 'Truck', 'Fleet'),
        read(A + '/FleetDemo.output.txt').rstrip('\n'),
        [has('(Truck)', 'Cast fleet.get(1) to Truck before calling printDetails().')])
checked('p2-list', 'Show.java', skeleton('import java.util.ArrayList;\npublic class Show'), read(B + '/Show.java'),
        files_at(B, 'Ticket', 'StudentTicket') + [driver('ShowCheck', """Show show = new Show();
show.sell(new Ticket("D1", 10));
show.sell(new StudentTicket("E2", 30, "2005555"));
show.printSeats();
System.out.println("Total: " + show.totalSales());
System.out.println(show.find("E2").getPrice());
System.out.println(show.find("X1") == null);""")],
        'D1: 10 dollars\nE2: 30 dollars\nTotal: 40\n30\ntrue',
        [has('ArrayList<Ticket>', 'Keep one ArrayList<Ticket>.')], xp=6)
checked('p2-demo', 'ShowDemo.java', skeleton('public class ShowDemo'), read(B + '/ShowDemo.java'), files_at(B, 'Ticket', 'StudentTicket', 'Show'),
        read(B + '/ShowDemo.output.txt').rstrip('\n'),
        [has('(StudentTicket)', 'Cast the ticket to StudentTicket before calling printTicket().')])

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


def option_codes(n):
    return [re.findall(r'\\texttt\{(.*?)\}', o)[0] for o in re.split(r'\\item\b', CHOICES.search(QUESTION_RAW[n])[1])[1:]]


def answer_index(n):
    return E[ID[n]]['answer']


# Code options: exactly the marked option behaves differently, checked by real compiles.
N24 = 'NoticeBoard board = new NoticeBoard();\nNotice n = new JobNotice("dara", "Campus Bookstore");\n'
assert [outcome(N24 + c, ONELIST) for c in option_codes('2.4')] == ['fine', 'fine', 'compile error', 'fine']
assert [outcome(N24.split('\n')[1] + '\n' + 'n.' + c[len('notice.'):] + ';', ONELIST) for c in option_codes('3.4')] == ['compile error', 'fine', 'compile error', 'compile error']
assert [outcome(MAMMAL_DECLS + c, MAMMALS, imports=True) for c in option_codes('3.5')] == ['fine', 'fine', 'fine', 'compile error']
assert [outcome('Notice n = new TextNotice("ada", "Hi");\nObject x = ' + c + ';', ONELIST) for c in option_codes('5.6')] == ['fine', 'run-time error', 'fine', 'compile error']
assert [outcome(c, ONELIST, imports=True) for c in option_codes('6.2')] == ['fine', 'fine', 'fine', 'compile error']
S86 = FILL + '\nAnimal old = shelter.oldest();\n'
assert [outcome(S86 + c, ANIMALS2 + [file('Shelter.java', SHELTER2)]) for c in option_codes('8.6')] == ['compile error', 'fine', 'compile error', 'compile error']
assert [answer_index(n) for n in ('2.4', '3.4', '3.5', '5.6', '6.2', '8.6')] == [2, 1, 3, 3, 3, 1]
# 4.3: the actual type survives the Notice variable.
assert run(demo('Actual', 'Notice n = new TextNotice("ada", "Study group at 4pm.");\nSystem.out.println(n.getClass().getName());'), ONELIST) == 'TextNotice'
# 6.4: Notice's superclass is Object.
assert run(demo('Super', 'System.out.println(Notice.class.getSuperclass().getName());'), ONELIST) == 'java.lang.Object'
# 7.2: a PhotoNotice goes on the board with no change to it.
PHOTO = 'public class PhotoNotice extends Notice\n{\n    public PhotoNotice(String author)\n    {\n        super(author);\n    }\n}\n'
assert run(demo('Photo', 'NoticeBoard board = new NoticeBoard();\nboard.addNotice(new PhotoNotice("bo"));\nboard.show();'), ONELIST + [file('PhotoNotice.java', PHOTO)]) == 'bo  pins: 0'

# The web page has room for each println on one line; the PDF splits some.
from hl import unsplit  # noqa: E402
for spec in E.values():
    if spec.get('type') != 'code':
        continue
    spec['starter'] = unsplit(spec['starter'])
    spec['answer'] = b64(unsplit(base64.b64decode(spec['answer']).decode()))
    for f in spec['files']:
        f['content'] = unsplit(f['content'])

data = {'id': 'lecture-17', 'course': 'COMP 2001: Object-Oriented Programming',
        'title': 'Lecture 17 Workbook', 'subtitle': 'Chapter 12, Part 2: Subtyping and substitutable objects', 'exercises': E}
out = pathlib.Path(__file__).with_name('exercises.json')
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
print(f'wrote {out} with {len(E)} specs')
