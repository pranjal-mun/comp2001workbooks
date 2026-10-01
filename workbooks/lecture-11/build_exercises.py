"""Build Lecture 11 from the final printed workbook and clinic checkpoints.

Run this builder, then tools/check_workbook.py workbooks/lecture-11.
Answers are extracted from the workbook, compiled with the site Java 8 runner,
and compared with the fixed Chapter 6 outputs before writing the JSON.
Adapted from the Lecture 10 exercise builder.
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


def code_forms(*forms):
    """Accepted forms of a code blank: as written, without spaces, and with or without a final semicolon."""
    out = []
    for form in forms:
        for f in (form, form.rstrip(";") if form.endswith(";") else form + ";"):
            for g in (f, re.sub(r"\s+", "", f)):
                if g not in out:
                    out.append(g)
    return out


def no_semi(accept):
    return [a for a in accept if not a.endswith(";")]


def list_forms(*names):
    joined = ", ".join(names)
    forms = [f"[{joined}]", joined, "[" + ",".join(names) + "]", ",".join(names), " ".join(names)]
    if len(names) == 2:
        forms.append(f"{names[0]} and {names[1]}")
    elif len(names) > 2:
        forms.append(", ".join(names[:-1]) + ", and " + names[-1])
        forms.append(", ".join(names[:-1]) + " and " + names[-1])
    return forms


def box(starter, answer, extra=12):
    """Editor height: the starter's lines plus room to write."""
    n = max(starter.count("\n"), answer.count("\n")) + 2
    return {"minLines": n, "maxLines": n + extra}


SHORT = lambda answer, chars=20, rows=2, xp=2: {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}  # noqa: E731
CODE = {"caseSensitive": True, "width": "26rem"}
LINE = {"placeholder": "output line", "caseSensitive": True, "width": "14rem"}
BOOL = {"placeholder": "true / false"}
NUM = {"placeholder": "number", "width": "7rem"}
YESNO = {"placeholder": "yes / no"}
NO = ["no", "No", "no."]
E = {}


def demo(name, body, imports=''):
    return imports + driver(name, body)[0]['content'] + '\n'


def cls(name, members, imports=''):
    return imports + 'public class ' + name + '\n{\n' + members.rstrip('\n') + '\n}\n'


def context(files, omit):
    return [file(name, content) for name, content in files.items() if name != omit]


def indent_members(source):
    lines = source.splitlines(True)
    start = next((i + 1 for i, line in enumerate(lines) if line.strip() == '{'), None)
    if start is not None and start < len(lines) - 1:
        first = next((line for line in lines[start:-1] if line.strip()), '')
        if first and not first.startswith(' '):
            lines[start:-1] = ['    ' + line if line.strip() else line for line in lines[start:-1]]
    return ''.join(lines)


def add_code(eid, title, starter, answer, expected, files=(), check=()):
    starter, answer = indent_members(starter), indent_members(answer)
    actual = run(answer, files)
    assert actual == expected.rstrip('\n'), (eid, expected, actual)
    E[eid] = {'type': 'code', 'xp': 4, 'title': title,
              'minLines': min(32, max(8, starter.count('\n') + 2)), 'maxLines': 38,
              'starter': starter.rstrip('\n'), 'answer': b64(answer), 'files': list(files),
              'cases': [{'name': 'Checking program', 'expected': expected.rstrip('\n')}],
              'check': '\n'.join(check)}


def example(eid, title, code, expected, files=()):
    assert run(code, files) == expected.rstrip('\n'), eid
    E[eid] = {'type': 'example', 'title': title, 'code': code.rstrip('\n'),
              'output': expected.rstrip('\n'), 'files': list(files), 'maxLines': 32}


def blank(value, *others, kind='text', width='16rem', preserve_whitespace=False):
    return {'accept': [str(value), *map(str, others)], 'show': str(value),
            'caseSensitive': kind == 'code', 'placeholder': kind, 'width': width,
            **({'preserveWhitespace': True} if preserve_whitespace else {})}


def tab(eid, blanks):
    E[eid] = {'type': 'table', 'xp': 3, 'blanks': blanks}


def method_class(key, members='', imports=''):
    return cls('HelpBot', members + '\n' + JAVA[key], imports)


