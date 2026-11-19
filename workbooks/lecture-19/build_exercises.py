"""Build Lecture 19 exercises from the workbook and real Java runs.

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
CODE_DIR = LECTURES / "L19_Chapter_14A_Abstract_Classes_v4" / "code"
L18_CODE = LECTURES / "L18_Chapter_13_Dynamic_Method_Lookup_v4" / "code"


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
YES = {"accept": ["yes", "Yes", "yes.", "Yes."], "show": "yes", "placeholder": "yes / no", "width": "8rem"}
NO = {"accept": ["no", "No", "no.", "No."], "show": "no", "placeholder": "yes / no", "width": "8rem"}
E = {}

# ------------------------------------------------ workbook
sys.path.insert(0, str(ROOT.parent / 'scripts' / 'web_l19'))
from hl import unsplit  # noqa: E402
from workbook import question_code, answer_code, QUESTION_RAW, QUESTION_SOURCE, SOURCE, STUDENT, listings, inline, group  # noqa: E402

ID = {n: 'q' + n.replace('.', '-') for n in QUESTION_SOURCE}
assert len(ID) == 40, len(ID)


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


TABULAR = re.compile(r'\\begin\{tabular\}\{(?:[^{}]|\{[^}]*\})+\}(.*?)\\end\{tabular\}', re.S)


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



# The page compiles with a different compiler from javac, so its messages
# differ from the ones the workbook quotes (those come from javac runs in the
# code folder). Here only "compiles or not" is checked.
MAIN = '\n    public static void main(String[] args)\n    {\n    }\n}'


def part(member):
    """An abstract class Part holding `member`, with a main so that it runs."""
    lines = '\n'.join('    ' + x if x else x for x in member.split('\n'))
    return 'public abstract class Part\n{\n' + lines + MAIN


SHAPES = ('Shape', 'Rectangle', 'Square', 'Triangle')
FULL = files_at('shapes/full', *SHAPES)
SHAPE = read('shapes/full/Shape.java')
SQUARE = read('shapes/full/Square.java')


def add_member(src, member, note=None):
    """src with `member` (unindented) added before the closing brace."""
    lines = '\n'.join('    ' + x if x else x for x in member.split('\n'))
    return replaced(src, '\n}', '\n\n' + lines + '\n}')


def swap(files, name, content):
    return [file(name + '.java', content) if f['name'] == name + '.java' else f for f in files]


# The workbook prints these classes as they are in the code folder.
for path in ('shapes/full/Shape.java', 'shapes/first/Rectangle.java', 'workbook/unfinished/Triangle.java'):
    assert any(x.strip() == read(path).strip() for x in listings(SOURCE)), path
assert run(read('shapes/full/ShapeDemo.java'), FULL) == read('shapes/full/ShapeDemo.output.txt').rstrip('\n') == 'table has area 12.0\ntile has area 25.0\nsail has area 9.0\nTotal: 46.0'
assert run(read('shapes/first/ShapeDemo.java'), files_at('shapes/first', 'Shape', 'Rectangle', 'Square')) == '12.0\n25.0'
assert run(read('shapes/chain/ChainDemo.java'), files_at('shapes/chain', *SHAPES)) == '12.0\n25.0\n0.0'
assert compile_errors(read('workbook/unfinished/Triangle.java'), files_at('workbook/unfinished', 'Shape'))

# ------------------------------------------------ 1. Abstract methods
PERIM = answer_code('1.1')
assert PERIM == 'public abstract double perimeter();'
SQUARE_P = add_member(SQUARE, 'public double perimeter()\n{\n    return 4 * side;\n}')
checked('q1-1', 'Shape.java', add_member(SHAPE, '// Add the abstract method perimeter() here.'), add_member(SHAPE, PERIM),
        [file('Square.java', SQUARE_P), driver('PerimeterCheck', 'Shape s = new Square("tile", 5);\nSystem.out.println(s.perimeter());')],
        '20.0', [has('abstract double perimeter();', 'Write abstract, the return type double, the name and a semicolon instead of a body.')])
for line, (want,) in zip(code_lines('1.2'), answers_of('1.2')):
    ok = not compile_errors(part(tex_unescape(line)))
    assert ok == (want == 'yes'), line
auto_spec('q1-2', '1.2', YN)
E[ID['1.6']] = SHORT(solution('1.6'))

# ------------------------------------------------ 2. Abstract classes
for member, (want,) in zip(['private String name;', 'public Part(String name)\n{\n}', 'public int size()\n{\n    return 0;\n}', 'public abstract int sides();'], answers_of('2.2')):
    assert not compile_errors(part(member)) and want == 'yes', member
assert answers_of('2.2')[4] == ['no']
auto_spec('q2-2', '2.2', YN)
E[ID['2.6']] = SHORT(solution('2.6'))
AN = 'workbook/animals'
assert run(read(AN + '/AnimalDemo.java'), files_at(AN, 'Animal', 'Dog')) == read(AN + '/AnimalDemo.output.txt').rstrip('\n') == 'Rex says Woof'
assert question_code('3.6') in read(AN + '/AnimalDemo.java').replace('        ', '')
same(answer_code('2.7'), AN + '/Animal.java')
checked('q2-7', 'Animal.java', 'public abstract class Animal\n{\n    // Add the field, the constructor, getName() and makeSound().\n}\n', read(AN + '/Animal.java'),
        files_at(AN, 'Dog') + [driver('AnimalCheck', 'Animal a = new Dog("Rex");\nSystem.out.println(a.getName() + " says " + a.makeSound());')],
        'Rex says Woof', [has('public abstract String makeSound();', 'makeSound() is abstract: a header ending with a semicolon.')])

# ------------------------------------------------ 3. Subclasses
CIRCLE = read('workbook/circle/Circle.java')
same(answer_code('3.1'), 'workbook/circle/Circle.java')
checked('q3-1', 'Circle.java', 'public class Circle extends Shape\n{\n    // Add the field, the constructor and area().\n}\n', CIRCLE,
        files_at('workbook/circle', *SHAPES) + [driver('CircleCheck', 'Shape plate = new Circle("plate", 10);\nSystem.out.println(plate.describe());')],
        'plate has area 314.0', [has('super(name)', "Pass the name to Shape's constructor with super(name).")])
assert run(read('workbook/circle/CircleDemo.java'), files_at('workbook/circle', *SHAPES, 'Circle')) == read('workbook/circle/CircleDemo.output.txt').rstrip('\n')
E[ID['3.5']] = SHORT(solution('3.5'))
same(answer_code('3.6'), AN + '/Dog.java')
checked('q3-6', 'Dog.java', 'public class Dog extends Animal\n{\n    // Add the constructor and makeSound().\n}\n', read(AN + '/Dog.java'),
        files_at(AN, 'Animal') + [driver('DogCheck', question_code('3.6'))], 'Rex says Woof',
        [has('super(name)', "Pass the name to Animal's constructor with super(name).")])

# ------------------------------------------------ 4. Abstract types
TYPES = files_at('workbook/types', *SHAPES)
PREFIX = question_code('4.1') + '\n'
for line, (want,) in zip(code_lines('4.1'), answers_of('4.1')):
    ok = not compile_errors(demo('Lines', PREFIX + tex_unescape(line), 'import java.util.ArrayList;\n\n'), TYPES)
    assert ok == (want == 'yes'), line
auto_spec('q4-1', '4.1', YN)
LARGEST = read('workbook/largest/LargestDemo.java')
assert inside(answer_code('4.5'), LARGEST)
LARGEST_START = LARGEST.replace(answer_code('4.5').split('\n', 1)[1].replace('\n', '\n    '), '{\n        // Return the shape with the largest area.\n        return null;\n    }')
assert LARGEST_START != LARGEST
checked('q4-5', 'LargestDemo.java', LARGEST_START, LARGEST, files_at('workbook/largest', *SHAPES),
        read('workbook/largest/LargestDemo.output.txt').rstrip('\n'), [lacks('instanceof', 'Call area() on each shape; no instanceof is needed.')])
assert E['q4-5']['cases'][0]['expected'] == 'tile'
TOTALDEMO = read('workbook/circle/TotalDemo.java')
assert question_code('4.7') in TOTALDEMO.replace('\n        ', '\n')
got = run(TOTALDEMO, files_at('workbook/circle', *SHAPES, 'Circle'))
assert got == solution_output('4.7') == read('workbook/circle/TotalDemo.output.txt').rstrip('\n') == 'tile has area 25.0\nplate has area 314.0\nTotal: 339.0', got
lines_table('q4-7', got)

# ------------------------------------------------ 5. Shared code
SIZE = files_at('workbook/size', *SHAPES)
assert inside(question_code('5.1'), SIZE[0]['content'])
got = run(read('workbook/size/SizeDemo.java'), SIZE)
assert got == solution_output('5.1') == read('workbook/size/SizeDemo.output.txt').rstrip('\n') == 'table is large\ntile is large\nsail is small', got
lines_table('q5-1', got)
BIGGER = read('workbook/bigger/Shape.java')
assert BIGGER == add_member(SHAPE, answer_code('5.2')), 'bigger/Shape.java'
checked('q5-2', 'Shape.java', add_member(SHAPE, '// Add isBiggerThan here.'), BIGGER,
        files_at('workbook/bigger', 'Rectangle', 'Square', 'Triangle', 'BiggerDemo'),
        read('workbook/bigger/BiggerDemo.output.txt').rstrip('\n'), [has('other.area()', 'Compare area() with other.area().')])
assert E['q5-2']['cases'][0]['expected'] == 'true\nfalse'
E[ID['5.6']] = SHORT(solution('5.6'))
E[ID['5.7']] = SHORT(solution('5.7'))

# ------------------------------------------------ 6. Choosing
CHOICE_FORMS = {
 'abstract with an abstract method': ['abstract with an abstract method', 'abstract, with an abstract method', 'abstract with abstract method', 'abstract with an abstract method.'],
 'concrete': ['concrete', 'concrete.'],
 'abstract, no abstract methods': ['abstract, no abstract methods', 'abstract no abstract methods', 'abstract with no abstract methods', 'abstract, with no abstract methods', 'abstract, no abstract methods.'],
}
auto_spec('q6-1', '6.1', lambda v: word(*CHOICE_FORMS[v], width='16rem', placeholder='choice'))
E[ID['6.4']] = SHORT(solution('6.4'), chars=40, rows=3)

# ------------------------------------------------ 7. Review
auto_spec('q7-1', '7.1', TF)
BROKEN = '\n'.join(x.rstrip() for x in listings(QUESTION_SOURCE['7.3'])).rstrip()
assert BROKEN.strip() == read('workbook/review/broken/Instrument.java').strip()
FIXED = read('workbook/review/fixed/Instrument.java')
GUITAR = files_at('workbook/review/fixed', 'Guitar')
CHECK73 = driver('Band', 'Instrument i = new Guitar();\nSystem.out.println(i.getName() + ": " + i.sound());')
errors = compile_errors(BROKEN, GUITAR + [CHECK73])
assert 'must be an abstract class' in errors and 'do not specify a body' in errors, errors
assert run(read('workbook/review/fixed/BandDemo.java'), GUITAR + [file('Instrument.java', FIXED)]) == read('workbook/review/fixed/BandDemo.output.txt').rstrip('\n')
assert 'public abstract class Instrument' in solution('7.3') and 'public abstract String sound();' in solution('7.3')
E['q7-3'] = SHORT(solution('7.3'))
checked('q7-3-fix', 'Instrument.java', BROKEN, FIXED, GUITAR + [CHECK73], 'guitar: strum',
        [has('public abstract class Instrument', 'A class with an abstract method must be abstract.'),
         has('public abstract String sound();', 'An abstract method ends with a semicolon, with no body.')])

# ------------------------------------------------ Complete Java Programs
def skeleton(first):
    return next(x for x in listings(STUDENT) if x.startswith(first)).rstrip()


A, B = 'workbook/programA', 'workbook/programB'
for name in ('Vehicle', 'Car', 'Truck', 'Fleet', 'FleetDemo'):
    assert any(x.strip() == read(f'{A}/{name}.java').strip() for x in listings(SOURCE)), name
for name in ('Ticket', 'AdultTicket', 'StudentTicket', 'Show', 'ShowDemo'):
    assert any(x.strip() == read(f'{B}/{name}.java').strip() for x in listings(SOURCE)), name
assert run(read(A + '/FleetDemo.java'), files_at(A, 'Vehicle', 'Car', 'Truck', 'Fleet')) == read(A + '/FleetDemo.output.txt').rstrip('\n')
assert run(read(B + '/ShowDemo.java'), files_at(B, 'Ticket', 'AdultTicket', 'StudentTicket', 'Show')) == read(B + '/ShowDemo.output.txt').rstrip('\n')

VEHICLE18 = (L18_CODE / A / 'Vehicle.java').read_text()
VEHICLE_START = replaced(without(VEHICLE18, 'public String toString()', 'Add ratePerKm(), cost() and toString() here.'),
                         'public class Vehicle', '// Make this class abstract.\npublic class Vehicle')
checked('p1-vehicle', 'Vehicle.java', VEHICLE_START, read(A + '/Vehicle.java'),
        files_at(A, 'Car') + [driver('VehicleCheck', 'Vehicle v = new Car("CAR-9");\nv.drive(12);\nSystem.out.println(v);\nSystem.out.println(v.cost());')],
        'CAR-9: 12 km, cost 6.0\n6.0',
        [has('public abstract class Vehicle', 'Declare Vehicle abstract.'),
         has('public abstract double ratePerKm();', 'Add the abstract method ratePerKm(), with no body.')], xp=6)
checked('p1-truck', 'Truck.java', without(read(A + '/Truck.java'), 'public double ratePerKm()', 'Add ratePerKm() here.'), read(A + '/Truck.java'),
        files_at(A, 'Vehicle') + [driver('TruckCheck', 'Vehicle t = new Truck("TRK-8", 500);\nt.drive(70);\nSystem.out.println(t);')],
        'TRK-8: 70 km, cost 140.0')
checked('p1-fleet', 'Fleet.java', skeleton('import java.util.ArrayList;\npublic class Fleet'), read(A + '/Fleet.java'),
        files_at(A, 'Vehicle', 'Car', 'Truck', 'FleetDemo'), read(A + '/FleetDemo.output.txt').rstrip('\n'),
        [has('ArrayList<Vehicle>', 'Keep one ArrayList<Vehicle>.'), has('.cost()', 'Add up cost() of each vehicle.')], xp=6)

checked('p2-ticket', 'Ticket.java', skeleton('public abstract class Ticket'), read(B + '/Ticket.java'),
        files_at(B, 'AdultTicket') + [driver('TicketCheck', 'Ticket t = new AdultTicket("A3");\nSystem.out.println(t);\nSystem.out.println(t.getSeat());')],
        'A3: 20 dollars\nA3',
        [has('public abstract int price();', 'Keep the abstract method price(), with no body.'), has('price()', 'Use price() in toString().')], xp=6)
checked('p2-student', 'StudentTicket.java', skeleton('public class StudentTicket'), read(B + '/StudentTicket.java'),
        files_at(B, 'Ticket') + [driver('StudentCheck', 'Ticket t = new StudentTicket("B12", "2001234");\nSystem.out.println(t);')],
        'B12: 15 dollars, student 2001234',
        [has('super.toString()', 'Use super.toString() for the seat and the price.')])
checked('p2-show', 'Show.java', skeleton('import java.util.ArrayList;\npublic class Show'), read(B + '/Show.java'),
        files_at(B, 'Ticket', 'AdultTicket', 'StudentTicket', 'ShowDemo'), read(B + '/ShowDemo.output.txt').rstrip('\n'),
        [has('ArrayList<Ticket>', 'Keep one ArrayList<Ticket>.'), has('.price()', 'Add up price() of each ticket.')], xp=6)

# ------------------------------------------------ multiple choice
CHOICES = re.compile(r'\\begin\{choices\}(.*?)\\end\{choices\}', re.S)
MCQS = [n for n in QUESTION_SOURCE if CHOICES.search(QUESTION_RAW[n])]
assert len(MCQS) == 20, MCQS
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


# 1.4: areaOf has no Triangle test.
assert 'Triangle' not in read('shapes/chain/ChainDemo.java').split('areaOf')[1].split('main')[0] and answer_index('1.4') == 1
# 1.5: the made-up 0 is inherited.
assert run(read('shapes/fake/FakeDemo.java'), files_at('shapes/fake', 'Shape', 'Rectangle', 'Square', 'Triangle')) == '0.0' and answer_index('1.5') == 2
# 2.1: an abstract method in a class that is not abstract.
assert compile_errors(read('shapes/err/notabstract/Shape.java'))
assert answer_index('2.1') == 1
# 2.4: abstract with no abstract methods compiles; new Vehicle() does not.
NOABS = 'public abstract class Vehicle\n{\n    public int wheels()\n    {\n        return 4;\n    }\n}'
CAR = 'public class Car extends Vehicle\n{\n}'
assert run(demo('Abs', 'Vehicle v = new Car();\nSystem.out.println(v.wheels());'), [file('Vehicle.java', NOABS), file('Car.java', CAR)]) == '4'
assert compile_errors(demo('Abs', 'Vehicle v = new Vehicle();'), [file('Vehicle.java', NOABS)])
assert answer_index('2.4') == 1 and answer_index('6.3') == 2
# 2.5: abstract and final.
assert compile_errors(read('shapes/err/final/Shape.java')) and answer_index('2.5') == 2
# 3.2 D and 3.3: super.area() and new on an abstract Triangle.
ABS_TRI = replaced(read('workbook/unfinished/Triangle.java'), 'public class Triangle', 'public abstract class Triangle')
assert not compile_errors(ABS_TRI, files_at('workbook/unfinished', 'Shape'))
assert compile_errors(demo('Tri', 'Shape s = new Triangle("sail", 6, 3);'), [file('Triangle.java', ABS_TRI)] + files_at('workbook/unfinished', 'Shape'))
assert not compile_errors(demo('Tri', 'Shape s;\nTriangle t;\njava.util.ArrayList<Triangle> list = new java.util.ArrayList<>();'), [file('Triangle.java', ABS_TRI)] + files_at('workbook/unfinished', 'Shape'))
SUPER_TRI = replaced(ABS_TRI, 'this.height = height;', 'this.height = height;\n        super.area();')
assert compile_errors(SUPER_TRI, files_at('workbook/unfinished', 'Shape'))
assert answer_index('3.2') == 2 and answer_index('3.3') == 2
# 4.2: Square's area runs.
assert run(demo('Tile', 'Shape s = new Square("tile", 5);\nSystem.out.println(s.area());'), FULL) == '25.0' and answer_index('4.2') == 1
# 4.6: totalArea is unchanged with a Circle in the list.
TOTAL = read('shapes/full/ShapeDemo.java')
assert 'Circle' not in TOTAL
WITH_CIRCLE = replaced(TOTAL, 'shapes.add(new Triangle("sail", 6, 3));', 'shapes.add(new Triangle("sail", 6, 3));\n        shapes.add(new Circle("plate", 10));')
assert run(WITH_CIRCLE, FULL + [file('Circle.java', CIRCLE)]).endswith('plate has area 314.0\nTotal: 360.0') and answer_index('4.6') == 3
# 7.2: only new Shape fails.
assert compile_errors(demo('Box', 'Shape s = new Shape("box");'), FULL) and answer_index('7.2') == 2

# The web page has room for each println on one line; the PDF splits some.
from hl import unsplit  # noqa: E402
for spec in E.values():
    if spec.get('type') != 'code':
        continue
    spec['starter'] = unsplit(spec['starter'])
    spec['answer'] = b64(unsplit(base64.b64decode(spec['answer']).decode()))
    for f in spec['files']:
        f['content'] = unsplit(f['content'])

data = {'id': 'lecture-19', 'course': 'COMP 2001: Object-Oriented Programming',
        'title': 'Lecture 19 Workbook', 'subtitle': 'Chapter 14, Part 1: Abstract classes', 'exercises': E}
out = pathlib.Path(__file__).with_name('exercises.json')
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
print(f'wrote {out} with {len(E)} specs')
