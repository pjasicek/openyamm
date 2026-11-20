// The host's line to the core: one `oymap serve` child process, JSON-RPC 2.0, one message a line. The host holds no
// map logic and no document state; if the child dies it is started again on the next call, and nothing is lost,
// because the project's files are the state. The child keeps its own caches (by project and source revision), so one
// child serves every browser and MCP client of a host: lane I of S5_BROWSER_EDITOR.md 2.4.3.
//
// Calls go to the child one at a time, in the order they were made (the core is single-threaded; a queue here keeps
// a slow call from flooding the pipe behind it and makes the order explicit).
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';

export class Core {
  // `assets`: the session's asset root (serve --assets), or empty for none.
  constructor(oymapPath, { assets } = {}) {
    this.oymapPath = oymapPath;
    this.assets = assets;
    this.child = null;
    this.nextId = 1;
    this.waiting = new Map();
    this.queue = Promise.resolve();
  }

  start() {
    const args = ['serve', ...(this.assets ? ['--assets', this.assets] : [])];
    this.child = spawn(this.oymapPath, args, { stdio: ['pipe', 'pipe', 'inherit'] });
    const lines = createInterface({ input: this.child.stdout });
    lines.on('line', (line) => {
      let message;
      try {
        message = JSON.parse(line);
      } catch {
        return;
      }
      const entry = this.waiting.get(message.id);
      if (!entry) return;
      this.waiting.delete(message.id);
      entry.resolve(message);
    });
    const child = this.child;
    const fail = (text) => {
      if (this.child === child) this.child = null;
      for (const entry of this.waiting.values()) {
        entry.resolve({ error: { code: -32603, message: text, data: { kind: 'failed' } } });
      }
      this.waiting.clear();
    };
    child.on('exit', () => fail('the oymap core stopped; call again'));
    child.on('error', (error) => fail(`could not start ${this.oymapPath}: ${error.message}`));
  }

  // One call: resolves {result} or {error: {code, message, data}} exactly as the core answered (typed refusals
  // keep their data.kind). Never rejects.
  call(method, params) {
    const run = () => new Promise((resolve) => {
      if (!this.child) this.start();
      const id = this.nextId++;
      this.waiting.set(id, { resolve });
      this.child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params: params ?? {} }) + '\n');
    }).then((message) => (message.error ? { error: message.error } : { result: message.result }));
    const answer = this.queue.then(run, run);
    this.queue = answer.then(() => undefined, () => undefined);
    return answer;
  }

  // The result, or a thrown Error carrying the core's error object (`error.rpc`).
  async request(method, params) {
    const answer = await this.call(method, params);
    if (answer.error) {
      const error = new Error(answer.error.message);
      error.rpc = answer.error;
      throw error;
    }
    return answer.result;
  }

  // Runs one oymap command line: {exit, stdout, stderr}. Only for the MCP tools that have no method of the request
  // list yet (tools.mjs says which); never reachable from a browser.
  run(command, args = []) {
    return this.request('run', { command, args: args.map(String) });
  }

  // Runs a command that prints JSON; throws with the command's own words when it fails without printing any.
  async json(command, args = []) {
    const result = await this.run(command, args);
    try {
      return { exit: result.exit, data: JSON.parse(result.stdout), stderr: result.stderr };
    } catch {
      throw new Error((result.stderr || result.stdout || `oymap ${command} failed`).trim());
    }
  }

  stop() {
    if (this.child) this.child.stdin.end();
  }

  // Cancels what the child is doing by killing it (lane J: the core is single-threaded and has no cooperative stop;
  // S5_BROWSER_EDITOR.md 2.4.3). Every waiting call answers `cancelled`; the next call starts a fresh child, whose
  // caches fill again. The core writes atomically, so a killed call leaves no half file.
  kill() {
    const child = this.child;
    if (!child) return false;
    this.child = null;
    for (const entry of this.waiting.values()) {
      entry.resolve({ error: { code: -32000, message: 'cancelled: the job was stopped', data: { kind: 'failed' } } });
    }
    this.waiting.clear();
    child.kill('SIGKILL');
    return true;
  }
}
