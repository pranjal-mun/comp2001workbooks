"""Build Lecture 10 from the final printed workbook and clinic checkpoints.

Run this builder, then tools/check_workbook.py workbooks/lecture-10.
Answers are extracted from the workbook, compiled with the site Java 8 runner,
and compared with the fixed Chapter 6 outputs before writing the JSON.
Adapted from the Lecture 9 exercise builder.
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

COURSE = ROOT.parent
PRINT = COURSE / 'output/L11_Chapter_6A_Library_Classes_v3'
TEXT = (PRINT / 'L10_Chapter_6A_Workbook_Content.tex').read_text()
JAVA = dict(re.findall(r'% JAVA: ([^\n]+)\n\\begin\{lstlisting\}\[style=java\]\n(.*?)\\end\{lstlisting\}', TEXT, re.S))
OUTPUT = dict(re.findall(r'% OUTPUT: ([^\n]+)\n\\begin\{lstlisting\}\[style=output\]\n(.*?)\\end\{lstlisting\}', TEXT, re.S))
CONTRACT = (PRINT / 'Chapter_6_contract.md').read_text()
assert re.findall(r'% QUESTION (\d+)', TEXT) == [str(i) for i in range(1, 26)]


def project(label):
    result = {}
    for name in ['Appointment', 'ClinicSchedule', 'ClinicDemo']:
        keys = sorted((key for key in JAVA if key.startswith(label + '-' + name + '-')),
                      key=lambda key: int(key.rsplit('-', 1)[1]))
        result[name + '.java'] = ''.join(JAVA[key] for key in keys)
    return result


START = project('starting')
PART10 = project('part10')
PART9 = dict(START)
PART9['ClinicSchedule.java'] = START['ClinicSchedule.java'].rstrip()[:-1] + '\n' + ''.join('    '+line if line.strip() else line for line in JAVA['q12-search'].splitlines(True)) + '}\n'
PART9['ClinicDemo.java'] = JAVA['q13-demo']
HELPBOT = (PRINT / 'code/final/HelpBot.java').read_text()
REPLIES = [
    'Can you describe that in more detail?',
    'Have you checked the course web page?',
    'That question comes up often. Let us look at it together.',
    'Please post that on the discussion board so others can see the answer.'
]
assert all(reply in CONTRACT and reply in HELPBOT for reply in REPLIES)
assert OUTPUT['q13-demo'] in CONTRACT and OUTPUT['q24-demo'] in CONTRACT
# Compare every complete clinic class to the handout, not just its output.
sections = re.split(r'\n## (?:Starting files|Part 9: Search with cleaned names|Part 10: Random patient choice)\n',
                    (PRINT / 'Clinic appointments L10.md').read_text())[1:]
for files, section in zip([START, PART9, PART10], sections):
    assert files == dict(re.findall(r'#### (\w+\.java)\n\n```java\n(.*?)```', section, re.S))


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


E['q1'] = SHORT('ArrayList stores ordered elements, String supplies text operations, and Random generates pseudo-random numbers. Before calling a method, know its name, parameter types, return type, behaviour, and restrictions on its arguments.', rows=3)
imports = {'Random':'java.util.Random', 'ArrayList':'java.util.ArrayList', 'String':'java.lang.String', 'Integer':'java.lang.Integer'}
tab('q2', {**{name+'-name': blank(qualified, kind='code') for name, qualified in imports.items()},
           **{name+'-import': blank('import '+qualified+';', 'import '+qualified, kind='code', width='23rem')
              if name in ('Random','ArrayList') else blank('none', 'no import', 'not needed') for name,qualified in imports.items()}})
E['q3-why'] = SHORT('The wildcard makes Random available from java.util but does not include java.util.function: subpackages are separate packages. Explicit imports show which classes the file uses.')
add_code('q3', 'QualifiedDemo.java', demo('QualifiedDemo', '// Create a generator without an import.\nSystem.out.println(generator != null);'),
         demo('QualifiedDemo', JAVA['q03-qualified'] + 'System.out.println(generator != null);'), 'true')
tab('q4', {k:blank(v, 'public documentation' if v=='documentation' else 'private implementation') for k,v in [('a','documentation'),('b','documentation'),('c','implementation')]})
E['q4-why'] = SHORT('The documented behaviour says get(0) returns the first element when the list is nonempty. Its private storage details do not affect how we make the call.')
tab('q5', {'access':blank('public',kind='code'),'result':blank('boolean',kind='code'),'name':blank('startsWith',kind='code'),
           'param':blank('String',kind='code'),'signature':blank('startsWith(String)', 'startsWith (String)',kind='code'),
           'caller':blank('no','No; any suitable String expression')})
tab('q6', {'add':blank('public boolean add(String e)',kind='code',width='25rem'),
           'get':blank('public String get(int index)',kind='code',width='25rem'), 'integer':blank('Integer',kind='code')})
E['q6-why'] = SHORT('The diamond lets Java infer the element type from the declaration: new ArrayList<>() here creates an ArrayList<String>. E is a type placeholder, not a class to import.')
example('generics-example', 'GenericDemo.java', demo('GenericDemo', JAVA['q06-generics']+'System.out.println(first);',JAVA['q02-imports']), REPLIES[0])
trace = JAVA['q07-trace']
tab('q7', {**{k+'-text': blank('"'+v+'"',kind='code',width='26rem',preserve_whitespace=True) for k,v in [('typed','   How do I SUBMIT my work?  '),('trimmed','How do I SUBMIT my work?'),('cleaned','how do i submit my work?')]},
           **{k+'-length': blank(v,kind='number',width='7rem') for k,v in [('typed',29),('trimmed',24),('cleaned',24)]}})
example('strings-example','StringTrace.java',demo('StringTrace',trace + '\n' + '\n'.join('System.out.println("[" + '+k+' + "] " + '+k+'.length());' for k in ['typed','trimmed','cleaned'])),
        '[   How do I SUBMIT my work?  ] 29\n[How do I SUBMIT my work?] 24\n[how do i submit my work?] 24')
EXPRESSIONS = [('typed.contains("submit")','false','boolean'),('cleaned.contains("submit")','true','boolean'),
               ('cleaned.startsWith("how")','true','boolean'),('cleaned.endsWith("?")','true','boolean'),
               ('cleaned.indexOf("submit")','9','int'),('cleaned.indexOf("absent")','-1','int'),
               ('cleaned.substring(0, 3)','"how"','String'),('cleaned.isEmpty()','false','boolean')]
tab('q8', {**{str(i)+'-result':blank(v, *(['how'] if t=='String' else []), kind='code') for i,(_,v,t) in enumerate(EXPRESSIONS)},
           **{str(i)+'-type':blank(t,kind='code',width='9rem') for i,(_,v,t) in enumerate(EXPRESSIONS)}})
assert run(demo('OperationsDemo',trace+'\n'+'\n'.join('System.out.println('+e+');' for e,_,_ in EXPRESSIONS))) == '\n'.join(v.strip('"') for _,v,_ in EXPRESSIONS)
E['q8-why'] = SHORT('Contains is case sensitive. The original contains uppercase SUBMIT, so lowercase submit is absent until conversion. Substring(0, 3) takes positions 0, 1, and 2; the end position is excluded.')
tab('q9', {'original-text':blank('"  Ana  "',kind='code',preserve_whitespace=True),'original-length':blank(7,kind='number'),
           'cleaned-text':blank('"Ana"','Ana',kind='code',preserve_whitespace=True),'cleaned-length':blank(3,kind='number')})
E['q9-why'] = SHORT('The variable original can be reassigned to another String. This changes its reference, not the characters in the old object. Immutability describes the object, not whether a variable can hold a new reference.')
tab('q10-output', {'first':blank(7,kind='number'),'second':blank(3,kind='number')})
example('discard-example','DiscardDemo.java',demo('DiscardDemo',JAVA['q10-discard']), '7\n3')
repaired = JAVA['q10-discard'].replace('name.trim();', 'name = name.trim();', 1)
add_code('q10','DiscardDemo.java',demo('DiscardDemo',JAVA['q10-discard']),demo('DiscardDemo',repaired),'3\n3')
E['q10-why'] = SHORT('Store the returned String with name = name.trim(). The assignment changes which String name refers to; it does not edit the original object.')
clean_driver = driver('CleanCheck','HelpBot bot = new HelpBot();\nSystem.out.println(bot.clean("   How do I SUBMIT my work?  "));\nSystem.out.println("[" + bot.clean("   ") + "]");')
add_code('q11-clean','HelpBot.java',cls('HelpBot','public String clean(String question)\n{\n    // Chain two String operations.\n    return question;\n}'),method_class('q11-clean'),'how do i submit my work?\n[]',clean_driver,
         [has('.trim().toLowerCase()', 'Use chained trim() and toLowerCase() calls.')])
add_code('q11-message','MessageDemo.java',demo('MessageDemo','// Create and print the two-line message.'),demo('MessageDemo',JAVA['q11-multiline']),OUTPUT['q11-message'])
E['q11-why'] = SHORT('Trim returns a String, so toLowerCase can be called on that result. A newline escape in the value creates a new output line; a source line break alone does not.')

search_stub = JAVA['q12-search'].replace('String cleanedName = name.trim().toLowerCase();','String cleanedName = name; // Clean the request.')
search_stub = search_stub.replace('storedName.trim().toLowerCase().equals(cleanedName)','false /* compare the cleaned stored name */').replace('return index;', 'return -1; // Return the matching index.')
search_stub = search_stub.replace('The name to search for; must not be null.', 'Describe the parameter and its assumption here.').replace('The first matching index, or -1 if no name matches.', 'Describe the result and missing case here.')
search_starter = START['ClinicSchedule.java'].rstrip()[:-1] + '\n' + ''.join('    '+line if line.strip() else line for line in search_stub.splitlines(True)) + '}\n'
# Same demonstration, followed by boundary and preservation checks.
search_check_body = '''ClinicSchedule schedule = new ClinicSchedule();
System.out.println(schedule.findPatientIndexIgnoringCase("Ana"));
schedule.addAppointment(new Appointment("Ana", 15));
schedule.addAppointment(new Appointment("Ben", 20));
schedule.addAppointment(new Appointment("Cara", 10));
schedule.addAppointment(new Appointment("  ANA  ", 15));
System.out.println(schedule.findPatientIndexIgnoringCase("  aNa  "));
System.out.println(schedule.findPatientIndexIgnoringCase("bEN"));
System.out.println(schedule.findPatientIndexIgnoringCase("  cara  "));
System.out.println(schedule.findPatientIndexIgnoringCase("  DANA  "));
System.out.println(schedule.findPatientIndex("ANA"));
System.out.println(schedule.findPatientIndex("  ANA  "));
schedule.printAllPatients();
System.out.println(schedule.getCount());
System.out.println(schedule.totalWaitingMinutes());
ClinicSchedule spaced = new ClinicSchedule();
Appointment spacedAna = new Appointment("  ANA  ", 15);
spaced.addAppointment(spacedAna);
System.out.println(spaced.findPatientIndexIgnoringCase("ana"));
System.out.println("[" + spacedAna.getPatientName() + "]");'''
search_files = [file('Appointment.java',START['Appointment.java'])] + driver('SearchCheck', search_check_body)
add_code('q12','ClinicSchedule.java',search_starter,PART9['ClinicSchedule.java'], '-1\n0\n1\n2\n-1\n-1\n3\nAna\nBen\nCara\n  ANA  \n4\n60\n0\n[  ANA  ]',search_files,
         [has('@param name','Document the name parameter.'),has('@return','Document the result.'),has('.trim()', 'Trim both names.'),has('.toLowerCase()', 'Compare lowercase text.'),has('.equals(', 'Compare String contents with equals.')])
# Numbered output predictions remain separate from the runnable demonstration.
tab('q13', {str(i):blank(line,kind='code',width='27rem') for i,line in enumerate(OUTPUT['q13-demo'].rstrip('\n').splitlines())})
example('part9-example','ClinicDemo.java',PART9['ClinicDemo.java'],OUTPUT['q13-demo'],context(PART9,'ClinicDemo.java'))
E['q13-why'] = SHORT('The exact search for ANA returns -1. The cleaned searches return 0, 1, and 2; Dana is absent. The stored names and three-appointment list remain unchanged. Searching an empty schedule returns -1 without accessing an element.')

retained_answer = cls('RetainedDemo', JAVA['q14-field'] + '\npublic RetainedDemo()\n{\n' + JAVA['q14-init'] + '}\npublic boolean hasGenerator()\n{\n    return randomGenerator != null;\n}', JAVA['q14-import'])
retained_starter = retained_answer.replace(JAVA['q14-field'].strip(), '// Declare the private generator field here.').replace(JAVA['q14-init'].strip(),'// Initialize the retained generator here.').replace(JAVA['q14-import'].strip(),'// Import Random explicitly.')
add_code('q14','RetainedDemo.java',retained_starter,retained_answer,'true',driver('RetainedCheck','System.out.println(new RetainedDemo().hasGenerator());'),[has('import java.util.Random;', 'Import Random explicitly.'),has('private Random randomGenerator;', 'Keep the retained generator private.'),has('new Random()', 'Use the normal application setup: new Random().')])
E['q14-why'] = SHORT('The import goes above the class, the private field inside the class, and the initialization inside its constructor. Keeping one generator continues its sequence. Reconstructing it on every selection is unnecessary; repeatedly using the same seed restarts its sequence.')
tab('q15', {'any':blank('any int, including negative values','any int','any integer'), 'four':blank('0, 1, 2, 3','0 1 2 3','0 through 3','0 to 3'),
            'one':blank(0,kind='number'), 'zero':blank('IllegalArgumentException: bound must be positive','IllegalArgumentException','invalid; bound must be positive','bound must be positive')})
die_body = 'Random randomGenerator = new Random(42);\n'+JAVA['q15-die']+'System.out.println(roll);'
add_code('q15-die','DieDemo.java',demo('DieDemo','Random randomGenerator = new Random(42);\nint roll = 0; // Replace with a 1-through-6 expression.\nSystem.out.println(roll);',JAVA['q14-import']),demo('DieDemo',die_body,JAVA['q14-import']),'3',[ ],[has('nextInt(6)','Use an exclusive bound of 6 for six possibilities.')])
E['q15-why'] = SHORT('NextInt(bound) includes 0 and excludes the bound. Adding 1 to nextInt(6) turns 0 through 5 into 1 through 6. NextInt() without a bound may return an invalid list index.')
reply_members = 'private ArrayList<String> generalReplies;\nprivate Random randomGenerator;\npublic HelpBot()\n{\n    generalReplies = new ArrayList<>();\n    randomGenerator = new Random();\n'+''.join('    generalReplies.add('+json.dumps(reply)+');\n' for reply in REPLIES)+'}\n'
reply_imports = JAVA['q02-imports']
pick_check = driver('ReplyCheck', '''HelpBot bot = new HelpBot();
boolean allValid = true;
for(int i = 0; i < 1000; i++) {
    String reply = bot.pickGeneralReply();
    boolean valid = ''' + ' || '.join(json.dumps(reply)+'.equals(reply)' for reply in REPLIES)+''';
    if(!valid) {
        allValid = false;
    }
}
System.out.println(allValid);''')
pick_answer = method_class('q16-pick',reply_members,reply_imports)
add_code('q16','HelpBot.java',pick_answer.replace(JAVA['q16-pick'].strip(),'public String pickGeneralReply()\n{\n    // Choose and return one current entry.\n    return "";\n}'),pick_answer,'true',pick_check,[has('nextInt(generalReplies.size())','Use the current list size as the bound.'),lacks('generalReplies.remove(', 'Leave the selected reply in the list.')])
E['q16-why'] = SHORT('With four entries, size() + 1 permits index 4, which is invalid. A possibly empty list needs a check before nextInt(0). HelpBot always has four replies; a selected reply stays available and can appear again.')
reply_answer = method_class('q17-reply',reply_members+JAVA['q11-clean']+JAVA['q16-pick'],reply_imports)
reply_driver = driver('QuestionCheck', '''HelpBot bot = new HelpBot();
System.out.println(bot.replyTo("   "));
String reply = bot.replyTo("   How do I SUBMIT my work?  ");
System.out.println('''+' || '.join(json.dumps(reply)+'.equals(reply)' for reply in REPLIES)+''');''')
add_code('q17','HelpBot.java',reply_answer.replace(JAVA['q17-reply'].strip(),'public String replyTo(String question)\n{\n    // Clean, check for empty text, then choose a reply.\n    return "";\n}'),reply_answer,'Please type a question.\ntrue',reply_driver,[has('clean(question)','Reuse clean(question).'),has('pickGeneralReply()', 'Use the reply-selection method.')])
E['q17-why'] = SHORT('Spaces clean to empty text, giving Please type a question. The messy submit question gets one of the four general replies. Its exact reply cannot be predicted without a seed and call history. This bot still ignores the question\'s meaning.')

tab('q18-types', {name:blank(wrapper,kind='code') for name,wrapper in [('int','Integer'),('double','Double'),('boolean','Boolean'),('char','Character')]})
add_code('q18','RatingsDemo.java',demo('RatingsDemo','// Create ratings, add 5, 3, 4, and read the first into int first.\nSystem.out.println(ratings.size());\nSystem.out.println(first);','import java.util.ArrayList;\n'),demo('RatingsDemo',JAVA['q18-boxing']+'System.out.println(ratings.size());\nSystem.out.println(first);','import java.util.ArrayList;\n'),'3\n5')
E['q18-why'] = SHORT('Use ArrayList<Integer>, since a generic element type must be a reference type. Each add boxes an int into an Integer. Assigning get(0) to int first unboxes it; first is 5. The numeric value is unchanged, and this list has no null entries.')
rating_members = 'private ArrayList<Integer> ratings = new ArrayList<>();\n'
rating_import = 'import java.util.ArrayList;\n'
rating_answer = method_class('q19-ratings',rating_members,rating_import)
rating_driver = driver('RatingCheck','''HelpBot bot = new HelpBot();
System.out.println(bot.numberOfRatings());
bot.addRating(5);
bot.addRating(3);
bot.addRating(4);
bot.addRating(0);
bot.addRating(6);
System.out.println(bot.numberOfRatings());
bot.addRating(1);
bot.addRating(2);
System.out.println(bot.numberOfRatings());''')
add_code('q19','HelpBot.java',method_class('q19-ratings',rating_members,rating_import).replace(JAVA['q19-ratings'].strip(),'public void addRating(int rating)\n{\n    // Accept only 1 through 5 inclusive.\n}\npublic int numberOfRatings()\n{\n    return 0;\n}'),rating_answer,'0\n3\n5',rating_driver)
E['q19-why'] = SHORT('After 5, 3, 4, 0, and 6, only three entries remain: 5, 3, and 4. Both invalid ratings are ignored. Use ratings.size(), so there is no separate count field to keep synchronized.')
average_answer = method_class('q20-average',rating_members+JAVA['q19-ratings'],rating_import)
average_driver = driver('AverageCheck','''HelpBot bot = new HelpBot();
System.out.println(bot.averageRating());
bot.addRating(5);
bot.addRating(3);
bot.addRating(4);
System.out.println(bot.numberOfRatings());
System.out.println(bot.averageRating());
HelpBot separate = new HelpBot();
separate.addRating(5);
separate.addRating(4);
System.out.println(separate.averageRating());''')
add_code('q20','HelpBot.java',average_answer.replace(JAVA['q20-average'].strip(),'public int averageRating()\n{\n    // Check for empty; sum with a for-each loop; divide by size.\n    return 0;\n}'),average_answer,'0\n3\n4\n4',average_driver,[matches(r'.*\bfor\(int\p{javaJavaIdentifierStart}\p{javaJavaIdentifierPart}*:ratings\).*', 'Use a for-each loop over the ratings.')])
tab('q20-trace', {**{str(i)+'-total':blank(v,kind='number') for i,v in enumerate([5,8,12])},
                 **{str(i)+'-count':blank(i+1,kind='number') for i in range(3)},'main':blank(4,kind='number'),'separate':blank(4,kind='number')})
E['q20-why'] = SHORT('The total is 12 and the count is 3, so the average is 4. The separate list gives 9 / 2 = 4 with integer division. The loop unboxes each Integer into int. An empty check avoids division by zero.')
documented = method_class('q21-methoddoc')
add_code('q21-method','HelpBot.java',method_class('q11-clean'),documented,'how do i submit my work?\n[]',clean_driver,[has('/**','Begin the documentation comment with /**.'),has('@param question','Describe the question parameter and its non-null assumption.'),has('@return','Describe the returned cleaned text.')])
add_code('q21-class','HelpBot.java',cls('HelpBot',''),JAVA['q21-classdoc'],'true',driver('ClassCheck','System.out.println(new HelpBot() != null);'),[has('/**','Use a Javadoc comment.'),has('@author Pranjal Patra','Include the stated author.'),has('@version 1.0','Include version 1.0.')])
E['q21-why'] = SHORT('A plain /* block comment is not a Javadoc comment; Javadoc begins with /** before the declaration. Describe purpose and assumptions, rather than just restating the method name. Omit @return for void methods and constructors.')
E['q22'] = SHORT(JAVA['q22-private'].strip()+'\nCallers record ratings through addRating, which checks the allowed range. The setup helper fillGeneralReplies should be private. Private storage and helper code can change while public method names, parameter types, return types, and promised behaviour stay the same.',rows=4)

random_starter = PART9['ClinicSchedule.java'].rstrip()[:-1] + '\n    public String randomPatientName()\n    {\n        // Handle empty before using one retained generator.\n        return null;\n    }\n}\n'
random_driver = driver('RandomCheck','''ClinicSchedule schedule = new ClinicSchedule();
System.out.println(schedule.randomPatientName());
Appointment ben = new Appointment("Ben", 20);
schedule.addAppointment(new Appointment("Ana", 15));
schedule.addAppointment(ben);
schedule.addAppointment(new Appointment("Cara", 10));
ben.checkIn();
System.out.println(schedule.randomPatientName());
System.out.println(schedule.randomPatientName());
System.out.println(schedule.randomPatientName());
System.out.println(schedule.getCount());
System.out.println(schedule.countWaiting());
System.out.println(schedule.totalWaitingMinutes());
System.out.println(schedule.findPatientIndex("ANA"));
System.out.println(schedule.findPatientIndexIgnoringCase("  ANA  "));
boolean selectedBen = false;
for(int i = 0; i < 100; i++) {
    if("Ben".equals(schedule.randomPatientName())) {
        selectedBen = true;
    }
}
System.out.println(selectedBen);
schedule.checkInAll();
System.out.println(schedule.countWaiting());
schedule.removeCheckedIn();
System.out.println(schedule.randomPatientName());''')
add_code('q23','ClinicSchedule.java',random_starter,PART10['ClinicSchedule.java'], 'null\nCara\nAna\nAna\n3\n2\n25\n-1\n0\ntrue\n0\nnull',
         [file('Appointment.java',PART10['Appointment.java'])]+random_driver,
         [has('import java.util.Random;', 'Import Random explicitly.'),has('private Random randomGenerator;', 'Retain a private generator field.'),has('new Random(42)', 'Use seed 42 for this repeatable demonstration.'),has('nextInt(appointments.size())','Use the current appointment count as the bound.'),has('@return','Document the returned name and empty case.')])
E['q23-why'] = SHORT('The empty check must run before nextInt, so an empty choice consumes no generated value. Three appointments have valid indices 0, 1, and 2. Repeated names are allowed. Selection does not cancel or check in an appointment. Seed 42 is for the demonstration; a normal application can use new Random().')
part10_starter = demo('ClinicDemo','// Print the empty choice, add Ana/15, Ben/20, Cara/10, and check in Ben.\n// Print three choices, the appointment count, and waiting count.')
add_code('q24-demo','ClinicDemo.java',part10_starter,PART10['ClinicDemo.java'],OUTPUT['q24-demo'],context(PART10,'ClinicDemo.java'))
tab('q24', {str(i):blank(line,kind='code',width='25rem') for i,line in enumerate(OUTPUT['q24-demo'].rstrip('\n').splitlines())})
E['q24-why'] = SHORT('The first three indices are 2, 0, and 0, producing Cara, Ana, Ana. Ben remains eligible because selection includes checked-in appointments. Three appointments remain and two are waiting. A caller must check for null before calling a String method, since null refers to no String object.')
E['q25'] = SHORT('(a) The original String is unchanged; store or use the returned uppercase String. (b) NextInt(4) returns 0 through 3, never 4. (c) Use ArrayList<Integer>. (d) No: -1 signals a missing name and is not a valid index. (e) The reply ignores the question\'s meaning. Lecture 11 will use a map to connect a recognised keyword with its specific reply.',rows=5)

# Complete runnable projects, with each supporting class also shown on the page.
example('starting-example','ClinicDemo.java',START['ClinicDemo.java'],OUTPUT['starting-demo'],context(START,'ClinicDemo.java'))
example('part10-example','ClinicDemo.java',PART10['ClinicDemo.java'],OUTPUT['part10-demo'],context(PART10,'ClinicDemo.java'))
help_driver = driver('HelpBotCheck','''HelpBot bot = new HelpBot();
System.out.println(bot.clean("   How do I SUBMIT my work?  "));
System.out.println(bot.replyTo("   "));
System.out.println("General replies: " + bot.numberOfGeneralReplies());
System.out.println("Known reply: " + bot.hasGeneralReply(bot.pickGeneralReply()));
System.out.println("Empty average: " + bot.averageRating());
bot.addRating(5);
bot.addRating(3);
bot.addRating(4);
bot.addRating(0);
bot.addRating(6);
System.out.println("Ratings: " + bot.numberOfRatings());
System.out.println("Average: " + bot.averageRating());''')
example('summary-example','HelpBot.java',HELPBOT,'how do i submit my work?\nPlease type a question.\nGeneral replies: 4\nKnown reply: true\nEmpty average: 0\nRatings: 3\nAverage: 4',help_driver)

old_headers = re.findall(r'^    public [^\n]+\([^\n]*\)', START['ClinicSchedule.java'], re.M)
for eid in ['q12', 'q23']:
    E[eid]['check'] += '\n' + '\n'.join(has(header.strip(), 'Keep the existing clinic operation: ' + header.strip()) for header in old_headers)

DATA = {'id':'lecture-10','course':'COMP 2001','title':'Lecture 10 Workbook',
        'subtitle':'Chapter 6, Part 1: Learning and using library classes','exercises':E}
if __name__ == '__main__':
    target = pathlib.Path(__file__).with_name('exercises.json')
    target.write_text(json.dumps(DATA,indent=2)+'\n')
    kinds = {kind:sum(spec['type']==kind for spec in E.values()) for kind in ['code','table','short','example']}
    print(f'Wrote {target}: {sum(kinds[k] for k in ["code","table","short"])} exercises, {kinds["example"]} runnable examples.')
