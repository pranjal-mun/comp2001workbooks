"""Build Lecture 16 exercises from the workbook and real Java runs.

Question N.M has the id qN-M; p1-* and p2-* are the three classes of each
complete program. Multiple-choice questions take their options, the right one
(marked \\correct) and the explanation from the workbook. Every code case is computed by run(),
then pinned by an assert against the output the workbook prints. The classes
come from the lecture's code folder, where they were compiled and run.
"""
import base64, html, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402

CODE_DIR = ROOT.parent / "output" / "L16_Chapter_12A_Inheritance_v4" / "code"


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
sys.path.insert(0, str(ROOT.parent / 'scripts' / 'web_l16'))
from workbook import question_code, answer_code, QUESTION_RAW, QUESTION_SOURCE, SOURCE, STUDENT, listings, inline, group  # noqa: E402

ID = {n: 'q' + n.replace('.', '-') for n in QUESTION_SOURCE}
assert len(ID) == 44, len(ID)


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


def same(listing, path):
    """The workbook prints the class exactly as it is in the code folder."""
    assert listing.strip() == read(path).strip(), path


SUPER = files_at('notices/superclass', 'Notice', 'TextNotice', 'EventNotice')
same(next(x for x in listings(STUDENT) if x.startswith('public class Notice\n')), 'notices/superclass/Notice.java')

# ------------------------------------------------ explanations
for n in ('3.2', '4.3', '5.2', '6.2', '6.3', '8.1'):
    E[ID[n]] = SHORT(solution(n))

# 1.1: the board prints by kind.
ORDER = files_at('workbook/order', 'TextNotice', 'EventNotice', 'NoticeBoard')
got = run(demo('Prediction', question_code('1.1')), ORDER)
assert got == """eli: Room 2 is free.
  pins: 0
fay: Chess club, day 3
  pins: 0
gil: Git basics, day 5
  pins: 0""", got
lines_table('q1-1', got)
E['q1-1-why'] = SHORT(solution('1.1'))

# 2.1: which calls compile.
MADE = question_code('2.1') + '\n'
for call, ok in [('note.pin();', True), ('note.getPins();', True), ('note.printSummary();', True),
                 ('plain.getAuthor();', True), ('plain.printSummary();', False)]:
    errors = compile_errors(demo('Calls', MADE + call), SUPER)
    assert (errors == '') == ok, (call, errors)
table_spec('q2-1', {'0': YES, '1': YES, '2': YES, '3': YES, '4': NO})

# 2.2: trace an event notice.
TRACE = files_at('workbook/trace', 'Notice', 'EventNotice')
got = run(demo('Prediction', question_code('2.2')), TRACE)
assert got == 'fay\n2\nfay: Chess club, day 3\n  pins: 2', got
lines_table('q2-2', got)

# 2.3: where each field is declared.
assert 'private String author;' in read('notices/superclass/Notice.java')
assert 'private int day;' in read('notices/superclass/EventNotice.java')
table_spec('q2-3', {'0': word('Notice'), '1': word('Notice'), '2': word('EventNotice'), '3': word('EventNotice')})

# 3.1: construction order, shown by printing from each statement.
TRACED = (replaced(replaced(read('notices/superclass/Notice.java'),
                            '        this.author = author;\n', '        this.author = author;\n        System.out.println("author");\n'),
                   '        pins = 0;\n', '        pins = 0;\n        System.out.println("pins");\n'))
TRACED_TEXT = replaced(read('notices/superclass/TextNotice.java'),
                       '        this.message = message;\n', '        this.message = message;\n        System.out.println("message");\n')
assert run(demo('Order', 'new TextNotice("chen", "Lost calculator.");'),
           [file('Notice.java', TRACED), file('TextNotice.java', TRACED_TEXT)]) == 'author\npins\nmessage'
