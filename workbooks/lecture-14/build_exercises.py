"""Build Lecture 14 exercises from the approved workbook and real Java runs.

New page: q1 to q28 follow questions 1.1 to 11.2 in order. Suffixes
identify an output table, explanation or second class in the same question.
Program classes use p1-* and p2-* as in Lecture 13. Every code case is
computed by run(), then pinned by an assert. Hidden drivers test the edge
cases described on the page. Run from anywhere; no server is needed.
"""
import base64, html, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402

CODE_DIR = ROOT.parent / "output" / "L14_Chapter_8_Designing_Classes_v3" / "code"


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
sys.path.insert(0, str(ROOT.parent / 'scripts' / 'web_l14'))
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


# 1. Change; 2. Silent bugs
E['q1'] = {'type':'table','xp':2,'blanks':{'lines':num(2),'classes':num(1)}}
E['q1-why'] = SHORT(solution('1.1'))
E['q2'] = SHORT(solution('1.2'))
PARCEL = '''public class Parcel
{
    public int getCharge()
    {
        return 300;
    }
    public String getLabel()
    {
        return "Delivery 250";
    }
}'''
output('2.1','q3-output','300\nDelivery 250',[file('Parcel.java',PARCEL)])
E['q4'] = SHORT(solution('2.2'))

# 3. Duplication
FOOTER_START = '''public class Reports
{
    public void printReceipt()
    {
        System.out.println("Thank you");
        System.out.println("Please visit again");
    }

    public void printSummary()
    {
        System.out.println("Thank you");
        System.out.println("Please visit again");
    }
}'''
FOOTER = '''public class Reports
{
    private void printFooter()
    {
        System.out.println("Thank you");
        System.out.println("Please visit again");
    }

    public void printReceipt()
    {
        printFooter();
    }

    public void printSummary()
    {
        printFooter();
    }
}'''
checked('q5','Reports.java',FOOTER_START,FOOTER,driver('ReportCheck','''Reports reports = new Reports();
reports.printReceipt();
reports.printSummary();'''),'Thank you\nPlease visit again\nThank you\nPlease visit again',[
 has('private void printFooter()', 'Extract a private printFooter method.'),
 'require(source.split("Thank you", -1).length == 2, "Keep the thank-you text in one place.");',
 'require(source.split("Please visit again", -1).length == 2, "Keep the invitation text in one place.");'])
E['q6'] = SHORT(solution('3.2'))
E['q7'] = SHORT(solution('3.3'))

# 4. Loans Part 1
BOOK1=read('loans/part1/Book.java')
DESK1=read('loans/part1/LoanDesk.java')
LOAN_DEMO=read('loans/part1/LoanDemo.java')
BOOK1_FILES=[file('Book.java',BOOK1)]
DESK1_FILES=BOOK1_FILES+[file('LoanDesk.java',DESK1)]
BOOK_BODY='''Book book = new Book("Dune", 10);
System.out.println(book.getTitle());
System.out.println(book.getDueDay());
System.out.println(book.isReturned());
System.out.println(book.daysLate(9));
System.out.println(book.daysLate(10));
System.out.println(book.daysLate(12));
System.out.println(book.daysLate(12));
book.returnBook();
System.out.println(book.isReturned());
System.out.println(book.daysLate(12));
book.returnBook();
System.out.println(book.daysLate(20));'''
BOOK_EXPECT='Dune\n10\nfalse\n0\n0\n2\n2\ntrue\n0\n0'
BOOK_CHECKS=[has('private String title;', 'Make the title field private.'),
 has('private int dueDay;', 'Make the due-day field private.'),
 has('private boolean returned;', 'Make the returned field private.')]
checked('q8-book','Book.java',read('loans/starter/Book.java'),BOOK1,
 driver('BookCheck',BOOK_BODY),BOOK_EXPECT,BOOK_CHECKS,xp=6)
DESK_BODY='''LoanDesk empty = new LoanDesk();
empty.printOverdue(12);
empty.printTotal(12);
LoanDesk desk = new LoanDesk();
Book dune = new Book("Dune", 10);
desk.addBook(dune);
desk.addBook(new Book("Emma", 14));
desk.addBook(new Book("Holes", 3));
desk.addBook(new Book("Due today", 12));
Book returned = new Book("Returned", 1);
returned.returnBook();
desk.addBook(returned);
desk.printOverdue(12);
desk.printTotal(12);
desk.printTotal(12);
dune.returnBook();
desk.printOverdue(12);
desk.printTotal(12);'''
DESK_EXPECT='Total fines: 0\nDune: 2 days late, fine 50\nHoles: 9 days late, fine 225\nTotal fines: 275\nTotal fines: 275\nHoles: 9 days late, fine 225\nTotal fines: 225'
RATE_CHECKS=[has('private static final int FINE_PER_DAY = 25;', 'Keep the 25-cent rate in one private static final constant.'),
 has('private int fineFor(Book book, int today)', 'Add the private fineFor helper.'),
 lacks('book.returned','Ask Book for its lateness instead of reading its fields.'),
 lacks('book.dueDay','Ask Book for its lateness instead of reading its fields.'),
 lacks('book.title','Ask Book for its title instead of reading its fields.'),
 'require(source.split("\\\\b25\\\\b", -1).length == 2, "Keep the daily rate in one place.");',
 'require(source.replaceAll("\\\\s+", "").split("fineFor\\\\(", -1).length >= 4, "Use fineFor for both reports.");']