COURSE = ROOT.parent
PRINT = COURSE / 'output/L12_Chapter_6B_Maps_Sets_Static_v3'
TEXT = (PRINT / 'L11_Chapter_6B_Workbook_Content.tex').read_text()
CONTRACT = (COURSE / 'output/L11_Chapter_6A_Library_Classes_v3/Chapter_6_contract.md').read_text()
JAVA = dict(re.findall(r'% JAVA: ([^\n]+)\n\\begin\{lstlisting\}\[style=java\]\n(.*?)\\end\{lstlisting\}', TEXT, re.S))
OUTPUT = dict(re.findall(r'% OUTPUT: ([^\n]+)\n\\begin\{lstlisting\}\[style=output\]\n(.*?)\\end\{lstlisting\}', TEXT, re.S))
assert re.findall(r'% QUESTION (\d+)', TEXT) == [str(i) for i in range(1,26)]


def project(label):
    return {name+'.java': ''.join(JAVA[k] for k in sorted(
        (k for k in JAVA if k.startswith(label+'-'+name+'-')),
        key=lambda k:int(k.rsplit('-',1)[1])))
        for name in ['Appointment','ClinicSchedule','ClinicDemo']}


def append_method(source, method, imports=''):
    return imports + source.rstrip()[:-1] + '\n' + method.rstrip() + '\n}\n'


START = project('starting')
PART12 = project('part12')
PART11 = dict(START)
PART11['ClinicSchedule.java'] = append_method(START['ClinicSchedule.java'], JAVA['q11-counts']+JAVA['q12-names'], JAVA['q11-import']+JAVA['q12-import'])
PART11['ClinicDemo.java'] = JAVA['q13-demo']
for folder, files in [('starting',START),('part11',PART11),('part12',PART12)]:
    for name, source in files.items():
        reference = (PRINT/'code'/folder/name).read_text()
        # Explicit import order can differ; class bodies remain identical.
        assert re.sub(r'\s+','',re.sub(r'^import .*\n','',source,flags=re.M)) == re.sub(r'\s+','',re.sub(r'^import .*\n','',reference,flags=re.M)), (folder,name)
        assert set(re.findall(r'^import .*;',source,re.M)) == set(re.findall(r'^import .*;',reference,re.M))
for key in ['q13-demo','q24-demo']:
    assert OUTPUT[key] in CONTRACT
HELPBOT = (PRINT/'code/final/HelpBot.java').read_text()
BOTFILES = [file('HelpBot.java',HELPBOT)]

# Extract each prose answer from the printed content, including nested TeX braces.
def braced(text, start):
    depth=1; end=start
    while depth:
        char=text[end]
        if char=='{' and (end==0 or text[end-1]!='\\'): depth+=1
        if char=='}' and (end==0 or text[end-1]!='\\'): depth-=1
        end+=1
    return text[start:end-1]


def plain(text):
    text = re.sub(r'\\(?:texttt|textbf)\{([^{}]*)\}',r'\1',text)
    text = text.replace(r'\_', '_').replace(r'\&','&')
    text = ' '.join(text.split())
    return text.replace('in the solutions appendix', 'in the complete examples below').replace('in this edition','below').replace('follows the starting-project appendix', 'follows the starting project')


ANSWERS = {}
for n in range(1,26):
    section=TEXT.split('% QUESTION '+str(n)+'\n',1)[1].split('% QUESTION ',1)[0]
    pos=section.index('\\solution{')+len('\\solution{')
    ANSWERS[n]=plain(braced(section,pos))


def prose(n):
    E[f'q{n}-why'] = SHORT(ANSWERS[n],rows=3)


# 1: place the exact printed setup in a small complete class.
setup=JAVA['q01-map-setup'].splitlines()
map_answer=cls('MapSetup', setup[1]+'\npublic MapSetup()\n{\n'+'    '+setup[2]+'\n}\npublic int size()\n{\n    return replyMap.size();\n}',setup[0]+'\n')
map_starter=map_answer.replace(setup[0],'// Import HashMap explicitly.').replace(setup[1],'// Declare the private map.').replace(setup[2],'// Create an empty map.')
add_code('q1','MapSetup.java',map_starter,map_answer,'0',driver('MapSetupCheck','System.out.println(new MapSetup().size());'),[has(setup[0],'Import HashMap explicitly.'),has(setup[1],'Use a private map with String keys and values.')])
prose(1); E['q2']=SHORT(ANSWERS[2])
for n,key in [(3,'q03-lookup'),(5,'q05-replacement'),(10,'q10-set'),(16,'q16-counter'),(20,'q20-calls'),(22,'q22-main')]:
    tab(f'q{n}-output',{str(i):blank(line,kind='code',width='28rem') for i,line in enumerate(OUTPUT[key].rstrip().splitlines())})
    prose(n)