ORDINAL = lambda k, n, w: word(k, n, w, width='7rem', placeholder='1st to 4th')  # noqa: E731
table_spec('q3-1', {'0': ORDINAL('4th', '4', 'fourth'), '1': ORDINAL('3rd', '3', 'third'),
                  '2': ORDINAL('1st', '1', 'first'), '3': ORDINAL('2nd', '2', 'second')})

# 3.2: without super, the Workshop does not compile.
errors = compile_errors(read('workbook/workshop_nosuper/Workshop.java'), files_at('workbook/workshop_nosuper', 'Notice', 'EventNotice'))
assert 'Implicit super constructor EventNotice() is undefined' in errors, errors  # the site's compiler (ECJ) words it this way

# 3.3: the Workshop constructor.
WORKSHOP = read('workbook/workshop/Workshop.java')
assert inside(answer_code('3.3'), WORKSHOP)
WORKSHOP_START = """public class Workshop extends EventNotice
{
    private String room;
    // Write the constructor here.
    public String getRoom()
    {
        return room;
    }
}
"""
checked('q3-3', 'Workshop.java', WORKSHOP_START, WORKSHOP,
        files_at('workbook/workshop', 'Notice', 'EventNotice', 'WorkshopDemo'),
        'gil: Git basics, day 5\n  pins: 1\n  room: EN-2036',
        [has('super(author,title,day)', 'Call super(author, title, day) to set up the EventNotice part.')])

# 4.1: author and pins are private in Notice.
errors = compile_errors(read('workbook/fields/EventNotice.java'), files_at('workbook/fields', 'Notice'))
assert errors.count('is not visible') == 2 and 'Notice.author' in errors and 'Notice.pins' in errors, errors
ERR = lambda: word('error', 'an error', width='9rem', placeholder='compiles / error')  # noqa: E731
OK = lambda: word('compiles', 'fine', width='9rem', placeholder='compiles / error')  # noqa: E731
table_spec('q4-1', {'0': ERR(), '1': OK(), '2': OK(), '3': ERR()})

# 4.2: printShort.
SHORT_TEXT = read('workbook/short/TextNotice.java')
assert inside(answer_code('4.2'), SHORT_TEXT)
TEXT_START = replaced(read('notices/superclass/TextNotice.java'), '\n}', '\n    // Add printShort() here.\n}')
checked('q4-2', 'TextNotice.java', TEXT_START, SHORT_TEXT,
        files_at('workbook/short', 'Notice', 'ShortDemo'), 'ada (2 pins)',
        [has('getAuthor()', 'Use getAuthor(): author is private in Notice.'),
         has('getPins()', 'Use getPins(): pins is private in Notice.')])

# 5.1, 5.3, 7.5, 8.2
ISA = lambda: word('is-a', 'is a', width='7rem', placeholder='is-a / has-a')  # noqa: E731
HASA = lambda: word('has-a', 'has a', width='7rem', placeholder='is-a / has-a')  # noqa: E731
EXT = lambda: word('extends', 'with extends', width='9rem', placeholder='extends / field')  # noqa: E731
FIELD = lambda *more: word('a field', 'field', 'with a field', *more, width='9rem', placeholder='extends / field')  # noqa: E731
table_spec('q5-1', {'0-0': ISA(), '0-1': EXT(), '1-0': HASA(), '1-1': FIELD(), '2-0': HASA(), '2-1': FIELD('a list', 'a field (a list)', 'list'),
                   '3-0': ISA(), '3-1': EXT()})
# 5.5: pin() is inherited two levels down.
assert run(demo('Up', 'Workshop w = new Workshop("gil", "Git basics", 5, "EN-2036");\nw.pin();\nSystem.out.println(w.getPins());'),
           files_at('workbook/workshop', 'Notice', 'EventNotice', 'Workshop')) == '1'
