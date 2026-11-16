// The host's jobs (S5_BROWSER_EDITOR.md 2.4.3 "Jobs" and "Two lanes", 3.11, 3.14, 3.15, D10; slice S5a5): work that
// takes more than about a second runs here, never on lane I, so a click is never kept waiting behind it.
//
// Two lanes of jobs, each one job at a time:
//   core     lane J: a second `oymap serve` child of the same binary with its own caches (checks, compare). Cancel
//            kills the child (the core is single-threaded, with no cooperative stop) and the next call starts a fresh
//            one; the core writes atomically, so a killed call leaves no half file.
//   process  the Python checks (D10: local only, never in the hosted page) and the game's pictures and playtests:
//            child processes of their own, in their own process group, cancelled by killing the group. One at a time,
//            so one game runs at once (agents' runs: SDL_AUDIODRIVER=dummy, minimised).
// A process job that needs a build or an install asks lane J for it (build.run, session.configure, build.install).
//
// A job: {id, kind, project (the host's key), revision (the source revision it ran on), state queued | running |
// done | failed | cancelled, background, params, created, started, finished, seconds, progress (the last lines),
// error, result (its kind's output schema: schema/rpc/jobs.rpc.json $defs/<kind>_job_result), pictures (files under
// its folder)}. Its folder is <project>/.oymap/jobs/<revision>/<job>/ (job.json, result.json, log.txt, its pictures); the newest
// KEEP_JOBS jobs of a project are kept. Results belong to the revision they ran on: the scorecard greys a result whose
// revision is not the project's.
//
// Background checks (S5_BROWSER_EDITOR.md 2.5, W5): when a browser opens a project and after each change (a few
// seconds after the last), the kinds of backgroundKinds() are queued for the new revision unless a job of that kind
// already ran or waits for it; queued background jobs of older revisions are dropped.
import { spawn, spawnSync } from 'node:child_process';
import { randomBytes } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { indoorProfile, outdoorProfile, overviewPose, pagePicture, readLightingPages, shotConsole } from './lighting.mjs';

export const KINDS = {
  checks: { title: 'Audit, reach and solve', lane: 'core' },
  compare: { title: 'Compare with the original', lane: 'core' },
  scale_bands: { title: 'Room sizes against the shipped dungeons', lane: 'process', python: true },
  town_feel: { title: 'Town feel against the shipped towns', lane: 'process', python: true },
  building_shots: { title: 'Buildings beside the original\'s, in the game', lane: 'process', python: true, game: true },
  pins_tour: { title: 'The game\'s pictures at the pins\' poses', lane: 'process', game: true },
  playtest: { title: 'The project\'s playtest in the game', lane: 'process', game: true },
  // S6: the repository's Cycles bake on the project's build (lighting.mjs), local only.
  lighting_bake: { title: 'Lighting bake (Cycles), with pictures', lane: 'process', game: true, blender: true },
};

const KEEP_JOBS = 40;
const KEEP_LINES = 400;
const NOTICE_EVERY_MS = 250;
export const BACKGROUND_DELAY_MS = 3000;
const PICTURE = /\.(png|jpg)$/i;
// The lines a scenario's run logs: its steps, its failures and its verdict (as tools.mjs's map_playtest reads them).
const PLAYTEST_LINE = /^(PLAY|FAIL|ASSERT fail|Scenario|WALK done|CLICK)/;

// The background checks of a project (W5): indoor the audit with reach and solve, and the compare of a rebuild or
// the room sizes of a new map; outdoor the audit, the compare of a rebuild and the town feel; an overlay its audit.
export function backgroundKinds({ kind, reference, base }) {
  if (base) return ['checks'];
  if (kind === 'outdoor') return ['checks', ...(reference ? ['compare'] : []), 'town_feel'];
  return ['checks', reference ? 'compare' : 'scale_bands'];
}

// A job's params as jobs.rpc.json's $defs/job_params has them; the reason when not. The host checks them itself (its
// methods are not the core's): an `original` is a map's file name, never a path the core would read a project from.
export function jobParamsProblem(params) {
  const strings = (value, pattern) => Array.isArray(value) && value.length <= 200
    && value.every((item) => typeof item === 'string' && item.length > 0 && (!pattern || pattern.test(item)));
  const rules = {
    original: (value) => typeof value === 'string' && /^[A-Za-z0-9_-]+\.(blv|odm)$/.test(value),
    only: (value) => strings(value, /^[A-Za-z0-9_:.-]+$/),
    pins: (value) => strings(value, /^pin:[A-Za-z0-9_]+$/),
    status: (value) => strings(value, /^(open|claimed|resolved|accepted|declined)$/) && value.length <= 5,
    runs: (value) => Number.isInteger(value) && value >= 1 && value <= 8,
    scenario: (value) => typeof value === 'string' && /^[A-Za-z0-9_.-]+\.yml$/.test(value),
    start: (value) => typeof value === 'boolean',
    samples: (value) => Number.isInteger(value) && value >= 1 && value <= 1024,
    units_per_texel: (value) => Number.isInteger(value) && value >= 4 && value <= 64,
  };
  for (const [key, value] of Object.entries(params ?? {})) {
    if (!rules[key]) return `a job takes no param ${key}`;
    if (!rules[key](value)) return `the job's param ${key} is not of its form (jobs.rpc.json $defs/job_params)`;
  }
  return null;
}