map_entries='\n'.join(re.findall(r'        replyMap\.put\("[^\"]+",.*?\);',HELPBOT,re.S))
assert map_entries.count('replyMap.put')==4
map_entries='\n'.join(line[4:] for line in map_entries.splitlines())
lookup_setup='private HashMap<String, String> replyMap = new HashMap<>();\npublic LookupDemo()\n{\n'+map_entries+'\n}\n'
def lookup_class(fragment):
    body=fragment.replace('replyMap.get("room")', 'replyMap.get(keyword)').rstrip()
    return cls('LookupDemo',lookup_setup+'public void printReplyLength(String keyword)\n{\n'+
               '\n'.join('    '+line for line in body.splitlines())+'\n}', 'import java.util.HashMap;\n')
safe_answer=lookup_class(JAVA['q04-safe'])
safe_starter=lookup_class(JAVA['q04-unsafe'])
lookup_driver=driver('LookupCheck', 'LookupDemo lookup = new LookupDemo();\nlookup.printReplyLength("room");\nlookup.printReplyLength("test");')
add_code('q4','LookupDemo.java',safe_starter,safe_answer,'Unknown keyword\n48',lookup_driver)
E['q4']['cases'][0]['name']='Absent and present reply lengths'
prose(4); E['q6']=SHORT(ANSWERS[6],rows=5)
counts=[('timesAsked("submit")','2'),('timesAsked("compile")','1'),('timesAsked("test")','1'),('timesAsked("late")','0'),('numberOfTopicsAsked()','3')]
tab('q7',{str(i):blank(value,kind='number',width='8rem') for i,(_,value) in enumerate(counts)}); prose(7)
record_members='''private HashMap<String, Integer> keywordCounts = new HashMap<>();
private HashSet<String> topicsAsked = new HashSet<>();
public void record(String keyword)
{
    recordKeyword(keyword);
}
public int timesAsked(String keyword)
{
    return keywordCounts.getOrDefault(keyword, 0);
}
public int numberOfTopicsAsked()
{
    return topicsAsked.size();
}
'''
record_answer=cls('KeywordRecorder',record_members+JAVA['q08-record'],'import java.util.HashMap;\nimport java.util.HashSet;\n')
record_starter=record_answer.replace(JAVA['q08-record'].strip(),'private void recordKeyword(String keyword)\n{\n    // Update the count and topic set.\n}')
record_driver=driver('RecordCheck','''KeywordRecorder r = new KeywordRecorder();
System.out.println(r.timesAsked("late"));
System.out.println(r.numberOfTopicsAsked());
r.record("submit"); r.record("compile"); r.record("submit"); r.record("test");
System.out.println(r.timesAsked("submit"));
System.out.println(r.timesAsked("compile"));
System.out.println(r.timesAsked("test"));
System.out.println(r.timesAsked("late"));
System.out.println(r.numberOfTopicsAsked());
r.record("submit");
System.out.println(r.timesAsked("submit"));
System.out.println(r.numberOfTopicsAsked());''')
add_code('q8','KeywordRecorder.java',record_starter,record_answer,'0\n0\n2\n1\n1\n0\n3\n3\n3',record_driver,[has('private void recordKeyword(String keyword)','Keep the recording helper private.'),has('getOrDefault(', 'Read a missing count with getOrDefault.')]); prose(8)
E['q9']=SHORT(ANSWERS[9],rows=3)
traverse=demo('TopicDemo',JAVA['q10-set']+JAVA['q10-traversal'],'import java.util.HashSet;\n')
add_code('q10-loop','TopicDemo.java',demo('TopicDemo',JAVA['q10-set']+'// Visit every remaining topic.','import java.util.HashSet;\n'),traverse,OUTPUT['q10-set']+'submit',check=[matches(r'.*for\(String[A-Za-z_$][\w$]*:topics\).*','Use a for-each loop over topics, with any local variable name.')])