checked('q8-desk','LoanDesk.java',read('loans/starter/LoanDesk.java'),DESK1,
 BOOK1_FILES+driver('DeskCheck',DESK_BODY),DESK_EXPECT,RATE_CHECKS,xp=6)
checked('q8-demo','LoanDemo.java',demo('LoanDemo','// Create the three books and print the overdue report and total.'),LOAN_DEMO,
 DESK1_FILES,read('loans/part1/expected.txt').strip(),xp=3)
output('4.2','q9-output','0\n2\n0',BOOK1_FILES)

# 5. Encapsulation
PRIVATE_ORDER=read('cafe/private/Order.java')
checked('q10','PhoneCaller.java',demo('PhoneCaller','Order order = new Order("Ada Lim", "555-0101");\n// Print the phone using its public query.'),
 demo('PhoneCaller','Order order = new Order("Ada Lim", "555-0101");\n'+answer_code('5.1')),
 [file('Order.java',PRIVATE_ORDER)],'555-0101',[has('order.getCustomerPhone()', 'Ask for the phone with getCustomerPhone().')],xp=2)
E['q11'] = SHORT(solution('5.2'))
E['q12'] = SHORT(solution('5.3'))

# 6. Responsibility
ANY_ORDER=add_before_end(PRIVATE_ORDER,answer_code('6.1'))
checked('q13','Order.java',PRIVATE_ORDER,ANY_ORDER,driver('AnyItemCheck','''Order empty = new Order("Ada", "1");
System.out.println(empty.hasAnyItem());
Order coffee = new Order("Bo", "2");
coffee.addCoffee();
System.out.println(coffee.hasAnyItem());
Order tea = new Order("Chen", "3");
tea.addTea();
System.out.println(tea.hasAnyItem());
Order muffin = new Order("Dev", "4");
muffin.addMuffin();
System.out.println(muffin.hasAnyItem());
System.out.println(empty.hasAnyItem());
System.out.println(coffee.hasAnyItem());'''),'false\ntrue\ntrue\ntrue\nfalse\ntrue',[
 has('public boolean hasAnyItem()', 'Add hasAnyItem to Order, which stores the choices.')])
E['q13-why'] = SHORT(solution('6.1'))
E['q14'] = SHORT(solution('6.2'))
output('6.3','q15-output','Order for Ada Lim\nPhone 555-0101\nTotal 0\n250',files_at('cafe/owner','Order'))

# 7. Cohesion; 8. Refactoring
E['q16'] = SHORT(solution('7.1'))
CAFE_FILES=files_at('cafe/better','Customer','MenuItem','Menu','Order')
output('7.2','q17-output','500\n500',CAFE_FILES,'import java.util.ArrayList;')
E['q18'] = SHORT('Draw two separate list entries. Both arrows end at the same Coffee MenuItem object. '+solution('7.3'),chars=25,rows=5)
E['q19'] = SHORT(solution('8.1'))
E['q20'] = SHORT(solution('8.2'))
output('8.3','q21-output','525\n700',CAFE_FILES,'import java.util.ArrayList;')

# 9. Loans Part 2: retain Part 1, then add returned text and a total query.
BOOK2=read('loans/part2/Book.java')
DESK2=read('loans/part2/LoanDesk.java')
BOOK2_FILES=[file('Book.java',BOOK2)]
DESK2_FILES=BOOK2_FILES+[file('LoanDesk.java',DESK2)]
checked('q22-book','Book.java',BOOK1,BOOK2,driver('BookLineCheck',BOOK_BODY+'''
Book emma = new Book("Emma", 14);
System.out.println(emma.getLine(12));
System.out.println(emma.getLine(14));
System.out.println(emma.getLine(16));
emma.returnBook();
System.out.println(emma.getLine(16));
System.out.println(emma.getLine(16));'''),
 BOOK_EXPECT+'\nEmma: 0 days late\nEmma: 0 days late\nEmma: 2 days late\nEmma: 0 days late\nEmma: 0 days late',BOOK_CHECKS+[
 lacks('FINE_PER_DAY','Keep the fine policy out of Book.')],xp=5)
