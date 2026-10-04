"""Build workbooks/lecture-07/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-07/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-07

The questions follow the printed Lecture 7 workbook. Their ids are q1 to q25,
shown as 1.1 to 8.1 by section, and the model answers are the ones in the
solutions edition. Section 9 adds two complete programs, one box per class. The two coding pauses
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

    public String getTitle()
    {
        return title;
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

PLAYLIST_HEAD = '''import java.util.ArrayList;

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

    public Track getTrack(int index)
    {
        return tracks.get(index);
    }

    public void printAllTracks()
    {
        for(Track track : tracks) {
            track.printDetails();
        }
    }
'''
FIND_INDEX = '''
    public int findFirstTrackIndex(String title)
    {
        int index = 0;
        boolean found = false;
        while(index < tracks.size() && !found) {
            Track track = tracks.get(index);
            if(track.getTitle().equals(title)) {
                found = true;
            }
            else {
                index++;
            }
        }
        if(found) {
            return index;
        }
        return -1;
    }
'''
FIND_TRACK = '''
    public Track findFirstTrack(String title)
    {
        int index = findFirstTrackIndex(title);
        if(index == -1) {
            return null;
        }
        return tracks.get(index);
    }
'''
REMOVE_ARTIST = '''
    public void removeTracksByArtist(String artist)
    {
        Iterator<Track> iterator = tracks.iterator();
        while(iterator.hasNext()) {
            Track track = iterator.next();
            if(track.getArtist().equals(artist)) {
                iterator.remove();
            }
        }
    }
'''
PLAYLIST_SEARCH = PLAYLIST_HEAD + FIND_INDEX + "}\n"
PLAYLIST_LOOKUP = PLAYLIST_HEAD + FIND_INDEX + FIND_TRACK + "}\n"
PLAYLIST_REMOVE = PLAYLIST_HEAD.replace("import java.util.ArrayList;", "import java.util.ArrayList;\nimport java.util.Iterator;") + REMOVE_ARTIST + "}\n"

# The clinic classes: Appointment and the Lecture 6 Part 2 schedule, then the
# Part 3 and Part 4 methods from Clinic appointments L7.md.
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

SCHEDULE_BODY = '''
public class ClinicSchedule
{
    private ArrayList<Appointment> appointments;

    public ClinicSchedule()
    {
        appointments = new ArrayList<>();
    }

    public void addAppointment(Appointment appointment)
    {
        appointments.add(appointment);
    }

    public int getCount()
    {
        return appointments.size();
    }

    public void printPatientAt(int index)
    {
        if(index < 0 || index >= appointments.size()) {
            System.out.println("Invalid index");
            return;
        }

        System.out.println(appointments.get(index).getPatientName());
    }

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
FIND_PATIENT = '''
    public int findPatientIndex(String name)
    {
        int index = 0;
        boolean found = false;

        while(index < appointments.size() && !found) {
            Appointment appointment = appointments.get(index);
            if(appointment.getPatientName().equals(name)) {
                found = true;
            }
            else {
                index++;
            }
        }

        if(found) {
            return index;
        }
        return -1;
    }
'''
REMOVE_CHECKED = '''
    public int removeCheckedIn()
    {
        int removed = 0;
        Iterator<Appointment> iterator = appointments.iterator();

        while(iterator.hasNext()) {
            Appointment appointment = iterator.next();
            if(appointment.hasCheckedIn()) {
                iterator.remove();
                removed++;
            }
        }

        return removed;
    }
'''
IMPORT_1 = "import java.util.ArrayList;\n"
IMPORT_2 = "import java.util.ArrayList;\nimport java.util.Iterator;\n"
SCHEDULE_3 = IMPORT_1 + SCHEDULE_BODY + FIND_PATIENT + "}\n"
SCHEDULE_4 = IMPORT_2 + SCHEDULE_BODY + FIND_PATIENT + REMOVE_CHECKED + "}\n"
PAUSE3_FILES = APPOINTMENT_FILE + [file("ClinicSchedule.java", SCHEDULE_3)]
PAUSE4_FILES = APPOINTMENT_FILE + [file("ClinicSchedule.java", SCHEDULE_4)]

DEMO_3 = '''public class ClinicDemo
{
    public static void main(String[] args)
    {
        ClinicSchedule schedule = new ClinicSchedule();
        System.out.println("Empty search: " + schedule.findPatientIndex("Ana"));

        schedule.addAppointment(new Appointment("Ana"));
        schedule.addAppointment(new Appointment("Ben"));
        schedule.addAppointment(new Appointment("Ana"));

        System.out.println("Ana index: " + schedule.findPatientIndex("Ana"));
        int benIndex = schedule.findPatientIndex("Ben");
        System.out.println("Ben index: " + benIndex);
        System.out.println("Cara index: " + schedule.findPatientIndex("Cara"));

        if(benIndex != -1) {
            schedule.printPatientAt(benIndex);
        }
    }
}
'''
DEMO_4 = '''public class ClinicDemo
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
        ana.checkIn();
        ben.checkIn();

        System.out.println("Before removal: " + schedule.getCount());
        System.out.println("Removed: " + schedule.removeCheckedIn());
        System.out.println("After removal: " + schedule.getCount());
        System.out.println("Waiting patients:");
        schedule.printWaitingPatients();
        System.out.println("Removed again: " + schedule.removeCheckedIn());
    }
}
'''


def no_semi(accept):
    return [a for a in accept if not a.endswith(";")]


LINE = {"placeholder": "output line", "caseSensitive": True, "width": "12rem"}
BOOL = {"placeholder": "true / false"}


def list_forms(*names):
    joined = ", ".join(names)
    return [f"[{joined}]", joined, "[" + ",".join(names) + "]", ",".join(names)]


# ---------------------------------------------------------------- Traversal
E["q1"] = SHORT("Definite iteration processes the set of elements chosen at the start. A search can stop when a match appears, so its stopping position is not known at the start. A failed search is still indefinite.", rows=3)

WHILE_COUNT = '''int count = 0;
while(count < 3) {
    System.out.println(count);
    count++;
}
System.out.println("final: " + count);'''
assert run(WHILE_COUNT) == "0\n1\n2\nfinal: 3"
E["q2"] = {"type": "table", "xp": 1, "blanks": {
    "o1": {"accept": ["0"], **LINE}, "o2": {"accept": ["1"], **LINE}, "o3": {"accept": ["2"], **LINE},
    "final": {"accept": ["3"], "placeholder": "value"},
    "from3": {"accept": ["0", "none", "no output", "nothing"], "placeholder": "how many lines?", "show": "0"}}}

E["q3"] = {"type": "table", "xp": 2, "blanks": {
    "init": {"accept": ["0"], "placeholder": "start", **CODE, "width": "6rem"},
    "cond": {"accept": no_semi(code_forms("index < tracks.size()")), "show": "index < tracks.size()", "placeholder": "condition", **CODE},
    "arg": {"accept": ["index"], "placeholder": "argument", **CODE, "width": "8rem"},
    "upd": {"accept": code_forms("index++", "index = index + 1", "index += 1", "++index"), "show": "index++;", "placeholder": "update", **CODE},
    "last": {"accept": ["3"], "placeholder": "final index"}}}
E["q3-why"] = SHORT("Without the update, a non-empty list keeps printing index 0 forever. An empty list runs zero passes; its index remains 0 and no get call occurs.", rows=2)
Q3_LOOP = '''import java.util.ArrayList;

public class Q3
{
    public static void main(String[] args)
    {
        ArrayList<Track> tracks = new ArrayList<>();
        tracks.add(new Track("Northern Sky", "Nick Drake", 224));
        tracks.add(new Track("Blue Train", "John Coltrane", 643));
        tracks.add(new Track("Teardrop", "Massive Attack", 330));
        int index = 0;
        while(index < tracks.size()) {
            Track track = tracks.get(index);
            System.out.println(index + ": " + track.getTitle());
            index++;
        }
        System.out.println(index);
    }
}
'''
assert run(Q3_LOOP, TRACK_FILE) == "0: Northern Sky\n1: Blue Train\n2: Teardrop\n3"

# ---------------------------------------------------------------- Search
E["q4"] = SHORT("Both conditions must hold to continue. OR would let the loop run after a match or past the end of the list.", rows=3)

STRINGS = '''String a = new String("Teardrop");
String b = new String("Teardrop");
System.out.println(a == b);
System.out.println(a.equals(b));'''
assert run(STRINGS) == "false\ntrue"
E["q5"] = {"type": "table", "xp": 1, "blanks": {
    "l1": {"accept": ["false"], **BOOL}, "l2": {"accept": ["true"], **BOOL}}}
E["q5-why"] = SHORT("Java shares equal string literals, so == may appear to work in a test. Text obtained at run time need not share a reference. Use equals for string contents.", rows=2)

SEARCH_DRIVER = driver("SearchCheck", '''Playlist empty = new Playlist();
System.out.println("Empty list: " + empty.findFirstTrackIndex("Northern Sky"));
Playlist playlist = new Playlist();
playlist.addTrack(new Track("Northern Sky", "Nick Drake", 224));
playlist.addTrack(new Track("Blue Train", "John Coltrane", 643));
playlist.addTrack(new Track("Northern Sky", "Nick Drake", 224));
System.out.println("Northern Sky: " + playlist.findFirstTrackIndex("Northern Sky"));
System.out.println("Blue Train: " + playlist.findFirstTrackIndex("Blue Train"));
System.out.println("So What: " + playlist.findFirstTrackIndex("So What"));''')
E["q6"] = {"type": "code", "xp": 5, "minLines": 44, "maxLines": 64, "title": "Playlist.java",
    "starter": PLAYLIST_HEAD + "\n    public int findFirstTrackIndex(String title)\n    {\n        int index = 0;\n        boolean found = false;\n        // Write the search loop and the two returns here.\n\n\n\n\n\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(PLAYLIST_SEARCH, TRACK_FILE + SEARCH_DRIVER)}],
    "check": "\n".join([
        has("public int findFirstTrackIndex(String title)", "Keep the header public int findFirstTrackIndex(String title)."),
        matches(r".*while\(index<tracks\.size\(\)&&!found\).*", "Continue while index < tracks.size() && !found."),
        has(".getTitle().equals(title)", "Compare the titles with equals: track.getTitle().equals(title)."),
        has("found = true;", "Set found = true; on a match."),
        has("return -1;", "Return -1 when there is no match.")]),
    "answer": b64(PLAYLIST_SEARCH), "files": TRACK_FILE + SEARCH_DRIVER}
assert E["q6"]["cases"][0]["expected"] == "Empty list: -1\nNorthern Sky: 0\nBlue Train: 1\nSo What: -1"
E["q6-why"] = SHORT("On a match, the index must stay at the matching position. Otherwise it moves on to check the next track. On each pass either the index advances or the flag changes, so the loop makes progress.", rows=2)

E["q7"] = {"type": "table", "xp": 3, "blanks": {
    "nc": {"accept": ["1"], "placeholder": "#"}, "ni": {"accept": ["0"], "placeholder": "index"}, "nf": {"accept": ["true"], **BOOL}, "nr": {"accept": ["0"], "placeholder": "return"},
    "bc": {"accept": ["2"], "placeholder": "#"}, "bi": {"accept": ["1"], "placeholder": "index"}, "bf": {"accept": ["true"], **BOOL}, "br": {"accept": ["1"], "placeholder": "return"},
    "sc": {"accept": ["3"], "placeholder": "#"}, "si": {"accept": ["3"], "placeholder": "index"}, "sf": {"accept": ["false"], **BOOL}, "sr": {"accept": ["-1"], "placeholder": "return"},
    "ec": {"accept": ["0"], "placeholder": "#"}, "ei": {"accept": ["0"], "placeholder": "index"}, "ef": {"accept": ["false"], **BOOL}, "er": {"accept": ["-1"], "placeholder": "return"}}}

SEARCH_SETUP = '''        Playlist playlist = new Playlist();
        playlist.addTrack(new Track("Northern Sky", "Nick Drake", 224));
        playlist.addTrack(new Track("Blue Train", "John Coltrane", 643));
        playlist.addTrack(new Track("Teardrop", "Massive Attack", 330));
'''
Q8_ANSWER = '''public class SearchDemo
{
    public static void main(String[] args)
    {
''' + SEARCH_SETUP + '''
        int index = playlist.findFirstTrackIndex("Teardrop");
        if(index != -1) {
            playlist.getTrack(index).printDetails();
        }
        else {
            System.out.println("Track not found");
        }
    }
}
'''
PLAYLIST_SEARCH_FILES = TRACK_FILE + [file("Playlist.java", PLAYLIST_SEARCH)]
E["q8"] = {"type": "code", "xp": 4, "minLines": 18, "maxLines": 30, "title": "SearchDemo.java",
    "starter": "public class SearchDemo\n{\n    public static void main(String[] args)\n    {\n" + SEARCH_SETUP + "\n        // Search for \"Teardrop\" and print its details, or \"Track not found\".\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(Q8_ANSWER, PLAYLIST_SEARCH_FILES)}],
    "check": "\n".join([
        has('findFirstTrackIndex("Teardrop")', 'Search with playlist.findFirstTrackIndex("Teardrop").'),
        has("-1", "Check the result against -1 before using it."),
        has(".getTrack(", "Retrieve the track with playlist.getTrack(index)."),
        has('System.out.println("Track not found");', 'Print "Track not found" when there is no match.')]),
    "answer": b64(Q8_ANSWER), "files": PLAYLIST_SEARCH_FILES}
assert E["q8"]["cases"][0]["expected"] == "Massive Attack - Teardrop"

# ---------------------------------------------------------------- Coding Pause 3
FIND_PATIENT_DRIVER = driver("FindPatientCheck", '''ClinicSchedule schedule = new ClinicSchedule();
System.out.println("Empty schedule: " + schedule.findPatientIndex("Ana"));
schedule.addAppointment(new Appointment("Ana"));
schedule.addAppointment(new Appointment("Ben"));
schedule.addAppointment(new Appointment("Ana"));
System.out.println("Ana: " + schedule.findPatientIndex("Ana"));
System.out.println("Ben: " + schedule.findPatientIndex("Ben"));
System.out.println("Cara: " + schedule.findPatientIndex("Cara"));
System.out.println("ana: " + schedule.findPatientIndex("ana"));''')
E["q9"] = {"type": "code", "xp": 6, "minLines": 80, "maxLines": 104, "title": "ClinicSchedule.java",
    "starter": IMPORT_1 + SCHEDULE_BODY + "\n    // Write findPatientIndex(String name) here.\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_3, APPOINTMENT_FILE + FIND_PATIENT_DRIVER)}],
    "check": "\n".join([
        matches(r".*publicintfindPatientIndex\(String\w+\).*", "Include public int findPatientIndex(String name)."),
        matches(r".*while\(\w+<(this\.)?appointments\.size\(\).*", "Use an indexed while loop: while(index < appointments.size() && !found)."),
        has("boolean found", "Use a boolean found flag."),
        has(".getPatientName().equals(", "Compare the names with equals."),
        has("return -1;", "Return -1 when there is no match.")]),
    "answer": b64(SCHEDULE_3), "files": APPOINTMENT_FILE + FIND_PATIENT_DRIVER}
assert E["q9"]["cases"][0]["expected"] == "Empty schedule: -1\nAna: 0\nBen: 1\nCara: -1\nana: -1"

E["q10"] = {"type": "table", "xp": 2, "blanks": {
    "o1": {"accept": ["Empty search: -1"], **LINE, "width": "14rem"},
    "o2": {"accept": ["Ana index: 0"], **LINE, "width": "14rem"},
    "o3": {"accept": ["Ben index: 1"], **LINE, "width": "14rem"},
    "o4": {"accept": ["Cara index: -1"], **LINE, "width": "14rem"},
    "o5": {"accept": ["Ben"], **LINE, "width": "14rem"}}}
E["q10-demo"] = {"type": "code", "xp": 4, "minLines": 20, "maxLines": 34, "title": "ClinicDemo.java",
    "starter": "public class ClinicDemo\n{\n    public static void main(String[] args)\n    {\n        ClinicSchedule schedule = new ClinicSchedule();\n        // Search an empty schedule, then add Ana, Ben, Ana and search again.\n\n\n\n\n\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(DEMO_3, PAUSE3_FILES)}],
    "check": "\n".join([
        has('findPatientIndex("Ana")', 'Search for Ana with findPatientIndex("Ana").'),
        has('findPatientIndex("Cara")', 'Search for Cara with findPatientIndex("Cara").'),
        has("-1", "Check Ben's result against -1 before calling printPatientAt."),
        has(".printPatientAt(", "Print Ben's name with printPatientAt.")]),
    "answer": b64(DEMO_3), "files": PAUSE3_FILES}
assert E["q10-demo"]["cases"][0]["expected"] == "Empty search: -1\nAna index: 0\nBen index: 1\nCara index: -1\nBen"

# ---------------------------------------------------------------- Iterator
ITER = '''import java.util.ArrayList;
import java.util.Iterator;

public class Q11
{
    public static void main(String[] args)
    {
        ArrayList<String> tracks = new ArrayList<>();
        tracks.add("A");
        tracks.add("B");
        Iterator<String> iterator = tracks.iterator();
        System.out.println(iterator.hasNext());
        System.out.println(iterator.hasNext());
        System.out.println(iterator.next());
        System.out.println(iterator.next());
        System.out.println(iterator.hasNext());
        try {
            iterator.next();
        }
        catch(java.util.NoSuchElementException e) {
            System.out.println("NoSuchElementException");
        }
    }
}
'''
assert run(ITER) == "true\ntrue\nA\nB\nfalse\nNoSuchElementException"
REF = {"placeholder": "result", "width": "14rem"}
E["q11"] = {"type": "table", "xp": 2, "blanks": {
    "h1": {"accept": ["true"], **REF}, "h2": {"accept": ["true"], **REF},
    "n1": {"accept": ["A", "reference to A", "a reference to A"], "show": "reference to A", **REF},
    "n2": {"accept": ["B", "reference to B", "a reference to B"], "show": "reference to B", **REF},
    "h3": {"accept": ["false"], **REF},
    "n3": {"accept": ["NoSuchElementException", "java.util.NoSuchElementException"], "show": "NoSuchElementException", "caseSensitive": True, **REF}}}

E["q12"] = {"type": "table", "xp": 2, "blanks": {
    "make": {"accept": no_semi(code_forms("tracks.iterator()")), "show": "tracks.iterator()", "placeholder": "expression", **CODE},
    "test": {"accept": no_semi(code_forms("iterator.hasNext()")), "show": "iterator.hasNext()", "placeholder": "condition", **CODE},
    "next": {"accept": no_semi(code_forms("iterator.next()")), "show": "iterator.next()", "placeholder": "expression", **CODE},
    "adv": {"accept": ["next", "next()", "iterator.next()"], "show": "next()", "placeholder": "method", **CODE, "width": "10rem"},
    "empty": {"accept": ["0", "zero", "none"], "show": "0", "placeholder": "how many?"}}}

# ---------------------------------------------------------------- Removal
E["q13"] = SHORT("For-each uses an iterator. Removing through the list changes its structure without updating that iterator, so it can throw ConcurrentModificationException. An exception is not guaranteed every time, so one successful run proves nothing.", rows=3)

E["q14"] = {"type": "table", "xp": 2, "blanks": {
    "after": {"accept": list_forms("A", "C", "D"), "show": "[A, C, D]", "placeholder": "list", "width": "10rem"},
    "next": {"accept": ["D", "index 2", "D at index 2"], "show": "D", "placeholder": "track"},
    "skip": {"accept": ["C"], "placeholder": "track"}}}

REMOVE_DRIVER = driver("RemoveCheck", '''Playlist playlist = new Playlist();
playlist.addTrack(new Track("Northern Sky", "Nick Drake", 224));
playlist.addTrack(new Track("Blue Train", "John Coltrane", 643));
playlist.addTrack(new Track("Naima", "John Coltrane", 265));
playlist.addTrack(new Track("Teardrop", "Massive Attack", 330));
playlist.removeTracksByArtist("John Coltrane");
System.out.println("After removing John Coltrane:");
playlist.printAllTracks();
playlist.removeTracksByArtist("Miles Davis");
System.out.println("After removing Miles Davis:");
playlist.printAllTracks();''')
E["q15"] = {"type": "code", "xp": 5, "minLines": 42, "maxLines": 60, "title": "Playlist.java",
    "starter": PLAYLIST_REMOVE[:PLAYLIST_REMOVE.index("        while(")] + "        // Visit the tracks and remove each one by this artist.\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(PLAYLIST_REMOVE, TRACK_FILE + REMOVE_DRIVER)}],
    "check": "\n".join([
        has("import java.util.Iterator;", "Keep import java.util.Iterator;"),
        has("iterator.hasNext()", "Loop while iterator.hasNext()."),
        has("iterator.next()", "Get each track with iterator.next()."),
        has("iterator.remove();", "Remove through the iterator: iterator.remove();"),
        lacks("tracks.remove(", "Do not call tracks.remove while iterating; use iterator.remove().")]),
    "answer": b64(PLAYLIST_REMOVE), "files": TRACK_FILE + REMOVE_DRIVER}
assert E["q15"]["cases"][0]["expected"] == ("After removing John Coltrane:\nNick Drake - Northern Sky\nMassive Attack - Teardrop\n"
                                             "After removing Miles Davis:\nNick Drake - Northern Sky\nMassive Attack - Teardrop")

E["q16"] = {"type": "table", "xp": 2, "blanks": {
    "next": {"accept": ["C"], "placeholder": "track"},
    "left": {"accept": list_forms("A", "D"), "show": "[A, D]", "placeholder": "list", "width": "10rem"},
    "twice": {"accept": ["no", "IllegalStateException", "no, IllegalStateException", "no; IllegalStateException"], "show": "no; IllegalStateException", "placeholder": "yes / no", "width": "14rem"}}}

LOOP = {"placeholder": "loop", "width": "14rem"}
FOREACH = ["for-each", "for each", "foreach", "for-each loop", "for each loop"]
E["q17"] = {"type": "table", "xp": 2, "blanks": {
    "a": {"accept": FOREACH, "show": "for-each", **LOOP},
    "b": {"accept": ["indexed while", "indexed while loop", "index while", "while with an index"], "show": "indexed while", **LOOP},
    "c": {"accept": ["iterator", "iterator with while", "iterator while", "iterator and while", "iterator with a while loop"], "show": "iterator with while", **LOOP},
    "d": {"accept": ["general while", "while", "while loop", "general while loop"], "show": "general while", **LOOP}}}

# ---------------------------------------------------------------- References
LOOKUP_DRIVER = driver("LookupCheck", '''Playlist playlist = new Playlist();
playlist.addTrack(new Track("Northern Sky", "Nick Drake", 224));
playlist.addTrack(new Track("Blue Train", "John Coltrane", 643));
Track found = playlist.findFirstTrack("Blue Train");
found.printDetails();
System.out.println("Same object as index 1: " + (found == playlist.getTrack(1)));
System.out.println("Teardrop is null: " + (playlist.findFirstTrack("Teardrop") == null));''')
E["q18"] = {"type": "code", "xp": 4, "minLines": 52, "maxLines": 72, "title": "Playlist.java",
    "starter": PLAYLIST_HEAD + FIND_INDEX + "\n    public Track findFirstTrack(String title)\n    {\n        int index = findFirstTrackIndex(title);\n        // Return null on failure, or the stored track.\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(PLAYLIST_LOOKUP, TRACK_FILE + LOOKUP_DRIVER)}],
    "check": "\n".join([
        has("public Track findFirstTrack(String title)", "Keep the header public Track findFirstTrack(String title)."),
        has("return null;", "Return null when there is no match."),
        has("tracks.get(index)", "Return the stored reference with tracks.get(index)."),
        lacks("new Track(", "Return the stored track, not a new one.")]),
    "answer": b64(PLAYLIST_LOOKUP), "files": TRACK_FILE + LOOKUP_DRIVER}
assert E["q18"]["cases"][0]["expected"] == "John Coltrane - Blue Train\nSame object as index 1: true\nTeardrop is null: true"
E["q18-why"] = SHORT("The return type is Track, not int, so -1 is not a possible result. null means there is no object to return; it is not a special Track object.", rows=2)

REPAIR_SETUP = '''        Playlist playlist = new Playlist();
        playlist.addTrack(new Track("Northern Sky", "Nick Drake", 224));
        playlist.addTrack(new Track("Blue Train", "John Coltrane", 643));
'''
Q19_ANSWER = '''public class RepairDemo
{
    public static void main(String[] args)
    {
''' + REPAIR_SETUP + '''
        Track result = playlist.findFirstTrack("Teardrop");
        if(result != null) {
            result.printDetails();
        }
        else {
            System.out.println("Track not found");
        }
    }
}
'''
PLAYLIST_LOOKUP_FILES = TRACK_FILE + [file("Playlist.java", PLAYLIST_LOOKUP)]
E["q19"] = {"type": "code", "xp": 4, "minLines": 16, "maxLines": 30, "title": "RepairDemo.java",
    "starter": "public class RepairDemo\n{\n    public static void main(String[] args)\n    {\n" + REPAIR_SETUP + "\n        // Repair this line.\n        playlist.findFirstTrack(\"Teardrop\").printDetails();\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(Q19_ANSWER, PLAYLIST_LOOKUP_FILES)}],
    "check": "\n".join([
        has('findFirstTrack("Teardrop")', 'Keep the lookup findFirstTrack("Teardrop").'),
        has("!= null", "Check the result with != null before calling printDetails."),
        has('System.out.println("Track not found");', 'Print "Track not found" when the lookup returns null.')]),
    "answer": b64(Q19_ANSWER), "files": PLAYLIST_LOOKUP_FILES}
assert E["q19"]["cases"][0]["expected"] == "Track not found"
E["q19-exc"] = {"type": "table", "xp": 1, "blanks": {
    "exc": {"accept": ["NullPointerException", "java.lang.NullPointerException"], "show": "NullPointerException", "caseSensitive": True, "placeholder": "exception", "width": "16rem"}}}

E["q20"] = SHORT("A reference field defaults to null, so calling size through it throws NullPointerException. An empty list is an object and size returns 0. A local variable must be assigned before it is read, or the code does not compile.", rows=3)

E["q21"] = {"type": "table", "xp": 1, "blanks": {
    "stmt": {"accept": code_forms('playlist.addTrack(new Track("So What", "Miles Davis", 545));'),
             "show": 'playlist.addTrack(new Track("So What", "Miles Davis", 545));', "placeholder": "one statement", **CODE}}}
E["q21-why"] = SHORT("The list stores the reference, so the object stays available. Keep a local variable if its name helps or if you will use the reference again.", rows=2)

CHAIN = '''Playlist playlist = new Playlist();
playlist.addTrack(new Track("Teardrop", "Massive Attack", 330));
int length = playlist.getTrack(0).getTitle().length();
System.out.println(length);'''
assert run(CHAIN, PLAYLIST_SEARCH_FILES) == "8"
TYPE = {"placeholder": "type", "caseSensitive": True, "width": "8rem"}
E["q22"] = {"type": "table", "xp": 2, "blanks": {
    "t1": {"accept": ["Track"], **TYPE}, "t2": {"accept": ["String"], **TYPE}, "t3": {"accept": ["int"], **TYPE},
    "value": {"accept": ["8"], "placeholder": "value"}}}
E["q22-why"] = SHORT("getTrack returns Track; getTitle returns String; length returns int, with value 8. If getTrack(0) returns null, the getTitle call throws NullPointerException, because there is no track to call it on.", rows=3)

# ---------------------------------------------------------------- Coding Pause 4
REMOVE_CHECKED_DRIVER = driver("RemoveCheckedCheck", '''ClinicSchedule schedule = new ClinicSchedule();
System.out.println("Empty schedule: " + schedule.removeCheckedIn());
Appointment ana = new Appointment("Ana");
Appointment ben = new Appointment("Ben");
Appointment cara = new Appointment("Cara");
Appointment dev = new Appointment("Dev");
schedule.addAppointment(ana);
schedule.addAppointment(ben);
schedule.addAppointment(cara);
schedule.addAppointment(dev);
ben.checkIn();
cara.checkIn();
System.out.println("Removed Ben and Cara: " + schedule.removeCheckedIn());
System.out.println("Count: " + schedule.getCount());
schedule.printPatientAt(0);
schedule.printPatientAt(1);
System.out.println("Nobody checked in: " + schedule.removeCheckedIn());''')
E["q23"] = {"type": "code", "xp": 6, "minLines": 98, "maxLines": 124, "title": "ClinicSchedule.java",
    "starter": "// imports\n" + IMPORT_1 + SCHEDULE_BODY + FIND_PATIENT + "\n    // Write removeCheckedIn() here.\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_4, APPOINTMENT_FILE + REMOVE_CHECKED_DRIVER)}],
    "check": "\n".join([
        has("import java.util.Iterator;", "Add import java.util.Iterator; above the class."),
        has("public int removeCheckedIn()", "Include public int removeCheckedIn()."),
        has(".iterator()", "Ask the list for an iterator with appointments.iterator()."),
        matches(r".*\w+\.remove\(\);.*", "Remove through the iterator: iterator.remove();"),
        lacks("appointments.remove(appointment)", "Do not remove through the list while iterating.")]),
    "answer": b64(SCHEDULE_4), "files": APPOINTMENT_FILE + REMOVE_CHECKED_DRIVER}
assert E["q23"]["cases"][0]["expected"] == ("Empty schedule: 0\nRemoved Ben and Cara: 2\nCount: 2\nAna\nDev\nNobody checked in: 0")

E["q24"] = {"type": "table", "xp": 2, "blanks": {
    "o1": {"accept": ["Before removal: 3"], **LINE, "width": "14rem"},
    "o2": {"accept": ["Removed: 2"], **LINE, "width": "14rem"},
    "o3": {"accept": ["After removal: 1"], **LINE, "width": "14rem"},
    "o4": {"accept": ["Waiting patients:"], **LINE, "width": "14rem"},
    "o5": {"accept": ["Cara"], **LINE, "width": "14rem"},
    "o6": {"accept": ["Removed again: 0"], **LINE, "width": "14rem"}}}
E["q24-demo"] = {"type": "code", "xp": 4, "minLines": 24, "maxLines": 40, "title": "ClinicDemo.java",
    "starter": "public class ClinicDemo\n{\n    public static void main(String[] args)\n    {\n        // Keep a reference to each appointment so you can check in Ana and Ben.\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": run(DEMO_4, PAUSE4_FILES)}],
    "check": "\n".join([
        matches(r".*Appointment(\w+)=newAppointment\(\"Ana\"\);.*\1\.checkIn\(\);.*", 'Keep Ana\'s reference and check her in: ana.checkIn();'),
        matches(r".*Appointment(\w+)=newAppointment\(\"Ben\"\);.*\1\.checkIn\(\);.*", 'Keep Ben\'s reference and check him in: ben.checkIn();'),
        matches(r".*removeCheckedIn\(\).*removeCheckedIn\(\).*", "Call removeCheckedIn() twice."),
        has(".printWaitingPatients()", "Print the waiting patients with printWaitingPatients().")]),
    "answer": b64(DEMO_4), "files": PAUSE4_FILES}
assert E["q24-demo"]["cases"][0]["expected"] == "Before removal: 3\nRemoved: 2\nAfter removal: 1\nWaiting patients:\nCara\nRemoved again: 0"
E["q24-why"] = SHORT("Adjacent matches expose an index loop that skips an element after removal. The iterator removes both Ana and Ben; Cara remains.", rows=2)

# ---------------------------------------------------------------- Review
YN = {"placeholder": "answer", "width": "10rem"}
E["q25"] = {"type": "table", "xp": 2, "blanks": {
    "a": {"accept": ["no"], "placeholder": "yes / no"},
    "b": {"accept": ["no"], "placeholder": "yes / no"},
    "c": {"accept": ["no"], "placeholder": "yes / no"},
    "d1": {"accept": ["3"], "placeholder": "first call"},
    "d2": {"accept": ["0"], "placeholder": "second call"}}}

# ---------------------------------------------------------------- Section 9: complete programs
# One box per class. The model classes go on the classpath of the later boxes,
# and a hidden driver calls a class that has no main of its own.
BOOK = '''public class Book
{
    private String title;
    private String author;
    private int pages;

    public Book(String title, String author, int pages)
    {
        this.title = title;
        this.author = author;
        this.pages = pages;
    }

    public String getTitle()
    {
        return title;
    }

    public String getAuthor()
    {
        return author;
    }

    public int getPages()
    {
        return pages;
    }

    public void printDetails()
    {
        System.out.println(title + " by " + author + " (" + pages + " pages)");
    }
}
'''
BOOKSHELF = '''import java.util.ArrayList;

public class BookShelf
{
    private ArrayList<Book> books;

    public BookShelf()
    {
        books = new ArrayList<>();
    }

    public void addBook(Book book)
    {
        books.add(book);
    }

    public int findBookIndex(String title)
    {
        int index = 0;
        boolean found = false;
        while(index < books.size() && !found) {
            if(books.get(index).getTitle().equals(title)) {
                found = true;
            }
            else {
                index++;
            }
        }
        if(found) {
            return index;
        }
        return -1;
    }

    public Book findBook(String title)
    {
        int index = findBookIndex(title);
        if(index == -1) {
            return null;
        }
        return books.get(index);
    }

    public void printWithIndices()
    {
        int index = 0;
        while(index < books.size()) {
            System.out.println(index + ": " + books.get(index).getTitle());
            index++;
        }
    }
}
'''
BOOKSHELF_DEMO = '''public class BookShelfDemo
{
    public static void main(String[] args)
    {
        BookShelf shelf = new BookShelf();
        shelf.addBook(new Book("Kindred", "Octavia Butler", 264));
        shelf.addBook(new Book("Dune", "Frank Herbert", 412));
        shelf.addBook(new Book("The Dispossessed", "Ursula Le Guin", 341));

        shelf.printWithIndices();

        Book found = shelf.findBook("Dune");
        if(found != null) {
            found.printDetails();
        }

        Book missing = shelf.findBook("Solaris");
        if(missing == null) {
            System.out.println("Solaris was not found");
        }
    }
}
'''
STUDENT = '''public class Student
{
    private String name;
    private String program;

    public Student(String name, String program)
    {
        this.name = name;
        this.program = program;
    }

    public String getName()
    {
        return name;
    }

    public String getProgram()
    {
        return program;
    }

    public void printDetails()
    {
        System.out.println(name + " - " + program);
    }
}
'''
ROSTER = '''import java.util.ArrayList;
import java.util.Iterator;

public class CourseRoster
{
    private ArrayList<Student> students;

    public CourseRoster()
    {
        students = new ArrayList<>();
    }

    public void enrol(Student student)
    {
        students.add(student);
    }

    public void printAllStudents()
    {
        for(Student student : students) {
            student.printDetails();
        }
    }

    public void removeStudentsFromProgram(String program)
    {
        Iterator<Student> iterator = students.iterator();
        while(iterator.hasNext()) {
            Student student = iterator.next();
            if(student.getProgram().equals(program)) {
                iterator.remove();
            }
        }
    }
}
'''
ROSTER_DEMO = '''public class CourseRosterDemo
{
    public static void main(String[] args)
    {
        CourseRoster roster = new CourseRoster();
        roster.enrol(new Student("Amina", "Computer Science"));
        roster.enrol(new Student("Diego", "Mathematics"));
        roster.enrol(new Student("Hana", "Mathematics"));
        roster.enrol(new Student("Linh", "Business"));

        System.out.println("Before removal:");
        roster.printAllStudents();

        roster.removeStudentsFromProgram("Mathematics");

        System.out.println("After removal:");
        roster.printAllStudents();
    }
}
'''

BOOK_STARTER = '''public class Book
{
    private String title;
    private String author;
    private int pages;

    public Book(String title, String author, int pages)
    {
        // Assign the three fields.
    }

    public String getTitle()
    {
    }

    public String getAuthor()
    {
    }

    public int getPages()
    {
    }

    public void printDetails()
    {
    }
}
'''
BOOKSHELF_STARTER = '''import java.util.ArrayList;

public class BookShelf
{
    private ArrayList<Book> books;

    public BookShelf()
    {
        books = new ArrayList<>();
    }

    public void addBook(Book book)
    {
    }

    public int findBookIndex(String title)
    {
        // Indexed while with a found flag.
    }

    public Book findBook(String title)
    {
        // Use findBookIndex.
    }

    public void printWithIndices()
    {
        // Indexed while.
    }
}
'''
BOOKSHELF_DEMO_STARTER = '''public class BookShelfDemo
{
    public static void main(String[] args)
    {
        BookShelf shelf = new BookShelf();
        // 1. Add the three books as anonymous objects.
        // 2. Print the shelf with indices.
        // 3. Look up "Dune"; if it was found, print its details.
        // 4. Look up "Solaris"; if it was not found, print "Solaris was not found".
    }
}
'''
STUDENT_STARTER = '''public class Student
{
    private String name;
    private String program;

    public Student(String name, String program)
    {
        // Assign the two fields.
    }

    public String getName()
    {
    }

    public String getProgram()
    {
    }

    public void printDetails()
    {
    }
}
'''
ROSTER_STARTER = '''import java.util.ArrayList;
import java.util.Iterator;

public class CourseRoster
{
    private ArrayList<Student> students;

    public CourseRoster()
    {
        students = new ArrayList<>();
    }

    public void enrol(Student student)
    {
    }

    public void printAllStudents()
    {
        // For-each.
    }

    public void removeStudentsFromProgram(String program)
    {
        // Iterator with while.
    }
}
'''
ROSTER_DEMO_STARTER = '''public class CourseRosterDemo
{
    public static void main(String[] args)
    {
        CourseRoster roster = new CourseRoster();
        // 1. Enrol the four students as anonymous objects.
        // 2. Print "Before removal:" and the roster.
        // 3. Remove the Mathematics students.
        // 4. Print "After removal:" and the roster.
    }
}
'''

BOOK_FILE = [file("Book.java", BOOK)]
BOOKSHELF_FILES = BOOK_FILE + [file("BookShelf.java", BOOKSHELF)]
STUDENT_FILE = [file("Student.java", STUDENT)]
ROSTER_FILES = STUDENT_FILE + [file("CourseRoster.java", ROSTER)]

BOOK_DRIVER = driver("BookCheck", '''Book book = new Book("Dune", "Frank Herbert", 412);
System.out.println(book.getTitle());
System.out.println(book.getAuthor());
System.out.println(book.getPages());
book.printDetails();''')
E["p1-book"] = {"type": "code", "xp": 3, "minLines": 34, "maxLines": 44, "title": "Book.java",
    "starter": BOOK_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(BOOK, BOOK_DRIVER)}],
    "check": "\n".join([
        has("public Book(String title, String author, int pages)", "Keep the constructor header Book(String title, String author, int pages)."),
        has("public void printDetails()", "Include public void printDetails().")]),
    "answer": b64(BOOK), "files": BOOK_DRIVER}
assert E["p1-book"]["cases"][0]["expected"] == "Dune\nFrank Herbert\n412\nDune by Frank Herbert (412 pages)"

SHELF_DRIVER = driver("BookShelfCheck", '''BookShelf empty = new BookShelf();
System.out.println("Empty shelf: " + empty.findBookIndex("Dune"));
System.out.println("Empty lookup is null: " + (empty.findBook("Dune") == null));
empty.printWithIndices();
BookShelf shelf = new BookShelf();
Book kindred = new Book("Kindred", "Octavia Butler", 264);
shelf.addBook(kindred);
shelf.addBook(new Book("Dune", "Frank Herbert", 412));
shelf.addBook(new Book("Kindred", "Octavia Butler", 264));
shelf.printWithIndices();
System.out.println("Kindred: " + shelf.findBookIndex("Kindred"));
System.out.println("Dune: " + shelf.findBookIndex("Dune"));
System.out.println("Solaris: " + shelf.findBookIndex("Solaris"));
System.out.println("First Kindred returned: " + (shelf.findBook("Kindred") == kindred));
System.out.println("Solaris is null: " + (shelf.findBook("Solaris") == null));''')
E["p1-shelf"] = {"type": "code", "xp": 6, "minLines": 50, "maxLines": 66, "title": "BookShelf.java",
    "starter": BOOKSHELF_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(BOOKSHELF, BOOK_FILE + SHELF_DRIVER)}],
    "check": "\n".join([
        matches(r".*while\(\w+<(this\.)?books\.size\(\)&&!found\).*", "Search with an indexed while: while(index < books.size() && !found)."),
        has(".getTitle().equals(title)", "Compare the titles with equals."),
        has("return -1;", "Return -1 when no title matches."),
        has("return null;", "Return null from findBook when there is no match."),
        matches(r".*publicBookfindBook\(String\w+\)\{[^}]*findBookIndex\(.*", "Call findBookIndex inside findBook.")]),
    "answer": b64(BOOKSHELF), "files": BOOK_FILE + SHELF_DRIVER}
assert E["p1-shelf"]["cases"][0]["expected"] == ("Empty shelf: -1\nEmpty lookup is null: true\n0: Kindred\n1: Dune\n2: Kindred\n"
    "Kindred: 0\nDune: 1\nSolaris: -1\nFirst Kindred returned: true\nSolaris is null: true")

E["p1-demo"] = {"type": "code", "xp": 4, "minLines": 22, "maxLines": 34, "title": "BookShelfDemo.java",
    "starter": BOOKSHELF_DEMO_STARTER,
    "cases": [{"name": "Program output", "expected": run(BOOKSHELF_DEMO, BOOKSHELF_FILES)}],
    "check": "\n".join([
        has("shelf.addBook(new Book(", "Add each book as an anonymous object: shelf.addBook(new Book(...));"),
        has('findBook("Dune")', 'Look up Dune with shelf.findBook("Dune").'),
        has("null", "Check each lookup result against null before using it.")]),
    "answer": b64(BOOKSHELF_DEMO), "files": BOOKSHELF_FILES}
assert E["p1-demo"]["cases"][0]["expected"] == ("0: Kindred\n1: Dune\n2: The Dispossessed\n"
    "Dune by Frank Herbert (412 pages)\nSolaris was not found")

STUDENT_DRIVER = driver("StudentCheck", '''Student student = new Student("Amina", "Computer Science");
System.out.println(student.getName());
System.out.println(student.getProgram());
student.printDetails();''')
E["p2-student"] = {"type": "code", "xp": 3, "minLines": 28, "maxLines": 38, "title": "Student.java",
    "starter": STUDENT_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(STUDENT, STUDENT_DRIVER)}],
    "check": "\n".join([
        has("public Student(String name, String program)", "Keep the constructor header Student(String name, String program)."),
        has("public void printDetails()", "Include public void printDetails().")]),
    "answer": b64(STUDENT), "files": STUDENT_DRIVER}
assert E["p2-student"]["cases"][0]["expected"] == "Amina\nComputer Science\nAmina - Computer Science"

ROSTER_DRIVER = driver("CourseRosterCheck", '''CourseRoster empty = new CourseRoster();
empty.removeStudentsFromProgram("Mathematics");
empty.printAllStudents();
CourseRoster roster = new CourseRoster();
roster.enrol(new Student("Diego", "Mathematics"));
roster.enrol(new Student("Hana", "Mathematics"));
roster.enrol(new Student("Amina", "Computer Science"));
roster.enrol(new Student("Omar", "Mathematics"));
roster.removeStudentsFromProgram("Mathematics");
System.out.println("After removing Mathematics:");
roster.printAllStudents();
roster.removeStudentsFromProgram("Physics");
System.out.println("After removing Physics:");
roster.printAllStudents();''')
E["p2-roster"] = {"type": "code", "xp": 5, "minLines": 34, "maxLines": 46, "title": "CourseRoster.java",
    "starter": ROSTER_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(ROSTER, STUDENT_FILE + ROSTER_DRIVER)}],
    "check": "\n".join([
        matches(r".*for\(Student\w+:(this\.)?students\).*", "Print the roster with a for-each loop over students."),
        has(".iterator()", "Get an iterator with students.iterator()."),
        has(".hasNext()", "Loop while iterator.hasNext()."),
        has(".remove();", "Remove through the iterator: iterator.remove();"),
        lacks("students.remove(", "Do not call students.remove while iterating; use iterator.remove()."),
        has(".getProgram().equals(program)", "Compare the programs with equals.")]),
    "answer": b64(ROSTER), "files": STUDENT_FILE + ROSTER_DRIVER}
assert E["p2-roster"]["cases"][0]["expected"] == ("After removing Mathematics:\nAmina - Computer Science\n"
    "After removing Physics:\nAmina - Computer Science")

E["p2-demo"] = {"type": "code", "xp": 4, "minLines": 22, "maxLines": 34, "title": "CourseRosterDemo.java",
    "starter": ROSTER_DEMO_STARTER,
    "cases": [{"name": "Program output", "expected": run(ROSTER_DEMO, ROSTER_FILES)}],
    "check": "\n".join([
        has("roster.enrol(new Student(", "Enrol each student as an anonymous object: roster.enrol(new Student(...));"),
        has('removeStudentsFromProgram("Mathematics")', 'Remove with roster.removeStudentsFromProgram("Mathematics").')]),
    "answer": b64(ROSTER_DEMO), "files": ROSTER_FILES}
assert E["p2-demo"]["cases"][0]["expected"] == ("Before removal:\nAmina - Computer Science\nDiego - Mathematics\n"
    "Hana - Mathematics\nLinh - Business\nAfter removal:\nAmina - Computer Science\nLinh - Business")

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-07",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 7 Workbook",
    "subtitle": "Chapter 4, Part 2: Traversal, Search and Removal",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