// A job's answer to the browser: everything but its result (jobs.status gives that).
export function jobSummary(job) {
  const { result, ...rest } = publicJob(job);
  return { ...rest, has_result: rest.has_result === true || (result !== undefined && result !== null) };
}

// A job without what only the host holds while it runs (its processes, its whole log).
function publicJob(job) {
  const { children, log, lastNotice, cancelled, ...rest } = job;
  return rest;
}

// What a finished job says in one line (the Jobs panel, the notices).
export function resultLine(kind, result) {
  if (!result) return '';
  switch (kind) {
  case 'checks': {
    const counts = { error: 0, warning: 0, info: 0 };
    for (const finding of result.findings ?? []) counts[finding.severity] = (counts[finding.severity] ?? 0) + 1;
    const solve = result.solve ? `; solve ${result.solve.waves.length} steps, ${result.solve.never_reached.length} never reached` : '';
    return `${counts.error} errors, ${counts.warning} warnings; coplanar ${result.coplanar.new} new${solve}`;
  }
  case 'compare':
    return `${(result.score * 100).toFixed(1)} % (${result.band.within ? 'within' : 'outside'} the band of ${result.band.at_least * 100} %)`;
  case 'scale_bands':
    return `${result.below_p25} of ${result.figures.length} figures below the shipped 25th percentile`;
  case 'town_feel':
    return `${result.outside} of ${result.rules.length} figures outside the shipped ranges`;
  case 'building_shots':
    return `${result.buildings.length} buildings, ${result.pictures} pictures`;
  case 'pins_tour':
    return `${result.shots.filter((shot) => shot.picture).length} of ${result.shots.length} pins pictured`;
  case 'playtest':
    return `${result.passed} of ${result.runs} runs passed`;
  case 'lighting_bake':
    return `${result.pages.length} lightmap page(s), ${result.report.faces_lightmapped ?? '?'} faces lit`
      + `${result.report.bake_seconds !== undefined ? ` in ${result.report.bake_seconds} s of Cycles` : ''}`;
  default:
    return '';
  }
}