# Independent editors for the two snapshot methods. Both retain every old method.
old_headers=re.findall(r'^    public [^\n]+\([^\n]*\)',START['ClinicSchedule.java'],re.M)
keep_checks=[has(h.strip(),'Keep the existing clinic operation: '+h.strip()) for h in old_headers]
for n,key,im in [(11,'q11-counts','q11-import'),(12,'q12-names','q12-import')]:
    answer=append_method(START['ClinicSchedule.java'],JAVA[key],JAVA[im])
    signature='public HashMap<String, Integer> countAppointmentsByName()' if n==11 else 'public HashSet<String> uniquePatientNames()'
    stub='    /**\n     * Describe the fresh snapshot and exact names.\n     * @return Describe the empty and nonempty result.\n     */\n    '+signature+'\n    {\n        // Build the snapshot from current appointments.\n        return null;\n    }\n'
    starter=append_method(START['ClinicSchedule.java'],stub,'// Add the explicit collection import.\n')
    if n==11:
        body='''ClinicSchedule s = new ClinicSchedule();
System.out.println(s.countAppointmentsByName().size());
Appointment ana = new Appointment("Ana", 15);
ana.checkIn();
s.addAppointment(ana);
s.addAppointment(new Appointment("Ben", 20));
s.addAppointment(new Appointment("Cara", 10));
s.addAppointment(new Appointment("Ana", 15));
s.addAppointment(new Appointment("  ANA  ", 15));
java.util.HashMap<String, Integer> old = s.countAppointmentsByName();
System.out.println(old.get("Ana"));
System.out.println(old.get("  ANA  "));
System.out.println(old.get("Dana"));
System.out.println(old.getOrDefault("Dana", 0));
System.out.println(old.size());
System.out.println(s.cancelPatient("Ben"));
System.out.println(old.get("Ben"));
System.out.println(s.countAppointmentsByName().getOrDefault("Ben", 0));
old.put("Ana", 99);
System.out.println(s.countAppointmentsByName().get("Ana"));
System.out.println(s.getCount());'''
        expected='0\n2\n1\nnull\n0\n4\ntrue\n1\n0\n2\n4'
    else:
        body='''ClinicSchedule s = new ClinicSchedule();
System.out.println(s.uniquePatientNames().size());
Appointment ana = new Appointment("Ana", 15); ana.checkIn();
s.addAppointment(ana);
s.addAppointment(new Appointment("Ben", 20));
s.addAppointment(new Appointment("Cara", 10));
s.addAppointment(new Appointment("Ana", 15));
s.addAppointment(new Appointment("  ANA  ", 15));
java.util.HashSet<String> old = s.uniquePatientNames();
System.out.println(old.size());
System.out.println(old.contains("Ana"));
System.out.println(old.contains("  ANA  "));
System.out.println(old.contains("Dana"));
System.out.println(s.cancelPatient("Ben"));
System.out.println(old.contains("Ben"));
System.out.println(s.uniquePatientNames().contains("Ben"));
old.clear();
System.out.println(s.uniquePatientNames().size());
System.out.println(s.getCount());'''
        expected='0\n4\ntrue\ntrue\nfalse\ntrue\ntrue\nfalse\n3\n4'
    checks=keep_checks+[has(JAVA[im].strip(),'Use the explicit collection import.'),has('@return','Document the returned snapshot.')]
    checks += ['require(ClinicSchedule.class.getDeclaredFields().length == 2, "Keep only the existing list and retained random generator fields.");']
    add_code(f'q{n}','ClinicSchedule.java',starter,answer,expected,[file('Appointment.java',START['Appointment.java'])]+driver('SnapshotCheck',body),checks)
    prose(n)
q13_labels=['Empty counts','Empty names','Ana count','Ben count','Cara count','Dana via get','Dana via getOrDefault, default 0','Different names','Count entries','Has Ana','Has Dana','Appointments']
q13_values=['0','0','2','1','1','null','0','3','3','true','false','4']
tab('q13',{str(i):blank(v,kind='code',width='8rem') for i,v in enumerate(q13_values)}); prose(13)
E['q14']=SHORT(ANSWERS[14],rows=3); E['q15']=SHORT(ANSWERS[15],rows=4)
ratings_answer=HELPBOT
for printed in JAVA['q17-ratings'].split('\n\n'):
    assert re.sub(r'\s+','',printed) in re.sub(r'\s+','',ratings_answer)