INH = lambda: word('inheritance', 'extends', width='9rem', placeholder='inheritance / field')  # noqa: E731
table_spec('q7-5', {'0': INH(), '1': word('a field', 'field', 'a list', width='9rem', placeholder='inheritance / field'), '2': INH()})
E['q7-5-why'] = SHORT(solution('7.5'))
TF = lambda v: word(v, width='7rem', placeholder='true / false')  # noqa: E731
table_spec('q8-2', {'0': TF('true'), '1': TF('false'), '2': TF('false'), '3': TF('true')})

# 6.1: SaleNotice.
SALE = read('workbook/sale/SaleNotice.java')
assert answer_code('6.1').strip() == SALE.strip()
SALE_START = """public class SaleNotice extends Notice
{
    // Fields, constructor and printSummary().
}
"""
SALE_DRIVER = driver('SaleCheck', """SaleNotice sale = new SaleNotice("eli", "a bike", 40);
sale.pin();
sale.printSummary();
SaleNotice desk = new SaleNotice("fay", "a desk lamp", 12);
desk.printSummary();""")
checked('q6-1', 'SaleNotice.java', SALE_START, SALE, files_at('workbook/sale', 'Notice') + [SALE_DRIVER],
        'eli: selling a bike for 40 dollars\n  pins: 1\nfay: selling a desk lamp for 12 dollars\n  pins: 0',
        [has('extendsNotice', 'SaleNotice extends Notice.'), has('super(author)', 'Call super(author) first.')], xp=6)

# 6.2: the four pieces of the answer, placed in the board with three lists.
FIELD62, CTOR62, ADD62, LOOP62 = [x.strip('\n') for x in re.split(r'\n\n(?://[^\n]*\n)?', answer_code('6.2'))]
assert FIELD62.startswith('private') and ADD62.startswith('public void addSaleNotice') and LOOP62.startswith('for'), answer_code('6.2')
indent = lambda text, k: '\n'.join(' ' * k + x if x else x for x in text.split('\n'))  # noqa: E731
BOARD62 = read('notices/job/NoticeBoard.java')
BOARD62 = replaced(BOARD62, '    private ArrayList<JobNotice> jobNotices;\n', '    private ArrayList<JobNotice> jobNotices;\n' + indent(FIELD62, 4) + '\n')
BOARD62 = replaced(BOARD62, '        jobNotices = new ArrayList<>();\n', '        jobNotices = new ArrayList<>();\n' + indent(CTOR62, 8) + '\n')
BOARD62 = replaced(BOARD62, '    public void show()\n', indent(ADD62, 4) + '\n    public void show()\n')
BOARD62 = BOARD62.rstrip()[:-1].rstrip()[:-1].rstrip() + '\n' + indent(LOOP62, 8) + '\n    }\n}\n'
assert run(demo('SaleBoard', """NoticeBoard board = new NoticeBoard();
board.addSaleNotice(new SaleNotice("eli", "a bike", 40));
board.addJobNotice(new JobNotice("dara", "Campus Bookstore"));
board.show();"""), files_at('notices/job', 'Notice', 'TextNotice', 'EventNotice', 'JobNotice') + files_at('workbook/sale', 'SaleNotice') + [file('NoticeBoard.java', BOARD62)]) == """dara: job at Campus Bookstore
  pins: 0
eli: selling a bike for 40 dollars
  pins: 0"""

# ------------------------------------------------ the shelter
PART1 = 'shelter/part1'
PART2 = 'shelter/part2'
assert read(PART1 + '/Animal.java').strip() == read(PART2 + '/Animal.java').strip()
for n, path in [('7.1', PART1 + '/Animal.java'), ('7.2', PART1 + '/Dog.java'), ('7.3', PART2 + '/Cat.java'), ('7.4', PART2 + '/Rabbit.java')]:
    assert answer_code(n).strip() == read(path).strip(), n
