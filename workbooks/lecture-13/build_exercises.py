"""Build Lecture 13 exercises from the approved workbook and real Java runs.

New page: q1 to q30 follow questions 1.1 to 11.2 in order. Suffixes
identify an output table, explanation or second class in the same question.
Program classes use p1-* and p2-* as in Lecture 12. Every code case is
computed by run(), then pinned by an assert. Hidden drivers test the edge
cases described on the page. Run from anywhere; no server is needed.
"""
import base64, html, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402

CODE_DIR = ROOT.parent / "output" / "L13_Chapter_7B_Object_Arrays_Grids_v3" / "code"


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
sys.path.insert(0, str(ROOT.parent / 'scripts' / 'web_l13'))
from workbook import question_code, answer_code, QUESTION_RAW, inline

def solution(n):
    from workbook import group
    m = re.search(r'\\solution\{', QUESTION_RAW[n])
    return html.unescape(re.sub('<[^>]+>', '', inline(group(QUESTION_RAW[n], m.end()-1)[0])))

STUDENT = read('studygroup/Student.java')
GROUP = read('studygroup/StudyGroup.java')
STUDENT_FILE = [file('Student.java', STUDENT)]
GROUP_FILES = STUDENT_FILE + [file('StudyGroup.java', GROUP)]
SEAT = read('theatre/part1/SeatRow.java')
SEAT_FILE = [file('SeatRow.java', SEAT)]
THEATRE1 = read('theatre/part1/Theatre.java')
THEATRE2 = read('theatre/part2/Theatre.java')
THEATRE_FILES = SEAT_FILE + [file('Theatre.java', THEATRE1)]
THEATRE2_FILES = SEAT_FILE + [file('Theatre.java', THEATRE2)]
IMPORT = 'import java.util.Arrays;\n'

def output(n, eid, expected, files=(), imports='', why=True):
    value = run(demo('Prediction', question_code(n), imports), files)
    assert value == expected, (n,value)
    lines_table(eid, value)
    if why: E[eid+'-why'] = SHORT(solution(n))
    return value

def method_box(n, eid, cls, header, files, body, expected, checks=()):
    starter = without_method(cls, header)
    assert code_box(eid, re.search(r'public class (\w+)', cls)[1]+'.java', starter,
                    cls, files + driver('QuestionCheck', body), list(checks)) == expected

# ------------------------------------------------ 1. Object arrays
prefix = question_code('1.1').rsplit('\n',1)[0]
v = run(demo('NullPrefix',prefix),STUDENT_FILE)
assert v == 'Ada\ntrue'
assert throws(demo('NullCall',question_code('1.1')), 'NullPointerException',STUDENT_FILE)
lines_table('q1-output',v)
E['q1-why'] = SHORT(solution('1.1'))
loop = answer_code('1.2')
assert code_box('q2','PrintNames.java', demo('PrintNames',question_code('1.2')+'\n// Print the non-null names.'),
                demo('PrintNames',question_code('1.2')+'\n'+loop),STUDENT_FILE,[]) == 'Ada\nBo'
assert run(demo('EmptyNames','Student[] group = {};\n'+loop),STUDENT_FILE) == ''
output('1.3','q3-output','Ada Lee',STUDENT_FILE)
line = answer_code('1.4')
assert run(demo('Pair',line+'\nfor(Student s : pair) { System.out.println(s.getName()); }'),STUDENT_FILE) == 'Rae\nIvo'
E['q4'] = {'type':'table','xp':2,'blanks':{'line':{'accept':code_forms(line),'show':line,**CODE,'width':'100%'}}}

