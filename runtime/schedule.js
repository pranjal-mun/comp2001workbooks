// The course schedule: units, lectures, their dates, and which workbooks are
// posted. The landing page draws its dashboard from this, and a workbook
// page stays locked until OPEN_HOUR on the day of its lecture (instructor
// mode, see instructor.js, ignores the lock).
//
// When a new workbook is finished, set its `built` flag here. That is the
// only edit a lecture branch makes outside its own workbook folder.

export const OPEN_HOUR = 10; // workbooks open at 10:00 local time on lecture day

export const UNITS = [
  { n: 1, name: "Objects, classes, and collaboration (Chapters 1 to 3)" },
  { n: 2, name: "Collections, lambdas, and streams (Chapters 4 and 5)" },
  { n: 3, name: "Library classes, arrays, and design (Chapters 6 to 9)" },
  { n: 4, name: "Inheritance, polymorphism, and interfaces (Chapters 12 to 14)" },
  { n: 5, name: "Graphical user interfaces (Chapter 17)" },
];

// Titles may contain <code>…</code>; they are inserted as HTML.
export const LECTURES = [
  { n: 1, unit: 1, date: "2026-09-10", title: "Course introduction and a first Java program", built: false },
  { n: 2, unit: 1, date: "2026-09-15", title: "Chapter 1: Objects have state and behavior", built: true },
  { n: 3, unit: 1, date: "2026-09-17", title: "Chapter 2, Part 1: A class defines an object's state", built: true },
  { n: 4, unit: 1, date: "2026-09-22", title: "Chapter 2, Part 2: Methods make state useful", built: false },
  { n: 5, unit: 1, date: "2026-09-24", title: "Chapter 3: Objects collaborate", built: false },
  { n: 6, unit: 2, date: "2026-09-29", title: "Chapter 4, Part 1: Storing and processing groups of objects", built: false },
  { n: 7, unit: 2, date: "2026-10-01", title: "Chapter 4, Part 2: Traversal, searching, and safe removal", built: false },
  { n: 8, unit: 2, date: "2026-10-06", title: "Chapter 5, Part 1: Lambdas and internal iteration", built: false },
  { n: 9, unit: 2, date: "2026-10-08", title: "Chapter 5, Part 2: Filtering and transforming with streams", built: false },
  { n: 10, unit: 2, date: "2026-10-15", title: "Term Test 1 (Lectures 2 to 9)", built: false, test: true },
  { n: 11, unit: 3, date: "2026-10-20", title: "Chapter 6, Part 1: Learning and using library classes", built: false },
  { n: 12, unit: 3, date: "2026-10-22", title: "Chapter 6, Part 2: Maps, sets, and class-level members", built: false },
  { n: 13, unit: 3, date: "2026-10-27", title: "Chapter 7, Part 1: Fixed-size collections and the <code>for</code> loop", built: false },
  { n: 14, unit: 3, date: "2026-10-29", title: "Chapter 7, Part 2: Arrays of objects, grids, and representation choices", built: false },
  { n: 15, unit: 3, date: "2026-11-03", title: "Chapter 8: Designing classes that are easy to change", built: false },
  { n: 16, unit: 3, date: "2026-11-05", title: "Chapter 9: Testing, debugging, and well-behaved objects", built: false },
  { n: 17, unit: 4, date: "2026-11-10", title: "Chapter 12, Part 1: Inheritance can remove genuine duplication", built: false },
  { n: 18, unit: 4, date: "2026-11-12", title: "Chapter 12, Part 2: Subtyping and substitutable objects", built: false },
  { n: 19, unit: 4, date: "2026-11-17", title: "Term Test 2 (Lectures 11 to 18)", built: false, test: true },
  { n: 20, unit: 4, date: "2026-11-19", title: "Chapter 13: Dynamic method lookup and overriding", built: false },
  { n: 21, unit: 4, date: "2026-11-24", title: "Chapter 14, Part 1: Abstract classes", built: false },
  { n: 22, unit: 4, date: "2026-11-26", title: "Chapter 14, Part 2: Interfaces", built: false },
  { n: 23, unit: 5, date: "2026-12-01", title: "Chapter 17, Part 1: Building a basic GUI", built: false },
  { n: 24, unit: 5, date: "2026-12-03", title: "Chapter 17, Part 2: Events and GUI design", built: false },
];

export const KEY_DATES = [
  { name: "Fall lecture break", date: "2026-10-13", note: "No class" },
  { name: "Term Test 1", date: "2026-10-15", note: "Lectures 2 to 9, in the lecture slot" },
  { name: "Term Test 2", date: "2026-11-17", note: "Lectures 11 to 18, in the lecture slot" },
  { name: "Final examination", when: "Dec 10 to 18", note: "Registrar-scheduled" },
];

export const workbookId = (n) => `lecture-${String(n).padStart(2, "0")}`;

export function lecture(n) {
  return LECTURES.find((l) => l.n === n) ?? null;
}

/** The schedule entry for a workbook id such as "lecture-04", or null. */
export function lectureFor(id) {
  const m = /^lecture-(\d+)$/.exec(id ?? "");
  return m ? lecture(Number(m[1])) : null;
}

/** Local time at which the workbook for this lecture opens. */
export function opensAt(entry) {
  const d = new Date(`${entry.date}T00:00:00`);
  d.setHours(OPEN_HOUR, 0, 0, 0);
  return d;
}

export function isOpen(entry, now = new Date()) {
  return now >= opensAt(entry);
}

/** "Wed, Oct 7" style; pass `weekday: null` for "Oct 7". */
export function fmtDate(iso, { weekday = "short" } = {}) {
  return new Date(`${iso}T12:00:00`).toLocaleDateString("en-CA", { ...(weekday ? { weekday } : {}), month: "short", day: "numeric" });
}

export function fmtOpens(entry) {
  const t = opensAt(entry);
  const time = t.toLocaleTimeString("en-CA", { hour: "numeric", minute: "2-digit" });
  return `${fmtDate(entry.date)} at ${time}`;
}