ratings_starter=ratings_answer.replace('public static final int MIN_RATING = 1;', '// Declare the public minimum rating constant.').replace('public static final int MAX_RATING = 5;', '// Declare the public maximum rating constant.')
ratings_starter=ratings_starter.replace('        if(rating >= MIN_RATING && rating <= MAX_RATING) {\n            ratings.add(rating);\n        }', '        // Accept ratings inside the constant bounds.')
# Inspect identifiers in the method body, without fixing operand order or branches.
rating_constant_use=r'''String cleanSource = source.replaceAll("(?s)/\\*.*?\\*/|//[^\\r\\n]*|\\\"(?:\\\\.|[^\\\"\\\\])*\\\"", " ");
java.util.regex.Matcher method = java.util.regex.Pattern.compile("\\bvoid\\s+addRating\\s*\\([^)]*\\)\\s*\\{").matcher(cleanSource);
require(method.find(), "Keep the addRating method.");
int start = method.end();
int end = start;
int depth = 1;
while(end < cleanSource.length() && depth > 0) {
    char next = cleanSource.charAt(end++);
    if(next == '{') { depth++; }
    else if(next == '}') { depth--; }
}
String body = cleanSource.substring(start, end - 1);
require(java.util.regex.Pattern.compile("\\bMIN_RATING\\b").matcher(body).find(), "Use the minimum constant in addRating.");
require(java.util.regex.Pattern.compile("\\bMAX_RATING\\b").matcher(body).find(), "Use the maximum constant in addRating.");'''
rating_boundaries='''HelpBot minimum = new HelpBot();
minimum.addRating(1);
require(minimum.numberOfRatings() == 1 && minimum.averageRating() == 1, "Accept rating 1.");
HelpBot maximum = new HelpBot();
maximum.addRating(5);
require(maximum.numberOfRatings() == 1 && maximum.averageRating() == 5, "Accept rating 5.");
HelpBot below = new HelpBot();
below.addRating(0);
require(below.numberOfRatings() == 0 && below.averageRating() == 0, "Ignore rating 0.");
HelpBot above = new HelpBot();
above.addRating(6);
require(above.numberOfRatings() == 0 && above.averageRating() == 0, "Ignore rating 6.");'''
add_code('q17','HelpBot.java',ratings_starter,ratings_answer,'3\n4',driver('RatingCheck','HelpBot bot = new HelpBot();\nbot.addRating(5); bot.addRating(3); bot.addRating(4); bot.addRating(0); bot.addRating(6);\nSystem.out.println(bot.numberOfRatings());\nSystem.out.println(bot.averageRating());'),[has('public static final int MIN_RATING = 1;', 'Declare the public minimum constant.'),has('public static final int MAX_RATING = 5;', 'Declare the public maximum constant.'),rating_constant_use,rating_boundaries]); prose(17)
duration_answer=START['Appointment.java'].replace('private int minutes;','private final int minutes;')
assert re.sub(r'\s+','',JAVA['q18-duration']) in re.sub(r'\s+','',duration_answer.replace('    private String patientName;\n    private boolean checkedIn;\n',''))
duration_starter=duration_answer.replace('private final int minutes;','// Declare the final minutes field.').replace('this.minutes = minutes;','// Store the duration once.')
add_code('q18','Appointment.java',duration_starter,duration_answer,'15\n20\n10',driver('DurationCheck','''System.out.println(new Appointment("Ana", 15).getMinutes());
System.out.println(new Appointment("Ben", 20).getMinutes());
System.out.println(new Appointment("Cara", 10).getMinutes());'''),[has('private final int minutes;','Keep duration private and final.')]); prose(18)
E['q19']=SHORT(ANSWERS[19],rows=3)
getter_answer=cls('HelpBot','private static int botsCreated = 0;\n'+JAVA['q20-getter'])
add_code('q20','HelpBot.java',cls('HelpBot','private static int botsCreated = 0;\n// Add the public static getter.'),getter_answer,OUTPUT['q20-calls'],driver('ClassCallCheck',JAVA['q20-calls']),[has('public static int numberOfBots()','Use a class method.')])
receiver_answer=cls('ReceiverDemo',JAVA['q21-receiver'])
add_code('q21','ReceiverDemo.java',cls('ReceiverDemo','// Add the static helper with a HelpBot parameter.'),receiver_answer,'4',BOTFILES+driver('ReceiverCheck','System.out.println(ReceiverDemo.numberOfReplies(new HelpBot()));'),[matches(r'.*publicstaticintnumberOfReplies\(HelpBot[A-Za-z_$][\w$]*\).*','Declare a static helper with one HelpBot parameter.')]); prose(21)