assert run(read(PART1 + '/ShelterDemo.java'), files_at(PART1, 'Animal', 'Dog', 'Cat')) == """Rex, age 3, Beagle, adopted: false
Mia, age 2, indoor: true, adopted: true
Biscuit, age 5, Collie, adopted: false"""
assert run(read(PART2 + '/ShelterDemo.java'), files_at(PART2, 'Animal', 'Dog', 'Cat', 'Rabbit')) == """Rex the Beagle
Mia, indoor cat
Biscuit the Collie
Clover, brown rabbit"""
ANIMAL = files_at(PART2, 'Animal')
checked('q7-1', 'Animal.java', 'public class Animal\n{\n    // Fields: name, age and adopted.\n}\n', read(PART1 + '/Animal.java'),
        [driver('AnimalCheck', """Animal a = new Animal("Rex", 3);
System.out.println(a.getName() + ", age " + a.getAge() + ", adopted: " + a.isAdopted());
a.adopt();
System.out.println("adopted: " + a.isAdopted());""")],
        'Rex, age 3, adopted: false\nadopted: true', xp=4)
checked('q7-2', 'Dog.java', 'public class Dog extends Animal\n{\n    // The breed, the constructor and getBreed().\n}\n', read(PART1 + '/Dog.java'),
        ANIMAL + [driver('DogCheck', """Dog d = new Dog("Rex", 3, "Beagle");
System.out.println(d.getName() + ", age " + d.getAge() + ", " + d.getBreed());
d.adopt();
System.out.println("adopted: " + d.isAdopted());""")],
        'Rex, age 3, Beagle\nadopted: true', [has('super(name,age)', 'Call super(name, age) first.')])
checked('q7-3', 'Cat.java', 'public class Cat extends Animal\n{\n    // indoor, the constructor, isIndoor() and getLabel().\n}\n', read(PART2 + '/Cat.java'),
        ANIMAL + [driver('CatCheck', """Cat mia = new Cat("Mia", 2, true);
Cat tom = new Cat("Tom", 4, false);
System.out.println(mia.getLabel());
System.out.println(tom.getLabel());
System.out.println(tom.isIndoor() + " " + tom.getAge());""")],
        'Mia, indoor cat\nTom, outdoor cat\nfalse 4', [has('super(name,age)', 'Call super(name, age) first.')], xp=6)
checked('q7-4', 'Rabbit.java', 'public class Rabbit extends Animal\n{\n    // colour, the constructor, getColour() and getLabel().\n}\n', read(PART2 + '/Rabbit.java'),
        ANIMAL + [driver('RabbitCheck', """Rabbit r = new Rabbit("Clover", 1, "brown");
System.out.println(r.getLabel());
System.out.println(r.getColour() + " " + r.getAge() + " " + r.isAdopted());""")],
        'Clover, brown rabbit\nbrown 1 false', [has('super(name,age)', 'Call super(name, age) first.')], xp=6)

# ------------------------------------------------ 8.1: PhotoNotice
PHOTO = read('workbook/review/PhotoNotice.java')
assert question_code('8.1').strip() == PHOTO.strip()
REVIEW = files_at('workbook/review', 'Notice')
errors = compile_errors(PHOTO, REVIEW)
assert 'Constructor call must be the first statement in a constructor' in errors and 'Notice.author is not visible' in errors, errors
PHOTO_FIXED = replaced(replaced(PHOTO, '        this.caption = caption;\n        super(author);\n',
                                '        super(author);\n        this.caption = caption;\n'),
                       'println(author +', 'println(getAuthor() +')
assert compile_errors(PHOTO_FIXED, REVIEW) == ''
checked('q8-1-fix', 'PhotoNotice.java', PHOTO, PHOTO_FIXED,
        REVIEW + [driver('PhotoCheck', 'PhotoNotice p = new PhotoNotice("bo", "the hackathon team");\np.printSummary();')],
        'bo: photo, the hackathon team', [has('getAuthor()', 'Use getAuthor(): author is private in Notice.')])

# ------------------------------------------------ Complete Java Programs
def skeletons(first):
    return next(x for x in listings(STUDENT) if x.startswith(first)).rstrip()