# ------------------------------------------------ 2. Seats Part 1
THEATRE_START = '''public class Theatre
{
    // Add the field, constructor, book and countBooked.
}
'''
assert code_box('q5','Theatre.java', THEATRE_START,THEATRE1,SEAT_FILE+driver('TheatreCheck','''Theatre empty = new Theatre(0, 3);
System.out.println("Empty: " + empty.countBooked());
System.out.println("Empty book: " + empty.book(0, 0));
Theatre zero = new Theatre(2, 0);
System.out.println("Zero seats: " + zero.book(0, 0));
Theatre t = new Theatre(2, 2);
System.out.println("Initial: " + t.countBooked());
System.out.println("First: " + t.book(0, 0));
System.out.println("Repeat: " + t.book(0, 0));
System.out.println("Other row: " + t.book(1, 0));
System.out.println("Bad row: " + t.book(-1, 0));
System.out.println("Past row: " + t.book(2, 0));
System.out.println("Bad seat: " + t.book(0, -1));
System.out.println("Past seat: " + t.book(0, 2));
System.out.println("Count: " + t.countBooked());
System.out.println("Count again: " + t.countBooked());'''),[
 has('SeatRow[] rows','Store the rows in a SeatRow array.'),
 has('new SeatRow(seatsPerRow)','Create a separate SeatRow for each slot.')],xp=6) == 'Empty: 0\nEmpty book: false\nZero seats: false\nInitial: 0\nFirst: true\nRepeat: false\nOther row: true\nBad row: false\nPast row: false\nBad seat: false\nPast seat: false\nCount: 2\nCount again: 2'
DEMO1 = read('theatre/part1/TheatreDemo.java')
assert code_box('q5-demo','TheatreDemo.java',demo('TheatreDemo','// Create the theatre, try the bookings and print the results.'),DEMO1,THEATRE_FILES,[],name='Program output') == read('theatre/part1/expected.txt').strip()
output('2.2','q6-output','true\nfalse\nfalse\n1',THEATRE_FILES)

# ------------------------------------------------ 3. Copying
output('3.1','q7-output','4 9')
output('3.2','q8-output','Rae Tan\nIvo\nnull',STUDENT_FILE,IMPORT)
line = answer_code('3.3')
assert run(demo('Five','Student[] members = {new Student("Ada")};\n'+line+'\nSystem.out.println(five.length);\nSystem.out.println(five[0] == members[0]);\nSystem.out.println(five[4]);',IMPORT),STUDENT_FILE) == '5\ntrue\nnull'
E['q9'] = {'type':'table','xp':2,'blanks':{'line':{'accept':code_forms(line),'show':line,**CODE,'width':'100%'},'extra':{'accept':['null','four nulls','all null','4 nulls'],'show':'null',**CODE}}}

# ------------------------------------------------ 4. Grids
fixed = 'int[][] grid = new int[3][];\n'+answer_code('4.1')+'\ngrid[1][2] = 9;\nSystem.out.println(grid[1].length);\nSystem.out.println(grid[1][2]);'
assert code_box('q10','CreateRow.java',demo('CreateRow',fixed.replace(answer_code('4.1'),'// Create row 1 here.')),demo('CreateRow',fixed),[],[has('new int[4]','Create row 1 with four int cells.')]) == '4\n9'
assert throws(demo('NullRow',question_code('4.1')),'NullPointerException')
output('4.2','q11-output','8\n2 3',why=False)
statement = answer_code('4.3')
assert code_box('q12','ChenMinutes.java',demo('ChenMinutes','StudyGroup group = new StudyGroup();\n// Print Chen\'s name and minutes for day 6.'),demo('ChenMinutes','StudyGroup group = new StudyGroup();\n'+statement),GROUP_FILES,[has('group.getMember(2)','Use getMember(2) for Chen.'),has('group.getMinutes(2, 6)','Read Chen\'s minutes with getMinutes(2, 6).')]) == 'Chen: 90'

