"""Build workbooks/lecture-01/exercises.json.

Lecture 1 has no questions and awards no XP. The page is the reference copy of
the course introduction, and each Java example from the slides is live. The
outputs are produced by actually compiling and running the code through the
same runner the page uses. Run from anywhere (needs `java` on the PATH):

    python3 workbooks/lecture-01/build_exercises.py
    python3 tools/check_workbook.py workbooks/lecture-01
"""
import json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_workbook import run as run_java  # noqa: E402


def run(code, files=()):
    status, stdout, stderr, _ = run_java(code.rstrip("\n"), (), None, files)
    assert status == "ok", f"{status}\n{stderr}"
    return stdout.rstrip("\n")


def file(name, content):
    return {"name": name, "content": content.rstrip("\n")}


def example(code, **kw):
    code = code.rstrip("\n")
    return {"type": "example", "code": code, "output": run(code, kw.get("files", ())), **kw}


COURSE = [file("Course.java", '''class Course
{
    String code;
    String instructor;

    Course(String code, String instructor)
    {
        this.code = code;
        this.instructor = instructor;
    }
}
''')]

E = {}

E["ex-hello"] = example('''public class Hello
{
    public static void main(String[] args)
    {
        System.out.println("Hello, MUN!");
    }
}
''', title="Hello.java")

E["ex-variables"] = example('''String course = "COMP 2001";
int students = 85;
boolean atMun = true;

// Added so you can see the values:
System.out.println(course);
System.out.println(students);
System.out.println(atMun);
''')

E["ex-operators"] = example('''int labs = 28;
int tests = 35;

int total = labs + tests;
boolean passing = total >= 50 && labs > 0;

// Added so you can see the results:
System.out.println(total);
System.out.println(passing);
''')

E["ex-conditionals"] = example('''String city = "St. John's";

if (city.equals("St. John's")) {
    System.out.println("Welcome to MUN");
}
else {
    System.out.println("Welcome");
}
''')

E["ex-while"] = example('''int week = 1;

while (week <= 3) {
    System.out.println("Week " + week);
    week++;
}
''')

E["ex-for"] = example('''for (int week = 1; week <= 3; week++) {
    System.out.println("Week " + week);
}
''')

E["ex-foreach"] = example('''String[] pets = {"Oliver", "Sabina"};

for (String pet : pets) {
    System.out.println(pet);
}
''')

E["ex-lists"] = example('''import java.util.ArrayList;

public class Main
{
    public static void main(String[] args)
    {
        ArrayList<String> pets =
            new ArrayList<>();
        pets.add("Oliver");
        pets.add("Sabina");
        pets.add("Milo");

        String first = pets.get(0);
        int count = pets.size();

        // Added so you can see the results:
        System.out.println(first);
        System.out.println(count);
    }
}
''')

E["ex-maps"] = example('''import java.util.HashMap;

public class Main
{
    public static void main(String[] args)
    {
        HashMap<String, String> course =
            new HashMap<>();
        course.put("code", "COMP 2001");
        course.put("program", "Computer Science");

        System.out.println(course.get("program"));
    }
}
''')

E["ex-methods"] = example('''public class Main
{
    static String label(String code, int n)
    {
        return code + " " + n;
    }

    public static void main(String[] args)
    {
        String course = label("COMP", 2001);

        // Added so you can see the result:
        System.out.println(course);
    }
}
''')

E["ex-objects"] = example('''Course comp2001 = new Course(
    "COMP 2001",
    "Pranjal Patra"
);

System.out.println(comp2001.instructor);
''', files=COURSE)

E["ex-inheritance"] = example('''class Pet {
    String speak() { return "..."; }
}

class Dog extends Pet {
    @Override
    String speak() { return "woof"; }
}

public class Main
{
    public static void main(String[] args)
    {
        Dog oliver = new Dog();

        // Added so you can see which speak() runs:
        System.out.println(oliver.speak());
    }
}
''')

E["ex-exceptions"] = example('''String text = "2001";

try {
    int number = Integer.parseInt(text);
    System.out.println(number);
}
catch (NumberFormatException error) {
    System.out.println("Not a number");
}
''')

data = {
    "id": "lecture-01",
    "course": "COMP 2001: Object-Oriented Programming",
    "title": "Lecture 1 Workbook",
    "subtitle": "Object-Oriented Programming and Java",
    "exercises": E,
}

out = pathlib.Path(__file__).with_name("exercises.json")
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {out} ({len(E)} examples)")
