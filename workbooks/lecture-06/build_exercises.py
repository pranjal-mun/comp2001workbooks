"""Build workbooks/lecture-06/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-06/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-06

The questions follow the printed Lecture 6 workbook, numbered 1 to 25, and the
model answers are the ones in the solutions edition. The two coding pauses
build the clinic classes step by step. A box that asks for part of a class
starts from the rest of that class, and a small driver class on its classpath
(the `files` list) calls the student's code and prints what comes back; the
runner uses that main when the editor's class has none.
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


def method(source, header):
    """The text of one method in `source`, from its header to its closing brace."""
    start = source.index("    " + header)
    end = source.index("\n    }\n", start) + len("\n    }\n")
    return source[start:end]


SHORT = lambda answer, chars=20, rows=2, xp=2: {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}  # noqa: E731
CODE = {"caseSensitive": True, "width": "26rem"}
E = {}

# ---------------------------------------------------------------- classes
# Track and Playlist as in the slides.
TRACK = '''public class Track
{
    private String title;
    private String artist;
    private int durationSeconds;

    public Track(String title, String artist, int durationSeconds)
    {
        this.title = title;
        this.artist = artist;
        this.durationSeconds = durationSeconds;
    }

    public String getArtist()
    {
        return artist;
    }

    public void printDetails()
    {
        System.out.println(artist + " - " + title);
    }
}
'''
TRACK_FILE = [file("Track.java", TRACK)]

PLAYLIST_TOP = '''import java.util.ArrayList;

public class Playlist
{
    private ArrayList<Track> tracks;

    public Playlist()
    {
        tracks = new ArrayList<>();
    }

    public void addTrack(Track track)
    {
        tracks.add(track);
    }

'''
PRINT_TRACK = '''    public void printTrack(int index)
    {
        if(index >= 0 && index < tracks.size()) {
            Track track = tracks.get(index);
            track.printDetails();
        }
    }
'''
PRINT_TRACK_ANSWER = '''    public void printTrack(int index)
    {
        if(index >= 0 && index < tracks.size()) {
            Track track = tracks.get(index);
            track.printDetails();
        }
        else {
            System.out.println("Invalid index");
        }
    }
'''

# The clinic classes. Appointment and the Part 1 methods come from
# Clinic appointments.md; the fragments asked for in Q9, Q10, Q19 and Q21 are
# the solutions-edition answers.
APPOINTMENT = '''public class Appointment
{
    private String patientName;
    private boolean checkedIn;

    public Appointment(String patientName)
    {
        this.patientName = patientName;
        checkedIn = false;
    }

    public String getPatientName()
    {
        return patientName;
    }

    public boolean hasCheckedIn()
    {
        return checkedIn;
    }

    public void checkIn()
    {
        checkedIn = true;
    }
}
'''
APPOINTMENT_FILE = [file("Appointment.java", APPOINTMENT)]

SCHEDULE_TOP = '''import java.util.ArrayList;

public class ClinicSchedule
{
    private ArrayList<Appointment> appointments;

    public ClinicSchedule()
    {
        appointments = new ArrayList<>();
    }

    public int getCount()
    {
        return appointments.size();
    }

'''
ADD = '''    public void addAppointment(Appointment appointment)
    {
        appointments.add(appointment);
    }
'''
PRINT_AT = '''
    public void printPatientAt(int index)
    {
        if(index < 0 || index >= appointments.size()) {
            System.out.println("Invalid index");
            return;
        }

        System.out.println(appointments.get(index).getPatientName());
    }
'''
CANCEL = '''
    public boolean cancel(int index)
    {
        if(index < 0 || index >= appointments.size()) {
            return false;
        }

        if(appointments.get(index).hasCheckedIn()) {
            return false;
        }

        appointments.remove(index);
        return true;
    }
'''
WAITING = '''
    public void printWaitingPatients()
    {
        boolean found = false;

        for(Appointment appointment : appointments) {
            if(!appointment.hasCheckedIn()) {
                System.out.println(appointment.getPatientName());
                found = true;
            }
        }

        if(!found) {
            System.out.println("No waiting patients");
        }
    }
'''
SCHEDULE_1 = SCHEDULE_TOP + ADD + PRINT_AT + "}\n"
SCHEDULE_2 = SCHEDULE_TOP + ADD + PRINT_AT + CANCEL + WAITING + "}\n"
PAUSE1_FILES = APPOINTMENT_FILE + [file("ClinicSchedule.java", SCHEDULE_1)]
PAUSE2_FILES = APPOINTMENT_FILE + [file("ClinicSchedule.java", SCHEDULE_2)]

DEMO_1 = '''public class ClinicDemo
{
    public static void main(String[] args)
    {
        ClinicSchedule schedule = new ClinicSchedule();
        schedule.addAppointment(new Appointment("Ana"));
        schedule.addAppointment(new Appointment("Ben"));
        schedule.addAppointment(new Appointment("Cara"));

        System.out.println(schedule.getCount());
        schedule.printPatientAt(1);
        schedule.printPatientAt(5);
    }
}
'''
DEMO_2 = '''public class ClinicDemo
{
    public static void main(String[] args)
    {
        ClinicSchedule schedule = new ClinicSchedule();
        Appointment ana = new Appointment("Ana");
        Appointment ben = new Appointment("Ben");
        Appointment cara = new Appointment("Cara");

        schedule.addAppointment(ana);
        schedule.addAppointment(ben);
        schedule.addAppointment(cara);
        ben.checkIn();

        System.out.println(schedule.getCount());
        schedule.printWaitingPatients();

        System.out.println(schedule.cancel(1));
        System.out.println(schedule.cancel(0));
        System.out.println(schedule.cancel(5));

        schedule.printPatientAt(0);
        System.out.println(schedule.getCount());
        schedule.printWaitingPatients();
    }
}
'''

# ---------------------------------------------------------------- Section 1
E["q1"] = {"type": "table", "xp": 1, "blanks": {
    "stmt": {"accept": code_forms('Track northernSky = new Track("Northern Sky", "Nick Drake", 224);'),
             "show": 'Track northernSky = new Track("Northern Sky", "Nick Drake", 224);',
             "placeholder": "one statement", **CODE}}}
E["q2"] = SHORT("`Track`, because it stores the artist for one recording. The playlist can ask that track for its artist.")
E["q3"] = SHORT("The field declaration creates no list object; the field starts as `null`. After the constructor runs, the `Playlist`'s `tracks` field refers to an empty `ArrayList<Track>`, with no `Track` objects created.", rows=3)
E["q4"] = SHORT("The first line compiles. The second fails because `\"Blue Train\"` is a `String`, but this list expects `Track` references.", rows=3)
E["q5"] = {"type": "table", "xp": 1, "blanks": {
    "objects": {"accept": ["1", "one"], "placeholder": "how many?", "show": "1"},
    "elements": {"accept": ["2", "two"], "placeholder": "how many?", "show": "2"}}}

# ---------------------------------------------------------------- Section 2
def list_forms(*names):
    joined = ", ".join(names)
    return [f"[{joined}]", joined, "[" + ",".join(names) + "]", ",".join(names)]


E["q6"] = {"type": "table", "xp": 1, "blanks": {
    "l1": {"accept": list_forms("Ana"), "show": "[Ana]", "placeholder": "list", "width": "12rem"},
    "s1": {"accept": ["1"], "placeholder": "size"},
    "l2": {"accept": list_forms("Ana", "Ben"), "show": "[Ana, Ben]", "placeholder": "list", "width": "12rem"},
    "s2": {"accept": ["2"], "placeholder": "size"},
    "l3": {"accept": list_forms("Ana", "Ben", "Cara"), "show": "[Ana, Ben, Cara]", "placeholder": "list", "width": "12rem"},
    "s3": {"accept": ["3"], "placeholder": "size"}}}
VALID = {"placeholder": "valid / invalid"}
E["q7"] = {"type": "table", "xp": 1, "blanks": {
    "m1": {"accept": ["invalid"], **VALID},
    "z": {"accept": ["valid"], **VALID},
    "two": {"accept": ["valid"], **VALID},
    "three": {"accept": ["invalid"], **VALID},
    "last": {"accept": code_forms("tracks.get(tracks.size() - 1)", "tracks.get(2)"),
             "show": "tracks.get(tracks.size() - 1)", "placeholder": "expression", **CODE}}}

PLAYLIST_DRIVER = driver("PlaylistCheck", '''Playlist playlist = new Playlist();
playlist.addTrack(new Track("Blue Train", "John Coltrane", 643));
playlist.addTrack(new Track("Northern Sky", "Nick Drake", 224));
playlist.printTrack(0);
playlist.printTrack(1);
playlist.printTrack(2);
playlist.printTrack(-1);''')
PLAYLIST_ANSWER = PLAYLIST_TOP + PRINT_TRACK_ANSWER + "}\n"
E["q8"] = {"type": "code", "xp": 3, "minLines": 20, "maxLines": 40, "title": "Playlist.java",
    "starter": PLAYLIST_TOP + PRINT_TRACK + "}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(PLAYLIST_ANSWER, TRACK_FILE + PLAYLIST_DRIVER)}],
    "check": "\n".join([
        has("public void printTrack(int index)", "Keep the header public void printTrack(int index)."),
        has('System.out.println("Invalid index");', 'Print the message with System.out.println("Invalid index");'),
        has("tracks.get(index)", "Keep the call tracks.get(index) for a valid index.")]),
    "answer": b64(PLAYLIST_ANSWER), "files": TRACK_FILE + PLAYLIST_DRIVER}
assert E["q8"]["cases"][0]["expected"] == "John Coltrane - Blue Train\nNick Drake - Northern Sky\nInvalid index\nInvalid index"

# ---------------------------------------------------------------- Coding Pause 1
APPOINTMENT_METHODS = APPOINTMENT[APPOINTMENT.index("    public String getPatientName()"):]
APPOINTMENT_DRIVER = driver("AppointmentCheck", '''Appointment appointment = new Appointment("Ana");
System.out.println(appointment.getPatientName() + ", checked in: " + appointment.hasCheckedIn());
appointment.checkIn();
System.out.println(appointment.getPatientName() + ", checked in: " + appointment.hasCheckedIn());''')
E["q9"] = {"type": "code", "xp": 4, "minLines": 30, "maxLines": 44, "title": "Appointment.java",
    "starter": "public class Appointment\n{\n    // Write the two field declarations and the constructor here.\n\n\n\n\n\n\n\n\n\n\n" + APPOINTMENT_METHODS,
    "cases": [{"name": "Output of the checking program", "expected": run(APPOINTMENT, APPOINTMENT_DRIVER)}],
    "check": "\n".join([
        has("private String patientName;", "Declare private String patientName;"),
        has("private boolean checkedIn;", "Declare private boolean checkedIn;"),
        matches(r".*publicAppointment\(String\w+\).*", "The constructor takes the name: public Appointment(String patientName)."),
        lacks("new ArrayList", "Appointment stores one patient; it does not need a list.")]),
    "answer": b64(APPOINTMENT), "files": APPOINTMENT_DRIVER}
assert E["q9"]["cases"][0]["expected"] == "Ana, checked in: false\nAna, checked in: true"

SCHEDULE_Q10 = SCHEDULE_TOP + ADD + "}\n"
COUNT_DRIVER = driver("ScheduleCheck", '''ClinicSchedule schedule = new ClinicSchedule();
System.out.println("New schedule: " + schedule.getCount());
schedule.addAppointment(new Appointment("Ana"));
schedule.addAppointment(new Appointment("Ben"));
schedule.addAppointment(new Appointment("Cara"));
System.out.println("After three additions: " + schedule.getCount());''')
E["q10"] = {"type": "code", "xp": 5, "minLines": 26, "maxLines": 40, "title": "ClinicSchedule.java",
    "starter": "// import\n\npublic class ClinicSchedule\n{\n    // field, constructor, and getCount()\n\n\n\n\n\n\n\n\n\n\n\n\n\n" + ADD + "}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_Q10, APPOINTMENT_FILE + COUNT_DRIVER)}],
    "check": "\n".join([
        has("import java.util.ArrayList;", "Start with import java.util.ArrayList;"),
        has("private ArrayList<Appointment> appointments;", "Declare private ArrayList<Appointment> appointments;"),
        has("public ClinicSchedule()", "Include the constructor public ClinicSchedule()."),
        matches(r".*(this\.)?appointments=newArrayList<(Appointment)?>\(\);.*", "Create the list in the constructor: appointments = new ArrayList<>();"),
        has("public int getCount()", "Include public int getCount()."),
        matches(r".*return(this\.)?appointments\.size\(\);.*", "getCount() returns the list's size: return appointments.size();"),
        lacks("private int", "Do not add a separate count field; the list knows its size.")]),
    "answer": b64(SCHEDULE_Q10), "files": APPOINTMENT_FILE + COUNT_DRIVER}
assert E["q10"]["cases"][0]["expected"] == "New schedule: 0\nAfter three additions: 3"

E["q11"] = {"type": "table", "xp": 1, "blanks": {
    "cond": {"accept": code_forms("index >= 0 && index < appointments.size()", "0 <= index && index < appointments.size()",
                                  "index < appointments.size() && index >= 0"),
             "show": "index >= 0 && index < appointments.size()", "placeholder": "condition", **CODE}}}
# Drop code_forms' semicolon variants: this blank is a condition, not a statement.
E["q11"]["blanks"]["cond"]["accept"] = [a for a in E["q11"]["blanks"]["cond"]["accept"] if not a.endswith(";")]

PRINT_AT_DRIVER = driver("PrintPatientCheck", '''ClinicSchedule schedule = new ClinicSchedule();
schedule.printPatientAt(0);
schedule.addAppointment(new Appointment("Ana"));
schedule.addAppointment(new Appointment("Ben"));
schedule.addAppointment(new Appointment("Cara"));
schedule.printPatientAt(0);
schedule.printPatientAt(2);
schedule.printPatientAt(3);
schedule.printPatientAt(-1);''')
E["q11-code"] = {"type": "code", "xp": 4, "minLines": 34, "maxLines": 52, "title": "ClinicSchedule.java",
    "starter": SCHEDULE_TOP + ADD + "\n    // Write printPatientAt(int index) here.\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_1, APPOINTMENT_FILE + PRINT_AT_DRIVER)}],
    "check": "\n".join([
        matches(r".*publicvoidprintPatientAt\(int\w+\).*", "Include public void printPatientAt(int index)."),
        has('System.out.println("Invalid index");', 'Print the message with System.out.println("Invalid index");'),
        has(".getPatientName()", "Print the name with getPatientName()."),
        lacks("for(", "No loop is needed here."),
        lacks("while(", "No loop is needed here.")]),
    "answer": b64(SCHEDULE_1), "files": APPOINTMENT_FILE + PRINT_AT_DRIVER}
assert E["q11-code"]["cases"][0]["expected"] == "Invalid index\nAna\nCara\nInvalid index\nInvalid index"

LINE = {"placeholder": "output line", "caseSensitive": True, "width": "12rem"}
E["q12"] = {"type": "table", "xp": 1, "blanks": {
    "o1": {"accept": ["3"], **LINE},
    "o2": {"accept": ["Ben"], **LINE},
    "o3": {"accept": ["Invalid index"], **LINE}}}
E["q12-demo"] = {"type": "code", "xp": 3, "minLines": 14, "maxLines": 24, "title": "ClinicDemo.java",
    "starter": "public class ClinicDemo\n{\n    public static void main(String[] args)\n    {\n        // Add Ana, Ben, and Cara. Print the count and the patients at indices 1 and 5.\n\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(DEMO_1, PAUSE1_FILES)}],
    "check": "\n".join([
        has("new ClinicSchedule()", "Create the schedule with new ClinicSchedule()."),
        has('new Appointment("Ana")', 'Add Ana with new Appointment("Ana").'),
        has(".getCount()", "Print the count with getCount()."),
        has(".printPatientAt(1)", "Print the patient at index 1 with printPatientAt(1)."),
        has(".printPatientAt(5)", "Try index 5 with printPatientAt(5).")]),
    "answer": b64(DEMO_1), "files": PAUSE1_FILES}
assert E["q12-demo"]["cases"][0]["expected"] == "3\nBen\nInvalid index"

# ---------------------------------------------------------------- Removal
E["q13"] = {"type": "table", "xp": 1, "blanks": {
    "list": {"accept": list_forms("Ben", "Cara"), "show": "[Ben, Cara]", "placeholder": "list", "width": "12rem"},
    "size": {"accept": ["2", "two"], "placeholder": "size", "show": "2"},
    "first": {"accept": ["Ben", "Ben's appointment"], "placeholder": "object", "show": "Ben"}}}
E["q14"] = SHORT("No. Removal takes the reference out of the list; the separate variable still refers to Ana's appointment, so that object remains available.", rows=3)

# ---------------------------------------------------------------- Visiting and selecting
E["q15"] = {"type": "table", "xp": 1, "blanks": {
    "p1": {"accept": ["a"], "placeholder": "object"},
    "p2": {"accept": ["b"], "placeholder": "object"},
    "p3": {"accept": ["c"], "placeholder": "object"},
    "empty": {"accept": ["0", "zero", "none"], "placeholder": "how many?", "show": "0"}}}
E["q16"] = {"type": "table", "xp": 1, "blanks": {
    "three": {"accept": ["3", "three", "all three", "all"], "placeholder": "how many?", "show": "3"},
    "none": {"accept": ["No matching tracks"], "placeholder": "output", "caseSensitive": True, "width": "14rem"}}}

NAMES = ["appointment", "a", "appt", "app", "ap", "current", "x"]
E["q17"] = {"type": "table", "xp": 2, "blanks": {
    "loop": {"accept": code_forms(*[f"Appointment {n} : appointments" for n in NAMES]),
             "show": "Appointment appointment : appointments", "placeholder": "loop header", **CODE},
    "test": {"accept": code_forms(*[f"!{n}.hasCheckedIn()" for n in NAMES] + [f"{n}.hasCheckedIn() == false" for n in NAMES]),
             "show": "!appointment.hasCheckedIn()", "placeholder": "condition", **CODE},
    "print": {"accept": code_forms(*[f"{n}.getPatientName()" for n in NAMES]),
              "show": "appointment.getPatientName()", "placeholder": "what to print", **CODE}}}
for key in ("loop", "test", "print"):
    E["q17"]["blanks"][key]["accept"] = [a for a in E["q17"]["blanks"][key]["accept"] if not a.endswith(";")]
# The table's answer must be a real loop: confirm it prints the unchecked names.
Q17_LOOP = '''for(Appointment appointment : appointments) {
    if(!appointment.hasCheckedIn()) {
        System.out.println(appointment.getPatientName());
    }
}'''
Q17_CHECK = ('import java.util.ArrayList;\npublic class Q17\n{\n    public static void main(String[] args)\n    {\n'
             '        ArrayList<Appointment> appointments = new ArrayList<>();\n'
             '        Appointment ben = new Appointment("Ben");\n        ben.checkIn();\n'
             '        appointments.add(new Appointment("Ana"));\n        appointments.add(ben);\n        appointments.add(new Appointment("Cara"));\n'
             + "\n".join("        " + line for line in Q17_LOOP.splitlines()) + "\n    }\n}\n")
assert run(Q17_CHECK, APPOINTMENT_FILE) == "Ana\nCara"

# ---------------------------------------------------------------- Coding Pause 2
YESNO = {"placeholder": "yes / no"}
BOOL = {"placeholder": "true / false"}
E["q18"] = {"type": "table", "xp": 2, "blanks": {
    "r1": {"accept": ["no"], **YESNO}, "v1": {"accept": ["false"], **BOOL},
    "r2": {"accept": ["no"], **YESNO}, "v2": {"accept": ["false"], **BOOL},
    "r3": {"accept": ["yes"], **YESNO}, "v3": {"accept": ["true"], **BOOL}}}

CANCEL_DRIVER = driver("CancelCheck", '''ClinicSchedule schedule = new ClinicSchedule();
System.out.println("cancel(0) on an empty schedule: " + schedule.cancel(0));
Appointment ana = new Appointment("Ana");
Appointment ben = new Appointment("Ben");
schedule.addAppointment(ana);
schedule.addAppointment(ben);
schedule.addAppointment(new Appointment("Cara"));
ben.checkIn();
System.out.println("cancel(-1): " + schedule.cancel(-1));
System.out.println("cancel(3): " + schedule.cancel(3));
System.out.println("cancel(1), Ben checked in: " + schedule.cancel(1) + ", count " + schedule.getCount());
System.out.println("cancel(0), Ana waiting: " + schedule.cancel(0) + ", count " + schedule.getCount());
schedule.printPatientAt(0);''')
SCHEDULE_Q19 = SCHEDULE_TOP + ADD + PRINT_AT + CANCEL + "}\n"
E["q19"] = {"type": "code", "xp": 6, "minLines": 46, "maxLines": 66, "title": "ClinicSchedule.java",
    "starter": SCHEDULE_TOP + ADD + PRINT_AT + "\n    // Write cancel(int index) here.\n\n\n\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_Q19, APPOINTMENT_FILE + CANCEL_DRIVER)}],
    "check": "\n".join([
        matches(r".*publicbooleancancel\(int\w+\).*", "cancel returns a boolean: public boolean cancel(int index)."),
        has(".hasCheckedIn()", "Test whether the patient has checked in with hasCheckedIn()."),
        matches(r".*(this\.)?appointments\.remove\(\w+\);.*", "Remove the appointment with appointments.remove(index);"),
        lacks("for(", "No loop is needed in cancel."),
        lacks("while(", "No loop is needed in cancel.")]),
    "answer": b64(SCHEDULE_Q19), "files": APPOINTMENT_FILE + CANCEL_DRIVER}
assert E["q19"]["cases"][0]["expected"] == ("cancel(0) on an empty schedule: false\ncancel(-1): false\ncancel(3): false\n"
                                             "cancel(1), Ben checked in: false, count 3\ncancel(0), Ana waiting: true, count 2\nBen")

E["q20"] = SHORT("Start `found` at `false`. Set it to `true` inside the `if` when an unchecked patient's name is printed; do not reset it during the loop.", rows=3)

WAITING_DRIVER = driver("WaitingCheck", '''ClinicSchedule schedule = new ClinicSchedule();
System.out.println("Empty schedule:");
schedule.printWaitingPatients();
Appointment ana = new Appointment("Ana");
Appointment ben = new Appointment("Ben");
Appointment cara = new Appointment("Cara");
schedule.addAppointment(ana);
schedule.addAppointment(ben);
schedule.addAppointment(cara);
ben.checkIn();
System.out.println("Ben checked in:");
schedule.printWaitingPatients();
ana.checkIn();
cara.checkIn();
System.out.println("Everyone checked in:");
schedule.printWaitingPatients();''')
E["q21"] = {"type": "code", "xp": 6, "minLines": 56, "maxLines": 80, "title": "ClinicSchedule.java",
    "starter": SCHEDULE_TOP + ADD + PRINT_AT + CANCEL + "\n    // Write printWaitingPatients() here.\n\n\n\n\n\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_2, APPOINTMENT_FILE + WAITING_DRIVER)}],
    "check": "\n".join([
        has("public void printWaitingPatients()", "Include public void printWaitingPatients()."),
        matches(r".*for\(Appointment\w+:(this\.)?appointments\).*", "Use a for-each loop: for(Appointment appointment : appointments)"),
        has(".hasCheckedIn()", "Select the waiting patients with hasCheckedIn()."),
        has('System.out.println("No waiting patients");', 'Print the message with System.out.println("No waiting patients");')]),
    "answer": b64(SCHEDULE_2), "files": APPOINTMENT_FILE + WAITING_DRIVER}
assert E["q21"]["cases"][0]["expected"] == ("Empty schedule:\nNo waiting patients\nBen checked in:\nAna\nCara\n"
                                             "Everyone checked in:\nNo waiting patients")

E["q22"] = {"type": "table", "xp": 2, "blanks": {
    "ben": {"accept": ["false"], **BOOL},
    "ana": {"accept": ["true"], **BOOL},
    "five": {"accept": ["false"], **BOOL},
    "final": {"accept": list_forms("Ben", "Cara"), "show": "[Ben, Cara]", "placeholder": "list", "width": "12rem"}}}
E["q22-demo"] = {"type": "code", "xp": 4, "minLines": 24, "maxLines": 40, "title": "ClinicDemo.java",
    "starter": "public class ClinicDemo\n{\n    public static void main(String[] args)\n    {\n        // Keep a reference to each appointment so you can check in Ben.\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(DEMO_2, PAUSE2_FILES)}],
    "check": "\n".join([
        matches(r".*Appointment(\w+)=newAppointment\(\"Ben\"\);.*\1\.checkIn\(\);.*", 'Keep Ben\'s reference and check him in: Appointment ben = new Appointment("Ben"); then ben.checkIn();'),
        has(".cancel(1)", "Try cancelling Ben at index 1 with cancel(1)."),
        has(".cancel(0)", "Try cancelling Ana with cancel(0)."),
        has(".cancel(5)", "Try index 5 with cancel(5)."),
        has(".printPatientAt(0)", "Print the patient now at index 0 with printPatientAt(0)."),
        matches(r".*printWaitingPatients\(\).*printWaitingPatients\(\).*", "Call printWaitingPatients() once before and once after cancellation.")]),
    "answer": b64(DEMO_2), "files": PAUSE2_FILES}
assert E["q22-demo"]["cases"][0]["expected"] == "3\nAna\nCara\nfalse\ntrue\nfalse\nBen\n2\nCara"

E["q23"] = {"type": "table", "xp": 1, "blanks": {
    "out": {"accept": ["No waiting patients"], "placeholder": "output", "caseSensitive": True, "width": "14rem"}}}

# ---------------------------------------------------------------- Review
TOOL = {"placeholder": "tool", "width": "10rem"}
E["q24"] = {"type": "table", "xp": 2, "blanks": {
    "a": {"accept": ["size()", "size"], "show": "size()", **TOOL},
    "b": {"accept": ["for-each", "for each", "foreach", "for-each loop", "for each loop"], "show": "for-each", **TOOL},
    "c": {"accept": ["get(index)", "get"], "show": "get(index)", **TOOL},
    "d": {"accept": ["remove(index)", "remove"], "show": "remove(index)", **TOOL}}}
OWNER = {"placeholder": "class", "caseSensitive": True, "width": "10rem"}
E["q25"] = {"type": "table", "xp": 2, "blanks": {
    "a": {"accept": ["Appointment"], **OWNER},
    "b": {"accept": ["ClinicSchedule"], **OWNER},
    "c": {"accept": ["ClinicDemo"], **OWNER}}}

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-06",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 6 Workbook",
    "subtitle": "Chapter 4, Part 1: Collections of objects",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