# ------------------------------------------------ 5. Nested loops
trace = question_code('5.1').replace('sum += values[row][col];','sum += values[row][col];\n        System.out.println(sum);')
v = run(demo('RunningSum',trace))
assert v == '2\n6\n7\n10'
E['q13'] = {'type':'table','xp':2,'blanks':{str(i):num(x) for i,x in enumerate(v.splitlines())}}
E['q13-why'] = SHORT(solution('5.1'))
OVER = add_before_end(GROUP,answer_code('5.2'))
method_box('5.2','q14',OVER,'public int studentsOver(int day, int limit)',STUDENT_FILE,'''StudyGroup g = new StudyGroup();
System.out.println(g.studentsOver(5, 30));
System.out.println(g.studentsOver(5, 150));
System.out.println(g.studentsOver(5, -1));
System.out.println(g.studentsOver(1, 30));
System.out.println(g.studentsOver(5, 30));''','2\n0\n4\n1\n2')
condition = answer_code('5.3')
assert run(demo('AllCells',question_code('5.3').replace('col < marks.length',condition))) == '1\n2\n3\n4\n5\n6'
E['q15'] = {'type':'table','xp':2,'blanks':{'condition':{'accept':code_forms(condition,semicolon=False),'show':condition,**CODE}}}
v = run(demo('StrictTie',question_code('5.4')))
w = run(demo('LastTie',question_code('5.4').replace(' > ',' >= ')))
assert v == '0' and w == '1'
E['q16'] = {'type':'table','xp':2,'blanks':{'strict':num(v),'equal':num(w)}}
E['q16-why'] = SHORT(solution('5.4'))

# ------------------------------------------------ 6. Ragged rows
output('6.1','q17-output','10\n20\n30\n40')
rows = answer_code('6.2')
check_rows = '''for(int[] row : rows) {
    System.out.println(row.length);
    for(int value : row) {
        System.out.println(value);
    }
}'''
assert code_box('q18','MakeRows.java',demo('MakeRows','// Create rows of lengths 2, 0 and 5.\n'+check_rows),demo('MakeRows',rows+'\n'+check_rows),[],[]) == '2\n0\n0\n0\n5\n0\n0\n0\n0\n0'

# ------------------------------------------------ 7. Arrays class
output('7.1','q19-output','[9, 3, 6]\n[3, 6, 9]\n[0, 0, 0]',imports=IMPORT)
output('7.2','q20-output','false\ntrue\nfalse',imports=IMPORT)
output('7.3','q21-output','Rae',STUDENT_FILE,IMPORT)

# ------------------------------------------------ 8. Choosing
E['q22'] = SHORT(solution('8.1'),rows=3)
output('8.2','q23-output','Ada: 60',STUDENT_FILE)

# ------------------------------------------------ 9. Seats Part 2
MAP_ONLY = without_method(THEATRE2,'public int bestRow()')
method_box('9.1','q24',MAP_ONLY,'public void printSeatMap()',SEAT_FILE,'''Theatre none = new Theatre(0, 2);
none.printSeatMap();
Theatre zero = new Theatre(2, 0);
zero.printSeatMap();
Theatre t = new Theatre(2, 2);
t.printSeatMap();
t.book(0, 1);
t.book(1, 0);
t.printSeatMap();
t.printSeatMap();''','Row 0: \nRow 1: \nRow 0: ..\nRow 1: ..\nRow 0: .X\nRow 1: X.\nRow 0: .X\nRow 1: X.')
DEMO2 = read('theatre/part2/TheatreDemo.java')
assert code_box('q24-demo','TheatreDemo.java',DEMO1,DEMO2,THEATRE2_FILES,[],name='Program output') == read('theatre/part2/expected.txt').strip()
method_box('9.2','q25',THEATRE2,'public int bestRow()',SEAT_FILE,'''System.out.println(new Theatre(0, 2).bestRow());
System.out.println(new Theatre(2, 0).bestRow());
Theatre t = new Theatre(2, 1);
System.out.println(t.bestRow());
t.book(0, 0);
System.out.println(t.bestRow());
t.book(1, 0);
System.out.println(t.bestRow());
System.out.println(t.bestRow());
System.out.println(t.countBooked());''','-1\n0\n0\n1\n0\n0\n2')

# ------------------------------------------------ 10. Review
E['q26'] = SHORT(solution('10.1'),rows=3)
TOTAL = add_before_end(GROUP,answer_code('10.2'))
method_box('10.2','q27',TOTAL,'public int groupTotal()',STUDENT_FILE,'''StudyGroup g = new StudyGroup();
System.out.println(g.groupTotal());
System.out.println(g.groupTotal());''','1185\n1185',[has('totalForStudent(','Use totalForStudent to obtain each row total.')])
for expr,exception in [('cells[1][0]','NullPointerException'),('cells[0][2]','ArrayIndexOutOfBoundsException')]:
    assert throws(demo('BadCell','int[][] cells = {{1, 2}, null, {3}};\nSystem.out.println('+expr+');'),exception)
