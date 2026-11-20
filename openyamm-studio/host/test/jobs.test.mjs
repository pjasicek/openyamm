// The host's jobs (S5_BROWSER_EDITOR.md 2.4.3, 3.11, D10; S5a5: src/jobs.mjs): the background checks a browser's
// opening starts (lane J and the Python checks), their results against the output schemas of jobs.rpc.json, no
// second run for the same revision, a change queuing them again, cancel by kill (lane J started again for the next
// job), a queued job dropped, the job byte route, refusals, and the jobs read back by a new host from disk.
// Works on scratch copies of an example project and of Castle Darkmoor's (a check slow enough to cancel).
//   node test/jobs.test.mjs        (OYMAP=<binary>; JOBS_GAME=1 also runs a pins tour and a playtest in the game)
import assert from 'node:assert/strict';
import { cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import http from 'node:http';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import WebSocket from 'ws';
import { backgroundKinds, resultLine } from '../src/jobs.mjs';
import { readOriginal } from '../src/projects.mjs';
import { startStudio } from '../src/studio.mjs';

const started = performance.now();
const here = path.dirname(fileURLToPath(import.meta.url));
const studioDir = path.resolve(here, '../..');
const repo = path.resolve(studioDir, '..');
const assets = path.join(repo, 'assets_dev');
const oymap = process.env.OYMAP ?? path.join(studioDir, 'build-s4/oymap');
const withGame = process.env.JOBS_GAME === '1';
const token = 'jobs-' + Math.random().toString(36).slice(2);
const port = 30000 + Math.floor(Math.random() * 5000);

// The background kinds, by project.
assert.deepEqual(backgroundKinds({ kind: 'indoor', reference: '6d01.blv', base: '' }), ['checks', 'compare']);
assert.deepEqual(backgroundKinds({ kind: 'indoor', reference: '', base: '' }), ['checks', 'scale_bands']);
assert.deepEqual(backgroundKinds({ kind: 'outdoor', reference: '7out02.odm', base: '' }), ['checks', 'compare', 'town_feel']);
assert.deepEqual(backgroundKinds({ kind: 'outdoor', reference: '', base: '' }), ['checks', 'town_feel']);
assert.deepEqual(backgroundKinds({ kind: '', reference: '', base: '6d01.blv' }), ['checks']);

// The output schemas (ajv comes with the MCP SDK; the contract suite uses it the same way).
const require = createRequire(import.meta.url);
const Ajv2020 = require('ajv/dist/2020').default;
const ajv = new Ajv2020({ strict: false, allErrors: true });
ajv.addKeyword({
  keyword: 'x-decimals',
  type: 'number',
  schemaType: 'number',
  validate: (decimals, value) => Math.abs(Math.round(value * 10 ** decimals) / 10 ** decimals - value) === 0,
});
const rpcDir = path.join(studioDir, 'schema/rpc');
const base = 'https://openyamm.local/schema/';
for (const file of [...readdirSync(rpcDir).filter((n) => n.endsWith('.rpc.json')).map((n) => path.join(rpcDir, n)),
  ...readdirSync(path.join(studioDir, 'schema')).filter((n) => n.endsWith('.schema.json'))
    .map((n) => path.join(studioDir, 'schema', n))]) {
  ajv.addSchema({ ...JSON.parse(readFileSync(file, 'utf8')), $id: base + path.basename(file) });
}
const valid = (ref, value) => {
  const validate = ajv.getSchema(base + ref);
  assert.ok(validate, `no schema ${ref}`);
  if (!validate(value)) {
    assert.fail(`${ref}: ${ajv.errorsText(validate.errors)}`);
  }
};

// Scratch copies: the example (indoor, a rebuild of Goblinwatch by its card), a new map (no reference), Darkmoor.
const scratch = mkdtempSync(path.join(tmpdir(), 'oymap-jobs-'));
const root = path.join(scratch, 'projects');
const copy = (from, to) => cpSync(from, path.join(root, to), { recursive: true,
  filter: (source) => !/\/(\.oymap|build|gen)(\/|$)/.test(source) });
copy(path.join(studioDir, 'examples/gatehouse_cellars'), 'cellars');
copy(path.join(studioDir, 'examples/gatehouse_cellars'), 'fresh');
copy(path.join(repo, 'devdocs/map_studio/briefs/mm6_cd2/L4'), 'darkmoor');
// The fresh copy names no original: a new map (its encounter slots in full).
const freshCard = path.join(root, 'fresh', 'project.yml');
writeFileSync(freshCard, readFileSync(freshCard, 'utf8').replace(/^  reference: .*$/m,
  '  slots:\n    - {monster: Rat, tier: 1, per_marker: [2, 3], weight: 100}'));
assert.deepEqual(readOriginal(freshCard), { reference: '', base: '' });
assert.deepEqual(readOriginal(path.join(root, 'cellars', 'project.yml')), { reference: '6d01.blv', base: '' });

const logLines = [];
const host = await startStudio({ port, token, repo, assets, mount: null, roots: [root], web: path.join(scratch, 'no-web'),
  rpcDir, oymap, game: path.join(repo, 'build/game/openyamm'), inbox: path.join(scratch, 'inbox'),
  discovery: path.join(scratch, 'host.json'), playMounts: path.join(scratch, 'play_mounts'),
  log: (line) => { logLines.push(line); if (process.env.OYMAP_HOST_LOG) console.error(`host: ${line}`); } });
const keyOf = (name) => host.jail.keyOf(path.join(root, name));

async function browser() {
  const socket = await new Promise((resolve, reject) => {
    const client = new WebSocket(`ws://127.0.0.1:${port}/rpc?token=${token}`, { origin: `http://127.0.0.1:${port}` });
    client.once('open', () => resolve(client));
    client.once('error', reject);
  });
  let nextId = 1;
  const waiting = new Map();
  const notices = [];
  const watchers = [];
  socket.on('message', (data) => {
    const message = JSON.parse(String(data));
    if (message.id === undefined || message.id === null) {
      notices.push(message);
      for (const watcher of [...watchers]) watcher();
      return;
    }
    waiting.get(message.id)?.(message);
    waiting.delete(message.id);
  });
  return {
    socket, notices,
    ask: (method, params) => new Promise((resolve) => {
      const id = nextId++;
      waiting.set(id, resolve);
      socket.send(JSON.stringify({ jsonrpc: '2.0', id, method, params }));
    }),
    next: (test, ms, from = 0) => new Promise((resolve, reject) => {
      const look = () => {
        const found = notices.slice(from).find(test);
        if (found) {
          watchers.splice(watchers.indexOf(look), 1);
          clearTimeout(timer);
          resolve(found);
        }
      };
      const timer = setTimeout(() => {
        watchers.splice(watchers.indexOf(look), 1);
        reject(new Error(`no such notice within ${ms} ms; got ${JSON.stringify(notices.slice(from).map((n) => [n.method, n.params?.job?.kind, n.params?.job?.state]))}`));
      }, ms);
      watchers.push(look);
      look();
    }),
  };
}

const get = (route, headers = {}) => new Promise((resolve, reject) => {
  http.get({ host: '127.0.0.1', port, path: route, headers: { Host: `127.0.0.1:${port}`, ...headers } }, (response) => {
    const chunks = [];
    response.on('data', (chunk) => chunks.push(chunk));
    response.on('end', () => resolve({ status: response.statusCode, body: Buffer.concat(chunks) }));
  }).on('error', reject);
});

const done = (key, kind, revision) => (notice) => notice.method === 'job_done' && notice.params.project === key
  && notice.params.job.kind === kind && (!revision || notice.params.job.revision === revision);

const a = await browser();
const hello = await a.ask('session.hello', {});
assert.equal(hello.result.host.jobs, true);
assert.equal(typeof hello.result.host.python, 'boolean');

// 1. Opening a rebuild: its checks and its compare in the background, each against its output schema.
const cellars = keyOf('cellars');
let t0 = performance.now();
const opened = await a.ask('host.subscribe', { project: cellars });
const revision = opened.result.revision;
const checksDone = await a.next(done(cellars, 'checks', revision), 120000);
const compareDone = await a.next(done(cellars, 'compare', revision), 120000);
const filled = Math.round(performance.now() - t0);
for (const notice of [checksDone, compareDone]) {
  assert.equal(notice.params.job.state, 'done', JSON.stringify(notice.params.job));
  assert.equal(notice.params.job.background, true);
  valid('jobs.rpc.json#/$defs/job', notice.params.job);
}
const checks = (await a.ask('jobs.status', { project: cellars, job: checksDone.params.job.id })).result.job;
valid('jobs.rpc.json#/$defs/job', checks);
valid('jobs.rpc.json#/$defs/checks_job_result', checks.result);
assert.ok(checks.result.solve, 'the checks of an indoor map carry the solve');
assert.ok(checks.result.reachability.ran);
const compared = (await a.ask('jobs.status', { project: cellars, job: compareDone.params.job.id })).result.job;
valid('jobs.rpc.json#/$defs/compare_job_result', compared.result);
assert.equal(compared.result.original, '6d01.blv');
assert.match(compared.line, /% \((within|outside) the band of 97 %\)/);
assert.equal(resultLine('compare', compared.result), compared.line);
console.log(`a rebuild's scorecard filled in ${filled} ms (checks ${checks.seconds} s, compare ${compared.seconds} s)`);

// The progress notices came first: queued, then running.
const states = a.notices.filter((n) => n.method === 'job_progress' && n.params.job.id === checks.id).map((n) => n.params.job.state);
assert.equal(states[0], 'queued');
assert.ok(states.includes('running'));

// 2. Opening again at the same revision queues nothing new.
let mark = a.notices.length;
await a.ask('host.subscribe', { project: null });
await a.ask('host.subscribe', { project: cellars });
await new Promise((resolve) => setTimeout(resolve, 1800));
assert.equal(a.notices.slice(mark).filter((n) => n.method === 'job_progress').length, 0, 'no second run for a revision');
const listed = (await a.ask('jobs.list', { project: cellars })).result.jobs;
assert.equal(listed.length, 2);
assert.ok(listed.every((job) => job.result === undefined && job.has_result === true));
valid('jobs.rpc.json#/methods/list/result', { jobs: listed });

// 3. The job's files through the byte route: the token, the jail and the path rules.
const route = `/job/${encodeURIComponent(cellars)}/${checks.revision}/${checks.id}/log.txt`;
assert.equal((await get(route)).status, 401);
const log = await get(route, { Authorization: `Bearer ${token}` });
assert.equal(log.status, 200);
assert.match(String(log.body), /check\.audit/);
assert.equal((await get(`/job/${encodeURIComponent(cellars)}/${checks.revision}/${checks.id}/..%2Fjob.json`,
  { Authorization: `Bearer ${token}` })).status, 404);
assert.equal((await get(`/job/${encodeURIComponent(cellars)}/${checks.revision}/${checks.id}/job.json`,
  { Authorization: `Bearer ${token}` })).status, 404);

// 4. A change: the background checks again for the new revision.
mark = a.notices.length;
const edited = await a.ask('edit.apply', { project: cellars, author: 'user', label: 'a slower gate',
  ops: [{ op: 'set', id: 'door:gate', fields: { speed: 70 } }] });
assert.equal(edited.result.applied, true);
const revision2 = edited.result.revision_after;
await a.next(done(cellars, 'checks', revision2), 120000, mark);
await a.next(done(cellars, 'compare', revision2), 120000, mark);
assert.equal((await a.ask('jobs.list', { project: cellars })).result.jobs.length, 4);

// 5. A new map: its room sizes against the shipped dungeons (calibration/scale_bands.py), when Python is here.
const fresh = keyOf('fresh');
if (hello.result.host.python) {
  mark = a.notices.length;
  await a.ask('host.subscribe', { project: fresh });
  const bands = await a.next(done(fresh, 'scale_bands'), 180000, mark);
  assert.equal(bands.params.job.state, 'done', JSON.stringify(bands.params.job));
  const result = (await a.ask('jobs.status', { project: fresh, job: bands.params.job.id })).result.job.result;
  valid('jobs.rpc.json#/$defs/scale_bands_job_result', result);
  assert.equal(result.figures.length, 5);
  await a.next(done(fresh, 'checks'), 120000, mark);
  assert.equal(a.notices.slice(mark).some((n) => n.method === 'job_progress' && n.params.job.kind === 'compare'), false,
    'a new map has no compare');
}

// 6. Cancel by kill: Darkmoor's background checks (tens of seconds) stopped while they run, its queued compare
// dropped; lane J answers the next job.
const darkmoor = keyOf('darkmoor');
mark = a.notices.length;
await a.ask('host.subscribe', { project: darkmoor });
const slowRunning = await a.next((n) => n.method === 'job_progress' && n.params.project === darkmoor
  && n.params.job.kind === 'checks' && n.params.job.state === 'running', 30000, mark);
const slow = slowRunning.params.job;
valid('jobs.rpc.json#/$defs/job', slow);
const queuedNotice = await a.next((n) => n.method === 'job_progress' && n.params.project === darkmoor
  && n.params.job.kind === 'compare' && n.params.job.state === 'queued', 10000, mark);
await new Promise((resolve) => setTimeout(resolve, 1500));
// The queued one first: dropped, never run.
const dropped = await a.ask('jobs.cancel', { project: darkmoor, job: queuedNotice.params.job.id });
assert.equal(dropped.result.job.state, 'cancelled');
t0 = performance.now();
const cancelled = await a.ask('jobs.cancel', { project: darkmoor, job: slow.id });
assert.equal(cancelled.result.job.id, slow.id);
const stopped = await a.next((n) => n.method === 'job_done' && n.params.job.id === slow.id, 10000, mark);
assert.equal(stopped.params.job.state, 'cancelled');
console.log(`a running job cancelled in ${Math.round(performance.now() - t0)} ms`);
const after = (await a.ask('jobs.start', { project: darkmoor, kind: 'compare' })).result.job;
assert.equal(after.background, false);
const again = await a.next((n) => n.method === 'job_done' && n.params.job.id === after.id, 120000, mark);
assert.equal(again.params.job.state, 'done', 'lane J answers after a kill');
assert.equal((await a.ask('jobs.cancel', { project: darkmoor, job: slow.id })).error.data.kind, 'no_such_object');
const darkmoorJobs = (await a.ask('jobs.list', { project: darkmoor })).result.jobs;
assert.deepEqual(darkmoorJobs.map((job) => job.state).sort(), ['cancelled', 'cancelled', 'done']);

// 7. Refusals: an unknown kind, a project outside the jail, a job that is not there, params of the wrong form.
assert.equal((await a.ask('jobs.start', { project: cellars, kind: 'nonsense' })).error.data.kind, 'bad_request');
assert.equal((await a.ask('jobs.start', { project: '../etc', kind: 'checks' })).error.data.kind, 'not_a_project');
assert.equal((await a.ask('jobs.status', { project: cellars, job: 'j1-abc' })).error.data.kind, 'no_such_object');
assert.equal((await a.ask('jobs.start', { project: cellars, kind: 'checks', params: [] })).error.data.kind, 'invalid_params');
assert.equal((await a.ask('jobs.status', { project: cellars })).error.data.kind, 'invalid_params');
// An original is a map's file name, never a path (the core would read a project from it).
assert.equal((await a.ask('jobs.start', { project: cellars, kind: 'compare', params: { original: '/etc/passwd' } })).error.data.kind,
  'invalid_params');
assert.equal((await a.ask('jobs.start', { project: cellars, kind: 'playtest', params: { runs: 99 } })).error.data.kind, 'invalid_params');
assert.equal((await a.ask('jobs.start', { project: cellars, kind: 'checks', params: { nonsense: 1 } })).error.data.kind, 'invalid_params');

// 8. Optional, the game: a pins tour and a playtest of the example (JOBS_GAME=1).
if (withGame) {
  await a.ask('host.subscribe', { project: cellars });
  mark = a.notices.length;
  const pin = await a.ask('pins.add', { project: cellars, text: 'Look here.', author: 'user', at: [256, 256, 0],
    map: 'studio01.blv', world: 'mm6',
    pose: { position: [600, 256, 1], yaw_radians: 3.1416, pitch_degrees: 0, heading_yaw_units: 1024 } });
  assert.ok(pin.result.pin.id);
  const tour = (await a.ask('jobs.start', { project: cellars, kind: 'pins_tour' })).result.job;
  const toured = await a.next((n) => n.method === 'job_done' && n.params.job.id === tour.id, 300000, mark);
  assert.equal(toured.params.job.state, 'done', JSON.stringify(toured.params.job));
  const result = (await a.ask('jobs.status', { project: cellars, job: tour.id })).result.job;
  valid('jobs.rpc.json#/$defs/pins_tour_job_result', result.result);
  const picture = await get(`/job/${encodeURIComponent(cellars)}/${result.revision}/${result.id}/${result.pictures[0]}`,
    { Authorization: `Bearer ${token}` });
  assert.equal(picture.status, 200);
  assert.equal(picture.body.subarray(1, 4).toString(), 'PNG');
  console.log(`pins tour: ${result.line} in ${result.seconds} s`);
}

// 9. A new host reads the jobs back from disk (results included).
await host.close();
const second = await startStudio({ background: false, port: port + 1, token, repo, assets, mount: null, roots: [root],
  web: path.join(scratch, 'no-web'), rpcDir, oymap, inbox: path.join(scratch, 'inbox'),
  discovery: path.join(scratch, 'host2.json') });
// A job the first host left running (written as running, never finished) is read back as stopped with its host.
const leftJob = { id: 'jzz-abcdef', kind: 'checks', title: 'Audit, reach and solve', project: cellars, revision: revision2, state: 'running',
  background: true, params: {}, created: '2099-01-01T00:00:00.000Z', started: '2099-01-01T00:00:00.000Z', finished: null, seconds: null,
  progress: [], error: null, line: '', pictures: [] };
mkdirSync(path.join(root, 'cellars', '.oymap', 'jobs', revision2, leftJob.id), { recursive: true });
writeFileSync(path.join(root, 'cellars', '.oymap', 'jobs', revision2, leftJob.id, 'job.json'), JSON.stringify(leftJob));
const left = second.jobs.status(cellars, leftJob.id);
assert.equal(left.state, 'failed');
assert.match(left.error, /host stopped/);
rmSync(path.join(root, 'cellars', '.oymap', 'jobs', revision2, leftJob.id), { recursive: true, force: true });
const listedAgain = second.jobs.list(cellars);
assert.equal(listedAgain.length, 4 + (withGame ? 1 : 0), `${listedAgain.length} jobs read back`);
const readBack = second.jobs.status(cellars, checks.id);
assert.equal(readBack.state, 'done');
valid('jobs.rpc.json#/$defs/checks_job_result', readBack.result);
await second.close();
a.socket.close();

assert.ok(existsSync(path.join(root, 'cellars', '.oymap', 'jobs', revision, checks.id, 'result.json')));
rmSync(scratch, { recursive: true, force: true });
console.log(`jobs: all checks passed in ${Math.round(performance.now() - started)} ms`);
process.exit(0);
