"""Build Lecture 20 exercises from the workbook and real Java runs.

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
CODE_DIR = LECTURES / "L20_Chapter_14B_Interfaces_v4" / "code"
L19_CODE = LECTURES / "L19_Chapter_14A_Abstract_Classes_v4" / "code"


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
sys.path.insert(0, str(ROOT.parent / 'scripts' / 'web_l20'))
from hl import unsplit  # noqa: E402
from workbook import question_code, answer_code, QUESTION_RAW, QUESTION_SOURCE, SOURCE, STUDENT, listings, inline, group  # noqa: E402

ID = {n: 'q' + n.replace('.', '-') for n in QUESTION_SOURCE}
ID['7.4'] = 'q7-5'  # 7.4 was 7.5 before the java.util.function cut; the id keeps its published meaning
assert len(ID) == 41, len(ID)


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


def swap(files, name, content):
    return [file(name + '.java', content) if f['name'] == name + '.java' else f for f in files]


def stub(src, header, comment, ret=None):
    """src with the body of the method `header` replaced by a comment."""
    lines = src.rstrip('\n').split('\n')
    i = lines.index('    ' + header)
    assert lines[i + 1] == '    {', header
    j = lines.index('    }', i)
    body = ['    {', '        // ' + comment] + (['        return ' + ret + ';'] if ret else []) + ['    }']
    return '\n'.join(lines[:i + 1] + body + lines[j + 1:]) + '\n'


def output(path):
    return read(path).rstrip('\n')


def shows(text):
    """The workbook prints this output listing."""
    assert any(x.rstrip('\n') == text for x in listings(SOURCE)), text


SHAPE_FILES = ('Drawable', 'Shape', 'Square', 'Label')
MULTI = files_at('multi', 'Drawable', 'Resizable', 'Shape', 'Square', 'Label')

# ------------------------------------------------ the notes
# Classes the notes print in full are the ones in the code folder.
for path in ('iface/Drawable.java', 'iface/Label.java', 'multi/Resizable.java', 'default/Drawable.java', 'lambda/Drawable.java'):
    assert any(x.strip() == read(path).strip() for x in listings(SOURCE)), path
assert any(unsplit(x).strip() == read('iface/Square.java').strip() for x in listings(SOURCE))
for folder, demo_name, classes in [
        ('iface', 'DrawDemo', SHAPE_FILES), ('passon', 'PassDemo', ('Drawable', 'Shape', 'Square')),
        ('multi', 'GrowDemo', ('Drawable', 'Resizable', 'Shape', 'Square', 'Label')),
        ('default', 'FrameDemo', SHAPE_FILES), ('conflict', 'InfoDemo', ('Drawable', 'Resizable', 'Shape', 'Square')),
        ('listspec', 'ListDemo', ()), ('lambda', 'LambdaDemo', SHAPE_FILES),]:
    got = run(read(f'{folder}/{demo_name}.java'), files_at(folder, *classes))
    assert got == output(f'{folder}/{demo_name}.output.txt'), (folder, got)
    shows(got)
assert run(read('listspec/ListDemo2.java')) == output('listspec/ListDemo.output.txt')
for folder in ('twoparents', 'ctor', 'field', 'unfinished', 'weaker', 'addabstract', 'conflict'):
    names = [p.stem for p in (CODE_DIR / 'err' / folder).glob('*.java')]
    main = names[-1]
    assert compile_errors(read(f'err/{folder}/{main}.java'), [file(n + '.java', read(f'err/{folder}/{n}.java')) for n in names if n != main]), folder
assert compile_errors(read('err/newiface/Test.java'), files_at('err/newiface', 'Drawable'))

# ------------------------------------------------ 1. One superclass
E[ID['1.4']] = SHORT(solution('1.4'))

# ------------------------------------------------ 2. Interfaces
PL = 'workbook/playable'
assert run(read(PL + '/SongDemo.java'), files_at(PL, 'Playable', 'Song')) == output(PL + '/SongDemo.output.txt') == 'Playing Rain\n185 seconds'
SONG_CHECK = driver('SongCheck', 'Playable p = new Song("Rain", 185);\np.play();\nSystem.out.println(p.length() + " seconds");')
same(answer_code('2.1'), PL + '/Playable.java')
checked('q2-1', 'Playable.java', 'public interface Playable\n{\n    // Add play() and length().\n}\n', read(PL + '/Playable.java'),
        files_at(PL, 'Song') + [SONG_CHECK], 'Playing Rain\n185 seconds',
        [has('void play();', 'play() is a header ending with a semicolon.'), has('int length();', 'length() returns an int and has no body.')])
LINES = demo('Lines', 'System.out.println("ok");')
for line, (want,) in zip(code_lines('2.2'), answers_of('2.2')):
    member = tex_unescape(line)
    ok = not compile_errors(LINES, [file('Drawable.java', 'public interface Drawable\n{\n    ' + member + '\n}')])
    assert ok == (want == 'yes'), line
auto_spec('q2-2', '2.2', YN)

# ------------------------------------------------ 3. Implements
same(answer_code('3.1'), PL + '/Song.java')
checked('q3-1', 'Song.java', 'public class Song implements Playable\n{\n    // Add the fields, the constructor, play() and length().\n}\n', read(PL + '/Song.java'),
        files_at(PL, 'Playable') + [SONG_CHECK], 'Playing Rain\n185 seconds',
        [has('implements Playable', 'Song implements Playable.'), has('public void play()', 'play() must be public.')])
CI = 'workbook/circle'
assert run(read(CI + '/CircleDemo.java'), files_at(CI, 'Drawable', 'Shape', 'Circle')) == output(CI + '/CircleDemo.output.txt') == 'Circle plate, area 314.0'
assert unsplit(answer_code('3.6')).strip() == read(CI + '/Circle.java').strip()
checked('q3-6', 'Circle.java', 'public class Circle extends Shape implements Drawable\n{\n    // Add the field, the constructor, area() and draw().\n}\n', read(CI + '/Circle.java'),
        files_at(CI, 'Drawable', 'Shape') + [driver('CircleCheck', read(CI + '/CircleDemo.java').split('{\n', 2)[2].rsplit('    }', 1)[0].replace('        ', ''))],
        'Circle plate, area 314.0', [has('super(name)', "Pass the name to Shape's constructor with super(name)."), has('public void draw()', 'draw() must be public.')])

# ------------------------------------------------ 4. Interface types
for line, (want,) in zip(code_lines('4.1'), answers_of('4.1')):
    ok = not compile_errors(demo('Lines', tex_unescape(line)), MULTI)
    assert ok == (want == 'yes'), line
auto_spec('q4-1', '4.1', YN)
PREFIX = question_code('4.2') + '\n'
for line, (want,) in zip(code_lines('4.2'), answers_of('4.2')):
    ok = not compile_errors(demo('Lines', PREFIX + tex_unescape(line)), MULTI)
    assert ok == (want == 'yes'), line
auto_spec('q4-2', '4.2', YN)
TR = 'workbook/trace'
TRACE = read(TR + '/TraceDemo.java')
assert question_code('4.6') in TRACE.replace('\n        ', '\n')
got = run(TRACE, files_at(TR, 'Drawable', 'Resizable', 'Shape', 'Square', 'Label'))
assert got == solution_output('4.6') == output(TR + '/TraceDemo.output.txt') == 'Square rug, area 36.0\nLabel: Open', got
lines_table('q4-6', got)
DA = 'workbook/drawall'
DRAWALL = read(DA + '/DrawAllDemo.java')
assert inside(answer_code('4.7'), DRAWALL)
checked('q4-7', 'DrawAllDemo.java', stub(DRAWALL, 'public static void drawAll(ArrayList<Drawable> items)', 'Draw each item, then print the count.'), DRAWALL,
        files_at(DA, *SHAPE_FILES), output(DA + '/DrawAllDemo.output.txt'),
        [has('.draw()', 'Call draw() on each item.'), has('items.size()', 'Use items.size() for the count.')])
assert E['q4-7']['cases'][0]['expected'] == 'Label: Exit\nSquare tile, area 25.0\n2 items drawn'

# ------------------------------------------------ 5. Default methods
FR = 'workbook/framed'
FRAMED = read(FR + '/FramedDemo.java')
assert question_code('5.2') in FRAMED.replace('\n        ', '\n')
got = run(FRAMED, files_at(FR, *SHAPE_FILES))
assert got == solution_output('5.2') == output(FR + '/FramedDemo.output.txt'), got
lines_table('q5-2', got)
TW = 'workbook/twice'
same(answer_code('5.4'), TW + '/Drawable.java')
checked('q5-4', 'Drawable.java', 'public interface Drawable\n{\n    void draw();\n\n    // Add the default method drawTwice() here.\n}\n', read(TW + '/Drawable.java'),
        files_at(TW, 'Label', 'TwiceDemo'), output(TW + '/TwiceDemo.output.txt'),
        [has('default void drawTwice()', 'Write default, then the header void drawTwice(), then a body.')])
assert E['q5-4']['cases'][0]['expected'] == 'Label: Exit\nLabel: Exit'

# ------------------------------------------------ 6. Library
E[ID['6.3']] = SHORT(solution('6.3'), chars=30, rows=3)
CL = 'workbook/countlong'
COUNT = read(CL + '/CountDemo.java')
assert inside(answer_code('6.4'), COUNT)
checked('q6-4', 'CountDemo.java', stub(COUNT, 'public static int countLong(List<String> names)', 'Count the names with more than 4 characters.', '0'), COUNT,
        [], output(CL + '/CountDemo.output.txt'), [has('.length()', 'Use length() on each name.')])
assert E['q6-4']['cases'][0]['expected'] == '2\n1'

# ------------------------------------------------ 7. Lambdas
FN = 'workbook/functional'
INTERFACES = files_at(FN, 'Interfaces')
assert run(read(FN + '/Lambdas.java'), INTERFACES) == output(FN + '/Lambdas.output.txt') == 'run\ntrue'
assert question_code('7.1').strip() == read(FN + '/Interfaces.java').strip()
LAMBDA = {'A': 'A x = () -> System.out.println("run");', 'B': 'B x = () -> System.out.println("up");',
          'C': 'C x = () -> 0;', 'D': 'D x = () -> System.out.println("hi");'}
for line, (want,) in zip(code_lines('7.1'), answers_of('7.1')):
    ok = not compile_errors(demo('Lines', LAMBDA[line]), INTERFACES)
    assert ok == (want == 'yes'), line
auto_spec('q7-1', '7.1', YN)
ST = 'workbook/star'
STAR = read(ST + '/StarDemo.java')
assert '        ' + answer_code('7.3') in STAR
checked('q7-3', 'StarDemo.java', STAR.replace(answer_code('7.3'), '// Make the Drawable star from a lambda here.'), STAR,
        files_at(ST, 'Drawable'), output(ST + '/StarDemo.output.txt'), [has('->', 'Write a lambda: () -> followed by the statement.')])
assert E['q7-3']['cases'][0]['expected'] == '*****\n*****'

# ------------------------------------------------ 8. Choosing
CHOICE_FORMS = {
 'abstract class': ['abstract class', 'an abstract class', 'abstract'],
 'interface': ['interface', 'an interface'],
 'both': ['both', 'both.'],
}
auto_spec('q8-1', '8.1', lambda v: word(*CHOICE_FORMS[v], width='11rem', placeholder='choice'))
E[ID['8.4']] = SHORT(solution('8.4'), chars=40, rows=3)

# ------------------------------------------------ 9. Review
auto_spec('q9-1', '9.1', TF)
BROKEN = listings(QUESTION_SOURCE['9.3'])[0].rstrip()
assert BROKEN.strip() == read('workbook/review/broken/Phone.java').strip()
FIXED = read('workbook/review/fixed/Phone.java')
CHARGE = files_at('workbook/review/fixed', 'Chargeable')
CHECK93 = driver('PhoneCheck', 'Phone p = new Phone();\nChargeable c = p;\nc.charge();\nSystem.out.println("Battery: " + p.getBattery());')
assert compile_errors(BROKEN, CHARGE + [CHECK93])
assert compile_errors(replaced(BROKEN, 'extends', 'implements'), CHARGE + [CHECK93])
assert compile_errors(replaced(BROKEN, '    void charge()', '    public void charge()'), CHARGE + [CHECK93])
assert run(read('workbook/review/fixed/PhoneDemo.java'), CHARGE + [file('Phone.java', FIXED)]) == output('workbook/review/fixed/PhoneDemo.output.txt') == 'Battery: 100'
E['q9-3'] = SHORT(solution('9.3'))
checked('q9-3-fix', 'Phone.java', BROKEN, FIXED, CHARGE + [CHECK93], 'Battery: 100',
        [has('implements Chargeable', 'A class implements an interface.'),
         has('public void charge()', 'The method of an interface is public, so charge() must be public too.')])

# ------------------------------------------------ Complete Java Programs
def skeleton(first):
    return next(x for x in listings(STUDENT) if x.startswith(first)).rstrip()


A, B = 'workbook/programA', 'workbook/programB'
for name in ('Billable', 'Parking', 'Invoice', 'InvoiceDemo'):
    assert any(x.strip() == read(f'{A}/{name}.java').strip() for x in listings(SOURCE)), name
for name in ('Sellable', 'Ticket', 'Snack', 'Order', 'OrderDemo'):
    # The PDF splits two lines of OrderDemo; compare without whitespace.
    assert any(re.sub(r'\s+', '', x) == re.sub(r'\s+', '', read(f'{B}/{name}.java')) for x in listings(SOURCE)), name
INVOICE_ALL = files_at(A, 'Billable', 'Vehicle', 'Car', 'Truck', 'Parking', 'Invoice')
ORDER_ALL = files_at(B, 'Sellable', 'Ticket', 'AdultTicket', 'StudentTicket', 'Snack', 'Order')
got = run(read(A + '/InvoiceDemo.java'), INVOICE_ALL)
assert got == output(A + '/InvoiceDemo.output.txt'); shows(got)
got = run(read(B + '/OrderDemo.java'), ORDER_ALL)
assert got == output(B + '/OrderDemo.output.txt'); shows(got)
# Vehicle, Car, Truck, AdultTicket and StudentTicket come from Lecture 19.
VEHICLE19 = (L19_CODE / A / 'Vehicle.java').read_text()
assert read(A + '/Vehicle.java') == replaced(replaced(VEHICLE19, 'public abstract class Vehicle', 'public abstract class Vehicle implements Billable'),
                                             '    public double cost()', '    @Override\n    public double cost()')
for name in ('Car', 'Truck'):
    assert read(f'{A}/{name}.java') == (L19_CODE / A / f'{name}.java').read_text(), name
for name in ('AdultTicket', 'StudentTicket'):
    assert read(f'{B}/{name}.java') == (L19_CODE / B / f'{name}.java').read_text(), name

checked('p1-billable', 'Billable.java', skeleton('public interface Billable'), read(A + '/Billable.java'),
        files_at(A, 'Parking') + [driver('BillableCheck', 'Billable b = new Parking("CAR-1", 2);\nSystem.out.println(b.cost());')],
        '6.0', [has('double cost();', 'cost() returns a double and has no body.')])
checked('p1-vehicle', 'Vehicle.java', replaced(VEHICLE19, 'public abstract class Vehicle', '// Make Vehicle implement Billable.\npublic abstract class Vehicle'), read(A + '/Vehicle.java'),
        files_at(A, 'Billable', 'Car') + [driver('VehicleCheck', 'Vehicle v = new Car("CAR-9");\nv.drive(12);\nBillable b = v;\nSystem.out.println(b.cost());')],
        '6.0', [has('implements Billable', 'Add implements Billable to the header.')])
checked('p1-parking', 'Parking.java', skeleton('public class Parking'), read(A + '/Parking.java'),
        files_at(A, 'Billable') + [driver('ParkingCheck', 'Billable p = new Parking("CAR-7", 4);\nSystem.out.println(p);')],
        'Parking CAR-7: 4 hours, cost 12.0', [has('implements Billable', 'Parking implements Billable.')], xp=6)
checked('p1-invoice', 'Invoice.java', skeleton('import java.util.ArrayList;\npublic class Invoice'), read(A + '/Invoice.java'),
        INVOICE_ALL[:-1] + files_at(A, 'InvoiceDemo'), output(A + '/InvoiceDemo.output.txt'),
        [has('ArrayList<Billable>', 'Keep one ArrayList<Billable>.'), has('.cost()', 'Add up cost() of each item.')], xp=6)

checked('p2-sellable', 'Sellable.java', skeleton('public interface Sellable'), read(B + '/Sellable.java'),
        files_at(B, 'Snack') + [driver('SellableCheck', 'Sellable s = new Snack("tea", 3);\nSystem.out.println(s.priceText());')],
        '3 dollars', [has('default String priceText()', 'priceText() is a default method.')])
checked('p2-ticket', 'Ticket.java', skeleton('public abstract class Ticket'), read(B + '/Ticket.java'),
        files_at(B, 'Sellable', 'AdultTicket') + [driver('TicketCheck', 'Ticket t = new AdultTicket("A3");\nSystem.out.println(t);\nSystem.out.println(t.getSeat());')],
        'A3: 20 dollars\nA3', [has('implements Sellable', 'Ticket implements Sellable.'), has('priceText()', 'Use priceText() in toString().')], xp=6)
checked('p2-snack', 'Snack.java', skeleton('public class Snack'), read(B + '/Snack.java'),
        files_at(B, 'Sellable') + [driver('SnackCheck', 'Sellable s = new Snack("popcorn", 6);\nSystem.out.println(s);')],
        'popcorn: 6 dollars', [has('implements Sellable', 'Snack implements Sellable.')], xp=6)
checked('p2-order', 'Order.java', skeleton('import java.util.ArrayList;\nimport java.util.List;\npublic class Order'), read(B + '/Order.java'),
        ORDER_ALL[:-1] + files_at(B, 'OrderDemo'), output(B + '/OrderDemo.output.txt'),
        [has('List<Sellable>', 'Keep one List<Sellable>.'), has('.price()', 'Add up price() of each item.')], xp=6)

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


IFACE = files_at('iface', *SHAPE_FILES)
# 1.1: two names after extends.
assert compile_errors(read('err/twoparents/Label.java'), files_at('err/twoparents', 'Text', 'Shape')) and answer_index('1.1') == 2
# 1.2: Label as a Shape with area() 0 compiles.
FAKE = 'public class Label extends Shape\n{\n    public Label(String text)\n    {\n        super(text);\n    }\n\n    public double area()\n    {\n        return 0;\n    }\n}'
assert run(demo('Fake', 'Shape s = new Label("Exit");\nSystem.out.println(s.area());'), files_at('iface', 'Shape') + [file('Label.java', FAKE)]) == '0.0' and answer_index('1.2') == 1
# 2.3: a constant, static and final.
CONST = [file('Drawable.java', 'public interface Drawable\n{\n    int MAX_ITEMS = 20;\n}')]
assert run(demo('Const', 'System.out.println(Drawable.MAX_ITEMS);'), CONST) == '20'
assert compile_errors(demo('Const', 'Drawable.MAX_ITEMS = 5;'), CONST) and answer_index('2.3') == 0
# 2.4: new Drawable() is a compile error.
assert compile_errors(demo('New', 'Drawable d = new Drawable();'), IFACE) and answer_index('2.4') == 2
# 3.4: only extends ... implements ... compiles.
SQ = read('iface/Square.java')
HEADERS = ['public class Square implements Drawable extends Shape', 'public class Square extends Shape, Drawable',
           'public class Square implements Shape, Drawable', 'public class Square extends Shape implements Drawable']
for i, header in enumerate(HEADERS):
    ok = not compile_errors(LINES, files_at('iface', 'Drawable', 'Shape') + [file('Square.java', SQ.replace('public class Square extends Shape implements Drawable', header))])
    assert ok == (i == answer_index('3.4')), header
# 3.5: Shape implements Drawable without draw() compiles; Square must write it.
assert not compile_errors(LINES, files_at('passon', 'Drawable', 'Shape', 'Square')) and answer_index('3.5') == 3
PASS_SQ = read('passon/Square.java')
NO_DRAW = PASS_SQ[:PASS_SQ.index('\n\n    public void draw()')] + '\n}\n'
assert compile_errors(LINES, files_at('passon', 'Drawable', 'Shape') + [file('Square.java', NO_DRAW)])
# 4.4: Label's draw() runs.
assert run(demo('One', 'Drawable d = new Label("Exit");\nd.draw();'), IFACE) == 'Label: Exit' and answer_index('4.4') == 0
# 4.5: a Label is not Resizable.
assert compile_errors(demo('Add', 'java.util.ArrayList<Resizable> items = new java.util.ArrayList<>();\nitems.add(new Label("Exit"));'), MULTI) and answer_index('4.5') == 3
# 5.5: Drawable.super.info() is the default in Drawable.
assert run(read('conflict/InfoDemo.java'), files_at('conflict', 'Drawable', 'Resizable', 'Shape', 'Square')) == 'can be drawn and can be resized' and answer_index('5.5') == 1
# 6.1: new List<>() is a compile error.
assert compile_errors(demo('L', 'List<String> x = new List<>();', 'import java.util.List;\n\n')) and answer_index('6.1') == 3
# 7.2: the annotation turns a second abstract method into an error.
TWO_ABS = '@FunctionalInterface\npublic interface Drawable\n{\n    void draw();\n    void erase();\n}'
assert compile_errors(LINES, [file('Drawable.java', TWO_ABS)]) and not compile_errors(LINES, files_at('lambda', 'Drawable')) and answer_index('7.2') == 1
# 7.4: removeIf with a lambda.
assert run(read('workbook/startsb/StartsDemo.java')) == output('workbook/startsb/StartsDemo.output.txt') == '[Ana, Cara]' and answer_index('7.4') == 3
# 9.2: a lambda Drawable goes in an ArrayList<Drawable>.
assert run(demo('Dash', 'Drawable d = () -> System.out.println("--------");\njava.util.ArrayList<Drawable> list = new java.util.ArrayList<>();\nlist.add(d);\nlist.get(0).draw();'), files_at('lambda', 'Drawable')) == '--------' and answer_index('9.2') == 0

# The web page has room for each println on one line; the PDF splits some.
for spec in E.values():
    if spec.get('type') != 'code':
        continue
    spec['starter'] = unsplit(spec['starter'])
    spec['answer'] = b64(unsplit(base64.b64decode(spec['answer']).decode()))
    for f in spec['files']:
        f['content'] = unsplit(f['content'])

assert len(E) == 50, len(E)
data = {'id': 'lecture-20', 'course': 'COMP 2001: Object-Oriented Programming',
        'title': 'Lecture 20 Workbook', 'subtitle': 'Chapter 14, Part 2: Interfaces', 'exercises': E}
out = pathlib.Path(__file__).with_name('exercises.json')
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
print(f'wrote {out} with {len(E)} specs')
