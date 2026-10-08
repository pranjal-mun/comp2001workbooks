"""Build workbooks/lecture-09/exercises.json.

Expected outputs are produced by actually compiling and running the code
through the same runner the page uses, so the specs cannot drift from Java's
real behaviour. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-09/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-09

The questions follow the printed Lecture 9 workbook, numbered 1.1 to 10.1,
and the model answers are the ones in the solutions edition. The ids q1 to q25
keep the meaning they had on the first published page (2.1 to 10.1, in the
same order); q26 is the new Question 1.1. Sections 5 and 9 build the clinic
classes step by step (Parts 7 and 8). Section 11 has two complete programs,
one box per class (ids p1-* and p2-*). A box that asks for part of a class
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
TRACK_T = {"accept": ["Track", "Track objects", "Track object", "Tracks", "Track references"], "show": "Track", "placeholder": "type", "width": "9rem"}
STRING_T = {"accept": ["String", "Strings", "String values", "String objects"], "show": "String", "placeholder": "type", "width": "9rem"}
NONE = ["none", "nothing", "(none)", "no names", "-", "nobody"]
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

# The five tracks every question starts with.
FIVE = [("Northern Sky", "Nick Drake", 224), ("Blue Train", "John Coltrane", 643), ("Teardrop", "Massive Attack", 330),
        ("Naima", "John Coltrane", 265), ("Angel", "Massive Attack", 379)]


def add_five(target, call, indent="", tracks=FIVE):
    return "".join(f'{indent}{target}.{call}(new Track("{t}", "{a}", {s}));\n' for t, a, s in tracks)


# The starting Playlist.java from the workbook.
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
        tracks.forEach(t -> t.printDetails());
    }

    public void removeTracksByArtist(String artist)
    {
        tracks.removeIf(t -> t.getArtist().equals(artist));
    }
'''


def playlist(method):
    return PLAYLIST_HEAD + method + "}\n"


def playlist_starter(header, comment):
    return PLAYLIST_HEAD + f"\n    {header}\n    {{\n        // {comment}\n\n\n\n\n    }}\n}}\n"


def playlist_driver(name, body):
    return driver(name, "Playlist playlist = new Playlist();\n" + add_five("playlist", "addTrack") + body)


# The clinic classes: the starting files and the Part 7 and Part 8 methods from Clinic appointments L9.md.
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
APPOINTMENT_8 = '''public class Appointment
{
    private String patientName;
    private boolean checkedIn;
    private int minutes;

    public Appointment(String patientName, int minutes)
    {
        this.patientName = patientName;
        this.minutes = minutes;
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

    public int getMinutes()
    {
        return minutes;
    }
}
'''
SCHEDULE_START = '''import java.util.ArrayList;

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

    public void printAllPatients()
    {
        appointments.forEach(appointment -> System.out.println(appointment.getPatientName()));
    }

    public void checkInAll()
    {
        appointments.forEach(Appointment::checkIn);
    }

    public int removeCheckedIn()
    {
        int before = appointments.size();
        appointments.removeIf(appointment -> appointment.hasCheckedIn());
        return before - appointments.size();
    }

    public boolean cancelPatient(String name)
    {
        return appointments.removeIf(appointment -> appointment.getPatientName().equals(name)
            && !appointment.hasCheckedIn());
    }
'''
PART7 = '''
    public long countWaiting()
    {
        return appointments.stream()
                           .filter(appointment -> !appointment.hasCheckedIn())
                           .count();
    }

    public void printWaitingNames()
    {
        appointments.stream()
                    .filter(appointment -> !appointment.hasCheckedIn())
                    .map(appointment -> appointment.getPatientName())
                    .forEach(name -> System.out.println(name));
    }
'''
PART8 = '''
    public int totalWaitingMinutes()
    {
        return appointments.stream()
                           .filter(appointment -> !appointment.hasCheckedIn())
                           .map(appointment -> appointment.getMinutes())
                           .reduce(0, (total, minutes) -> total + minutes);
    }
'''
SCHEDULE_7 = SCHEDULE_START + PART7 + "}\n"
SCHEDULE_8 = SCHEDULE_START + PART7 + PART8 + "}\n"
PAUSE7_FILES = [file("Appointment.java", APPOINTMENT), file("ClinicSchedule.java", SCHEDULE_7)]
PAUSE8_FILES = [file("Appointment.java", APPOINTMENT_8), file("ClinicSchedule.java", SCHEDULE_8)]

DEMO_7 = '''public class ClinicDemo
{
    public static void main(String[] args)
    {
        ClinicSchedule schedule = new ClinicSchedule();
        System.out.println("Empty waiting count: " + schedule.countWaiting());
        System.out.println("Empty waiting names:");
        schedule.printWaitingNames();

        Appointment ana = new Appointment("Ana");
        Appointment ben = new Appointment("Ben");
        Appointment cara = new Appointment("Cara");
        schedule.addAppointment(ana);
        schedule.addAppointment(ben);
        schedule.addAppointment(cara);
        ben.checkIn();

        System.out.println("Waiting count: " + schedule.countWaiting());
        System.out.println("Waiting names:");
        schedule.printWaitingNames();
        System.out.println("Appointments: " + schedule.getCount());

        schedule.checkInAll();
        System.out.println("After check-in: " + schedule.countWaiting());
        System.out.println("Waiting names after check-in:");
        schedule.printWaitingNames();
        System.out.println("Appointments: " + schedule.getCount());
    }
}
'''
DEMO_8 = '''public class ClinicDemo
{
    public static void main(String[] args)
    {
        ClinicSchedule schedule = new ClinicSchedule();
        System.out.println("Empty waiting minutes: " + schedule.totalWaitingMinutes());

        Appointment ana = new Appointment("Ana", 15);
        Appointment ben = new Appointment("Ben", 20);
        Appointment cara = new Appointment("Cara", 10);
        schedule.addAppointment(ana);
        schedule.addAppointment(ben);
        schedule.addAppointment(cara);
        ben.checkIn();

        System.out.println("Waiting names:");
        schedule.printWaitingNames();
        System.out.println("Waiting count: " + schedule.countWaiting());
        System.out.println("Waiting minutes: " + schedule.totalWaitingMinutes());
        System.out.println("Appointments: " + schedule.getCount());

        schedule.checkInAll();
        System.out.println("After check-in: " + schedule.totalWaitingMinutes());
        System.out.println("Appointments: " + schedule.getCount());
    }
}
'''

# A list of the five tracks as the first lines of a main method.
LIST_SETUP = "        ArrayList<Track> tracks = new ArrayList<>();\n" + add_five("tracks", "add", "        ")


def list_program(name, body, imports="import java.util.ArrayList;\n"):
    return f"{imports}\npublic class {name}\n{{\n    public static void main(String[] args)\n    {{\n{LIST_SETUP}{body}    }}\n}}\n"


def on_list(body):
    return run(list_program("Check", body), TRACK_FILE)


# ---------------------------------------------------------------- Streams
E["q26"] = SHORT("A lambda may read a local variable of the method around it, but it may not assign a new value to it, and this lambda assigns to total. forEach returns nothing (its return type is void), so it can never give back a total as a value. We need a terminal operation that returns a result: reduce, in Section 6.", rows=3)

E["q1"] = SHORT("A stream does not make a stored copy of the list. It has no get operation or index. After a terminal operation, that stream is used up. Call stream() on the original list again to process it again.", rows=3)

LOOP_PRINT = on_list("        for(Track track : tracks) {\n            track.printDetails();\n        }\n")
assert LOOP_PRINT == on_list("        tracks.stream()\n              .forEach(track ->\n                  track.printDetails());\n")
assert LOOP_PRINT.split("\n")[0] == "Nick Drake - Northern Sky (224 s)" and LOOP_PRINT.count("\n") == 4
E["q2"] = {"type": "table", "xp": 2, "blanks": {
    "src": {"accept": code_forms("stream()", "tracks.stream()", "stream"), "show": "stream()", "placeholder": "source", **CODE, "width": "10rem"},
    "term": {"accept": code_forms("forEach", "forEach()", ".forEach"), "show": "forEach", "placeholder": "terminal", **CODE, "width": "10rem"},
    "loop": {"accept": ["5", "five"], "show": "5", **NUM},
    "stream": {"accept": ["5", "five"], "show": "5", **NUM},
    "first": {"accept": ["Northern Sky", "Nick Drake - Northern Sky (224 s)", "Nick Drake - Northern Sky"], "show": "Northern Sky", "placeholder": "title", "width": "12rem"}}}

# ---------------------------------------------------------------- Filtering
BY_ARTIST = '''
    public void printTracksByArtist(String artist)
    {
        tracks.stream()
              .filter(t -> t.getArtist().equals(artist))
              .forEach(t -> t.printDetails());
    }
'''
BY_ARTIST_DRIVER = playlist_driver("ArtistCheck", '''System.out.println("John Coltrane:");
playlist.printTracksByArtist("John Coltrane");
System.out.println("Nobody At All:");
playlist.printTracksByArtist("Nobody At All");
System.out.println("Still " + playlist.getNumberOfTracks() + " tracks");''')
Q3_STARTER = playlist_starter("public void printTracksByArtist(String artist)", "Use tracks.stream(), filter, then forEach.")
E["q3"] = {"type": "code", "xp": 4, "title": "Playlist.java", **box(Q3_STARTER, playlist(BY_ARTIST)),
    "starter": Q3_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(playlist(BY_ARTIST), TRACK_FILE + BY_ARTIST_DRIVER)}],
    "check": "\n".join([
        has("public void printTracksByArtist(String artist)", "Keep the header public void printTracksByArtist(String artist)."),
        has("tracks.stream()", "Start the pipeline with tracks.stream()."),
        has(".filter(", "Select the tracks with filter(...)."),
        has(".getArtist().equals(artist)", "Compare the text with t.getArtist().equals(artist)."),
        has(".forEach(", "End with forEach(...) to print each track."),
        lacks("for(Track", "Use the pipeline; do not write a for-each loop.")]),
    "answer": b64(playlist(BY_ARTIST)), "files": TRACK_FILE + BY_ARTIST_DRIVER}
assert E["q3"]["cases"][0]["expected"] == ("John Coltrane:\nJohn Coltrane - Blue Train (643 s)\nJohn Coltrane - Naima (265 s)\n"
                                           "Nobody At All:\nStill 5 tracks")

FILTER_VS_REMOVE = on_list('''        tracks.stream()
              .filter(t -> t.getDurationSeconds() < 300)
              .forEach(t -> System.out.println(t.getTitle()));
        System.out.println(tracks.size());
        tracks.removeIf(t -> t.getDurationSeconds() < 300);
        tracks.forEach(t -> System.out.println(t.getTitle()));
        System.out.println(tracks.size());
''')
assert FILTER_VS_REMOVE == "Northern Sky\nNaima\n5\nBlue Train\nTeardrop\nAngel\n3"
E["q4"] = {"type": "table", "xp": 3, "blanks": {
    "pass": {"accept": list_forms("Northern Sky", "Naima"), "show": "Northern Sky, Naima", "placeholder": "tracks", "width": "14rem"},
    "fsize": {"accept": ["5"], **NUM},
    "ftype": TRACK_T,
    "left": {"accept": list_forms("Blue Train", "Teardrop", "Angel"), "show": "Blue Train, Teardrop, Angel", "placeholder": "tracks", "width": "18rem"},
    "rsize": {"accept": ["3"], **NUM}}}
E["q4-why"] = SHORT("True means pass onward for filter and delete from the list for removeIf. The filter leaves the list with all 5 tracks.", rows=2)

TWO_FILTERS = '''        tracks.stream()
              .filter(t -> t.getDurationSeconds() > 250)
              .filter(t -> t.getDurationSeconds() < 400)
              .forEach(t -> System.out.println(t.getTitle()));
'''
assert on_list(TWO_FILTERS) == "Teardrop\nNaima\nAngel"
assert on_list(TWO_FILTERS.replace("> 250", "#").replace("< 400", "> 250").replace("#", "< 400")) == "Teardrop\nNaima\nAngel"
E["q5"] = {"type": "table", "xp": 3, "blanks": {
    "f1": {"accept": list_forms("Blue Train", "Teardrop", "Naima", "Angel"), "show": "Blue Train, Teardrop, Naima, Angel", "placeholder": "tracks", "width": "20rem"},
    "f2": {"accept": list_forms("Teardrop", "Naima", "Angel"), "show": "Teardrop, Naima, Angel", "placeholder": "tracks", "width": "20rem"},
    "rev": {"accept": NO, "show": "no", **YESNO}}}
E["q5-why"] = SHORT("Reversing the filters gives the same final tracks in the same order because each predicate only reads the track and changes nothing. Only the tracks between the two filters can differ.", rows=2)

# ---------------------------------------------------------------- Mapping
ALL_TITLES = '''
    public void printAllTitles()
    {
        tracks.stream()
              .map(t -> t.getTitle())
              .forEach(title -> System.out.println(title));
    }
'''
TITLES_DRIVER = driver("TitlesCheck", '''Playlist empty = new Playlist();
System.out.println("Empty playlist:");
empty.printAllTitles();
Playlist playlist = new Playlist();
''' + add_five("playlist", "addTrack") + '''System.out.println("Five tracks:");
playlist.printAllTitles();
System.out.println("Still " + playlist.getNumberOfTracks() + " tracks");''')
Q6_STARTER = playlist_starter("public void printAllTitles()", "Use tracks.stream(), map, then forEach.")
E["q6"] = {"type": "code", "xp": 4, "title": "Playlist.java", **box(Q6_STARTER, playlist(ALL_TITLES)),
    "starter": Q6_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(playlist(ALL_TITLES), TRACK_FILE + TITLES_DRIVER)}],
    "check": "\n".join([
        has("public void printAllTitles()", "Keep the header public void printAllTitles()."),
        has("tracks.stream()", "Start the pipeline with tracks.stream()."),
        has(".map(", "Turn each track into its title with map(...)."),
        has(".getTitle()", "Map each track to getTitle()."),
        has(".forEach(", "End with forEach(...) to print each title."),
        lacks("for(Track", "Use the pipeline; do not write a for-each loop.")]),
    "answer": b64(playlist(ALL_TITLES)), "files": TRACK_FILE + TITLES_DRIVER}
assert E["q6"]["cases"][0]["expected"] == "Empty playlist:\nFive tracks:\nNorthern Sky\nBlue Train\nTeardrop\nNaima\nAngel\nStill 5 tracks"
E["q6-type"] = {"type": "table", "xp": 1, "blanks": {"n": {"accept": ["5", "five"], "show": "5", **NUM}, "type": STRING_T}}

assert run_java(list_program("Broken", "        tracks.stream()\n              .map(track -> track.getTitle())\n              .forEach(track -> track.printDetails());\n"),
                (), None, TRACK_FILE)[0] != "ok"
assert on_list("        tracks.stream()\n              .map(track -> track.getTitle())\n              .forEach(title -> System.out.println(title));\n").count("\n") == 4
E["q7"] = {"type": "table", "xp": 2, "blanks": {
    "fix": {"accept": code_forms(".forEach(title -> System.out.println(title));", ".forEach(System.out::println);",
                                 "forEach(title -> System.out.println(title))", "forEach(System.out::println)",
                                 ".forEach(track -> System.out.println(track));", "forEach(track -> System.out.println(track))"),
            "show": ".forEach(title -> System.out.println(title));", "placeholder": "new last line", **CODE}}}
E["q7-why"] = SHORT("After map, each element is a String. String has no printDetails method. A parameter's name does not determine its type.", rows=2)

BY_ARTIST_TITLES = '''        tracks.stream()
              .filter(t -> t.getArtist().equals("John Coltrane"))
              .map(t -> t.getTitle())
              .forEach(System.out::println);
'''
assert on_list(BY_ARTIST_TITLES) == "Blue Train\nNaima"
E["q8"] = {"type": "table", "xp": 3, "blanks": {
    "fvals": {"accept": list_forms("Blue Train", "Naima"), "show": "Blue Train, Naima", "placeholder": "values", "width": "12rem"},
    "ftype": TRACK_T,
    "mvals": {"accept": list_forms("Blue Train", "Naima") + list_forms('"Blue Train"', '"Naima"'), "show": "\"Blue Train\", \"Naima\"", "placeholder": "values", "width": "12rem"},
    "mtype": STRING_T,
    "o1": {"accept": ["Blue Train"], **LINE}, "o2": {"accept": ["Naima"], **LINE},
    "move": {"accept": NO, "show": "no", **YESNO}}}
E["q8-why"] = SHORT("The filter cannot move after this map unchanged: after map the values are Strings, and String has no getArtist method. System.out::println is the same action as title -> System.out.println(title).", rows=2)

COUNT_BY_ARTIST = '''
    public long countTracksByArtist(String artist)
    {
        return tracks.stream()
                     .filter(t -> t.getArtist().equals(artist))
                     .count();
    }
'''
COUNT_DRIVER = playlist_driver("CountCheck", '''System.out.println("John Coltrane: " + playlist.countTracksByArtist("John Coltrane"));
System.out.println("Nick Drake: " + playlist.countTracksByArtist("Nick Drake"));
System.out.println("Nobody At All: " + playlist.countTracksByArtist("Nobody At All"));
System.out.println("Still " + playlist.getNumberOfTracks() + " tracks");''')
Q9_STARTER = playlist_starter("public ____ countTracksByArtist(String artist)", "Fill in the return type, then filter and count.")
E["q9"] = {"type": "code", "xp": 4, "title": "Playlist.java", **box(Q9_STARTER, playlist(COUNT_BY_ARTIST)),
    "starter": Q9_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(playlist(COUNT_BY_ARTIST), TRACK_FILE + COUNT_DRIVER)}],
    "check": "\n".join([
        has("public long countTracksByArtist(String artist)", "count() returns long, so the header is public long countTracksByArtist(String artist)."),
        has("tracks.stream()", "Start the pipeline with tracks.stream()."),
        has(".filter(", "Select the artist's tracks with filter(...)."),
        has(".getArtist().equals(artist)", "Compare the text with t.getArtist().equals(artist)."),
        has(".count()", "End with count()."),
        lacks("count++", "Let count() do the counting; no counter variable is needed.")]),
    "answer": b64(playlist(COUNT_BY_ARTIST)), "files": TRACK_FILE + COUNT_DRIVER}
assert E["q9"]["cases"][0]["expected"] == "John Coltrane: 2\nNick Drake: 1\nNobody At All: 0\nStill 5 tracks"
E["q9-results"] = {"type": "table", "xp": 2, "blanks": {
    "type": {"accept": ["long"], "show": "long", "caseSensitive": True, "placeholder": "type", "width": "7rem"},
    "jc": {"accept": ["2"], **NUM}, "nd": {"accept": ["1"], **NUM}, "nb": {"accept": ["0"], **NUM}}}

# ---------------------------------------------------------------- Coding Pause 7
PART7_DRIVER = driver("WaitingCheck", '''ClinicSchedule schedule = new ClinicSchedule();
System.out.println("Empty count: " + schedule.countWaiting());
System.out.println("Empty names:");
schedule.printWaitingNames();
Appointment ana = new Appointment("Ana");
Appointment ben = new Appointment("Ben");
Appointment cara = new Appointment("Cara");
Appointment dev = new Appointment("Dev");
schedule.addAppointment(ana);
schedule.addAppointment(ben);
schedule.addAppointment(cara);
schedule.addAppointment(dev);
ben.checkIn();
dev.checkIn();
System.out.println("Waiting count: " + schedule.countWaiting());
System.out.println("Waiting names:");
schedule.printWaitingNames();
System.out.println("Appointments: " + schedule.getCount());
System.out.println("Ben still checked in: " + ben.hasCheckedIn());
schedule.checkInAll();
System.out.println("After check-in: " + schedule.countWaiting());
System.out.println("Names after check-in:");
schedule.printWaitingNames();
System.out.println("Old method:");
schedule.printWaitingPatients();''')
Q10_STARTER = SCHEDULE_START + "\n    // Write countWaiting() and printWaitingNames() here.\n\n\n\n\n\n\n\n\n\n\n\n}\n"
E["q10"] = {"type": "code", "xp": 6, "title": "ClinicSchedule.java", **box(Q10_STARTER, SCHEDULE_7),
    "starter": Q10_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_7, [file("Appointment.java", APPOINTMENT)] + PART7_DRIVER)}],
    "check": "\n".join([
        has("public long countWaiting()", "Include public long countWaiting()."),
        has("public void printWaitingNames()", "Include public void printWaitingNames()."),
        matches(r".*publiclongcountWaiting\(\)\{returnappointments\.stream\(\)\.filter\(.*", "countWaiting returns appointments.stream().filter(...)..."),
        matches(r".*publicvoidprintWaitingNames\(\)\{appointments\.stream\(\)\.filter\(.*", "printWaitingNames starts with appointments.stream().filter(...)."),
        matches(r".*!\w+\.hasCheckedIn\(\).*!\w+\.hasCheckedIn\(\).*!\w+\.hasCheckedIn\(\).*", "Both filters keep the appointments that have not checked in: !appointment.hasCheckedIn()."),
        has(".count();", "End countWaiting with count()."),
        has(".map(", "In printWaitingNames, map each appointment to its name."),
        has(".getPatientName())", "Map to getPatientName()."),
        lacks("waitingCount", "Do not add a count field.")]),
    "answer": b64(SCHEDULE_7), "files": [file("Appointment.java", APPOINTMENT)] + PART7_DRIVER}
assert E["q10"]["cases"][0]["expected"] == ("Empty count: 0\nEmpty names:\nWaiting count: 2\nWaiting names:\nAna\nCara\nAppointments: 4\n"
                                            "Ben still checked in: true\nAfter check-in: 0\nNames after check-in:\nOld method:\nNo waiting patients")
E["q10-types"] = {"type": "table", "xp": 2, "blanks": {
    "pred": {"accept": no_semi(code_forms("appointment -> !appointment.hasCheckedIn()", "!appointment.hasCheckedIn()", "a -> !a.hasCheckedIn()", "!a.hasCheckedIn()")),
             "show": "appointment -> !appointment.hasCheckedIn()", "placeholder": "predicate", **CODE},
    "ftype": {"accept": ["Appointment", "Appointments", "Appointment objects", "Appointment object"], "show": "Appointment", "placeholder": "type", "width": "10rem"},
    "mtype": STRING_T,
    "ctype": {"accept": ["long"], "show": "long", "caseSensitive": True, "placeholder": "type", "width": "7rem"}}}

DEMO7_OUT = run(DEMO_7, PAUSE7_FILES)
assert DEMO7_OUT == ("Empty waiting count: 0\nEmpty waiting names:\nWaiting count: 2\nWaiting names:\nAna\nCara\nAppointments: 3\n"
                     "After check-in: 0\nWaiting names after check-in:\nAppointments: 3")
ANA_CARA = list_forms("Ana", "Cara")
E["q11"] = {"type": "table", "xp": 3, "blanks": {
    "ec": {"accept": ["0"], **NUM}, "en": {"accept": NONE, "show": "none", "placeholder": "names", "width": "9rem"}, "ea": {"accept": ["0"], **NUM},
    "bc": {"accept": ["2"], **NUM}, "bn": {"accept": ANA_CARA, "show": "Ana, Cara", "placeholder": "names", "width": "9rem"}, "ba": {"accept": ["3"], **NUM},
    "ac": {"accept": ["0"], **NUM}, "an": {"accept": NONE, "show": "none", "placeholder": "names", "width": "9rem"}, "aa": {"accept": ["3"], **NUM}}}
Q11_STARTER = "public class ClinicDemo\n{\n    public static void main(String[] args)\n    {\n        ClinicSchedule schedule = new ClinicSchedule();\n        // Follow the three steps above. Keep a reference to Ben so you can check him in.\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n    }\n}\n"
E["q11-demo"] = {"type": "code", "xp": 4, "title": "ClinicDemo.java", **box(Q11_STARTER, DEMO_7, 8),
    "starter": Q11_STARTER,
    "cases": [{"name": "Program output", "expected": DEMO7_OUT}],
    "check": "\n".join([
        matches(r".*Appointment(\w+)=newAppointment\(\"Ben\"\);.*\1\.checkIn\(\);.*", "Keep Ben's reference and check him in: ben.checkIn();"),
        matches(r".*countWaiting\(\).*countWaiting\(\).*countWaiting\(\).*", "Print the waiting count three times with countWaiting()."),
        matches(r".*printWaitingNames\(\).*printWaitingNames\(\).*printWaitingNames\(\).*", "Call printWaitingNames() three times."),
        has(".checkInAll()", "Check everyone in with checkInAll()."),
        has(".getCount()", "Print the appointment count with getCount().")]),
    "answer": b64(DEMO_7), "files": PAUSE7_FILES}

# ---------------------------------------------------------------- Reduction
STREAM_WORDS = ["a stream", "stream", "Stream", "a Stream", "a new stream", "new stream"]
SOURCE_WORDS = STREAM_WORDS + ["stream of the list's elements", "a stream of the list's elements", "a stream of tracks", "stream of tracks"]
FILTER_WORDS = STREAM_WORDS + ["a stream, same type", "stream, same type", "a stream of the same type", "stream of the same type"]
MAP_WORDS = STREAM_WORDS + ["stream, one value per input", "a stream, one value per input", "a stream of new values", "stream of new values"]
KIND = {"placeholder": "kind", "width": "10rem"}
PRODUCES = {"placeholder": "produces", "width": "14rem"}
TERMINAL = ["terminal", "terminal operation", "Terminal"]
INTER = ["intermediate", "intermediate operation", "Intermediate"]
E["q12"] = {"type": "table", "xp": 3, "blanks": {
    "k1": {"accept": ["source", "Source", "the source"], "show": "source", **KIND}, "p1": {"accept": SOURCE_WORDS, "show": "a stream of the list's elements", **PRODUCES},
    "k2": {"accept": INTER, "show": "intermediate", **KIND}, "p2": {"accept": FILTER_WORDS, "show": "a stream, same type, no more elements", **PRODUCES},
    "k3": {"accept": INTER, "show": "intermediate", **KIND}, "p3": {"accept": MAP_WORDS, "show": "a stream, one value per input", **PRODUCES},
    "k4": {"accept": TERMINAL, "show": "terminal", **KIND}, "p4": {"accept": ["nothing", "no value", "void", "none", "an action", "no value; performs an action"], "show": "no value; performs an action", **PRODUCES},
    "k5": {"accept": TERMINAL, "show": "terminal", **KIND}, "p5": {"accept": ["long", "a long", "a long count", "long count"], "show": "long", **PRODUCES},
    "k6": {"accept": TERMINAL, "show": "terminal", **KIND}, "p6": {"accept": ["one value", "a single value", "one combined value", "a value", "single value", "one result", "a single result"], "show": "one combined value", **PRODUCES}}}

TOTAL = '''
    public int totalDuration()
    {
        return tracks.stream()
                     .map(t -> t.getDurationSeconds())
                     .reduce(0, (total, seconds) -> total + seconds);
    }
'''
TOTAL_DRIVER = driver("TotalCheck", '''Playlist empty = new Playlist();
System.out.println("Empty playlist: " + empty.totalDuration());
Playlist playlist = new Playlist();
''' + add_five("playlist", "addTrack") + '''System.out.println("Five tracks: " + playlist.totalDuration());
System.out.println("Still " + playlist.getNumberOfTracks() + " tracks");''')
Q13_STARTER = playlist_starter("public int totalDuration()", "Use tracks.stream(), map to seconds, then reduce(0, ...).")
E["q13"] = {"type": "code", "xp": 4, "title": "Playlist.java", **box(Q13_STARTER, playlist(TOTAL)),
    "starter": Q13_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(playlist(TOTAL), TRACK_FILE + TOTAL_DRIVER)}],
    "check": "\n".join([
        has("public int totalDuration()", "Keep the header public int totalDuration()."),
        has("return tracks.stream()", "Return the result of a pipeline on tracks.stream()."),
        has(".map(", "Map each track to its seconds."),
        has(".getDurationSeconds()", "Map to getDurationSeconds()."),
        has(".reduce(0,", "Reduce with the identity 0: reduce(0, ...)."),
        lacks("for(Track", "Use the pipeline; do not write a loop.")]),
    "answer": b64(playlist(TOTAL)), "files": TRACK_FILE + TOTAL_DRIVER}
assert E["q13"]["cases"][0]["expected"] == "Empty playlist: 0\nFive tracks: 1841\nStill 5 tracks"
E["q13-why"] = SHORT("The accumulator has two parameters, so parentheses are required. The first is the total so far, the second is the next duration. The method returns 1841.", rows=2)

RUNNING = on_list('''        int total = 0;
        for(Track t : tracks) {
            total = total + t.getDurationSeconds();
            System.out.println(total);
        }
''')
assert RUNNING == "224\n867\n1197\n1462\n1841"
E["q14"] = {"type": "table", "xp": 3, "blanks": {
    **{f"t{i + 1}": {"accept": [v], **NUM} for i, v in enumerate(RUNNING.split("\n"))},
    "a1": {"accept": ["1197"], **NUM}, "a2": {"accept": ["265"], **NUM}, "ret": {"accept": ["1462"], **NUM},
    "ident": {"accept": NO, "show": "no", **YESNO}}}
E["q14-why"] = SHORT("The identity is 0, a neutral starting value for addition, not the first track's length.", rows=2)

JOIN = '''        String joined = tracks.stream()
            .map(t -> t.getTitle())
            .reduce("", (text, title) -> text + title);
        System.out.println(joined);
        tracks.clear();
        String empty = tracks.stream()
            .map(t -> t.getTitle())
            .reduce("", (text, title) -> text + title);
        System.out.println("[" + empty + "]");
'''
assert on_list(JOIN) == "Northern SkyBlue TrainTeardropNaimaAngel\n[]"
E["q15"] = {"type": "table", "xp": 3, "blanks": {
    "id": {"accept": ['""'], "show": '""', "caseSensitive": True, "placeholder": "identity", "width": "7rem"},
    "res": {"accept": ["Northern SkyBlue TrainTeardropNaimaAngel", '"Northern SkyBlue TrainTeardropNaimaAngel"'], "show": "Northern SkyBlue TrainTeardropNaimaAngel",
            "caseSensitive": True, "placeholder": "result", "width": "22rem"},
    "empty": {"accept": ['""', "the empty string", "empty string", "an empty string", "empty"], "show": '""', "placeholder": "result", "width": "10rem"}}}
E["q15-why"] = SHORT("Joining an empty string to a title leaves the title unchanged, so the empty string is the identity for joining. No separators are added. Reduce is not restricted to numeric addition.", rows=2)

TOTAL_BY_ARTIST = '''
    public int totalDurationByArtist(String artist)
    {
        return tracks.stream()
                     .filter(t -> t.getArtist().equals(artist))
                     .map(t -> t.getDurationSeconds())
                     .reduce(0, (total, seconds) -> total + seconds);
    }
'''
TOTAL_ARTIST_DRIVER = playlist_driver("ArtistTotalCheck", '''System.out.println("John Coltrane: " + playlist.totalDurationByArtist("John Coltrane"));
System.out.println("Massive Attack: " + playlist.totalDurationByArtist("Massive Attack"));
System.out.println("Nobody At All: " + playlist.totalDurationByArtist("Nobody At All"));
System.out.println("Still " + playlist.getNumberOfTracks() + " tracks");''')
Q16_STARTER = playlist_starter("public int totalDurationByArtist(String artist)", "Filter by artist, map to seconds, then reduce(0, ...).")
E["q16"] = {"type": "code", "xp": 5, "title": "Playlist.java", **box(Q16_STARTER, playlist(TOTAL_BY_ARTIST)),
    "starter": Q16_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(playlist(TOTAL_BY_ARTIST), TRACK_FILE + TOTAL_ARTIST_DRIVER)}],
    "check": "\n".join([
        has("public int totalDurationByArtist(String artist)", "Keep the header public int totalDurationByArtist(String artist)."),
        has("return tracks.stream()", "Return the result of a pipeline on tracks.stream()."),
        matches(r".*\.filter\(.*\.map\(.*\.reduce\(0,.*", "Use filter, then map, then reduce(0, ...), in that order."),
        has(".getArtist().equals(artist)", "Compare the text with t.getArtist().equals(artist)."),
        has(".getDurationSeconds()", "Map to getDurationSeconds()."),
        lacks("for(Track", "Use the pipeline; do not write a loop.")]),
    "answer": b64(playlist(TOTAL_BY_ARTIST)), "files": TRACK_FILE + TOTAL_ARTIST_DRIVER}
assert E["q16"]["cases"][0]["expected"] == "John Coltrane: 908\nMassive Attack: 709\nNobody At All: 0\nStill 5 tracks"
E["q16-trace"] = {"type": "table", "xp": 2, "blanks": {
    "vals": {"accept": list_forms("643", "265"), "show": "643, 265", "placeholder": "values", "width": "10rem"},
    "totals": {"accept": list_forms("0", "643", "908") + list_forms("643", "908"), "show": "0, 643, 908", "placeholder": "running totals", "width": "12rem"},
    "ret": {"accept": ["908"], **NUM}}}

EMPTY_CASES = on_list('''        tracks.stream().filter(t -> t.getArtist().equals("Nobody")).forEach(t -> t.printDetails());
        System.out.println(tracks.stream().filter(t -> t.getArtist().equals("Nobody")).count());
        System.out.println(tracks.stream().filter(t -> t.getArtist().equals("Nobody")).map(t -> t.getDurationSeconds()).reduce(0, (a, b) -> a + b));
        tracks.clear();
        System.out.println(tracks.stream().count());
        System.out.println(tracks.stream().map(t -> t.getDurationSeconds()).reduce(0, (a, b) -> a + b));
''')
assert EMPTY_CASES == "0\n0\n0\n0"
E["q17"] = {"type": "table", "xp": 2, "blanks": {
    "print": {"accept": ["nothing", "nothing prints", "no output", "none", "prints nothing", "no lines"], "show": "nothing", "placeholder": "printing", "width": "10rem"},
    "count": {"accept": ["0"], **NUM}, "sum": {"accept": ["0"], **NUM}}}
E["q17-why"] = SHORT("An empty source list gives the same outcomes. No element reaches the terminal operation, so the print action never runs and the accumulator has nothing to combine. The sum returns its identity 0.", rows=2)

# ---------------------------------------------------------------- Reading pipelines
LONG_TITLES = on_list('''        tracks.stream()
              .filter(t -> t.getDurationSeconds() > 300)
              .map(t -> t.getTitle())
              .forEach(title -> System.out.println(title));
        System.out.println(tracks.size());
''')
assert LONG_TITLES == "Blue Train\nTeardrop\nAngel\n5"
E["q18"] = {"type": "table", "xp": 3, "blanks": {
    "ns": {"accept": ["5"], **NUM}, "ts": TRACK_T,
    "nf": {"accept": ["3"], **NUM}, "tf": TRACK_T,
    "nm": {"accept": ["3"], **NUM}, "tm": STRING_T,
    **{f"o{i + 1}": {"accept": [line], **LINE} for i, line in enumerate(LONG_TITLES.split("\n")[:3])},
    "stream": {"accept": NO, "show": "no", **YESNO},
    "size": {"accept": ["5"], **NUM}}}

BOOLS = on_list('''        tracks.stream()
              .map(t -> t.getArtist().equals("John Coltrane"))
              .forEach(System.out::println);
''')
assert BOOLS == "false\ntrue\nfalse\ntrue\nfalse"
E["q19"] = {"type": "table", "xp": 2, "blanks": {
    **{f"o{i + 1}": {"accept": [line], **BOOL} for i, line in enumerate(BOOLS.split("\n"))},
    "sel": {"accept": NO, "show": "no", **YESNO}}}
E["q19-why"] = SHORT("Map supplies five boolean values; it does not select tracks. The false values reach forEach and print just like the true values.", rows=2)

Q20_ANSWER = list_program("CountDemo", '''        tracks.stream()
              .filter(t -> t.getArtist().equals("John Coltrane"));

        long count = tracks.stream()
                           .filter(t -> t.getArtist().equals("John Coltrane"))
                           .count();
        System.out.println(count);
''')
Q20_STARTER = list_program("CountDemo", '''        tracks.stream()
              .filter(t -> t.getArtist().equals("John Coltrane"));

        // Replace this statement: store the Coltrane count in a variable, then print it.
        tracks.stream().count()
              .filter(t -> t.getArtist().equals("John Coltrane"));
''')
assert run_java(Q20_STARTER, (), None, TRACK_FILE)[0] != "ok"
E["q20"] = {"type": "code", "xp": 4, "title": "CountDemo.java", **box(Q20_STARTER, Q20_ANSWER, 6),
    "starter": Q20_STARTER,
    "cases": [{"name": "Program output", "expected": run(Q20_ANSWER, TRACK_FILE)}],
    "check": "\n".join([
        lacks("stream().count().filter(", "count() returns long, which has no filter method. Filter first."),
        matches(r".*\.filter\(\w+->\w+\.getArtist\(\)\.equals\(\"JohnColtrane\"\)\)\.count\(\).*", "Filter by artist, then count()."),
        has("System.out.println(", "Print the count.")]),
    "answer": b64(Q20_ANSWER), "files": TRACK_FILE}
assert E["q20"]["cases"][0]["expected"] == "2"
E["q20-why"] = SHORT("The first statement has no terminal operation, so its predicate does not run. In the second, count returns long, which has no filter method. A used-up stream cannot run again, so the same stream cannot then give the total duration. Each method in Questions 4.4 and 6.5 calls tracks.stream() to obtain a fresh stream.", rows=3)

# ---------------------------------------------------------------- Choosing a style
FIND_FIRST = '''
    public int findFirstTrackIndex(String title)
    {
        int index = 0;
        while(index < tracks.size()) {
            if(tracks.get(index).getTitle().equals(title)) {
                return index;
            }
            index = index + 1;
        }
        return -1;
    }
'''
assert run(playlist(FIND_FIRST), TRACK_FILE + playlist_driver("FindCheck", '''System.out.println(playlist.findFirstTrackIndex("Teardrop"));
System.out.println(playlist.findFirstTrackIndex("Unknown"));''')) == "2\n-1"
CHOICE = {"placeholder": "pipeline / loop", "width": "10rem"}
PIPE = ["pipeline", "a pipeline", "stream", "a stream", "stream pipeline", "a stream pipeline"]
LOOP = ["loop", "a loop", "explicit loop", "an explicit loop", "while", "while loop", "for loop", "for-each loop", "indexed loop"]
E["q21"] = {"type": "table", "xp": 3, "blanks": {
    "a": {"accept": PIPE, "show": "pipeline", **CHOICE}, "b": {"accept": LOOP, "show": "loop", **CHOICE},
    "c": {"accept": LOOP, "show": "loop", **CHOICE}, "d": {"accept": LOOP, "show": "loop", **CHOICE},
    "s1": {"accept": ["2"], **NUM}, "s2": {"accept": ["-1"], **NUM}}}
E["q21-why"] = SHORT("(a) filter, then forEach. (b) a loop keeps an index. (c) a loop can stop on the first match, Blue Train. (d) several updates are easier to follow together in one loop. A loop can also print by artist; shorter code is not automatically clearer.", rows=3)

WRONG_ID = '''        System.out.println(tracks.stream()
                     .filter(t -> t.getDurationSeconds() > 300)
                     .map(t -> t.getDurationSeconds())
                     .reduce(10, (total, seconds) -> total + seconds));
'''
assert on_list(WRONG_ID) == "1362" and on_list(WRONG_ID.replace("reduce(10", "reduce(0")) == "1352"
assert on_list("        tracks.clear();\n" + WRONG_ID) == "10"
E["q22"] = {"type": "table", "xp": 3, "blanks": {
    "cur": {"accept": ["1362"], **NUM},
    "fix": {"accept": code_forms(".reduce(0, (total, seconds) -> total + seconds);", "reduce(0, (total, seconds) -> total + seconds)", "0"),
            "show": ".reduce(0, (total, seconds) -> total + seconds);", "placeholder": "repaired last line", **CODE},
    "fixed": {"accept": ["1352"], **NUM},
    "e1": {"accept": ["10"], **NUM}, "e2": {"accept": ["0"], **NUM}}}

# ---------------------------------------------------------------- Coding Pause 8
APPT_DRIVER = driver("AppointmentCheck", '''Appointment ana = new Appointment("Ana", 15);
Appointment ben = new Appointment("Ben", 20);
System.out.println(ana.getPatientName() + " " + ana.getMinutes() + " " + ana.hasCheckedIn());
ben.checkIn();
System.out.println(ben.getPatientName() + " " + ben.getMinutes() + " " + ben.hasCheckedIn());''')
Q23A_STARTER = APPOINTMENT.replace("public class Appointment\n{", "public class Appointment\n{\n    // Add the minutes field, replace the constructor, and add getMinutes().", 1)
E["q23-appt"] = {"type": "code", "xp": 4, "title": "Appointment.java", **box(Q23A_STARTER, APPOINTMENT_8, 6),
    "starter": Q23A_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(APPOINTMENT_8, APPT_DRIVER)}],
    "check": "\n".join([
        has("private int minutes;", "Add the field private int minutes;."),
        matches(r".*publicAppointment\(String\w+,int\w+\).*", "Replace the constructor with Appointment(String patientName, int minutes)."),
        lacks("public Appointment(String patientName)", "Replace the old one-argument constructor; do not keep both."),
        has("public int getMinutes()", "Add public int getMinutes()."),
        lacks("setMinutes", "No setter is needed.")]),
    "answer": b64(APPOINTMENT_8), "files": APPT_DRIVER}
assert E["q23-appt"]["cases"][0]["expected"] == "Ana 15 false\nBen 20 true"

PART8_DRIVER = driver("MinutesCheck", '''ClinicSchedule schedule = new ClinicSchedule();
System.out.println("Empty: " + schedule.totalWaitingMinutes());
Appointment ana = new Appointment("Ana", 15);
Appointment ben = new Appointment("Ben", 20);
Appointment cara = new Appointment("Cara", 10);
Appointment dev = new Appointment("Dev", 30);
schedule.addAppointment(ana);
schedule.addAppointment(ben);
schedule.addAppointment(cara);
schedule.addAppointment(dev);
System.out.println("Nobody checked in: " + schedule.totalWaitingMinutes());
ben.checkIn();
dev.checkIn();
System.out.println("Ben and Dev checked in: " + schedule.totalWaitingMinutes());
System.out.println("Waiting count: " + schedule.countWaiting());
System.out.println("Appointments: " + schedule.getCount());
schedule.checkInAll();
System.out.println("After check-in: " + schedule.totalWaitingMinutes());''')
Q23_STARTER = SCHEDULE_7.rstrip()[:-1] + "\n    // Write totalWaitingMinutes() here.\n\n\n\n\n\n\n\n}\n"
E["q23"] = {"type": "code", "xp": 5, "title": "ClinicSchedule.java", **box(Q23_STARTER, SCHEDULE_8),
    "starter": Q23_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(SCHEDULE_8, [file("Appointment.java", APPOINTMENT_8)] + PART8_DRIVER)}],
    "check": "\n".join([
        has("public int totalWaitingMinutes()", "Include public int totalWaitingMinutes()."),
        matches(r".*publicinttotalWaitingMinutes\(\)\{returnappointments\.stream\(\)\.filter\(.*", "Return the result of appointments.stream().filter(...)..."),
        has(".getMinutes()", "Map each waiting appointment to getMinutes()."),
        matches(r".*publicinttotalWaitingMinutes\(\).*\.map\(.*\.reduce\(0,.*", "Map to minutes, then reduce(0, ...)."),
        lacks("totalMinutes;", "Do not store a total field.")]),
    "answer": b64(SCHEDULE_8), "files": [file("Appointment.java", APPOINTMENT_8)] + PART8_DRIVER}
assert E["q23"]["cases"][0]["expected"] == ("Empty: 0\nNobody checked in: 75\nBen and Dev checked in: 25\nWaiting count: 2\n"
                                            "Appointments: 4\nAfter check-in: 0")
E["q23-rec"] = {"type": "table", "xp": 2, "blanks": {
    "map": {"accept": no_semi(code_forms("appointment -> appointment.getMinutes()", "appointment.getMinutes()", "a -> a.getMinutes()", "Appointment::getMinutes")),
            "show": "appointment -> appointment.getMinutes()", "placeholder": "map expression", **CODE},
    "acc": {"accept": no_semi(code_forms("(total, minutes) -> total + minutes", "(a, b) -> a + b", "(total, m) -> total + m", "(sum, minutes) -> sum + minutes")),
            "show": "(total, minutes) -> total + minutes", "placeholder": "accumulator", **CODE}}}

DEMO8_OUT = run(DEMO_8, PAUSE8_FILES)
assert DEMO8_OUT == ("Empty waiting minutes: 0\nWaiting names:\nAna\nCara\nWaiting count: 2\nWaiting minutes: 25\nAppointments: 3\n"
                     "After check-in: 0\nAppointments: 3")
E["q24"] = {"type": "table", "xp": 3, "blanks": {
    "names": {"accept": ANA_CARA, "show": "Ana, Cara", "placeholder": "names", "width": "9rem"},
    "totals": {"accept": list_forms("0", "15", "25") + list_forms("15", "25"), "show": "0, 15, 25", "placeholder": "running totals", "width": "10rem"},
    "empty": {"accept": ["0"], **NUM}, "after": {"accept": ["0"], **NUM}, "count": {"accept": ["3"], **NUM}}}
Q24_STARTER = "public class ClinicDemo\n{\n    public static void main(String[] args)\n    {\n        ClinicSchedule schedule = new ClinicSchedule();\n        // Follow the steps above. Every constructor call now supplies minutes.\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n    }\n}\n"
E["q24-demo"] = {"type": "code", "xp": 4, "title": "ClinicDemo.java", **box(Q24_STARTER, DEMO_8, 8),
    "starter": Q24_STARTER,
    "cases": [{"name": "Program output", "expected": DEMO8_OUT}],
    "check": "\n".join([
        has('new Appointment("Ana", 15)', 'Add Ana for 15 minutes: new Appointment("Ana", 15).'),
        matches(r".*Appointment(\w+)=newAppointment\(\"Ben\",20\);.*\1\.checkIn\(\);.*", 'Keep Ben\'s reference (20 minutes) and check him in.'),
        has('new Appointment("Cara", 10)', 'Add Cara for 10 minutes: new Appointment("Cara", 10).'),
        matches(r".*totalWaitingMinutes\(\).*totalWaitingMinutes\(\).*totalWaitingMinutes\(\).*", "Print the waiting minutes three times."),
        has(".printWaitingNames()", "Print the waiting names with printWaitingNames()."),
        has(".checkInAll()", "Check everyone in with checkInAll().")]),
    "answer": b64(DEMO_8), "files": PAUSE8_FILES}
E["q24-why"] = SHORT("Ben has checked in, so the filter stops him and his 20 minutes never reach map or reduce. The appointment count stays 3 because nothing is removed.", rows=2)

# ---------------------------------------------------------------- Review
E["q25"] = {"type": "table", "xp": 3, "blanks": {
    "a": {"accept": ["5"], **NUM},
    "b": {"accept": ["filter", "use filter", "filter()", "Filter"], "show": "filter", "placeholder": "operation", "width": "9rem"},
    "c": {"accept": ["the identity", "identity", "its identity", "0", "the identity value"], "show": "the identity", "placeholder": "result", "width": "10rem"},
    "d": {"accept": ["long", "a long"], "show": "long", "placeholder": "type", "width": "7rem"}}}
E["q25-why"] = SHORT("(a) The source still has size 5. (b) Map supplies one output per input; use filter for selection. (c) Reduce can also join text, and with no elements this form returns its identity. (d) count returns long, not a stream, so any filter must come before it.", rows=3)

# ---------------------------------------------------------------- Complete Java Programs
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
}
'''

BOOKSHELF = '''import java.util.ArrayList;

public class Bookshelf
{
    private ArrayList<Book> books;

    public Bookshelf()
    {
        books = new ArrayList<>();
    }

    public void addBook(Book book)
    {
        books.add(book);
    }

    public int getNumberOfBooks()
    {
        return books.size();
    }

    public void printAuthors()
    {
        books.stream()
             .map(book -> book.getAuthor())
             .forEach(author -> System.out.println(author));
    }

    public void printTitlesBy(String author)
    {
        books.stream()
             .filter(book -> book.getAuthor().equals(author))
             .map(book -> book.getTitle())
             .forEach(title -> System.out.println(title));
    }

    public long countLongerThan(int pages)
    {
        return books.stream()
                    .filter(book -> book.getPages() > pages)
                    .count();
    }
}
'''

BOOKSHELF_DEMO = '''public class BookshelfDemo
{
    public static void main(String[] args)
    {
        Bookshelf shelf = new Bookshelf();
        shelf.addBook(new Book("Dune", "Frank Herbert", 412));
        shelf.addBook(new Book("Emma", "Jane Austen", 474));
        shelf.addBook(new Book("Persuasion", "Jane Austen", 249));
        shelf.addBook(new Book("Holes", "Louis Sachar", 233));
        shelf.addBook(new Book("Beloved", "Toni Morrison", 324));

        System.out.println("Authors:");
        shelf.printAuthors();
        System.out.println("Austen titles:");
        shelf.printTitlesBy("Jane Austen");
        System.out.println("Tolkien titles:");
        shelf.printTitlesBy("J. R. R. Tolkien");
        System.out.println("Over 300 pages: " + shelf.countLongerThan(300));
        System.out.println("Over 500 pages: " + shelf.countLongerThan(500));
        System.out.println("Books: " + shelf.getNumberOfBooks());
    }
}
'''

EXPENSE = '''public class Expense
{
    private String description;
    private String category;
    private int amount;

    public Expense(String description, String category, int amount)
    {
        this.description = description;
        this.category = category;
        this.amount = amount;
    }

    public String getDescription()
    {
        return description;
    }

    public String getCategory()
    {
        return category;
    }

    public int getAmount()
    {
        return amount;
    }
}
'''

EXPENSE_LOG = '''import java.util.ArrayList;

public class ExpenseLog
{
    private ArrayList<Expense> expenses;

    public ExpenseLog()
    {
        expenses = new ArrayList<>();
    }

    public void addExpense(Expense expense)
    {
        expenses.add(expense);
    }

    public int total()
    {
        return expenses.stream()
                       .map(expense -> expense.getAmount())
                       .reduce(0, (sum, amount) -> sum + amount);
    }

    public int totalFor(String category)
    {
        return expenses.stream()
                       .filter(expense -> expense.getCategory().equals(category))
                       .map(expense -> expense.getAmount())
                       .reduce(0, (sum, amount) -> sum + amount);
    }

    public int findFirstOver(int amount)
    {
        int index = 0;
        while(index < expenses.size()) {
            if(expenses.get(index).getAmount() > amount) {
                return index;
            }
            index = index + 1;
        }
        return -1;
    }
}
'''

EXPENSE_LOG_DEMO = '''public class ExpenseLogDemo
{
    public static void main(String[] args)
    {
        ExpenseLog log = new ExpenseLog();
        System.out.println("Empty total: " + log.total());

        log.addExpense(new Expense("Groceries", "Food", 85));
        log.addExpense(new Expense("Rent", "Housing", 900));
        log.addExpense(new Expense("Bus pass", "Transport", 60));
        log.addExpense(new Expense("Cafe", "Food", 12));
        log.addExpense(new Expense("Textbook", "School", 140));

        System.out.println("Total: " + log.total());
        System.out.println("Food: " + log.totalFor("Food"));
        System.out.println("Housing: " + log.totalFor("Housing"));
        System.out.println("Pets: " + log.totalFor("Pets"));
        System.out.println("First over 100: " + log.findFirstOver(100));
        System.out.println("First over 1000: " + log.findFirstOver(1000));
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
}
'''

BOOKSHELF_STARTER = '''import java.util.ArrayList;

public class Bookshelf
{
    private ArrayList<Book> books;

    public Bookshelf()
    {
        books = new ArrayList<>();
    }

    public void addBook(Book book)
    {
    }

    public int getNumberOfBooks()
    {
    }

    public void printAuthors()
    {
        // map, then forEach.
    }

    public void printTitlesBy(String author)
    {
        // filter, map, then forEach.
    }

    public long countLongerThan(int pages)
    {
        // filter, then count.
    }
}
'''

BOOKSHELF_DEMO_STARTER = '''public class BookshelfDemo
{
    public static void main(String[] args)
    {
        Bookshelf shelf = new Bookshelf();
        // 1. Add the five books in order.
        // 2. Print "Authors:" and the authors.
        // 3. Print "Austen titles:" and the titles by Jane Austen.
        // 4. Print "Tolkien titles:" and the titles by J. R. R. Tolkien.
        // 5. Print "Over 300 pages: " and "Over 500 pages: " with the counts.
        // 6. Print "Books: " and the number of books.
    }
}
'''

EXPENSE_STARTER = '''public class Expense
{
    private String description;
    private String category;
    private int amount;

    public Expense(String description, String category, int amount)
    {
        // Assign the three fields.
    }

    public String getDescription()
    {
    }

    public String getCategory()
    {
    }

    public int getAmount()
    {
    }
}
'''

EXPENSE_LOG_STARTER = '''import java.util.ArrayList;

public class ExpenseLog
{
    private ArrayList<Expense> expenses;

    public ExpenseLog()
    {
        expenses = new ArrayList<>();
    }

    public void addExpense(Expense expense)
    {
    }

    public int total()
    {
        // map, then reduce from 0.
    }

    public int totalFor(String category)
    {
        // filter, map, then reduce from 0.
    }

    public int findFirstOver(int amount)
    {
        // while loop; return the index or -1.
    }
}
'''

EXPENSE_LOG_DEMO_STARTER = '''public class ExpenseLogDemo
{
    public static void main(String[] args)
    {
        ExpenseLog log = new ExpenseLog();
        // 1. Print "Empty total: " and the total of the empty log.
        // 2. Add the five expenses in order.
        // 3. Print "Total: " and the total.
        // 4. Print "Food: ", "Housing: " and "Pets: " with their totals.
        // 5. Print "First over 100: " and "First over 1000: " with the indexes.
    }
}
'''

BOOK_FILE = [file("Book.java", BOOK)]
BOOKSHELF_FILES = BOOK_FILE + [file("Bookshelf.java", BOOKSHELF)]
EXPENSE_FILE = [file("Expense.java", EXPENSE)]
EXPENSE_LOG_FILES = EXPENSE_FILE + [file("ExpenseLog.java", EXPENSE_LOG)]
NO_LOOP = [lacks("for(", "Use one pipeline in each method; do not write an explicit loop."),
           lacks("while(", "Use one pipeline in each method; do not write an explicit loop.")]

BOOK_DRIVER = driver("BookCheck", """Book book = new Book("Emma", "Jane Austen", 474);
System.out.println(book.getTitle());
System.out.println(book.getAuthor());
System.out.println(book.getPages());""")
E["p1-item"] = {"type": "code", "xp": 3, "minLines": 28, "maxLines": 40, "title": "Book.java",
    "starter": BOOK_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(BOOK, BOOK_DRIVER)}],
    "check": "\n".join([
        has("public Book(String title, String author, int pages)", "Keep the constructor header Book(String title, String author, int pages)."),
        has("public int getPages()", "Include public int getPages().")]),
    "answer": b64(BOOK), "files": BOOK_DRIVER}
assert E["p1-item"]["cases"][0]["expected"] == "Emma\nJane Austen\n474"

BOOKSHELF_DRIVER = driver("BookshelfCheck", """Bookshelf empty = new Bookshelf();
System.out.println("Empty shelf:");
empty.printAuthors();
empty.printTitlesBy("Louis Sachar");
System.out.println("Longer than 0: " + empty.countLongerThan(0));
System.out.println("Books: " + empty.getNumberOfBooks());
Bookshelf shelf = new Bookshelf();
shelf.addBook(new Book("Holes", "Louis Sachar", 233));
shelf.addBook(new Book("Dune", "Frank Herbert", 412));
shelf.addBook(new Book("Small Steps", "Louis Sachar", 257));
System.out.println("Authors:");
shelf.printAuthors();
System.out.println("Sachar titles:");
shelf.printTitlesBy("Louis Sachar");
System.out.println("Longer than 250: " + shelf.countLongerThan(250));
System.out.println("Longer than 412: " + shelf.countLongerThan(412));
System.out.println("Books: " + shelf.getNumberOfBooks());""")
E["p1-collection"] = {"type": "code", "xp": 6, "minLines": 42, "maxLines": 58, "title": "Bookshelf.java",
    "starter": BOOKSHELF_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(BOOKSHELF, BOOK_FILE + BOOKSHELF_DRIVER)}],
    "check": "\n".join([
        has("books.stream()", "Start each pipeline with books.stream()."),
        has(".map(", "Use map to get the authors and the titles."),
        has(".filter(", "Use filter to choose the books."),
        has(".getAuthor().equals(author)", "Compare the authors with equals."),
        has(".count()", "Count with count()."),
        *NO_LOOP]),
    "answer": b64(BOOKSHELF), "files": BOOK_FILE + BOOKSHELF_DRIVER}
assert E["p1-collection"]["cases"][0]["expected"] == ("Empty shelf:\nLonger than 0: 0\nBooks: 0\nAuthors:\nLouis Sachar\nFrank Herbert\n"
    "Louis Sachar\nSachar titles:\nHoles\nSmall Steps\nLonger than 250: 2\nLonger than 412: 0\nBooks: 3")

E["p1-demo"] = {"type": "code", "xp": 4, "minLines": 16, "maxLines": 28, "title": "BookshelfDemo.java",
    "starter": BOOKSHELF_DEMO_STARTER,
    "cases": [{"name": "Program output", "expected": run(BOOKSHELF_DEMO, BOOKSHELF_FILES)}],
    "check": "\n".join([
        has("shelf.addBook(new Book(", "Add each book as an anonymous object: shelf.addBook(new Book(...));"),
        has('printTitlesBy("Jane Austen")', 'Print the titles by Jane Austen with printTitlesBy("Jane Austen").'),
        has('printTitlesBy("J. R. R. Tolkien")', 'Print the titles by J. R. R. Tolkien with printTitlesBy("J. R. R. Tolkien").'),
        has("countLongerThan(300)", "Count the books over 300 pages with countLongerThan(300)."),
        has("countLongerThan(500)", "Count the books over 500 pages with countLongerThan(500).")]),
    "answer": b64(BOOKSHELF_DEMO), "files": BOOKSHELF_FILES}
assert E["p1-demo"]["cases"][0]["expected"] == ("Authors:\nFrank Herbert\nJane Austen\nJane Austen\nLouis Sachar\nToni Morrison\n"
    "Austen titles:\nEmma\nPersuasion\nTolkien titles:\nOver 300 pages: 3\nOver 500 pages: 0\nBooks: 5")

EXPENSE_DRIVER = driver("ExpenseCheck", """Expense expense = new Expense("Rent", "Housing", 900);
System.out.println(expense.getDescription());
System.out.println(expense.getCategory());
System.out.println(expense.getAmount());""")
E["p2-item"] = {"type": "code", "xp": 3, "minLines": 28, "maxLines": 40, "title": "Expense.java",
    "starter": EXPENSE_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(EXPENSE, EXPENSE_DRIVER)}],
    "check": "\n".join([
        has("public Expense(String description, String category, int amount)", "Keep the constructor header Expense(String description, String category, int amount)."),
        has("public int getAmount()", "Include public int getAmount().")]),
    "answer": b64(EXPENSE), "files": EXPENSE_DRIVER}
assert E["p2-item"]["cases"][0]["expected"] == "Rent\nHousing\n900"

EXPENSE_LOG_DRIVER = driver("ExpenseLogCheck", """ExpenseLog empty = new ExpenseLog();
System.out.println("Empty total: " + empty.total());
System.out.println("Empty Food: " + empty.totalFor("Food"));
System.out.println("Empty first over 0: " + empty.findFirstOver(0));
ExpenseLog log = new ExpenseLog();
log.addExpense(new Expense("Lunch", "Food", 15));
log.addExpense(new Expense("Phone", "Bills", 50));
log.addExpense(new Expense("Dinner", "Food", 30));
log.addExpense(new Expense("Gym", "Health", 40));
System.out.println("Total: " + log.total());
System.out.println("Food: " + log.totalFor("Food"));
System.out.println("Travel: " + log.totalFor("Travel"));
System.out.println("First over 35: " + log.findFirstOver(35));
System.out.println("First over 50: " + log.findFirstOver(50));""")
E["p2-collection"] = {"type": "code", "xp": 6, "minLines": 44, "maxLines": 60, "title": "ExpenseLog.java",
    "starter": EXPENSE_LOG_STARTER,
    "cases": [{"name": "Output of the checking program", "expected": run(EXPENSE_LOG, EXPENSE_FILE + EXPENSE_LOG_DRIVER)}],
    "check": "\n".join([
        has("expenses.stream()", "Start the totals with expenses.stream()."),
        has(".map(", "Map each expense to its amount."),
        has(".reduce(0,", "Add the amounts with reduce(0, ...)."),
        has(".getCategory().equals(category)", "Compare the categories with equals."),
        has("while(", "Write findFirstOver with a while loop."),
        has("return -1;", "Return -1 when no expense is larger.")]),
    "answer": b64(EXPENSE_LOG), "files": EXPENSE_FILE + EXPENSE_LOG_DRIVER}
assert E["p2-collection"]["cases"][0]["expected"] == ("Empty total: 0\nEmpty Food: 0\nEmpty first over 0: -1\nTotal: 135\nFood: 45\n"
    "Travel: 0\nFirst over 35: 1\nFirst over 50: -1")

E["p2-demo"] = {"type": "code", "xp": 4, "minLines": 16, "maxLines": 28, "title": "ExpenseLogDemo.java",
    "starter": EXPENSE_LOG_DEMO_STARTER,
    "cases": [{"name": "Program output", "expected": run(EXPENSE_LOG_DEMO, EXPENSE_LOG_FILES)}],
    "check": "\n".join([
        has("log.addExpense(new Expense(", "Add each expense as an anonymous object: log.addExpense(new Expense(...));"),
        has('totalFor("Food")', 'Print the Food total with totalFor("Food").'),
        has('totalFor("Pets")', 'Print the Pets total with totalFor("Pets").'),
        has("findFirstOver(100)", "Search with findFirstOver(100)."),
        has("findFirstOver(1000)", "Search with findFirstOver(1000).")]),
    "answer": b64(EXPENSE_LOG_DEMO), "files": EXPENSE_LOG_FILES}
assert E["p2-demo"]["cases"][0]["expected"] == ("Empty total: 0\nTotal: 1197\nFood: 97\nHousing: 900\nPets: 0\n"
    "First over 100: 1\nFirst over 1000: -1")

# ---------------------------------------------------------------- write
data = {
    "id": "lecture-09",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 9 Workbook",
    "subtitle": "Chapter 5, Part 2: Stream Pipelines",
    "exercises": E,
}
out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} with {len(E)} specs")