checked('q22-desk','LoanDesk.java',DESK1,DESK2,BOOK2_FILES+driver('DeskTotalCheck',DESK_BODY+'''
System.out.println("Empty query: " + empty.totalFines(12));
System.out.println("Query: " + desk.totalFines(12));
System.out.println("Query again: " + desk.totalFines(12));
System.out.println("Earlier: " + desk.totalFines(2));'''),
 DESK_EXPECT+'\nEmpty query: 0\nQuery: 225\nQuery again: 225\nEarlier: 0',RATE_CHECKS+[
 has('book.getLine(today)', 'Use the text returned by Book.getLine(today).'),
 has('totalFines(today)', 'Use totalFines in the total printing method.')],xp=6)
checked('q22-demo','LoanDemo.java',demo('LoanDemo','// Keep the three books and the two report calls.'),LOAN_DEMO,
 DESK2_FILES,read('loans/part2/expected.txt').strip(),xp=3)
DESK30=read('loans/part2-rate30/LoanDesk.java')
checked('q22-rate','LoanDesk.java',DESK2,DESK30,BOOK2_FILES+driver('RateCheck','''LoanDesk empty = new LoanDesk();
System.out.println(empty.totalFines(12));
LoanDesk desk = new LoanDesk();
desk.addBook(new Book("Dune", 10));
desk.addBook(new Book("Emma", 14));
desk.addBook(new Book("Holes", 3));
desk.printOverdue(12);
desk.printTotal(12);
System.out.println(desk.totalFines(12));
System.out.println(desk.totalFines(12));'''),
 '0\nDune: 2 days late, fine 60\nHoles: 9 days late, fine 270\nTotal fines: 330\n330\n330',[
 has('private static final int FINE_PER_DAY = 30;', 'Change the one daily-rate constant to 30.')],xp=2)
line=run(demo('EmmaLine','Book emma = new Book("Emma", 14);\nSystem.out.println(emma.getLine(12));'),BOOK2_FILES)
assert line == 'Emma: 0 days late'
lines_table('q23-output',line)
E['q23-why'] = SHORT(solution('9.2'))

# 10. Review
E['q24'] = SHORT(solution('10.1'))
E['q25'] = SHORT(solution('10.2'))
E['q26'] = SHORT(solution('10.3'))

# 11. Complete Java Programs. Each class has its own editor and driver.
SONG=read('programA/Song.java');PLAYLIST=read('programA/Playlist.java')
SONG_FILES=[file('Song.java',SONG)]
PLAYLIST_FILES=SONG_FILES+[file('Playlist.java',PLAYLIST)]
checked('p1-item','Song.java','''public class Song
{
    // Add private fields, the constructor and the two queries.
}''',SONG,driver('SongCheck','''Song harbour = new Song("Harbour", 180);
Song silence = new Song("Silence", 0);
System.out.println(harbour.getLengthInSeconds());
System.out.println(harbour.getLine());
System.out.println(silence.getLengthInSeconds());
System.out.println(silence.getLine());
System.out.println(harbour.getLine());'''),
 '180\nHarbour 180 s\n0\nSilence 0 s\nHarbour 180 s',[
 has('private String title;', 'Keep the song title private.'),
 has('private int lengthInSeconds;', 'Keep the song length private.')])
checked('p1-collection','Playlist.java','''import java.util.ArrayList;

public class Playlist
{
    // Add the private fields, constructor and three methods.
}''',PLAYLIST,SONG_FILES+driver('PlaylistCheck','''Playlist list = new Playlist("Practice");
System.out.println(list.getTotalSeconds());
System.out.println(list.getReport());
Song harbour = new Song("Harbour", 180);
list.addSong(harbour);
list.addSong(new Song("Silence", 0));
list.addSong(harbour);
System.out.println(list.getTotalSeconds());
System.out.println(list.getReport());
System.out.println(list.getReport());'''),
 '0\nPlaylist Practice\nTotal 0 s\n360\nPlaylist Practice\nHarbour 180 s\nSilence 0 s\nHarbour 180 s\nTotal 360 s\nPlaylist Practice\nHarbour 180 s\nSilence 0 s\nHarbour 180 s\nTotal 360 s',[
 has('private ArrayList<Song> songs;', 'Keep the songs in a private ArrayList.'),
 has('song.getLengthInSeconds()', 'Ask each song for its length.')],xp=6)
checked('p1-demo','PlaylistDemo.java',demo('PlaylistDemo','// Create Morning, add the three songs and print its report.'),
 read('programA/PlaylistDemo.java'),PLAYLIST_FILES,read('programA/expected.txt').strip(),xp=3)