v = run(demo('GoodCell','int[][] cells = {{1, 2}, null, {3}};\nSystem.out.println(cells[2][0]);'))
assert v == '3'
E['q28'] = {'type':'table','xp':2,'blanks':{'null':{'accept':['NullPointerException','java.lang.NullPointerException'],'show':'NullPointerException',**CODE},'bounds':{'accept':['ArrayIndexOutOfBoundsException','java.lang.ArrayIndexOutOfBoundsException'],'show':'ArrayIndexOutOfBoundsException',**CODE},'value':num(v)}}
E['q28-why'] = SHORT(solution('10.3'))

# ------------------------------------------------ 11. Complete Java Programs
CAR = read('programA/Car.java')
LOT = read('programA/ParkingLot.java')
CAR_FILE = [file('Car.java',CAR)]
LOT_FILES = CAR_FILE + [file('ParkingLot.java',LOT)]
assert code_box('p1-item','Car.java','''public class Car
{
    // Add the field, constructor and getter.
}
''',CAR,driver('CarCheck','''Car a = new Car("ABC 123");
Car b = new Car("JKL 012");
System.out.println(a.getRegistration());
System.out.println(b.getRegistration());
System.out.println(a.getRegistration());'''),[]) == 'ABC 123\nJKL 012\nABC 123'
assert code_box('p1-collection','ParkingLot.java','''public class ParkingLot
{
    // Add spaces, the constructor and the four methods.
}
''',LOT,CAR_FILE+driver('LotCheck','''ParkingLot empty = new ParkingLot(0);
System.out.println("Empty free: " + empty.countFree());
System.out.println("Empty park: " + empty.park(0, new Car("A")));
System.out.println("Empty leave: " + empty.leave(0));
empty.printSpaces();
ParkingLot lot = new ParkingLot(2);
System.out.println("Free: " + lot.countFree());
System.out.println("Null: " + lot.park(0, null));
System.out.println("Negative: " + lot.park(-1, new Car("A")));
System.out.println("Past: " + lot.park(2, new Car("A")));
System.out.println("Leave empty: " + lot.leave(0));
System.out.println("Park: " + lot.park(1, new Car("ABC 123")));
System.out.println("Again: " + lot.park(1, new Car("B")));
System.out.println("Free: " + lot.countFree());
lot.printSpaces();
System.out.println("Leave negative: " + lot.leave(-1));
System.out.println("Leave past: " + lot.leave(2));
System.out.println("Leave: " + lot.leave(1));
System.out.println("Leave again: " + lot.leave(1));
System.out.println("Free: " + lot.countFree());
lot.printSpaces();'''),[has('Car[] spaces','Store the spaces in a Car array.')],xp=6) == 'Empty free: 0\nEmpty park: false\nEmpty leave: false\nFree: 2\nNull: false\nNegative: false\nPast: false\nLeave empty: false\nPark: true\nAgain: false\nFree: 1\n0: free\n1: ABC 123\nLeave negative: false\nLeave past: false\nLeave: true\nLeave again: false\nFree: 2\n0: free\n1: free'
LOT_DEMO = read('programA/ParkingLotDemo.java')
assert code_box('p1-demo','ParkingLotDemo.java',demo('ParkingLotDemo','// Try the parks and leaves, then print the final spaces.'),LOT_DEMO,LOT_FILES,[],name='Program output') == read('programA/expected.txt').strip()
# Extensions are the same method bodies as the solutions edition.
from workbook import SOURCE, listings
part_a = SOURCE.split(r'\subsection{11.1')[1].split(r'\subsection{11.2')[0]
FREE = listings(part_a[part_a.index(r'\ifsolutions'):])[0].strip()
LOT_FREE = add_before_end(LOT,FREE)
method_box('11.1','q29',LOT_FREE,'public int firstFree()',CAR_FILE,'''System.out.println(new ParkingLot(0).firstFree());
ParkingLot lot = new ParkingLot(2);
System.out.println(lot.firstFree());
lot.park(0, new Car("A"));
System.out.println(lot.firstFree());
lot.park(1, new Car("B"));
System.out.println(lot.firstFree());
lot.leave(0);
System.out.println(lot.firstFree());
System.out.println(lot.firstFree());''','-1\n0\n1\n-1\n0\n0')
COURSE = read('programB/Course.java')
BOOK = read('programB/Gradebook.java')
COURSE_FILE = [file('Course.java',COURSE)]
BOOK_FILES = COURSE_FILE+[file('Gradebook.java',BOOK)]
assert code_box('p2-item','Course.java','''public class Course
{
    // Add both fields, the constructor and both getters.
}
''',COURSE,driver('CourseCheck','''Course one = new Course("One", 1);
Course four = new Course("COMP 2001", 4);
System.out.println(one.getTitle() + ": " + one.getAssessmentCount());
System.out.println(four.getTitle() + ": " + four.getAssessmentCount());'''),[]) == 'One: 1\nCOMP 2001: 4'
assert code_box('p2-collection','Gradebook.java','''public class Gradebook
{
    // Add the course, marks, constructor and four methods.
}
''',BOOK,COURSE_FILE+driver('BookCheck','''Gradebook b = new Gradebook(new Course("Two", 2), 2);
System.out.println(b.getCourseTitle());
System.out.println("Initial: " + b.studentAverage(0));
System.out.println("Initial col: " + b.assessmentAverage(1));
System.out.println(b.record(-1, 0, 50));
System.out.println(b.record(2, 0, 50));
System.out.println(b.record(0, -1, 50));
System.out.println(b.record(0, 2, 50));
System.out.println(b.record(0, 0, -1));
System.out.println(b.record(0, 0, 101));
System.out.println(b.record(0, 0, 0));
System.out.println(b.record(0, 1, 100));
System.out.println(b.record(1, 0, 80));
System.out.println(b.record(1, 1, 81));
System.out.println("Row 0: " + b.studentAverage(0));
System.out.println("Row 1: " + b.studentAverage(1));
System.out.println("Col 0: " + b.assessmentAverage(0));
System.out.println("Col 1: " + b.assessmentAverage(1));
b.record(1, 0, 81);
System.out.println("Replace: " + b.studentAverage(1));
System.out.println("Again: " + b.studentAverage(1));
Gradebook one = new Gradebook(new Course("One", 1), 1);
one.record(0, 0, 75);
System.out.println("One: " + one.assessmentAverage(0));'''),[has('int[][] marks','Keep the marks in an int grid.')],xp=6) == 'Two\nInitial: 0.0\nInitial col: 0.0\nfalse\nfalse\nfalse\nfalse\nfalse\nfalse\ntrue\ntrue\ntrue\ntrue\nRow 0: 50.0\nRow 1: 80.5\nCol 0: 40.0\nCol 1: 90.5\nReplace: 81.0\nAgain: 81.0\nOne: 75.0'
BOOK_DEMO = read('programB/GradebookDemo.java')
assert code_box('p2-demo','GradebookDemo.java',demo('GradebookDemo','// Record all values and print the course and averages.'),BOOK_DEMO,BOOK_FILES,[],name='Program output') == read('programB/expected.txt').strip()
part_b = SOURCE.split(r'\subsection{11.2')[1]
OVERALL = listings(part_b[part_b.index(r'\ifsolutions'):])[0].strip()
BOOK_OVERALL = add_before_end(BOOK,OVERALL)
method_box('11.2','q30',BOOK_OVERALL,'public double overallAverage()',COURSE_FILE,'''Gradebook b = new Gradebook(new Course("Two", 2), 2);
System.out.println(b.overallAverage());
b.record(0, 0, 70);
b.record(0, 1, 80);
b.record(1, 0, 90);
b.record(1, 1, 85);
System.out.println(b.overallAverage());
System.out.println(b.overallAverage());''','0.0\n81.25\n81.25')

data = {'id':'lecture-13','course':'COMP 2001: Object-Oriented Programming',
        'title':'Lecture 13 Workbook','subtitle':'Chapter 7, Part 2: Arrays of Objects and Grids','exercises':E}
out = pathlib.Path(__file__).with_name('exercises.json')
out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print(f'wrote {out} with {len(E)} specs')