A, B = 'workbook/programA', 'workbook/programB'
for name in ('Vehicle', 'Truck', 'FleetDemo'):
    assert any(x.strip() == read(f'{A}/{name}.java').strip() for x in listings(SOURCE)), name
for name in ('Ticket', 'StudentTicket', 'TicketDemo'):
    assert any(x.strip() == read(f'{B}/{name}.java').strip() for x in listings(SOURCE)), name
VEHICLE_START = skeletons('public class Vehicle')
TRUCK_START, FLEET_START = skeletons('public class Truck').split('\n\npublic class FleetDemo')
FLEET_START = 'public class FleetDemo' + FLEET_START
TICKET_START, TDEMO_START = skeletons('public class Ticket').split('\n\npublic class TicketDemo')
TDEMO_START = 'public class TicketDemo' + TDEMO_START
STUDENT_START = skeletons('public class StudentTicket')

checked('p1-item', 'Vehicle.java', VEHICLE_START, read(A + '/Vehicle.java'),
        [driver('VehicleCheck', 'Vehicle v = new Vehicle("CAR-7");\nSystem.out.println(v.getPlate() + " " + v.getKm());\nv.drive(30);\nv.drive(20);\nSystem.out.println(v.getPlate() + " " + v.getKm());')],
        'CAR-7 0\nCAR-7 50')
checked('p1-sub', 'Truck.java', TRUCK_START, read(A + '/Truck.java'),
        files_at(A, 'Vehicle') + [driver('TruckCheck', 'Truck t = new Truck("TRK-9", 500);\nt.drive(40);\nt.printDetails();\nt.drive(60);\nt.printDetails();\nSystem.out.println(t.getMaxLoad());')],
        'TRK-9: 40 km, max load 500 kg\nTRK-9: 100 km, max load 500 kg\n500',
        [has('extendsVehicle', 'Truck extends Vehicle.'), has('super(plate)', 'Call super(plate) first.')], xp=6)
checked('p1-demo', 'FleetDemo.java', FLEET_START, read(A + '/FleetDemo.java'), files_at(A, 'Vehicle', 'Truck'),
        'CAR-7: 30 km\nTRK-42: 150 km, max load 900 kg\nLoad limit: 900',
        [has('newTruck("TRK-42",900)', 'Make the truck TRK-42 with a maximum load of 900.')])
checked('p2-item', 'Ticket.java', TICKET_START, read(B + '/Ticket.java'),
        [driver('TicketCheck', 'Ticket t = new Ticket("A3", 20);\nSystem.out.println(t.getSeat() + " " + t.getPrice());')],
        'A3 20')
checked('p2-sub', 'StudentTicket.java', STUDENT_START, read(B + '/StudentTicket.java'),
        files_at(B, 'Ticket') + [driver('StudentCheck', 'StudentTicket s = new StudentTicket("B12", 15, "2001234");\ns.printTicket();\nStudentTicket c = new StudentTicket("C1", 22, "2009876");\nc.printTicket();\nSystem.out.println(c.getStudentId() + " " + c.getDiscount());')],
        'Seat B12: 15 dollars, student 2001234\n  discount: 3 dollars\nSeat C1: 22 dollars, student 2009876\n  discount: 4 dollars\n2009876 4',
        [has('extendsTicket', 'StudentTicket extends Ticket.'), has('super(seat,price)', 'Call super(seat, price) first.'),
         has('getPrice()/5', 'The discount is getPrice() / 5.')], xp=6)
checked('p2-demo', 'TicketDemo.java', TDEMO_START, read(B + '/TicketDemo.java'), files_at(B, 'Ticket', 'StudentTicket'),
        'Seat A3: 20 dollars\nSeat B12: 15 dollars, student 2001234\n  discount: 3 dollars\nPay: 12 dollars',
        [has('newStudentTicket("B12",15,"2001234")', 'Make the student ticket for seat B12.')])

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
    head = f'Answer: {"ABCD"[right[0]]}. '
    assert text.startswith(head), (n, text[:40])
    E[ID[n]] = {'type': 'choice', 'xp': 1, 'options': len(opts), 'answer': right[0], 'explain': b64(text[len(head):])}

