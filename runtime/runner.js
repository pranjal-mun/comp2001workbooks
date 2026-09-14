// One Java worker per page, shared by every widget. Runs are queued so only
// one executes at a time; a run that exceeds its time limit terminates the
// worker and a fresh one is started for the next run.
//
// Every run compiles first. The first compile in a page can take a while
// (the compiler itself is warming up in the browser), so the run limit only
// starts once the worker reports that the program is running; compiling has
// its own, longer, limit.

const RUN_TIMEOUT_MS = 5_000;
const COMPILE_TIMEOUT_MS = 90_000;
const WORKER_URL = new URL("./java-worker.js", import.meta.url);

export class TimeoutError extends Error {
  constructor(ms) {
    super(`Execution stopped after reaching the ${ms / 1000}-second time limit.`);
    this.name = "TimeoutError";
  }
}

export class StoppedError extends Error {
  constructor() {
    super("Execution stopped.");
    this.name = "StoppedError";
  }
}

class Runner {
  constructor() {
    this.worker = null;
    this.readyPromise = null;
    this.queue = Promise.resolve();
    this.listeners = new Set();
    this.state = "idle";
    this.current = null;
    this.nextId = 1;
  }

  /** Subscribe to status changes: fn(state, text). States: idle, loading, ready, running, error. */
  onStatus(fn) {
    this.listeners.add(fn);
    fn(this.state, this.statusText());
    return () => this.listeners.delete(fn);
  }

  statusText() {
    return { idle: "Java not loaded", loading: "Loading Java…", ready: "Java ready", running: "Running…", error: "Java failed to load" }[this.state];
  }

  setState(state) {
    this.state = state;
    for (const fn of this.listeners) fn(state, this.statusText());
  }

  /** Start loading Java now (e.g. on page load) instead of on the first run. */
  warmUp() {
    this.ensureWorker().catch(() => {});
  }

  ensureWorker() {
    if (this.readyPromise) return this.readyPromise;
    this.setState("loading");
    const worker = new Worker(WORKER_URL);
    this.worker = worker;
    this.readyPromise = new Promise((resolve, reject) => {
      const onMessage = (event) => {
        if (event.data?.type === "ready") {
          worker.removeEventListener("message", onMessage);
          this.setState("ready");
          resolve(worker);
        } else if (event.data?.type === "fatal") {
          worker.removeEventListener("message", onMessage);
          this.failWorker(new Error(event.data.error), reject);
        }
      };
      worker.addEventListener("message", onMessage);
      worker.addEventListener("error", () => this.failWorker(new Error("The page could not load the Java runtime. Check your connection and reload the page."), reject));
    });
    return this.readyPromise;
  }

  failWorker(error, reject) {
    this.worker?.terminate();
    this.worker = null;
    this.readyPromise = null;
    this.setState("error");
    reject(error);
  }

  /**
   * Compile and run a project once. files is [{name, content}] with every
   * .java file; entry is the class whose main method runs. Resolves with the
   * worker's result object ({status, stdout, stderr, check}); status is ok,
   * error, compile-error or need-input. Rejects with TimeoutError,
   * StoppedError, or a load error.
   */
  run({ files, entry = "Main", inputs = [], echoInput = false, check = null, timeoutMs = RUN_TIMEOUT_MS }) {
    const job = () => this.execute({ files, entry, inputs, echoInput, check, timeoutMs });
    const result = this.queue.then(job, job);
    this.queue = result.catch(() => {});
    return result;
  }

  async execute(request) {
    const worker = await this.ensureWorker();
    this.setState("running");
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      const finish = (fn, value) => {
        clearTimeout(timer);
        worker.removeEventListener("message", onMessage);
        if (this.current?.id === id) this.current = null;
        if (this.state === "running") this.setState("ready");
        fn(value);
      };
      const onMessage = (event) => {
        if (event.data?.id !== id) return;
        if (event.data.type === "result") finish(resolve, event.data);
        else if (event.data.type === "phase" && event.data.phase === "running") {
          clearTimeout(timer);
          timer = setTimeout(expire, request.timeoutMs);
        }
      };
      const expire = () => {
        this.restart();
        finish(reject, new TimeoutError(request.timeoutMs));
      };
      let timer = setTimeout(expire, COMPILE_TIMEOUT_MS);
      this.current = { id, abort: () => { this.restart(); finish(reject, new StoppedError()); } };
      worker.addEventListener("message", onMessage);
      worker.postMessage({ type: "run", id, ...request });
    });
  }

  /** Abort the run in progress, if any. */
  stop() {
    this.current?.abort();
  }

  restart() {
    this.worker?.terminate();
    this.worker = null;
    this.readyPromise = null;
    this.setState("idle");
    this.warmUp();
  }
}

export const runner = new Runner();

/**
 * Run a program interactively against a console: output is appended as it
 * arrives, and each read from System.in becomes an inline text field. The
 * program is replayed from the top with every answer so far, so it must be
 * deterministic. Resolves with the final result once the program finishes
 * (or errors).
 *
 * console must provide: append(text), prompt(signal) -> Promise<string>,
 * error(text), clear(). Returns {status, stdout, stderr}.
 */
export async function runInteractive({ files, entry, console: out, inputs = [], signal, formatError = (text) => text }) {
  const answers = [...inputs];
  let shown = "";
  for (;;) {
    const result = await runner.run({ files, entry, inputs: answers, echoInput: true });
    // Replay is deterministic for course programs, so the new output is the
    // suffix past what is already on screen. If it isn't, redraw everything.
    if (result.stdout.startsWith(shown)) {
      out.append(result.stdout.slice(shown.length));
    } else {
      out.clear();
      out.append(result.stdout);
    }
    shown = result.stdout;
    if (result.status !== "need-input") {
      if (result.stderr) out.error(formatError(result.stderr));
      return result;
    }
    if (signal?.aborted) throw new StoppedError();
    const answer = await out.prompt(signal);
    answers.push(answer);
    shown += answer + "\n";
  }
}