part_a=SOURCE.split(r'\subsection{11.1')[1].split(r'\subsection{11.2')[0]
LONGER=listings(part_a[part_a.index(r'\ifsolutions'):])[0].strip()
PLAYLIST_LONGER=add_before_end(PLAYLIST,LONGER)
checked('q27','Playlist.java',PLAYLIST,PLAYLIST_LONGER,SONG_FILES+driver('LongerCheck','''Playlist empty = new Playlist("Empty");
System.out.println(empty.countLongerThan(180));
Playlist list = new Playlist("Morning");
Song harbour = new Song("Harbour", 180);
list.addSong(harbour);
list.addSong(new Song("Rain", 210));
list.addSong(new Song("Home", 150));
System.out.println(list.countLongerThan(180));
System.out.println(list.countLongerThan(210));
System.out.println(list.countLongerThan(0));
list.addSong(harbour);
System.out.println(list.countLongerThan(179));
System.out.println(list.countLongerThan(179));
System.out.println(list.getTotalSeconds());'''),
 '0\n1\n0\n3\n3\n3\n720',[has('song.getLengthInSeconds()', 'Ask each song for its length.')])
TICKET=read('programB/Ticket.java');OFFICE=read('programB/TicketOffice.java')
TICKET_FILES=[file('Ticket.java',TICKET)]
OFFICE_FILES=TICKET_FILES+[file('TicketOffice.java',OFFICE)]
checked('p2-item','Ticket.java','''public class Ticket
{
    // Add the private fields, constructor and getters.
}''',TICKET,driver('TicketCheck','''Ticket adult = new Ticket("Ada", 0);
Ticket student = new Ticket("Bo", 1);
System.out.println(adult.getName());
System.out.println(adult.getPriceCode());
System.out.println(student.getName());
System.out.println(student.getPriceCode());
System.out.println(adult.getPriceCode());'''),
 'Ada\n0\nBo\n1\n0',[has('private String name;', 'Keep the customer name private.'),
 has('private int priceCode;', 'Keep the price code private.')])
OFFICE_BODY='''TicketOffice office = new TicketOffice();
System.out.println(office.getTotal());
System.out.println(office.getReport());
office.addTicket(new Ticket("Bo", 1));
office.addTicket(new Ticket("Ada", 0));
office.addTicket(new Ticket("Chen", 0));
System.out.println(office.getTotal());
System.out.println(office.getReport());
System.out.println(office.getReport());'''
checked('p2-collection','TicketOffice.java','''import java.util.ArrayList;

public class TicketOffice
{
    // Add the one price table, private list, constructor and four methods.
}''',OFFICE,TICKET_FILES+driver('OfficeCheck',OFFICE_BODY),
 '0\nTickets\nTotal 0\n3200\nTickets\nBo 800\nAda 1200\nChen 1200\nTotal 3200\nTickets\nBo 800\nAda 1200\nChen 1200\nTotal 3200',[
 has('private static final int[] PRICES = {1200, 800};', 'Keep the prices in one private static final table.'),
 has('private int priceFor(Ticket ticket)', 'Use one private priceFor helper.'),
 has('private ArrayList<Ticket> tickets;', 'Keep the tickets in a private ArrayList.')],xp=6)
checked('p2-demo','TicketOfficeDemo.java',demo('TicketOfficeDemo','// Add Ada, Bo and Chen with their price codes, then print the report.'),
 read('programB/TicketOfficeDemo.java'),OFFICE_FILES,read('programB/expected.txt').strip(),xp=3)
OFFICE1500=OFFICE.replace('{1200, 800}','{1500, 800}')
checked('q28','TicketOffice.java',OFFICE,OFFICE1500,TICKET_FILES+driver('PriceCheck',OFFICE_BODY),
 '0\nTickets\nTotal 0\n3800\nTickets\nBo 800\nAda 1500\nChen 1500\nTotal 3800\nTickets\nBo 800\nAda 1500\nChen 1500\nTotal 3800',[
 has('private static final int[] PRICES = {1500, 800};', 'Change the adult price in the one table to 1500.')],xp=3)
E['q28-why']=SHORT('Both methods call priceFor, which reads the same table. There is no second price literal to update.')

# Pin the complete demo runs as well as the edge-case drivers above.
assert run(read('programA/PlaylistDemo.java'),PLAYLIST_FILES) == read('programA/expected.txt').strip()
assert run(read('programB/TicketOfficeDemo.java'),TICKET_FILES+[file('TicketOffice.java',OFFICE1500)]) == 'Tickets\nAda 1500\nBo 800\nChen 1500\nTotal 3800'
assert run(LOAN_DEMO,BOOK2_FILES+[file('LoanDesk.java',DESK30)]) == read('loans/part2-rate30/expected.txt').strip()

data={'id':'lecture-14','course':'COMP 2001: Object-Oriented Programming',
      'title':'Lecture 14 Workbook','subtitle':'Chapter 8: Designing Classes','exercises':E}
out=pathlib.Path(__file__).with_name('exercises.json')
out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print(f'wrote {out} with {len(E)} specs')
