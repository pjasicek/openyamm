// Walk mode's files and Play here in the host (S5a4: src/studio.mjs, src/play.mjs): the start console file and the
// game's exit pose file, host.walk_prepare (a build, the byte routes of the walk's files with the token, the worker's
// core without one), and game.play_here with a stand-in launcher that does what the game's two launch directives do
// (runs the `tp` of the start file, writes the exit pose), its game_started and game_exited notices, and the build
// installed into the mount. Needs a built oymap and the repository's assets_dev.  node test/play.test.mjs
import assert from 'node:assert/strict';
import { chmodSync, cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import http from 'node:http';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import WebSocket from 'ws';
import { Core } from '../src/core.mjs';
import { parseExitPose, startConsoleText } from '../src/play.mjs';
import { startStudio } from '../src/studio.mjs';

const started = performance.now();
const here = path.dirname(fileURLToPath(import.meta.url));
const studioDir = path.resolve(here, '../..');
const repo = path.resolve(studioDir, '..');
const assets = path.join(repo, 'assets_dev');
const oymap = process.env.OYMAP ?? path.join(studioDir, 'build-s4/oymap');

// --- the files ------------------------------------------------------------------------------------------------------

assert.equal(startConsoleText({ position: [640, 6976.25, 192], yaw_radians: 1.5708, pitch_degrees: -12.5 }, ['gold 5000']),
  '# The Map Studio\'s Play here: the party at the browser\'s camera (tp x y z yaw-radians pitch-degrees).\n'
  + 'tp 640 6976.25 192 1.5708 -12.5\ngold 5000\n');
// The game's own text (game/debug/ExitPose.cpp, tests/scenarios/debug/play_here.yml).
const gameText = '# Where the party stood when the game closed ([debug] exit_pose_path); the pose as `loc` prints it.\n'
  + 'format: 1\nworld: "mm6"\nmap: "6d01.blv"\npose:\n  position: [640.000, 6976.000, 192.000]\n  yaw_radians: 1.571\n'
  + '  pitch_degrees: -12.500\n  heading_yaw_units: 512\n';
assert.deepEqual(parseExitPose(gameText), { world: 'mm6', map: '6d01.blv',
  pose: { position: [640, 6976, 192], yaw_radians: 1.571, pitch_degrees: -12.5, heading_yaw_units: 512 } });
assert.equal(parseExitPose(gameText.replace('format: 1', 'format: 2')), null);
assert.equal(parseExitPose('format: 1\nworld: "mm6"\n'), null);

// --- the host -------------------------------------------------------------------------------------------------------

const scratch = mkdtempSync(path.join(tmpdir(), 'oymap-play-test-'));
const roots = path.join(scratch, 'projects');
mkdirSync(roots, { recursive: true });
cpSync(path.join(studioDir, 'examples/gatehouse_cellars'), path.join(roots, 'gatehouse'), {
  recursive: true, filter: (source) => !/(^|\/)(build|\.oymap)$/.test(source) });
const mount = path.join(scratch, 'mount');
const runs = path.join(scratch, 'runs');
// A stand-in for tools/run_game.sh: the game's start file and exit pose, nothing else (no window).
const launcher = path.join(scratch, 'launcher.mjs');
writeFileSync(launcher, `#!/usr/bin/env node
const args = process.argv.slice(2);
const set = (key) => args[args.findIndex((a, i) => a === '--set' && args[i + 1].startsWith(key + '=')) + 1].slice(key.length + 1);
const fs = await import('node:fs');
fs.writeFileSync(${JSON.stringify(path.join(scratch, 'launcher-args.json'))}, JSON.stringify(args));
const tp = fs.readFileSync(set('debug.startup_console_file'), 'utf8').split('\\n').filter((l) => l.startsWith('tp ')).at(-1).split(' ').slice(1).map(Number);
const map = args[args.indexOf('--map') + 1];
fs.writeFileSync(set('debug.exit_pose_path'), 'format: 1\\nworld: "mm6"\\nmap: "' + map + '"\\npose:\\n  position: [' + tp.slice(0, 3).map((v) => v.toFixed(3)).join(', ') + ']\\n  yaw_radians: ' + tp[3].toFixed(3) + '\\n  pitch_degrees: ' + tp[4].toFixed(3) + '\\n  heading_yaw_units: 0\\n');
`);
chmodSync(launcher, 0o755);

const token = 'play-token';
const port = 25000 + Math.floor(Math.random() * 4000);
const core = new Core(oymap, { assets });
const host = await startStudio({ background: false, port, token, repo, assets, mount, toolsMount: mount, core, roots: [roots],
  web: path.join(scratch, 'no-web'), rpcDir: path.join(studioDir, 'schema/rpc'), oymap, inbox: path.join(scratch, 'inbox'),
  coreWasm: [path.join(studioDir, 'build-wasm-s4'), path.join(studioDir, 'build-wasm')]
    .find((folder) => existsSync(path.join(folder, 'oymap_worker.mjs'))) ?? null,
  runGame: launcher, playRuns: runs, playMounts: mount });

const get = (pathname, headers = {}) => new Promise((resolve, reject) => {
  const request = http.request({ host: '127.0.0.1', port, path: pathname, headers: { Host: `127.0.0.1:${port}`, ...headers } },
    (response) => {
      const chunks = [];
      response.on('data', (chunk) => chunks.push(chunk));
      response.on('end', () => resolve({ status: response.statusCode, headers: response.headers, body: Buffer.concat(chunks) }));
    });
  request.on('error', reject);
  request.end();
});
const auth = { Authorization: `Bearer ${token}` };
const socket = await new Promise((resolve, reject) => {
  const client = new WebSocket(`ws://127.0.0.1:${port}/rpc?token=${token}`, { origin: `http://127.0.0.1:${port}` });
  client.once('open', () => resolve(client));
  client.once('error', reject);
});
let nextId = 1;
const waiting = new Map();
const notices = [];
socket.on('message', (data) => {
  const message = JSON.parse(String(data));
  if (message.id === undefined || message.id === null) notices.push(message);
  else {
    waiting.get(message.id)?.(message);
    waiting.delete(message.id);
  }
});
const ask = (method, params) => new Promise((resolve) => {
  const id = nextId++;
  waiting.set(id, resolve);
  socket.send(JSON.stringify({ jsonrpc: '2.0', id, method, params }));
});
const key = (await ask('host.projects', {})).result.projects[0].key;
await ask('host.subscribe', { project: key });

// Walk mode's files: built, named by route, served with the token only, and only those names.
const prepared = await ask('host.walk_prepare', { project: key });
assert.equal(prepared.result.kind, 'indoor');
assert.equal(prepared.result.map, 'studio01.blv');
assert.deepEqual(Object.keys(prepared.result.files).sort(), ['decorations', 'map', 'state']);
const state = await get(prepared.result.files.state, auth);
assert.equal(state.status, 200);
assert.match(state.body.toString(), /^studio_walk:\n/);
assert.equal((await get(prepared.result.files.map, auth)).body.length,
  readFileSync(path.join(roots, 'gatehouse/build/studio01.blv')).length);
assert.equal((await get(prepared.result.files.decorations, auth)).body.length,
  readFileSync(path.join(assets, 'engine/data_tables/decoration_data.txt')).length);
assert.equal((await get(prepared.result.files.state)).status, 401);
assert.equal((await get(`/walk/${encodeURIComponent(key)}/build.json`, auth)).status, 404);
assert.equal((await get(`/walk/${encodeURIComponent(key)}/..%2Fproject.yml`, auth)).status, 404);
assert.equal((await get(`/walk/${encodeURIComponent('../../etc')}/passwd.blv`, auth)).status, 404);
assert.equal((await ask('host.walk_prepare', { project: '../../etc' })).error.data.kind, 'not_a_project');
// The worker's core needs no token (a module a worker imports sends none); nothing else is served there.
if (existsSync(path.join(studioDir, 'build-wasm-s4/oymap_worker.mjs')) || existsSync(path.join(studioDir, 'build-wasm/oymap_worker.mjs'))) {
  const module = await get('/core/oymap_worker.mjs');
  assert.equal(module.status, 200);
  assert.match(module.headers['content-type'], /javascript/);
  assert.equal((await get('/core/oymap_worker.wasm')).headers['content-type'], 'application/wasm');
}
assert.equal((await get('/core/oymap.js')).status, 404);

// Play here: refused without a pose; then built, installed into the mount and started; the game closes and the
// notice carries where the party stood.
assert.equal((await ask('game.play_here', { project: key })).error.data.kind, 'invalid_params');
assert.equal((await ask('game.play_here', { project: key, pose: { position: [1, 2, 3], yaw_radians: 0, pitch_degrees: 0 },
  commands: ['gold 1; qbit set 1'] })).error.data.kind, 'invalid_params');
const pose = { position: [400, 700, 0], yaw_radians: 1.5708, pitch_degrees: -10, heading_yaw_units: 512 };
const play = await ask('game.play_here', { project: key, pose, visible: false, commands: ['tp 410 720 0 3.1416 -5'] });
assert.equal(play.result.map, 'studio01.blv');
assert.equal(play.result.world, 'mm6');
assert.match(play.result.run, /^studio-play-/);
const playMount = path.join(mount, readdirSync(mount)[0]);
assert.ok(existsSync(path.join(playMount, 'worlds/mm6/maps/studio01.blv')), 'installed into the project\'s own mount');
for (let i = 0; i < 100 && !notices.some((notice) => notice.method === 'game_exited'); ++i) {
  await new Promise((resolve) => setTimeout(resolve, 50));
}
const startedNotice = notices.find((notice) => notice.method === 'game_started');
assert.equal(startedNotice.params.run, play.result.run);
const exited = notices.find((notice) => notice.method === 'game_exited');
assert.equal(exited.params.project, key);
assert.equal(exited.params.code, 0);
assert.deepEqual(exited.params.exit, { world: 'mm6', map: 'studio01.blv',
  pose: { position: [410, 720, 0], yaw_radians: 3.142, pitch_degrees: -5, heading_yaw_units: 0 } });
const launched = JSON.parse(readFileSync(path.join(scratch, 'launcher-args.json'), 'utf8'));
assert.deepEqual(launched.slice(0, 2), ['--isolated', play.result.run]);
for (const expected of ['--world', 'mm6', '--map', 'studio01.blv', '--extra-mount', playMount, '--seconds', '0']) {
  assert.ok(launched.includes(expected), expected);
}
assert.ok(!launched.includes('--visible'), 'minimised unless the person asked to see it');
assert.equal(readFileSync(path.join(runs, play.result.run, 'start.console'), 'utf8'),
  startConsoleText(pose, ['tp 410 720 0 3.1416 -5']));

socket.close();
await host.close();
console.log(`play: all checks passed in ${Math.round(performance.now() - started)} ms`);
process.exit(0);