def option_codes(n):
    return [re.findall(r'\\texttt\{(.*?)\}', o) for o in re.split(r'\\item\b', CHOICES.search(QUESTION_RAW[n])[1])[1:]]

# 2.5: each object has its own pins.
assert run(demo('Pins', question_code('2.5')), SUPER) == '2 0'
# 3.5: only the two-argument TextNotice constructor exists.
for expr in ('new TextNotice("ada", "Study group at 4pm.")', 'new TextNotice("ada")', 'new TextNotice()', 'new Notice()'):
    assert any(expr in codes for codes in option_codes('3.5')), expr
    fails = bool(compile_errors(demo('Make', f'Object o = {expr};'), SUPER))
    assert fails == (expr != 'new TextNotice("ada", "Study group at 4pm.")'), expr
# 3.6: leaving out super(...) does not compile.
NO_SUPER = replaced(read('notices/superclass/TextNotice.java'), '        super(author);\n', '')
assert 'super' not in question_code('3.6') and 'this.message = message;' in question_code('3.6')
assert 'Implicit super constructor Notice() is undefined' in compile_errors(demo('Make', 'new TextNotice("ada", "Hi");'), [file('Notice.java', read('notices/superclass/Notice.java')), file('TextNotice.java', NO_SUPER)])
# 4.4, 4.7: no code outside Notice can name author.
for name in ('author', 'this.author', 'super.author'):
    bad = replaced(read('notices/superclass/TextNotice.java'), 'System.out.println(getAuthor() + ": "', f'System.out.println({name} + ": "')
    assert 'not visible' in compile_errors(demo('Make', 'new TextNotice("ada", "Hi").printSummary();'), [file('Notice.java', read('notices/superclass/Notice.java')), file('TextNotice.java', bad)]), name
# 4.6: a second author field compiles, and getAuthor() still returns the Notice field.
HIDE = replaced(replaced(read('notices/superclass/TextNotice.java'), '    private String message;', '    private String author;\n    private String message;'),
                '        super(author);\n', '        super(author);\n        this.author = author;\n')
assert run(demo('Hide', 'TextNotice t = new TextNotice("ada", "Hi");\nt.printSummary();\nSystem.out.println(t.getAuthor());'),
           [file('Notice.java', read('notices/superclass/Notice.java')), file('TextNotice.java', HIDE)]) == 'ada: Hi\n  pins: 0\nada'
# 5.5: a Workshop has every method of EventNotice and Notice.
assert run(demo('All', 'Workshop w = new Workshop("gil", "Git basics", 5, "EN-2036");\nw.pin();\nSystem.out.println(w.getAuthor() + " " + w.getPins() + " " + w.getRoom());\nw.printSummary();'),
           files_at('workbook/workshop', 'Notice', 'EventNotice', 'Workshop')) == 'gil 1 EN-2036\ngil: Git basics, day 5\n  pins: 1'
# 6.5: the second line shows the one pin.
assert run(demo('Job', question_code('6.5')), files_at('notices/job', 'Notice', 'JobNotice')).split('\n')[1] == '  pins: 1'
assert read('workbook/mcq/McqDemo.output.txt').rstrip('\n') == '2 0\ndara: job at Campus Bookstore\n  pins: 1'

data = {'id': 'lecture-16', 'course': 'COMP 2001: Object-Oriented Programming',
        'title': 'Lecture 16 Workbook', 'subtitle': 'Chapter 12, Part 1: Inheritance', 'exercises': E}
out = pathlib.Path(__file__).with_name('exercises.json')
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
print(f'wrote {out} with {len(E)} specs')
