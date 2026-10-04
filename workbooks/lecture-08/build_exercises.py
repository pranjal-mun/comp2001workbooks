"""Build workbooks/lecture-08/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-08/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-08

The questions follow the printed Lecture 8 workbook, numbered 1.1 to 10.1
(ids q1 to q25, in the same order), and the model answers are the ones in the
solutions edition. Sections 5 and 9 build the clinic classes step by step
(Parts 5 and 6). Section 11 has two complete programs, one box per class
(ids p1-* and p2-*). A box that asks for
part of a class starts from the rest of that class, and a small driver class
on its classpath (the `files` list) calls the student's code and prints what
comes back; the runner uses that main when the editor's class has none.
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
    forms = [f"[{joined}]", joined, "[" + ",".join(names) + "]", ",".join(names)]
    if len(names) == 2:
        forms.append(f"{names[0]} and {names[1]}")
    elif len(names) > 2:
        forms.append(", ".join(names[:-1]) + ", and " + names[-1])
        forms.append(", ".join(names[:-1]) + " and " + names[-1])
    return forms


SHORT = lambda answer, chars=20, rows=2, xp=2: {"type": "short", "xp": xp, "minChars": chars, "rows": rows, "answer": b64(answer)}  # noqa: E731
CODE = {"caseSensitive": True, "width": "26rem"}
LINE = {"placeholder": "output line", "caseSensitive": True, "width": "14rem"}
BOOL = {"placeholder": "true / false"}
E = {}

# ---------------------------------------------------------------- classes
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

    public int getDurationSeconds()
    {
        return durationSeconds;
    }

    public void printDetails()
    {
        System.out.println(artist + " - " + title + " (" + durationSeconds + " s)");
    }
}
'''
TRACK_FILE = [file("Track.java", TRACK)]

# The five tracks every question starts with, as statements on a list or a playlist.
FIVE = [("Northern Sky", "Nick Drake", 224), ("Blue Train", "John Coltrane", 643), ("Teardrop", "Massive Attack", 330),
        ("Naima", "John Coltrane", 265), ("Angel", "Massive Attack", 379)]


def add_five(target, call, indent="", tracks=FIVE):
    return "".join(f'{indent}{target}.{call}(new Track("{t}", "{a}", {s}));\n' for t, a, s in tracks)


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

    public int getNumberOfTracks()
    {
        return tracks.size();
    }

    public void printAllTracks()
    {
        tracks.forEach(Track::printDetails);
    }
'''
PRINT_TITLES = '''
    public void printAllTitles()
    {
        tracks.forEach((Track track) -> {
            System.out.println(track.getTitle());
        });
    }
'''
REMOVE_TITLE_ITER = '''
    public void removeTracksByTitle(String title)
    {
        Iterator<Track> iterator = tracks.iterator();
        while(iterator.hasNext()) {
            Track track = iterator.next();
            if(track.getTitle().equals(title)) {
                iterator.remove();
            }
        }
    }
'''
REMOVE_TITLE = '''
    public void removeTracksByTitle(String title)
    {
        tracks.removeIf(track -> track.getTitle().equals(title));
    }
'''
PLAYLIST_TITLES = PLAYLIST_HEAD + PRINT_TITLES + "}\n"
PLAYLIST_REMOVE = PLAYLIST_HEAD + REMOVE_TITLE + "}\n"
PLAYLIST_REMOVE_OLD = PLAYLIST_HEAD.replace("import java.util.ArrayList;", "import java.util.ArrayList;\nimport java.util.Iterator;") + REMOVE_TITLE_ITER + "}\n"

# The clinic classes: Appointment and the Lecture 7 Part 4 schedule, then the
# Part 5 and Part 6 methods from Clinic appointments L8.md.
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
REMOVE_CHECKED_ITER = '''
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
REMOVE_CHECKED = '''
    public int removeCheckedIn()
    {
        int before = appointments.size();
        appointments.removeIf(appointment -> appointment.hasCheckedIn());
        return before - appointments.size();
    }
'''
PART5 = '''
    public void printAllPatients()
    {
        appointments.forEach(appointment ->
            System.out.println(appointment.getPatientName()));
    }

    public void checkInAll()
    {
        appointments.forEach(Appointment::checkIn);
    }
'''
CANCEL_PATIENT = '''
    public boolean cancelPatient(String name)
    {
        return appointments.removeIf(appointment ->
            appointment.getPatientName().equals(name)
            && !appointment.hasCheckedIn());
    }
'''
IMPORT_1 = "import java.util.ArrayList;\n"
IMPORT_2 = "import java.util.ArrayList;\nimport java.util.Iterator;\n"
SCHEDULE_4 = IMPORT_2 + SCHEDULE_BODY + REMOVE_CHECKED_ITER + "}\n"
SCHEDULE_5 = IMPORT_2 + SCHEDULE_BODY + REMOVE_CHECKED_ITER + PART5 + "}\n"
SCHEDULE_6A = IMPORT_1 + SCHEDULE_BODY + REMOVE_CHECKED + PART5 + "}\n"
SCHEDULE_6 = IMPORT_1 + SCHEDULE_BODY + REMOVE_CHECKED + PART5 + CANCEL_PATIENT + "}\n"
PAUSE5_FILES = APPOINTMENT_FILE + [file("ClinicSchedule.java", SCHEDULE_5)]
PAUSE6_FILES = APPOINTMENT_FILE + [file("ClinicSchedule.java", SCHEDULE_6)]

DEMO_5 = '''public class ClinicDemo
{
    public static void main(String[] args)
    {
        ClinicSchedule schedule = new ClinicSchedule();
        schedule.addAppointment(new Appointment("Ana"));
        schedule.addAppointment(new Appointment("Ben"));
        schedule.addAppointment(new Appointment("Cara"));

        System.out.println("Patients:");
        schedule.printAllPatients();
        schedule.checkInAll();
        System.out.println("Waiting patients:");
        schedule.printWaitingPatients();
        System.out.println("Count: " + schedule.getCount());
    }
}
'''
DEMO_6 = '''public class ClinicDemo
{
    public static void main(String[] args)
    {
        ClinicSchedule schedule = new ClinicSchedule();
        Appointment ana = new Appointment("Ana");
        schedule.addAppointment(ana);
        schedule.addAppointment(new Appointment("Ben"));
        schedule.addAppointment(new Appointment("Cara"));
        ana.checkIn();

        System.out.println("Cancel Ana: " + schedule.cancelPatient("Ana"));
        System.out.println("Cancel Ben: " + schedule.cancelPatient("Ben"));
        System.out.println("Cancel Ben again: " + schedule.cancelPatient("Ben"));
        System.out.println("Removed: " + schedule.removeCheckedIn());
        System.out.println("Remaining: " + schedule.getCount());
        schedule.printAllPatients();
        System.out.println("Removed again: " + schedule.removeCheckedIn());
    }
}
'''

# A list of the five tracks as the first lines of a main method.
LIST_SETUP = "        ArrayList<Track> tracks = new ArrayList<>();\n" + add_five("tracks", "add", "        ")


def list_program(name, body, imports="import java.util.ArrayList;\n"):
    return f"{imports}\npublic class {name}\n{{\n    public static void main(String[] args)\n    {{\n{LIST_SETUP}{body}    }}\n}}\n"


# ---------------------------------------------------------------- Playlist
E["q1"] = SHORT("All three visit every track once, in list order. The body changes: call printDetails, print getTitle, or print getArtist. The repeated loop structure can stay inside a collection method while we supply the action.", rows=3)

# ---------------------------------------------------------------- Lambdas
E["q2"] = {"type": "table", "xp": 2, "blanks": {
    "params": {"accept": code_forms("(Track song)"), "show": "(Track song)", "placeholder": "parameter list", **CODE, "width": "12rem"},
    "arrow": {"accept": ["->"], "placeholder": "arrow", **CODE, "width": "6rem"},
    "body": {"accept": no_semi(code_forms("{ System.out.println(song.getArtist()); }")), "show": "{ System.out.println(song.getArtist()); }", "placeholder": "body", **CODE}}}
E["q2-why"] = SHORT("The lambda declares song in its own parameter list, so no earlier declaration is needed. The arrow separates the parameters from the body; it does not mean a value is returned. println returns nothing.", rows=2)
E["q3"] = SHORT("A lambda has no name or access modifier, and it writes no return type. It declares no class of its own, fields, or constructor. Writing it does not execute the body; the receiving method decides when to run it. A job needing its own fields, constructor, or identity still needs a class.", rows=3)

# ---------------------------------------------------------------- forEach
E["q4"] = {"type": "table", "xp": 2, "blanks": {
    "param": {"accept": code_forms("Track track"), "show": "Track track", "placeholder": "parameter", **CODE, "width": "12rem"},
    "body": {"accept": code_forms("System.out.println(track.getArtist());"), "show": "System.out.println(track.getArtist());", "placeholder": "statement", **CODE}}}
E["q4-why"] = SHORT("The first version uses external iteration: our loop controls repetition. The second uses internal iteration: forEach runs the loop and supplies each track to the lambda. Repetition still happens.", rows=2)

FOREACH_TRACE = list_program("Q4", '''        tracks.forEach((Track track) -> {
            track.printDetails();
        });
''')
assert run(FOREACH_TRACE, TRACK_FILE) == ("Nick Drake - Northern Sky (224 s)\nJohn Coltrane - Blue Train (643 s)\n"
                                           "Massive Attack - Teardrop (330 s)\nJohn Coltrane - Naima (265 s)\nMassive Attack - Angel (379 s)")
TITLE = {"placeholder": "title", "width": "10rem"}
E["q5"] = {"type": "table", "xp": 2, "blanks": {
    **{f"c{i + 1}": {"accept": [t], **TITLE} for i, (t, _, _) in enumerate(FIVE)},
    "what": {"accept": ["a track reference", "track reference", "a Track reference", "Track reference", "track", "a track", "Track", "a reference", "reference",
                        "a reference to a track", "reference to a track", "a Track"], "show": "a Track reference", "placeholder": "index or track?", "width": "12rem"},
    "empty": {"accept": ["0", "zero", "none"], "show": "0", "placeholder": "calls"}}}

TITLES_DRIVER = driver("TitlesCheck", '''Playlist empty = new Playlist();
System.out.println("Empty playlist:");
empty.printAllTitles();
Playlist playlist = new Playlist();
''' + add_five("playlist", "addTrack") + '''System.out.println("Five tracks:");
playlist.printAllTitles();
System.out.println("Still " + playlist.getNumberOfTracks() + " tracks");''')
E["q6"] = {"type": "code", "xp": 4, "minLines": 34, "maxLines": 50, "title": "Playlist.java",
    "starter": PLAYLIST_HEAD + "\n    public void printAllTitles()\n    {\n        // Use tracks.forEach with a fully written lambda.\n\n\n\n    }\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(PLAYLIST_TITLES, TRACK_FILE + TITLES_DRIVER)}],
    "check": "\n".join([
        has("public void printAllTitles()", "Keep the header public void printAllTitles()."),
        has("tracks.forEach(", "Call tracks.forEach(...)."),
        has("(Track track) ->", "Write the lambda in full: (Track track) -> { ... }."),
        has("track.getTitle()", "Print track.getTitle() for each track."),
        lacks("for(Track", "Let forEach do the loop; do not write a for-each loop.")]),
    "answer": b64(PLAYLIST_TITLES), "files": TRACK_FILE + TITLES_DRIVER}
assert E["q6"]["cases"][0]["expected"] == "Empty playlist:\nFive tracks:\nNorthern Sky\nBlue Train\nTeardrop\nNaima\nAngel\nStill 5 tracks"

# ---------------------------------------------------------------- Syntax
STAGES = ["(track) -> { System.out.println(track.getTitle()); }", "track -> { System.out.println(track.getTitle()); }",
          "track -> System.out.println(track.getTitle())"]
for stage in STAGES:
    assert run(list_program("Stage", f"        tracks.forEach({stage});\n"), TRACK_FILE).count("\n") == 4
E["q7"] = {"type": "table", "xp": 3, "blanks": {
    **{f"s{i + 2}": {"accept": no_semi(code_forms(st)), "show": st, "placeholder": f"stage {i + 2}", **CODE} for i, st in enumerate(STAGES)}}}
E["q7-why"] = SHORT("The list's element type supplies Track. One parameter with its type omitted needs no parentheses. A single method-call expression needs no braces or internal semicolon. In a complete call, the final semicolon still ends tracks.forEach(...);. Expand the last form by restoring these parts in reverse order.", rows=3)

SHORTEN_SETUP = '''        ArrayList<Track> tracks = new ArrayList<>();
''' + add_five("tracks", "add", "        ", FIVE[:2])
Q8_ANSWER = '''import java.util.ArrayList;

public class ShortenDemo
{
    public static void main(String[] args)
    {
''' + SHORTEN_SETUP + '''
        tracks.forEach(track -> {
            System.out.println(track.getTitle());
            System.out.println(track.getArtist());
        });
    }
}
'''
E["q8"] = {"type": "code", "xp": 3, "minLines": 16, "maxLines": 26, "title": "ShortenDemo.java",
    "starter": Q8_ANSWER.replace("tracks.forEach(track -> {", "tracks.forEach((Track track) -> {").replace("\n        tracks.forEach", "\n        // Shorten this call as far as allowed.\n        tracks.forEach"),
    "cases": [{"name": "Program output", "expected": run(Q8_ANSWER, TRACK_FILE)}],
    "check": "\n".join([
        lacks("(Track track)", "Omit the parameter type; the list's element type supplies Track."),
        matches(r".*forEach\(\w+->\{.*", "One parameter without a type needs no parentheses: track -> { ... }."),
        has("System.out.println(track.getTitle());", "Keep both statements, each with its semicolon."),
        has("System.out.println(track.getArtist());", "Keep both statements, each with its semicolon."),
        has("});", "The final semicolon still ends the forEach call.")]),
    "answer": b64(Q8_ANSWER), "files": TRACK_FILE}
assert E["q8"]["cases"][0]["expected"] == "Northern Sky\nNick Drake\nBlue Train\nJohn Coltrane"
E["q8-why"] = SHORT("The two-statement body keeps its braces and both statement semicolons. The final semicolon ends the forEach call. Zero or two parameters must keep parentheses; so must a parameter with a written type.", rows=2)

# ---------------------------------------------------------------- Method references
assert run(list_program("Q9", "        tracks.forEach(Track::printDetails);\n"), TRACK_FILE) == run(FOREACH_TRACE, TRACK_FILE)
E["q9"] = {"type": "table", "xp": 1, "blanks": {
    "ref": {"accept": code_forms("tracks.forEach(Track::printDetails);", "Track::printDetails"), "show": "tracks.forEach(Track::printDetails);", "placeholder": "new call", **CODE}}}
E["q9-why"] = SHORT("forEach supplies each track as the receiver of printDetails. System.out::println would pass each Track object to println; it would not call printDetails. A method reference must name the matching method.", rows=2)

ARTISTS_REF = '''import java.util.ArrayList;

public class Q10
{
    public static void main(String[] args)
    {
        ArrayList<String> artists = new ArrayList<>();
        artists.add("Nick Drake");
        artists.add("John Coltrane");
        artists.forEach(System.out::println);
    }
}
'''
assert run(ARTISTS_REF) == "Nick Drake\nJohn Coltrane"
E["q10"] = {"type": "table", "xp": 2, "blanks": {
    "ref": {"accept": code_forms("artists.forEach(System.out::println);", "System.out::println"), "show": "artists.forEach(System.out::println);", "placeholder": "new call", **CODE},
    "o1": {"accept": ["Nick Drake"], **LINE}, "o2": {"accept": ["John Coltrane"], **LINE}}}
E["q10-why"] = SHORT("forEach supplies each String as the argument to println on System.out.", rows=2)

# ---------------------------------------------------------------- Coding Pause 5
PART5_DRIVER = driver("ActionsCheck", '''ClinicSchedule schedule = new ClinicSchedule();
System.out.println("Empty schedule:");
schedule.printAllPatients();
schedule.checkInAll();
schedule.addAppointment(new Appointment("Ana"));
schedule.addAppointment(new Appointment("Ben"));
schedule.addAppointment(new Appointment("Cara"));
System.out.println("Patients:");
schedule.printAllPatients();
schedule.checkInAll();
System.out.println("Waiting patients:");
schedule.printWaitingPatients();
System.out.println("Count: " + schedule.getCount());''')
E["q11"] = {"type": "code", "xp": 6, "minLines": 110, "maxLines": 136, "title": "ClinicSchedule.java",
    "starter": SCHEDULE_4.rstrip()[:-1] + "\n    // Write printAllPatients() and checkInAll() here.\n\n\n\n\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_5, APPOINTMENT_FILE + PART5_DRIVER)}],
    "check": "\n".join([
        has("public void printAllPatients()", "Include public void printAllPatients()."),
        has("public void checkInAll()", "Include public void checkInAll()."),
        matches(r".*publicvoidprintAllPatients\(\)\{appointments\.forEach\(.*", "In printAllPatients, call appointments.forEach(...) with a lambda."),
        has(".getPatientName()", "Print each appointment's getPatientName()."),
        has("appointments.forEach(Appointment::checkIn);", "In checkInAll, use appointments.forEach(Appointment::checkIn);")]),
    "answer": b64(SCHEDULE_5), "files": APPOINTMENT_FILE + PART5_DRIVER}
assert E["q11"]["cases"][0]["expected"] == "Empty schedule:\nPatients:\nAna\nBen\nCara\nWaiting patients:\nNo waiting patients\nCount: 3"
E["q11-why"] = SHORT("The count stays the same. checkInAll changes each appointment's state. On an empty schedule both actions run zero times and nothing prints.", rows=2)

DEMO5_OUT = run(DEMO_5, PAUSE5_FILES)
assert DEMO5_OUT == "Patients:\nAna\nBen\nCara\nWaiting patients:\nNo waiting patients\nCount: 3"
E["q12"] = {"type": "table", "xp": 2, "blanks": {f"o{i + 1}": {"accept": [line], **LINE} for i, line in enumerate(DEMO5_OUT.split("\n"))}}
E["q12-demo"] = {"type": "code", "xp": 4, "minLines": 16, "maxLines": 30, "title": "ClinicDemo.java",
    "starter": "public class ClinicDemo\n{\n    public static void main(String[] args)\n    {\n        ClinicSchedule schedule = new ClinicSchedule();\n        // Add Ana, Ben, Cara, print them, check everyone in, then print the waiting patients and the count.\n\n\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": DEMO5_OUT}],
    "check": "\n".join([
        has(".printAllPatients()", "Print the names with printAllPatients()."),
        has(".checkInAll()", "Check everyone in with checkInAll()."),
        has(".printWaitingPatients()", "Print the waiting patients with printWaitingPatients()."),
        has(".getCount()", "Print the count with getCount().")]),
    "answer": b64(DEMO_5), "files": PAUSE5_FILES}

# ---------------------------------------------------------------- Predicates
E["q13"] = SHORT("println returns nothing. removeIf needs a predicate that receives one Track and returns boolean. forEach needs an action on one Track and uses no result. The receiving method determines the required shape, called a functional interface in the Java library.", rows=3)

PRED = list_program("Q14", '''        tracks.forEach(track -> System.out.println(track.getDurationSeconds() > 330));
''')
assert run(PRED, TRACK_FILE) == "false\ntrue\nfalse\nfalse\ntrue"
E["q14"] = {"type": "table", "xp": 2, "blanks": {
    **{f"r{i + 1}": {"accept": [str(s > 330).lower()], **BOOL} for i, (_, _, s) in enumerate(FIVE)}}}
E["q14-why"] = SHORT("It only reads the duration and answers a question. It changes nothing by itself. Teardrop, at exactly 330, gives false because > is strict; 379 gives true, as Angel shows.", rows=2)

PREDICATES = ['track -> track.getArtist().equals("John Coltrane")', 'track -> track.getTitle().contains("Blue")',
              "track -> { return track.getDurationSeconds() < 300; }"]
PRED_CHECK = list_program("Q15", "".join(f'''        ArrayList<Track> copy{i} = new ArrayList<>(tracks);
        copy{i}.removeIf(({p}).negate());
        copy{i}.forEach(track -> System.out.print(track.getTitle() + ";"));
        System.out.println();
''' for i, p in enumerate(f"(java.util.function.Predicate<Track>) {p}" for p in PREDICATES)))
assert run(PRED_CHECK, TRACK_FILE) == "Blue Train;Naima;\nBlue Train;\nNorthern Sky;Naima;"
TRACKS = {"placeholder": "matching tracks", "width": "14rem"}
E["q15"] = {"type": "table", "xp": 3, "blanks": {
    "a": {"accept": no_semi(code_forms(PREDICATES[0], '(Track track) -> track.getArtist().equals("John Coltrane")')), "show": PREDICATES[0], "placeholder": "predicate (a)", **CODE},
    "b": {"accept": no_semi(code_forms(PREDICATES[1], '(Track track) -> track.getTitle().contains("Blue")')), "show": PREDICATES[1], "placeholder": "predicate (b)", **CODE},
    "c": {"accept": no_semi(code_forms(PREDICATES[2], "(Track track) -> { return track.getDurationSeconds() < 300; }")), "show": PREDICATES[2], "placeholder": "predicate (c)", **CODE},
    "ma": {"accept": list_forms("Blue Train", "Naima"), "show": "Blue Train, Naima", **TRACKS},
    "mb": {"accept": list_forms("Blue Train"), "show": "Blue Train", **TRACKS},
    "mc": {"accept": list_forms("Northern Sky", "Naima"), "show": "Northern Sky, Naima", **TRACKS}}}
E["q15-why"] = SHORT("No if is needed. A boolean expression can give the answer directly. Use equals for string contents; == compares references.", rows=2)

# ---------------------------------------------------------------- Removal
REMOVE_DRIVER = driver("RemoveCheck", '''Playlist playlist = new Playlist();
''' + add_five("playlist", "addTrack") + '''playlist.removeTracksByTitle("Teardrop");
System.out.println("After removing Teardrop:");
playlist.printAllTracks();
playlist.removeTracksByTitle("So What");
System.out.println("Tracks after removing So What: " + playlist.getNumberOfTracks());''')
E["q16"] = {"type": "code", "xp": 4, "minLines": 30, "maxLines": 50, "title": "Playlist.java",
    "starter": PLAYLIST_REMOVE_OLD.replace("    public void removeTracksByTitle", "    // Rewrite this method with one removeIf call.\n    public void removeTracksByTitle"),
    "cases": [{"name": "Output of the checking program", "expected": run(PLAYLIST_REMOVE, TRACK_FILE + REMOVE_DRIVER)}],
    "check": "\n".join([
        has("public void removeTracksByTitle(String title)", "Keep the header public void removeTracksByTitle(String title)."),
        has("tracks.removeIf(", "Use one tracks.removeIf(...) call."),
        has(".getTitle().equals(title)", "Test each track with track.getTitle().equals(title)."),
        lacks(".iterator()", "removeIf does the traversal; no iterator is needed.")]),
    "answer": b64(PLAYLIST_REMOVE), "files": TRACK_FILE + REMOVE_DRIVER}
assert run(PLAYLIST_REMOVE_OLD, TRACK_FILE + REMOVE_DRIVER) == E["q16"]["cases"][0]["expected"]
assert E["q16"]["cases"][0]["expected"] == ("After removing Teardrop:\nNick Drake - Northern Sky (224 s)\nJohn Coltrane - Blue Train (643 s)\n"
                                             "John Coltrane - Naima (265 s)\nMassive Attack - Angel (379 s)\nTracks after removing So What: 4")
E["q16-why"] = SHORT("removeIf controls traversal and removal; our code supplies the test. Every matching track is removed. Delete the Iterator import if no other method uses it. For Teardrop, four tracks remain.", rows=2)

REMOVE_SHORT = list_program("Q17", '''        boolean changed = tracks.removeIf(track -> track.getArtist().equals("Massive Attack"));
        tracks.forEach(track -> System.out.println(track.getTitle()));
        System.out.println(tracks.size());
        System.out.println(changed);
''')
assert run(REMOVE_SHORT, TRACK_FILE) == "Northern Sky\nBlue Train\nNaima\n3\ntrue"
E["q17"] = {"type": "table", "xp": 3, "blanks": {
    "gone": {"accept": list_forms("Teardrop", "Angel"), "show": "Teardrop, Angel", **TRACKS},
    "left": {"accept": list_forms("Northern Sky", "Blue Train", "Naima"), "show": "Northern Sky, Blue Train, Naima", "placeholder": "survivors", "width": "18rem"},
    "size": {"accept": ["3"], "placeholder": "size"},
    "ret": {"accept": ["true"], **BOOL}}}
E["q17-why"] = SHORT("Their fields stay the same. Northern Sky, Blue Train, and Naima are now at indices 0, 1, and 2; Naima moves from index 3 to index 2.", rows=2)

TABLE_CHECK = '''import java.util.ArrayList;

public class Q18
{
    public static void main(String[] args)
    {
        ArrayList<Track> tracks = new ArrayList<>();
''' + add_five("tracks", "add", "        ") + '''        ArrayList<Track> a = new ArrayList<>(tracks);
        boolean ra = a.removeIf(track -> false);
        ArrayList<Track> b = new ArrayList<>(tracks);
        boolean rb = b.removeIf(track -> true);
        ArrayList<Track> c = new ArrayList<>(tracks);
        boolean rc = c.removeIf(track -> track.getArtist().equals("Nobody At All"));
        ArrayList<Track> d = new ArrayList<>();
        boolean rd = d.removeIf(track -> true);
        System.out.println(a.size() + " " + ra + " " + b.size() + " " + rb + " " + c.size() + " " + rc + " " + d.size() + " " + rd);
    }
}
'''
assert run(TABLE_CHECK, TRACK_FILE) == "5 false 0 true 5 false 0 false"
SIZE = {"placeholder": "size"}
E["q18"] = {"type": "table", "xp": 3, "blanks": {
    "f1": {"accept": ["5"], **SIZE}, "r1": {"accept": ["false"], **BOOL},
    "f2": {"accept": ["0"], **SIZE}, "r2": {"accept": ["true"], **BOOL},
    "f3": {"accept": ["5"], **SIZE}, "r3": {"accept": ["false"], **BOOL},
    "f4": {"accept": ["0"], **SIZE}, "r4": {"accept": ["false"], **BOOL}}}
E["q18-why"] = SHORT("An empty list has no element to remove. The predicate runs zero times and removeIf returns false. Its return value reports whether any removal occurred, not the answer the predicate would give.", rows=2)

LONG = list_program("Q19", '''        int seconds = 300;
        tracks.removeIf(track -> track.getDurationSeconds() > seconds);
        tracks.forEach(track -> System.out.println(track.getTitle()));
        System.out.println(tracks.size());
''')
assert run(LONG, TRACK_FILE) == "Northern Sky\nNaima\n2"
E["q19"] = {"type": "table", "xp": 3, "blanks": {
    "pred": {"accept": no_semi(code_forms("track -> track.getDurationSeconds() > seconds", "(Track track) -> track.getDurationSeconds() > seconds")),
             "show": "track -> track.getDurationSeconds() > seconds", "placeholder": "predicate", **CODE},
    "left": {"accept": list_forms("Northern Sky", "Naima"), "show": "Northern Sky, Naima", **TRACKS},
    "size": {"accept": ["2"], **SIZE},
    "exact": {"accept": ["no", "No", "no, it stays", "no, it remains"], "show": "no", "placeholder": "yes / no"}}}

REPAIR_TAIL = '''        int removed = before - tracks.size();
        System.out.println("Removed: " + removed);
'''
Q20_ANSWER = list_program("RepairDemo", '''        int before = tracks.size();
        tracks.removeIf(track -> track.getDurationSeconds() < 300);
''' + REPAIR_TAIL)
Q20_STARTER = list_program("RepairDemo", '''        int before = tracks.size();
        // Replace this forEach call with removeIf.
        tracks.forEach(track -> {
            if(track.getDurationSeconds() < 300) {
                tracks.remove(track);
            }
        });
''' + REPAIR_TAIL)
assert run_java(Q20_STARTER, (), None, TRACK_FILE)[0] != "ok"
E["q20"] = {"type": "code", "xp": 4, "minLines": 20, "maxLines": 30, "title": "RepairDemo.java",
    "starter": Q20_STARTER,
    "cases": [{"name": "Program output", "expected": run(Q20_ANSWER, TRACK_FILE)}],
    "check": "\n".join([
        has("tracks.removeIf(", "Replace the forEach call with tracks.removeIf(...)."),
        has(".getDurationSeconds() < 300", "Keep the test getDurationSeconds() < 300."),
        lacks("tracks.remove(", "Do not remove from the list inside a forEach action."),
        has("int removed = before - tracks.size();", "Keep the size calculation.")]),
    "answer": b64(Q20_ANSWER), "files": TRACK_FILE}
assert E["q20"]["cases"][0]["expected"] == "Removed: 2"
E["q20-exc"] = {"type": "table", "xp": 1, "blanks": {
    "exc": {"accept": ["ConcurrentModificationException", "java.util.ConcurrentModificationException"], "show": "ConcurrentModificationException", "caseSensitive": True, "placeholder": "exception", "width": "20rem"}}}
E["q20-why"] = SHORT("The original changes the same list's membership during forEach. A run without an exception does not prove it safe. checkInAll changes element state, not membership. The repaired code gives 5 minus 3, so removed is 2. removeIf itself returns a boolean, not this count.", rows=3)

# ---------------------------------------------------------------- Choices
CHOICE = {"placeholder": "choice", "width": "12rem"}
LOOP = ["explicit loop", "an explicit loop", "loop", "a loop", "while", "while loop", "indexed while", "indexed while loop", "for loop", "for-each loop"]
E["q21"] = {"type": "table", "xp": 2, "blanks": {
    "a": {"accept": ["forEach", "foreach", "for-each", "for each", "forEach()"], "show": "forEach", **CHOICE},
    "b": {"accept": ["removeIf", "removeif", "removeIf()"], "show": "removeIf", **CHOICE},
    "c": {"accept": LOOP, "show": "explicit loop", **CHOICE},
    "d": {"accept": LOOP, "show": "explicit loop", **CHOICE}}}
E["q21-why"] = SHORT("(a) forEach, though for-each also works. (b) removeIf. (c) An explicit loop, such as an indexed while. (d) An explicit loop: a lambda cannot change a local variable. An if inside a forEach action can choose what prints, but the action still receives every element.", rows=3)

# ---------------------------------------------------------------- Coding Pause 6
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
schedule.printAllPatients();
System.out.println("Nobody checked in: " + schedule.removeCheckedIn());''')
E["q22"] = {"type": "code", "xp": 5, "minLines": 110, "maxLines": 136, "title": "ClinicSchedule.java",
    "starter": SCHEDULE_5.replace("    public int removeCheckedIn()", "    // Rewrite this method with removeIf.\n    public int removeCheckedIn()"),
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_6A, APPOINTMENT_FILE + REMOVE_CHECKED_DRIVER)}],
    "check": "\n".join([
        has("public int removeCheckedIn()", "Keep the header public int removeCheckedIn()."),
        has("appointments.removeIf(", "Use appointments.removeIf(...)."),
        has(".hasCheckedIn()", "Remove the appointments where hasCheckedIn() is true."),
        matches(r".*return\w+-(this\.)?appointments\.size\(\);.*", "Return the size before minus the size after."),
        lacks(".iterator()", "removeIf does the traversal; remove the iterator loop."),
        lacks("import java.util.Iterator;", "Remove the unused import java.util.Iterator;")]),
    "answer": b64(SCHEDULE_6A), "files": APPOINTMENT_FILE + REMOVE_CHECKED_DRIVER}
assert E["q22"]["cases"][0]["expected"] == "Empty schedule: 0\nRemoved Ben and Cara: 2\nCount: 2\nAna\nDev\nNobody checked in: 0"

CANCEL_DRIVER = driver("CancelCheck", '''ClinicSchedule schedule = new ClinicSchedule();
System.out.println("Empty schedule: " + schedule.cancelPatient("Ben"));
Appointment checkedBen = new Appointment("Ben");
schedule.addAppointment(new Appointment("Ana"));
schedule.addAppointment(new Appointment("Ben"));
schedule.addAppointment(checkedBen);
schedule.addAppointment(new Appointment("Cara"));
schedule.addAppointment(new Appointment("Ben"));
checkedBen.checkIn();
System.out.println("Cancel Dev: " + schedule.cancelPatient("Dev"));
System.out.println("Cancel Ben: " + schedule.cancelPatient("Ben"));
System.out.println("Count: " + schedule.getCount());
System.out.println("Cancel Ben again: " + schedule.cancelPatient("Ben"));
schedule.printAllPatients();''')
E["q23"] = {"type": "code", "xp": 5, "minLines": 110, "maxLines": 136, "title": "ClinicSchedule.java",
    "starter": SCHEDULE_6A.rstrip()[:-1] + "\n    // Write cancelPatient(String name) here.\n\n\n\n\n\n\n\n}\n",
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_6, APPOINTMENT_FILE + CANCEL_DRIVER)}],
    "check": "\n".join([
        matches(r".*publicbooleancancelPatient\(String\w+\).*", "Include public boolean cancelPatient(String name)."),
        has("return appointments.removeIf(", "Return what appointments.removeIf(...) returns."),
        has(".getPatientName().equals(", "Compare the names with equals."),
        has("&&", "Both conditions must hold: use &&."),
        matches(r".*!\w+\.hasCheckedIn\(\).*", "Only remove appointments that have not checked in: !appointment.hasCheckedIn().")]),
    "answer": b64(SCHEDULE_6), "files": APPOINTMENT_FILE + CANCEL_DRIVER}
assert E["q23"]["cases"][0]["expected"] == "Empty schedule: false\nCancel Dev: false\nCancel Ben: true\nCount: 3\nCancel Ben again: false\nAna\nBen\nCara"
E["q23-why"] = SHORT("Both conditions must hold, so use AND. The method returns false for no match or an empty schedule. A checked-in appointment is kept even when its name matches.", rows=2)

DEMO6_OUT = run(DEMO_6, PAUSE6_FILES)
assert DEMO6_OUT == "Cancel Ana: false\nCancel Ben: true\nCancel Ben again: false\nRemoved: 1\nRemaining: 1\nCara\nRemoved again: 0"
E["q24"] = {"type": "table", "xp": 2, "blanks": {f"o{i + 1}": {"accept": [line], **LINE, "width": "16rem"} for i, line in enumerate(DEMO6_OUT.split("\n"))}}
E["q24-demo"] = {"type": "code", "xp": 4, "minLines": 20, "maxLines": 34, "title": "ClinicDemo.java",
    "starter": "public class ClinicDemo\n{\n    public static void main(String[] args)\n    {\n        ClinicSchedule schedule = new ClinicSchedule();\n        // Keep a reference to Ana so you can check her in.\n\n\n\n\n\n\n\n\n\n\n\n\n    }\n}\n",
    "cases": [{"name": "Program output", "expected": DEMO6_OUT}],
    "check": "\n".join([
        matches(r".*Appointment(\w+)=newAppointment\(\"Ana\"\);.*\1\.checkIn\(\);.*", "Keep Ana's reference and check her in: ana.checkIn();"),
        has('cancelPatient("Ana")', 'Cancel Ana with cancelPatient("Ana").'),
        matches(r'.*cancelPatient\("Ben"\).*cancelPatient\("Ben"\).*', "Cancel Ben twice."),
        matches(r".*removeCheckedIn\(\).*removeCheckedIn\(\).*", "Call removeCheckedIn() twice."),
        has(".printAllPatients()", "Print the remaining names with printAllPatients().")]),
    "answer": b64(DEMO_6), "files": PAUSE6_FILES}
E["q24-why"] = SHORT("Cancellation refuses to remove Ana because she has checked in. removeCheckedIn removes her for that same reason. Ben was cancelled, so only Cara remains.", rows=2)

# ---------------------------------------------------------------- Review
E["q25"] = {"type": "table", "xp": 2, "blanks": {
    "a1": {"accept": ["3"], "placeholder": "first call"}, "a2": {"accept": ["0"], "placeholder": "second call"},
    "b1": {"accept": ["true"], **BOOL}, "b2": {"accept": ["false"], **BOOL}}}
E["q25-why"] = SHORT("(b) Only the checked-in Ben remains. (c) Neither; forEach returns nothing. We still need separate steps to select elements, produce a different value from each, and combine values into one result. Lecture 9 uses streams for this. Loops can already solve these tasks.", rows=3)


# ---------------------------------------------------------------- Complete Java programs
# The classes and skeletons are the ones in Section 11 of the printed workbook.
PLANT = '''public class Plant
{
    private String name;
    private int daysSinceWatered;

    public Plant(String name, int daysSinceWatered)
    {
        this.name = name;
        this.daysSinceWatered = daysSinceWatered;
    }

    public String getName()
    {
        return name;
    }

    public int getDaysSinceWatered()
    {
        return daysSinceWatered;
    }

    public void water()
    {
        daysSinceWatered = 0;
    }

    public void printDetails()
    {
        System.out.println(name + " (" + daysSinceWatered + " days)");
    }
}
'''

GREENHOUSE = '''import java.util.ArrayList;

public class Greenhouse
{
    private ArrayList<Plant> plants;

    public Greenhouse()
    {
        plants = new ArrayList<>();
    }

    public void addPlant(Plant plant)
    {
        plants.add(plant);
    }

    public void printAll()
    {
        plants.forEach(Plant::printDetails);
    }

    public void waterAll()
    {
        plants.forEach(Plant::water);
    }

    public void printThirsty(int days)
    {
        plants.forEach(plant -> {
            if(plant.getDaysSinceWatered() >= days) {
                System.out.println(plant.getName());
            }
        });
    }

    public int removeNeglected(int days)
    {
        int before = plants.size();
        plants.removeIf(plant -> plant.getDaysSinceWatered() > days);
        return before - plants.size();
    }
}
'''

GREENHOUSE_DEMO = '''public class GreenhouseDemo
{
    public static void main(String[] args)
    {
        Greenhouse greenhouse = new Greenhouse();
        greenhouse.addPlant(new Plant("Fern", 3));
        greenhouse.addPlant(new Plant("Cactus", 20));
        greenhouse.addPlant(new Plant("Basil", 6));
        greenhouse.addPlant(new Plant("Orchid", 16));

        greenhouse.printAll();
        System.out.println("Thirsty:");
        greenhouse.printThirsty(5);
        System.out.println("Removed: " + greenhouse.removeNeglected(14));
        greenhouse.waterAll();
        greenhouse.printAll();
    }
}
'''

PLANT_STARTER = '''public class Plant
{
    private String name;
    private int daysSinceWatered;

    public Plant(String name, int daysSinceWatered)
    {
        // Assign the two fields.
    }

    public String getName()
    {
    }

    public int getDaysSinceWatered()
    {
    }

    public void water()
    {
    }

    public void printDetails()
    {
    }
}
'''

GREENHOUSE_STARTER = '''import java.util.ArrayList;

public class Greenhouse
{
    private ArrayList<Plant> plants;

    public Greenhouse()
    {
        plants = new ArrayList<>();
    }

    public void addPlant(Plant plant)
    {
    }

    public void printAll()
    {
        // forEach with a method reference.
    }

    public void waterAll()
    {
        // forEach with a method reference.
    }

    public void printThirsty(int days)
    {
        // forEach with a lambda.
    }

    public int removeNeglected(int days)
    {
        // removeIf; return the number removed.
    }
}
'''

GREENHOUSE_DEMO_STARTER = '''public class GreenhouseDemo
{
    public static void main(String[] args)
    {
        Greenhouse greenhouse = new Greenhouse();
        // 1. Add the four plants.
        // 2. Print all plants.
        // 3. Print "Thirsty:" and the plants not watered for at least 5 days.
        // 4. Remove plants neglected for more than 14 days; print "Removed: " and the count.
        // 5. Water all plants and print them again.
    }
}
'''

TASK = '''public class Task
{
    private String description;
    private boolean done;

    public Task(String description)
    {
        this.description = description;
        done = false;
    }

    public String getDescription()
    {
        return description;
    }

    public boolean isDone()
    {
        return done;
    }

    public void complete()
    {
        done = true;
    }

    public void printDetails()
    {
        if(done) {
            System.out.println("[x] " + description);
        }
        else {
            System.out.println("[ ] " + description);
        }
    }
}
'''

TASKLIST = '''import java.util.ArrayList;

public class TaskList
{
    private ArrayList<Task> tasks;

    public TaskList()
    {
        tasks = new ArrayList<>();
    }

    public void addTask(Task task)
    {
        tasks.add(task);
    }

    public void printAll()
    {
        tasks.forEach(Task::printDetails);
    }

    public void completeTask(String description)
    {
        tasks.forEach(task -> {
            if(task.getDescription().equals(description)) {
                task.complete();
            }
        });
    }

    public boolean removeDone()
    {
        return tasks.removeIf(Task::isDone);
    }
}
'''

TASKLIST_DEMO = '''public class TaskListDemo
{
    public static void main(String[] args)
    {
        TaskList list = new TaskList();
        list.addTask(new Task("Buy milk"));
        list.addTask(new Task("Write report"));
        list.addTask(new Task("Pay rent"));
        list.addTask(new Task("Book flights"));

        list.completeTask("Write report");
        list.completeTask("Pay rent");
        list.printAll();
        System.out.println("Removed done tasks: " + list.removeDone());
        System.out.println("Removed again: " + list.removeDone());
        list.printAll();
    }
}
'''

TASK_STARTER = '''public class Task
{
    private String description;
    private boolean done;

    public Task(String description)
    {
        // A new task is not done.
    }

    public String getDescription()
    {
    }

    public boolean isDone()
    {
    }

    public void complete()
    {
    }

    public void printDetails()
    {
        // [x] or [ ], then the description.
    }
}
'''

TASKLIST_STARTER = '''import java.util.ArrayList;

public class TaskList
{
    private ArrayList<Task> tasks;

    public TaskList()
    {
        tasks = new ArrayList<>();
    }

    public void addTask(Task task)
    {
    }

    public void printAll()
    {
        // forEach.
    }

    public void completeTask(String description)
    {
        // forEach with a lambda.
    }

    public boolean removeDone()
    {
        // removeIf with Task::isDone.
    }
}
'''

TASKLIST_DEMO_STARTER = '''public class TaskListDemo
{
    public static void main(String[] args)
    {
        TaskList list = new TaskList();
        // 1. Add the four tasks.
        // 2. Complete "Write report" and "Pay rent", then print all tasks.
        // 3. Print "Removed done tasks: " and the result of removeDone().
        // 4. Print "Removed again: " and the result of removeDone().
        // 5. Print all tasks.
    }
}
'''

PLANT_FILE = [file("Plant.java", PLANT)]
GREENHOUSE_FILES = PLANT_FILE + [file("Greenhouse.java", GREENHOUSE)]
TASK_FILE = [file("Task.java", TASK)]
TASKLIST_FILES = TASK_FILE + [file("TaskList.java", TASKLIST)]

PLANT_DRIVER = driver("PlantCheck", '''Plant plant = new Plant("Fern", 3);
System.out.println(plant.getName());
System.out.println(plant.getDaysSinceWatered());
plant.printDetails();
plant.water();
plant.printDetails();''')
E["p1-plant"] = {"type": "code", "xp": 3, "minLines": 28, "maxLines": 40, "title": "Plant.java",
    "starter": PLANT_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(PLANT, PLANT_DRIVER)}],
    "check": "\n".join([
        has("public Plant(String name, int daysSinceWatered)", "Keep the constructor header Plant(String name, int daysSinceWatered)."),
        has("public void water()", "Include public void water()."),
        has("public void printDetails()", "Include public void printDetails().")]),
    "answer": b64(PLANT), "files": PLANT_DRIVER}
assert E["p1-plant"]["cases"][0]["expected"] == "Fern\n3\nFern (3 days)\nFern (0 days)"

GREENHOUSE_DRIVER = driver("GreenhouseCheck", '''Greenhouse empty = new Greenhouse();
System.out.println("Empty greenhouse:");
empty.printAll();
empty.printThirsty(0);
System.out.println("Removed from empty: " + empty.removeNeglected(0));
Greenhouse greenhouse = new Greenhouse();
greenhouse.addPlant(new Plant("Ivy", 2));
greenhouse.addPlant(new Plant("Aloe", 30));
greenhouse.addPlant(new Plant("Yucca", 25));
greenhouse.addPlant(new Plant("Mint", 7));
System.out.println("Thirsty for 7 or more:");
greenhouse.printThirsty(7);
System.out.println("Removed: " + greenhouse.removeNeglected(7));
greenhouse.printAll();
System.out.println("Removed again: " + greenhouse.removeNeglected(7));
greenhouse.waterAll();
greenhouse.printAll();''')
E["p1-greenhouse"] = {"type": "code", "xp": 6, "minLines": 40, "maxLines": 56, "title": "Greenhouse.java",
    "starter": GREENHOUSE_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(GREENHOUSE, PLANT_FILE + GREENHOUSE_DRIVER)}],
    "check": "\n".join([
        has("plants.forEach(Plant::printDetails)", "Print all plants with plants.forEach(Plant::printDetails);"),
        has("plants.forEach(Plant::water)", "Water all plants with plants.forEach(Plant::water);"),
        has("plants.removeIf(", "Remove the neglected plants with plants.removeIf(...)."),
        lacks("for(", "Use forEach and removeIf; do not write an explicit loop."),
        lacks("while(", "Use forEach and removeIf; do not write an explicit loop.")]),
    "answer": b64(GREENHOUSE), "files": PLANT_FILE + GREENHOUSE_DRIVER}
assert E["p1-greenhouse"]["cases"][0]["expected"] == ("Empty greenhouse:\nRemoved from empty: 0\nThirsty for 7 or more:\nAloe\nYucca\nMint\n"
    "Removed: 2\nIvy (2 days)\nMint (7 days)\nRemoved again: 0\nIvy (0 days)\nMint (0 days)")

E["p1-demo"] = {"type": "code", "xp": 4, "minLines": 16, "maxLines": 28, "title": "GreenhouseDemo.java",
    "starter": GREENHOUSE_DEMO_STARTER,
    "cases": [{"name": "Program output", "expected": run(GREENHOUSE_DEMO, GREENHOUSE_FILES)}],
    "check": "\n".join([
        has("greenhouse.addPlant(new Plant(", "Add each plant as an anonymous object: greenhouse.addPlant(new Plant(...));"),
        has("printThirsty(5)", "Print the plants not watered for at least 5 days with printThirsty(5)."),
        has("removeNeglected(14)", "Remove the plants neglected for more than 14 days with removeNeglected(14).")]),
    "answer": b64(GREENHOUSE_DEMO), "files": GREENHOUSE_FILES}
assert E["p1-demo"]["cases"][0]["expected"] == ("Fern (3 days)\nCactus (20 days)\nBasil (6 days)\nOrchid (16 days)\nThirsty:\n"
    "Cactus\nBasil\nOrchid\nRemoved: 2\nFern (0 days)\nBasil (0 days)")

TASK_DRIVER = driver("TaskCheck", '''Task task = new Task("Pay rent");
System.out.println(task.getDescription());
System.out.println(task.isDone());
task.printDetails();
task.complete();
System.out.println(task.isDone());
task.printDetails();''')
E["p2-task"] = {"type": "code", "xp": 3, "minLines": 30, "maxLines": 44, "title": "Task.java",
    "starter": TASK_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(TASK, TASK_DRIVER)}],
    "check": "\n".join([
        has("public Task(String description)", "Keep the constructor header Task(String description)."),
        has("public boolean isDone()", "Include public boolean isDone()."),
        has("public void complete()", "Include public void complete().")]),
    "answer": b64(TASK), "files": TASK_DRIVER}
assert E["p2-task"]["cases"][0]["expected"] == "Pay rent\nfalse\n[ ] Pay rent\ntrue\n[x] Pay rent"

TASKLIST_DRIVER = driver("TaskListCheck", '''TaskList empty = new TaskList();
System.out.println("Empty list:");
empty.printAll();
empty.completeTask("Walk dog");
System.out.println("Removed from empty: " + empty.removeDone());
TaskList list = new TaskList();
list.addTask(new Task("Walk dog"));
list.addTask(new Task("Call home"));
list.addTask(new Task("Walk dog"));
list.addTask(new Task("Water plants"));
list.completeTask("Walk dog");
list.completeTask("Feed cat");
list.printAll();
System.out.println("Removed done tasks: " + list.removeDone());
list.printAll();
System.out.println("Removed again: " + list.removeDone());''')
E["p2-tasklist"] = {"type": "code", "xp": 6, "minLines": 34, "maxLines": 50, "title": "TaskList.java",
    "starter": TASKLIST_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(TASKLIST, TASK_FILE + TASKLIST_DRIVER)}],
    "check": "\n".join([
        has("tasks.forEach(", "Use tasks.forEach(...) in printAll and completeTask."),
        has(".getDescription().equals(description)", "Compare the descriptions with equals."),
        has("tasks.removeIf(Task::isDone)", "Remove the done tasks with tasks.removeIf(Task::isDone)."),
        has("return tasks.removeIf(", "Return what removeIf returns."),
        lacks("for(", "Use forEach and removeIf; do not write an explicit loop."),
        lacks("while(", "Use forEach and removeIf; do not write an explicit loop.")]),
    "answer": b64(TASKLIST), "files": TASK_FILE + TASKLIST_DRIVER}
assert E["p2-tasklist"]["cases"][0]["expected"] == ("Empty list:\nRemoved from empty: false\n[x] Walk dog\n[ ] Call home\n[x] Walk dog\n"
    "[ ] Water plants\nRemoved done tasks: true\n[ ] Call home\n[ ] Water plants\nRemoved again: false")

E["p2-demo"] = {"type": "code", "xp": 4, "minLines": 16, "maxLines": 28, "title": "TaskListDemo.java",
    "starter": TASKLIST_DEMO_STARTER,
    "cases": [{"name": "Program output", "expected": run(TASKLIST_DEMO, TASKLIST_FILES)}],
    "check": "\n".join([
        has("list.addTask(new Task(", "Add each task as an anonymous object: list.addTask(new Task(...));"),
        has('completeTask("Write report")', 'Complete Write report with list.completeTask("Write report").'),
        has('completeTask("Pay rent")', 'Complete Pay rent with list.completeTask("Pay rent").'),
        has("removeDone()", "Call removeDone() twice and print each result.")]),
    "answer": b64(TASKLIST_DEMO), "files": TASKLIST_FILES}
assert E["p2-demo"]["cases"][0]["expected"] == ("[ ] Buy milk\n[x] Write report\n[x] Pay rent\n[ ] Book flights\n"
    "Removed done tasks: true\nRemoved again: false\n[ ] Buy milk\n[ ] Book flights")

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-08",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 8 Workbook",
    "subtitle": "Chapter 5, Part 1: Lambdas and Collection Methods",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