const writeJson = (file, value) => {
  mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.${process.pid}.tmp`;
  writeFileSync(temporary, JSON.stringify(value, null, 1) + '\n');
  renameSync(temporary, file);
};

const readJson = (file) => {
  try {
    return JSON.parse(readFileSync(file, 'utf8'));
  } catch {
    return null;
  }
};

export class Jobs {
  // context: {coreJ (lane J: a Core), coreI (lane I, for the revision), repo, assets, game, python, oymap,
  // mountOf(key) (the project's play mount), folderOf(key) (the jail), notify(key, method, params), log,
  // runGame (tools/run_game.sh), env (the games' environment)}
  constructor(context) {
    this.context = context;
    this.jobs = new Map();
    this.queues = { core: [], process: [] };
    this.running = { core: null, process: null };
    this.backgroundTimers = new Map();
    this.counters = { started: 0, done: 0, failed: 0, cancelled: 0 };
    this.python = context.python ?? (spawnSync('python3', ['--version']).status === 0);
  }

  // --- the folders --------------------------------------------------------------------------------------------------

  jobsRoot(folder) {
    return path.join(folder, '.oymap', 'jobs');
  }

  jobFolder(folder, job) {
    return path.join(this.jobsRoot(folder), job.revision, job.id);
  }

  save(job) {
    const folder = this.context.folderOf(job.project);
    if (!folder) return;
    const { result, ...record } = publicJob(job);
    record.has_result = record.has_result === true || (result !== undefined && result !== null);
    writeJson(path.join(this.jobFolder(folder, job), 'job.json'), record);
  }

  // Every job of a project on disk, newest first (the host may have started since they ran).
  onDisk(folder) {
    const root = this.jobsRoot(folder);
    const found = [];
    let revisions = [];
    try {
      revisions = readdirSync(root, { withFileTypes: true }).filter((entry) => entry.isDirectory());
    } catch {
      return found;
    }
    for (const revision of revisions) {
      let entries = [];
      try {
        entries = readdirSync(path.join(root, revision.name), { withFileTypes: true }).filter((entry) => entry.isDirectory());
      } catch {
        continue;
      }
      for (const entry of entries) {
        const file = path.join(root, revision.name, entry.name, 'job.json');
        const job = readJson(file);
        if (!job || job.id !== entry.name) continue;
        // A job a host left queued or running when it stopped (this host does not run it): it ended with that host.
        if ((job.state === 'queued' || job.state === 'running') && !this.jobs.has(job.id)) {
          Object.assign(job, { state: 'failed', error: 'the host stopped while it waited or ran', line: 'the host stopped while it waited or ran',
            finished: job.finished ?? new Date().toISOString() });
          writeJson(file, job);
        }
        found.push(job);
      }
    }
    return found.sort((a, b) => (a.created < b.created ? 1 : a.created > b.created ? -1 : 0));
  }

  // The newest KEEP_JOBS jobs stay; older folders (and empty revision folders) go.
  prune(folder) {
    const root = this.jobsRoot(folder);
    const all = this.onDisk(folder).filter((job) => job.state !== 'running' && job.state !== 'queued');
    for (const job of all.slice(KEEP_JOBS)) {
      rmSync(path.join(root, job.revision, job.id), { recursive: true, force: true });
    }
    try {
      for (const revision of readdirSync(root)) {
        const where = path.join(root, revision);
        if (statSync(where).isDirectory() && readdirSync(where).length === 0) rmSync(where, { recursive: true, force: true });
      }
    } catch {
      // nothing to prune
    }
  }

  // --- the methods ----------------------------------------------------------------------------------------------

  // jobs.list: the project's jobs, newest first (running and queued from memory, the rest from disk).
  list(key) {
    const folder = this.context.folderOf(key);
    if (!folder) return [];
    const byId = new Map(this.onDisk(folder).map((job) => [job.id, job]));
    for (const job of this.jobs.values()) {
      if (job.project === key) byId.set(job.id, job);
    }
    return [...byId.values()].sort((a, b) => (a.created < b.created ? 1 : a.created > b.created ? -1 : 0)).map(jobSummary);
  }

  // jobs.status: one job with its result.
  status(key, id) {
    const live = this.jobs.get(id);
    if (live && live.project === key) return publicJob(live);
    const folder = this.context.folderOf(key);
    if (!folder || !/^j[0-9a-z]+-[0-9a-f]+$/.test(id)) return null;
    const job = this.onDisk(folder).find((entry) => entry.id === id);
    if (!job) return null;
    const result = readJson(path.join(this.jobFolder(folder, job), 'result.json'));
    return result === null ? job : { ...job, result };
  }

  // jobs.start: a job queued on its lane; {job} or {error} (a kind the host cannot run here).
  async start(key, kind, params = {}, { background = false, revision = null } = {}) {
    const spec = KINDS[kind];
    const folder = this.context.folderOf(key);
    if (!spec || !folder) return { error: `no job kind ${kind}` };
    const problem = jobParamsProblem(params);
    if (problem) return { error: problem, invalid: true };
    if (spec.python && !this.python) {
      return { error: `${kind} runs a Python check of the repository: this machine has no python3 (local mode only)` };
    }
    if (spec.game && !(this.context.game && existsSync(this.context.game))) {
      return { error: `${kind} runs the game: the host was started without a game binary` };
    }
    if (spec.blender && !this.hasBlender()) {
      return { error: `${kind} runs Blender's Cycles (tools/lighting): this machine has no ${this.blenderCommand()} (local mode only; the host's --blender)` };
    }
    let rev = revision;
    if (!rev) {
      const status = await this.context.coreI.call('project.status', { project: folder });
      if (status.error) return { error: status.error.message };
      rev = status.result.revision;
    }
    const id = `j${Date.now().toString(36)}-${randomBytes(3).toString('hex')}`;
    const job = { id, kind, title: spec.title, project: key, revision: rev, state: 'queued', background, params,
      created: new Date().toISOString(), started: null, finished: null, seconds: null, progress: [], error: null,
      line: '', pictures: [] };
    this.jobs.set(id, job);
    this.save(job);
    this.queues[spec.lane].push(job);
    this.counters.started += 1;
    this.notify(job, 'job_progress');
    this.pump(spec.lane);
    return { job };
  }

  // jobs.cancel: a queued job leaves its queue; a running one is killed (lane J's child, or the job's processes).
  cancel(key, id) {
    const job = this.jobs.get(id);
    if (!job || job.project !== key) return null;
    if (job.state === 'queued') {
      const queue = this.queues[KINDS[job.kind].lane];
      queue.splice(queue.indexOf(job), 1);
      this.finish(job, 'cancelled', null, 'cancelled before it started');
      return job;
    }
    if (job.state === 'running') {
      job.cancelled = true;
      if (KINDS[job.kind].lane === 'core' && this.running.core === job) this.context.coreJ.kill();
      for (const child of job.children ?? []) this.killGroup(child);
      // A step between two processes (a lane J call it waits for) notices `cancelled` when it returns.
    }
    return job;
  }

  // The host is closing: no more background checks, and the jobs' processes go with it.
  stop() {
    for (const timer of this.backgroundTimers.values()) clearTimeout(timer);
    this.backgroundTimers.clear();
    for (const lane of Object.keys(this.queues)) this.queues[lane].length = 0;
    for (const job of Object.values(this.running)) {
      if (!job) continue;
      job.cancelled = true;
      for (const child of job.children ?? []) this.killGroup(child);
    }
  }

  // --- background checks --------------------------------------------------------------------------------------

  // A project opened, or changed: its background checks a few seconds later, for the revision it has then.
  scheduleBackground(key, delay = BACKGROUND_DELAY_MS) {
    if (this.backgroundTimers.has(key)) clearTimeout(this.backgroundTimers.get(key));
    this.backgroundTimers.set(key, setTimeout(() => {
      this.backgroundTimers.delete(key);
      void this.background(key).catch((error) => this.context.log?.(`background ${key}: ${error.message}`));
    }, delay));
  }

  async background(key) {
    const folder = this.context.folderOf(key);
    if (!folder) return [];
    const status = await this.context.coreI.call('project.status', { project: folder });
    if (status.error || status.result.unreadable?.length) return [];
    const revision = status.result.revision;
    // A revision with errors is not checked (S5b1): the checks measure the built map, and a project with errors is
    // only ever lowered as a view build without the objects it cannot lower. The scorecard keeps the last revision
    // measured, greyed, until the errors are fixed.
    const validated = await this.context.coreI.call('check.validate', { project: folder });
    if (!validated.error && validated.result.ok === false) {
      this.context.log?.(`background ${key}: not checked at ${revision.slice(0, 12)}: the project has errors`);
      return [];
    }
    // Queued background jobs of older revisions would only measure the past.
    for (const lane of Object.keys(this.queues)) {
      for (const job of [...this.queues[lane]]) {
        if (job.project === key && job.background && job.revision !== revision) {
          this.queues[lane].splice(this.queues[lane].indexOf(job), 1);
          this.finish(job, 'cancelled', null, 'the project changed before it started');
        }
      }
    }
    const info = this.context.infoOf(key);
    const known = this.list(key).filter((job) => job.revision === revision && job.state !== 'cancelled'
      && job.state !== 'failed');
    const started = [];
    for (const kind of backgroundKinds(info)) {
      if (known.some((job) => job.kind === kind)) continue;
      if (KINDS[kind].python && !this.python) continue;
      const answer = await this.start(key, kind, {}, { background: true, revision });
      if (answer.job) started.push(answer.job);
    }
    return started;
  }

  // --- running ------------------------------------------------------------------------------------------------

  pump(lane) {
    if (this.running[lane] || this.queues[lane].length === 0) return;
    const job = this.queues[lane].shift();
    this.running[lane] = job;
    void this.run(job).finally(() => {
      this.running[lane] = null;
      this.pump(lane);
    });
  }

  notify(job, method) {
    this.context.notify?.(job.project, method, { job: jobSummary(job) });
  }

  progress(job, text) {
    for (const line of String(text).split('\n')) {
      if (!line.trim()) continue;
      job.progress.push(line);
      job.line = line.length > 200 ? `${line.slice(0, 200)}…` : line;
      job.log = (job.log ?? '') + line + '\n';
    }
    if (job.progress.length > 20) job.progress.splice(0, job.progress.length - 20);
    const now = Date.now();
    if (!job.lastNotice || now - job.lastNotice >= NOTICE_EVERY_MS) {
      job.lastNotice = now;
      this.notify(job, 'job_progress');
    }
  }

  finish(job, state, result, error = null) {
    job.state = state;
    job.finished = new Date().toISOString();
    job.seconds = job.started ? Math.round((Date.parse(job.finished) - Date.parse(job.started)) / 100) / 10 : 0;
    job.error = error;
    job.result = result ?? undefined;
    job.line = state === 'done' ? resultLine(job.kind, result) : error ?? state;
    const folder = this.context.folderOf(job.project);
    if (folder) {
      const where = this.jobFolder(folder, job);
      if (result) writeJson(path.join(where, 'result.json'), result);
      if (job.log) {
        mkdirSync(where, { recursive: true });
        writeFileSync(path.join(where, 'log.txt'), job.log.split('\n').slice(-KEEP_LINES).join('\n'));
      }
    }
    delete job.log;
    delete job.children;
    delete job.lastNotice;
    delete job.cancelled;
    this.counters[state === 'done' ? 'done' : state === 'cancelled' ? 'cancelled' : 'failed'] += 1;
    this.save(job);
    this.notify(job, 'job_done');
    this.context.log?.(`job ${job.id} ${job.kind} ${job.project}: ${state} in ${job.seconds} s ${job.line}`);
    this.jobs.delete(job.id);
    if (folder) this.prune(folder);
  }

  async run(job) {
    const folder = this.context.folderOf(job.project);
    job.state = 'running';
    job.started = new Date().toISOString();
    this.save(job);
    this.notify(job, 'job_progress');
    try {
      const runner = RUNNERS[job.kind];
      const result = await runner.call(this, job, folder, this.jobFolder(folder, job));
      if (job.cancelled) this.finish(job, 'cancelled', null, 'cancelled');
      else this.finish(job, 'done', result);
    } catch (error) {
      this.finish(job, job.cancelled ? 'cancelled' : 'failed', null, job.cancelled ? 'cancelled' : String(error.message ?? error));
    }
  }

  // A lane J call; throws with the core's words (or `cancelled`).
  async coreJ(job, method, params) {
    if (job.cancelled) throw new Error('cancelled');
    this.progress(job, `${method}`);
    const answer = await this.context.coreJ.call(method, params);
    if (job.cancelled) throw new Error('cancelled');
    if (answer.error) throw new Error(answer.error.message);
    return answer.result;
  }

  // A child process of the job, in a process group of its own (cancel kills the group); its lines are progress.
  // A step that runs longer than `timeoutMs` (default half an hour; building_shots takes about 35 minutes for two
  // maps and passes more) is killed and fails the job.
  spawnStep(job, command, args, { env, cwd, answerOnStdout = false, timeoutMs = 30 * 60 * 1000 } = {}) {
    if (job.cancelled) return Promise.reject(new Error('cancelled'));
    return new Promise((resolve, reject) => {
      const child = spawn(command, args, { cwd: cwd ?? this.context.repo, env: env ?? process.env, detached: true,
        stdio: ['ignore', 'pipe', 'pipe'] });
      job.children = [...(job.children ?? []), child];
      let timedOut = false;
      const timer = setTimeout(() => {
        timedOut = true;
        this.killGroup(child);
      }, timeoutMs);
      timer.unref();
      let stdout = '';
      let stderr = '';
      const lines = (chunk, keep) => {
        const text = chunk.toString();
        if (keep === 'out') stdout += text;
        else stderr += text;
        // A check that answers in JSON on its standard output: only its other stream is progress.
        if (keep === 'err' || !answerOnStdout) this.progress(job, text);
      };
      child.stdout.on('data', (chunk) => lines(chunk, 'out'));
      child.stderr.on('data', (chunk) => lines(chunk, 'err'));
      child.on('error', reject);
      child.on('close', (code, signal) => {
        clearTimeout(timer);
        job.children = (job.children ?? []).filter((other) => other !== child);
        if (job.cancelled) reject(new Error('cancelled'));
        else if (timedOut) reject(new Error(`${path.basename(command)} ran longer than ${Math.round(timeoutMs / 1000)} s`));
        else resolve({ code, signal, stdout, stderr });
      });
    });
  }

  killGroup(child) {
    if (child.exitCode !== null || child.signalCode !== null) return;
    try {
      process.kill(-child.pid, 'SIGTERM');
    } catch {
      child.kill('SIGTERM');
    }
    setTimeout(() => {
      try {
        if (child.exitCode === null && child.signalCode === null) process.kill(-child.pid, 'SIGKILL');
      } catch {
        // gone
      }
    }, 2000).unref();
  }

  blenderCommand() {
    return this.context.blender ?? 'blender';
  }

  // Whether Blender answers (asked once: a snap's Blender takes a second to start).
  hasBlender() {
    this.blender ??= spawnSync(this.blenderCommand(), ['--version'], { timeout: 60000 }).status === 0;
    return this.blender;
  }

  // The game's picture of a map of a scratch asset root at the party's start, without the HUD (lighting_bake's before
  // and after); null when it took none.
  async gameShot(job, root, world, map, file, pose = null) {
    mkdirSync(path.dirname(file), { recursive: true });
    const consoleFile = `${file}.console`;
    writeFileSync(consoleFile, shotConsole(pose));
    const run = await this.spawnStep(job, this.context.runGame, ['--isolated', `studio-${job.id}-${path.basename(file, '.png')}`,
      '--world', world, '--map', map, '--assets', root, '--warmup', '3', '--seconds', '16',
      '--set', `debug.startup_console_file=${consoleFile}`, '--set', `debug.screenshot_path=${file}`,
      '--set', 'debug.screenshot_delay_seconds=5'], { env: this.gameEnv() });
    rmSync(consoleFile, { force: true });
    if (!existsSync(file)) {
      this.progress(job, `the game took no picture (exit ${run.code}): ${run.stderr.trim().split('\n').slice(-2).join(' ')}`);
      return null;
    }
    return file;
  }

  pythonEnv() {
    return { ...process.env, OYMAP: this.context.oymap, PYTHONDONTWRITEBYTECODE: '1' };
  }

  gameEnv() {
    return { ...(this.context.env ?? process.env), SDL_AUDIODRIVER: 'dummy' };
  }

  calibration(name) {
    return path.join(this.context.repo, 'openyamm-studio', 'calibration', name);
  }

  // The project built and installed into its own play mount (with an outdoor map's terrain material file): what a
  // game run of the job reads in front of the asset root.
  async buildAndInstall(job, folder) {
    const built = await this.coreJ(job, 'build.run', { project: folder, dry_run: false });
    if (built.kind === 'overlay') throw new Error('an overlay project changes a shipped map: this job plays new maps only');
    const mount = this.context.mountOf(job.project);
    mkdirSync(mount, { recursive: true });
    await this.coreJ(job, 'session.configure', { asset_root: this.context.assets, mount });
    await this.coreJ(job, 'build.install', { project: folder });
    if (built.kind === 'outdoor') {
      const materials = await this.spawnStep(job, 'python3', [this.calibration('outdoor_materials.py'), folder, '--mount', mount],
        { env: this.pythonEnv() });
      if (materials.code !== 0) throw new Error(`the terrain material file was not made: ${materials.stderr.trim().split('\n').at(-1)}`);
    }
    return { built, mount };
  }
}

// A Python check's JSON answer: the last line block that parses (scripts print progress lines before it).
function pythonJson(output, what) {
  const start = output.stdout.indexOf('{');
  if (start < 0) {
    throw new Error(`${what} gave no answer: ${(output.stderr || output.stdout).trim().split('\n').slice(-3).join(' ')}`);
  }
  try {
    return JSON.parse(output.stdout.slice(start));
  } catch (error) {
    throw new Error(`${what} gave an answer that does not parse: ${error.message}`);
  }
}

const RUNNERS = {
  // check.audit with reach and (indoors) the solve, from one walk.
  async checks(job, folder) {
    const info = this.context.infoOf(job.project);
    return this.coreJ(job, 'check.audit', { map: folder, reach: true, solve: info.kind !== 'outdoor' && !info.base });
  },

  async compare(job, folder) {
    const params = { map: folder };
    if (job.params?.original) params.original = job.params.original;
    return this.coreJ(job, 'compare.run', params);
  },

  async scale_bands(job, folder) {
    const output = await this.spawnStep(job, 'python3', [this.calibration('scale_bands.py'), folder, '--json', '--assets',
      this.context.assets], { env: this.pythonEnv(), answerOnStdout: true });
    return pythonJson(output, 'scale_bands.py');
  },

  async town_feel(job, folder) {
    await this.coreJ(job, 'build.run', { project: folder, dry_run: false });
    const args = [this.calibration('town_feel.py'), '--project', folder, '--assets', this.context.assets, '--report-json'];
    if (job.params?.start) args.push('--start');
    const output = await this.spawnStep(job, 'python3', args, { env: this.pythonEnv(), answerOnStdout: true });
    return pythonJson(output, 'town_feel.py');
  },

  async building_shots(job, folder, where) {
    const info = this.context.infoOf(job.project);
    if (!info.reference) throw new Error('building_shots pairs a rebuild with its original: the project names none (map_stats.reference)');
    const { built, mount } = await this.buildAndInstall(job, folder);
    const out = path.join(where, 'shots');
    const args = [this.calibration('building_shots.py'), built.map, '--original', info.reference, '--world', info.world,
      '--assets', this.context.assets, '--mount', mount, '--build', path.join(folder, 'build', 'build.json'), '--out', out];
    if (Array.isArray(job.params?.only) && job.params.only.length > 0) args.push('--only', job.params.only.join(','));
    const output = await this.spawnStep(job, 'python3', args, { env: { ...this.pythonEnv(), SDL_AUDIODRIVER: 'dummy' },
      timeoutMs: 3 * 60 * 60 * 1000 });
    const index = readJson(path.join(out, 'index.json'));
    if (output.code !== 0 || !index) throw new Error(`building_shots.py failed: ${output.stderr.trim().split('\n').slice(-2).join(' ')}`);
    job.pictures = index.buildings.flatMap((building) => building.pictures.map((picture) => `shots/${picture}`));
    return { original: index.original, rebuilt: index.rebuilt, views: index.views, pictures: job.pictures.length,
      buildings: index.buildings.map((building) => ({ id: building.id, title: building.title, views: building.views,
        skipped: building.skipped, pictures: building.pictures.map((picture) => `shots/${picture}`),
        contact: building.contact ? `shots/${building.contact}` : null })) };
  },

  async pins_tour(job, folder, where) {
    const tourParams = { project: folder };
    if (Array.isArray(job.params?.pins) && job.params.pins.length > 0) tourParams.pins = job.params.pins;
    if (Array.isArray(job.params?.status) && job.params.status.length > 0) tourParams.status = job.params.status;
    const tour = await this.coreJ(job, 'pins.tour', tourParams);
    if (tour.shots.length === 0) return { map: tour.map, world: tour.world, shots: [], skipped: tour.skipped };
    const { built, mount } = await this.buildAndInstall(job, folder);
    const pictures = path.join(where, 'pictures');
    mkdirSync(pictures, { recursive: true });
    const lines = [`output_dir: ${JSON.stringify(pictures)}`, 'settle_seconds: 1.5', 'exit: true', 'shots:'];
    for (const shot of tour.shots) {
      // Review pictures without the HUD (the console's `render hud off`, as building_shots.py's tours).
      lines.push(`  - {name: ${JSON.stringify(shot.name)}, position: [${shot.position.join(', ')}], yaw: ${shot.yaw_radians}, `
        + `pitch: ${shot.pitch_radians}, commands: ["render hud off"]}`);
    }
    const tourFile = path.join(where, 'tour.yml');
    writeFileSync(tourFile, lines.join('\n') + '\n');
    const world = tour.world || this.context.infoOf(job.project).world;
    const map = built.map;
    const run = await this.spawnStep(job, this.context.runGame, ['--isolated', `studio-${job.id}`, '--world', world,
      '--map', map, '--assets', this.context.assets, '--extra-mount', mount, '--warmup', '3',
      '--seconds', String(30 + 4 * tour.shots.length), '--set', `debug.screenshot_tour_path=${tourFile}`],
    { env: this.gameEnv() });
    const taken = existsSync(pictures) ? readdirSync(pictures).filter((name) => PICTURE.test(name)).sort() : [];
    job.pictures = taken.map((name) => `pictures/${name}`);
    const shots = tour.shots.map((shot) => {
      const picture = taken.find((name) => name === `${shot.name}.png` || name.endsWith(`-${shot.name}.png`));
      return { pin: shot.pin, name: shot.name, picture: picture ? `pictures/${picture}` : null };
    });
    if (!shots.some((shot) => shot.picture)) {
      throw new Error(`the game took no picture (exit ${run.code}): ${run.stderr.trim().split('\n').slice(-2).join(' ')}`);
    }
    return { map, world, shots, skipped: tour.skipped };
  },

  // The repository's bake on the project's build (lighting.mjs): a hard-link copy of the asset root with the build
  // installed into it, the game's picture before, Blender's Cycles bake, the sidecar's pages as pictures, the sidecar
  // beside the map in the copy and the game's picture after. The copy is removed at the end; the asset root is not
  // written.
  async lighting_bake(job, folder, where) {
    const info = this.context.infoOf(job.project);
    if (info.base) {
      throw new Error('an overlay project changes a shipped map\'s scene and script: the map keeps its base\'s bake (a sidecar is keyed on the BLV\'s geometry); bake new maps and rebuilds');
    }
    const built = await this.coreJ(job, 'build.run', { project: folder, dry_run: false });
    const outdoor = built.kind === 'outdoor';
    const world = info.world || 'mm6';
    const stem = built.map.replace(/\.(blv|odm)$/i, '');
    const roots = this.context.bakeRoots ?? path.join(this.context.repo, 'output', 'studio_host', 'bake_roots');
    // The copy in a folder of the job's own: the game makes folders beside its asset root (assets_editor_dev).
    const jobRoot = path.join(roots, job.id);
    const root = path.join(jobRoot, 'assets');
    if (path.resolve(root) === path.resolve(this.context.assets)) throw new Error('the scratch copy would be the asset root');
    mkdirSync(jobRoot, { recursive: true });
    const pictures = path.join(where, 'pictures');
    mkdirSync(pictures, { recursive: true });
    const lastLines = (output) => (output.stderr || output.stdout).trim().split('\n').slice(-3).join(' ');
    try {
      this.progress(job, 'a hard-link copy of the asset root (cp -al)');
      const copied = await this.spawnStep(job, 'cp', ['-al', this.context.assets, root]);
      if (copied.code !== 0) {
        throw new Error(`the asset root was not copied (hard links need the asset root's disk: the host's bake roots, output/studio_host/bake_roots): ${lastLines(copied)}`);
      }
      const installed = await this.spawnStep(job, this.context.oymap, ['install', folder, '--root', root]);
      if (installed.code !== 0) throw new Error(`the build was not installed into the copy: ${lastLines(installed)}`);
      if (outdoor) {
        const materials = await this.spawnStep(job, 'python3', [this.calibration('outdoor_materials.py'), folder, '--root', root],
          { env: this.pythonEnv() });
        if (materials.code !== 0) throw new Error(`the terrain material file was not made: ${lastLines(materials)}`);
      }
      // Both pictures from one pose across the start's room (the layout as the view builds it).
      const layout = await this.coreJ(job, 'view.layout', { project: folder }).catch(() => null);
      const pose = overviewPose(layout);
      const before = await this.gameShot(job, root, world, built.map, path.join(pictures, 'before.png'), pose);

      // The bake, with the job's profile.
      const samples = Number(job.params?.samples ?? 32);
      const profile = outdoor
        ? outdoorProfile(JSON.parse(readFileSync(path.join(this.context.repo, 'tools', 'lighting', 'baked_outdoors', 'profiles', 'mm6_oute3.yml'), 'utf8')),
          { world, map: built.map, samples })
        : indoorProfile({ world, map: built.map, samples, unitsPerTexel: Number(job.params?.units_per_texel ?? 16) });
      const profileFile = path.join(where, 'profile.json');
      writeFileSync(profileFile, JSON.stringify(profile, null, 1) + '\n');
      const out = path.join(where, 'bake');
      const script = path.join(this.context.repo, 'tools', 'lighting', outdoor ? 'bake_outdoor.py' : 'bake_indoor.py');
      const baked = await this.spawnStep(job, this.blenderCommand(), ['--background', '--factory-startup', '--python-exit-code', '1',
        '--python', script, '--', '--profile', profileFile, '--output', out, '--assets', root,
        '--sources', path.join(this.context.repo, 'assets_source'), '--game-binary', this.context.game],
      { env: { ...this.pythonEnv(), SDL_AUDIODRIVER: 'dummy' }, timeoutMs: 2 * 60 * 60 * 1000 });
      const sidecar = path.join(out, `${stem}.lighting`);
      if (baked.code !== 0 || !existsSync(sidecar)) throw new Error(`the bake failed (exit ${baked.code}): ${lastLines(baked)}`);

      // Its pages as pictures.
      const read = readLightingPages(readFileSync(sidecar));
      const pages = read.pages.map((page, index) => {
        const drawn = pagePicture(page);
        const name = `pictures/page_${index}.png`;
        writeFileSync(path.join(where, name), drawn.png);
        return { width: page.width, height: page.height, picture: name, mean: Math.round(drawn.mean * 1000) / 1000, covered: drawn.covered };
      });

      // The sidecar beside the map in the copy (as one installs it: INDOOR_BAKED_LIGHTING.md), and the game again.
      const maps = path.join(root, 'worlds', world, 'maps');
      const recipe = path.join(out, `${stem}.bake.json`);
      for (const file of [sidecar, recipe].filter((name) => existsSync(name))) {
        const target = path.join(maps, path.basename(file));
        // A new file in the copy's folder (a name of the asset root would be unlinked first, never written through).
        rmSync(target, { force: true });
        copyFileSync(file, target);
      }
      const after = await this.gameShot(job, root, world, built.map, path.join(pictures, 'after.png'), pose);
      job.pictures = [...(before ? ['pictures/before.png'] : []), ...(after ? ['pictures/after.png'] : []), ...pages.map((page) => page.picture)];
      const report = readJson(path.join(out, 'report.json')) ?? {};
      const kept = Object.fromEntries(['faces_lightmapped', 'face_count', 'charts', 'texels', 'pages', 'bake_seconds', 'blender', 'output_bytes',
        'lights', 'emitter_faces'].filter((key) => report[key] !== undefined).map((key) => [key, report[key]]));
      return { map: built.map, world, family: read.family, version: read.version, pages,
        before: before ? 'pictures/before.png' : null, after: after ? 'pictures/after.png' : null, report: kept,
        sidecar: [sidecar, recipe].filter((name) => existsSync(name)).map((name) => path.relative(where, name)) };
    } finally {
      rmSync(jobRoot, { recursive: true, force: true });
    }
  },

  async playtest(job, folder) {
    const name = job.params?.scenario ?? 'playtest.yml';
    if (!/^[A-Za-z0-9_.-]+\.yml$/.test(name) || !existsSync(path.join(folder, name))) {
      throw new Error(`the project has no scenario ${name}`);
    }
    const runs = Math.min(Math.max(Number(job.params?.runs ?? 1) || 1, 1), 8);
    const { mount } = await this.buildAndInstall(job, folder);
    const info = this.context.infoOf(job.project);
    // The scenario runs headless in a folder of its own (the game writes its run files beside it).
    const runFolder = path.join(path.dirname(mount), `playtest_${job.id}`);
    mkdirSync(runFolder, { recursive: true });
    const results = [];
    let log = [];
    for (let run = 1; run <= runs; ++run) {
      this.progress(job, `run ${run} of ${runs}`);
      const output = await this.spawnStep(job, this.context.game, ['--asset-root', this.context.assets, '--extra-mount',
        mount, '--world', info.world, '--headless-run-scenario', path.join(folder, name), '--scenario-no-color'],
      { cwd: runFolder, env: this.gameEnv() });
      const text = `${output.stdout}\n${output.stderr}`;
      log = text.split('\n').filter((line) => PLAYTEST_LINE.test(line));
      const passed = /^Scenario passed/m.test(text);
      const failure = log.find((line) => /^(FAIL|ASSERT fail)/.test(line)) ?? null;
      results.push({ passed, failure });
      this.progress(job, `run ${run}: ${passed ? 'passed' : `failed${failure ? `: ${failure}` : ''}`}`);
    }
    rmSync(runFolder, { recursive: true, force: true });
    return { scenario: name, runs, passed: results.filter((entry) => entry.passed).length, results,
      log: log.length > 80 ? [...log.slice(0, 80), `... ${log.length - 80} more`] : log };
  },
};