# Part 12 edits the existing Appointment, preserving the old operations.
appointment_answer=PART12['Appointment.java']
appointment_starter=START['Appointment.java'].replace('    private int minutes;','    // Make the duration field final.\n    private int minutes;').replace('    private String patientName;', '    // Add the default constant and shared creation counter.\n    private String patientName;').replace('        checkedIn = false;','        checkedIn = false;\n        // Increment the creation counter once.').rstrip()[:-1]+'\n    // Add the documented class getter.\n}\n'
appointment_checks=[has('public static final int DEFAULT_MINUTES = 15;','Declare the default duration constant.'),has('private static int appointmentsCreated = 0;','Declare the private shared counter.'),has('private final int minutes;','Make each duration final.'),has('public static int numberOfAppointmentsCreated()','Use a class getter.'),has('@return','Document the creation count.'),
'require(Appointment.class.getDeclaredConstructors().length == 1, "Keep the existing two-parameter constructor only.");',
'require(Appointment.numberOfAppointmentsCreated() == 4, "Cancellation must not lower the lifetime count.");\nAppointment extra = new Appointment("Dana", 15);\nrequire(Appointment.numberOfAppointmentsCreated() == 5, "Construction must count even before adding to a schedule.");\nextra.checkIn();\nrequire(extra.hasCheckedIn() && extra.getMinutes() == 15 && extra.getPatientName().equals("Dana"), "Keep the old instance operations.");']
add_code('q23','Appointment.java',appointment_starter,appointment_answer,OUTPUT['q24-demo'],context(PART12,'Appointment.java'),appointment_checks); prose(23)
q24_labels=['Created before','Default minutes','Created after base','Appointments','Cancelled Ana','Appointments after cancellation','Created after cancellation','Created after another Ana','Appointments after another Ana','Current Ana count']
q24_values=[line.split(': ',1)[1] for line in OUTPUT['q24-demo'].rstrip().splitlines()]
tab('q24',{str(i):blank(v,kind='code',width='8rem') for i,v in enumerate(q24_values)}); prose(24)
E['q25']=SHORT(ANSWERS[25],rows=4)

example('summary-example','HelpBot.java',HELPBOT,(PRINT/'code/final/expected.txt').read_text(),[file('HelpBotDemo.java',(PRINT/'code/final/HelpBotDemo.java').read_text())])
example('starting-example','ClinicDemo.java',START['ClinicDemo.java'],OUTPUT['starting-demo'],context(START,'ClinicDemo.java'))
example('part11-example','ClinicDemo.java',PART11['ClinicDemo.java'],OUTPUT['q13-demo'],context(PART11,'ClinicDemo.java'))
example('part12-example','ClinicDemo.java',PART12['ClinicDemo.java'],OUTPUT['part12-demo'],context(PART12,'ClinicDemo.java'))
example('main-example','HelpBotDemo.java',JAVA['q22-main'],OUTPUT['q22-main'],BOTFILES)
DATA={'id':'lecture-11','course':'COMP 2001','title':'Lecture 11 Workbook', 'subtitle':'Chapter 6, Part 2: Maps, sets, and class-level members','exercises':E}
if __name__=='__main__':
    target=pathlib.Path(__file__).with_name('exercises.json')
    target.write_text(json.dumps(DATA,indent=2)+'\n')
    kinds={kind:sum(s['type']==kind for s in E.values()) for kind in ['code','table','short','example']}
    print(f'Wrote {target}: {sum(kinds[k] for k in ["code","table","short"])} exercises, {kinds["example"]} runnable examples.')
