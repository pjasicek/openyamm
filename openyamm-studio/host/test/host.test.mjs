// The browser editor's local host (src/studio.mjs) end to end: the Host header check on HTTP and on the WebSocket
// upgrade, the token on the byte routes, the texture route against real cooked textures (BC7 from assets_dev, BC1
// and BC5 copied into a scratch mount), the path jail (the core is never called for a refused key), methods that are
// not exposed, host.projects and project.new's folders, project.open through the socket and the mesh route. Needs a built oymap and the
// repository's assets_dev.  node test/host.test.mjs
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, realpathSync } from 'node:fs';
import http from 'node:http';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import WebSocket from 'ws';
import { Core } from '../src/core.mjs';
import { startStudio } from '../src/studio.mjs';
import { LOW_CACHE_LEVEL, TextureStore, levelSizes, readTextureHeader } from '../src/textures.mjs';

const started = performance.now();
const here = path.dirname(fileURLToPath(import.meta.url));
const studioDir = path.resolve(here, '../..');
const repo = path.resolve(studioDir, '..');
const assets = path.join(repo, 'assets_dev');
const oymap = process.env.OYMAP ?? path.join(studioDir, 'build-s4/oymap');
const token = 'test-token-' + Math.random().toString(36).slice(2);
const port = 20000 + Math.floor(Math.random() * 5000);

// A scratch mount with a BC1 and a BC5 texture under face-texture names (the face textures of assets_dev are BC7).
const mount = mkdtempSync(path.join(tmpdir(), 'oymap-host-test-'));
mkdirSync(path.join(mount, 'worlds/mm6/textures_x4'), { recursive: true });
copyFileSync(path.join(assets, 'engine/models/textures/014f21dcb45eabac7210dfdb3d92b1cf.oytex'),
  path.join(mount, 'worlds/mm6/textures_x4/test_bc1.oytex'));
copyFileSync(path.join(assets, 'engine/models/textures/02e83bca9ad6afdd7ad4c564257979cc.oytex'),
  path.join(mount, 'worlds/mm6/textures_x4/test_bc5.oytex'));

// The real core, counted: a refused key must never reach it.
const core = new Core(oymap, { assets });
let coreCalls = 0;
const counted = { call: (method, params) => { coreCalls += 1; return core.call(method, params); }, stop: () => core.stop() };
// A second root for project.new: new projects are made in it (never in the repository's examples).
mkdirSync(path.join(mount, 'new'));
const host = await startStudio({ background: false, port, token, repo, assets, mount, core: counted,
  roots: [path.join(studioDir, 'examples'), path.join(mount, 'new')], web: path.join(mount, 'no-web'), rpcDir: path.join(studioDir, 'schema/rpc'),
  oymap, game: path.join(repo, 'build/game/openyamm'), inbox: path.join(mount, 'inbox'),
  allowOrigins: ['https://studio.example.test'] });

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

// Host header, on HTTP and on the upgrade.
assert.equal((await get('/', { Host: `evil.example:${port}` })).status, 421);
assert.equal((await get('/tex/mm6/6dirttyl', { Host: `evil.example:${port}`, ...auth })).status, 421);
assert.equal((await get('/', { Host: `localhost:${port}` })).status, 404); // no web build in this test: says so
assert.match((await get('/')).body.toString(), /not built/);
const upgradeStatus = (headers) => new Promise((resolve) => {
  const request = http.request({ host: '127.0.0.1', port, path: `/rpc?token=${token}`, headers: { Connection: 'Upgrade',
    Upgrade: 'websocket', 'Sec-WebSocket-Version': '13', 'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==', ...headers } });
  request.on('upgrade', (response, socket) => { socket.destroy(); resolve(response.statusCode); });
  request.on('response', (response) => resolve(response.statusCode));
  request.on('error', () => resolve('error'));
  request.end();
});
assert.equal(await upgradeStatus({ Host: `evil.example:${port}` }), 421);
assert.equal(await upgradeStatus({ Host: `127.0.0.1:${port}`, Origin: 'https://evil.example' }), 403);
assert.equal(await upgradeStatus({ Host: `127.0.0.1:${port}` }), 101);

// The token on the byte routes, in the Authorization header only.
assert.equal((await get('/tex/mm6/6dirttyl')).status, 401);
assert.equal((await get(`/tex/mm6/6dirttyl?token=${token}`)).status, 401);
assert.equal((await get('/tex/mm6/6dirttyl', { Authorization: 'Bearer wrong' })).status, 401);

// Textures: the header and the un-framed blocks; `from` gives the tail of the levels.
for (const [name, codec, scale] of [['6dirttyl', 1, '4'], ['test_bc1', 7, '4'], ['test_bc5', 3, '4']]) {
  const whole = await get(`/tex/mm6/${name}`, auth);
  assert.equal(whole.status, 200, name);
  const header = readTextureHeader(whole.body);
  assert.equal(header.codec, codec, name);
  const sizes = levelSizes(header);
  assert.equal(sizes.reduce((sum, size) => sum + size, 0), header.blockBytes, name);
  assert.equal(whole.body.length, 120 + header.blockBytes, name);
  assert.equal(whole.headers['x-texture-scale'], scale);
  assert.equal(whole.headers['x-texture-levels'], String(header.levels));
  const from = header.levels - 3;
  const tail = await get(`/tex/mm6/${name}?from=${from}`, auth);
  assert.equal(tail.headers['x-texture-from'], String(from));
  const tailBytes = sizes.slice(from).reduce((sum, size) => sum + size, 0);
  assert.equal(tail.body.length, 120 + tailBytes, name);
  assert.ok(tail.body.subarray(120).equals(whole.body.subarray(whole.body.length - tailBytes)), name);
}
assert.equal((await get('/tex/mm6/no_such_texture_here', auth)).status, 404);
assert.equal((await get('/tex/mm6/..%2F..%2Fengine', auth)).status, 404);
assert.ok(host.textures.stats.hits >= 3, 'the second request of a texture comes from the LRU');

// The low levels kept across runs: a second store (a later run of the host) answers the low pass from its cache
// folder without un-framing anything, with the same bytes; the full pass un-frames.
{
  const cacheDir = mkdtempSync(path.join(tmpdir(), 'oymap-texcache-'));
  const first = new TextureStore([mount, assets], { cacheDir });
  const low = await first.answer('mm6', '6dirttyl', LOW_CACHE_LEVEL);
  assert.equal(first.stats.unframed, 1);
  await new Promise((resolve) => setTimeout(resolve, 200));
  assert.equal(first.stats.lowWritten, 1);
  const later = new TextureStore([mount, assets], { cacheDir });
  const again = await later.answer('mm6', '6dirttyl', LOW_CACHE_LEVEL);
  assert.equal(later.stats.unframed, 0, 'the low pass of a later run un-frames nothing');
  assert.equal(later.stats.lowHits, 1);
  assert.ok(again.body.equals(low.body));
  assert.equal(again.headers['X-Texture-From'], low.headers['X-Texture-From']);
  const deeper = await later.answer('mm6', '6dirttyl', LOW_CACHE_LEVEL + 1);
  assert.equal(later.stats.unframed, 0);
  assert.ok(deeper.body.subarray(120).equals(low.body.subarray(low.body.length - (deeper.body.length - 120))));
  const whole = await later.answer('mm6', '6dirttyl', 0);
  assert.equal(later.stats.unframed, 1, 'the full pass un-frames');
  assert.equal(whole.body.length, 120 + readTextureHeader(whole.body).blockBytes);
}

// The mesh route: names and keys are checked.
const example = 'openyamm-studio/examples/gatehouse_cellars';
assert.equal((await get(`/mesh/${encodeURIComponent(example)}/not-a-mesh.txt`, auth)).status, 404);
assert.equal((await get(`/mesh/${encodeURIComponent('../../etc')}/abc-def.mesh`, auth)).status, 404);
assert.equal((await get(`/mesh/${encodeURIComponent(example)}/0123abcd-none-0123456789ab.mesh`, auth)).status, 404);
assert.equal((await get(`/mesh/${encodeURIComponent(example)}/0123abcd-none-0123456789ab.mesh`)).status, 401);

// The socket.
const socket = await new Promise((resolve, reject) => {
  const client = new WebSocket(`ws://127.0.0.1:${port}/rpc?token=${token}`, { origin: `http://127.0.0.1:${port}` });
  client.once('open', () => resolve(client));
  client.once('error', reject);
});
let nextId = 1;
const waiting = new Map();
socket.on('message', (data) => {
  const message = JSON.parse(String(data));
  waiting.get(message.id)?.(message);
  waiting.delete(message.id);
});
const ask = (method, params) => new Promise((resolve) => {
  const id = nextId++;
  waiting.set(id, resolve);
  socket.send(JSON.stringify({ jsonrpc: '2.0', id, method, params }));
});

for (const method of ['session.configure', 'run', 'commands', 'ping', 'no.such']) {
  const answer = await ask(method, method === 'run' ? { command: 'status', args: [] } : {});
  assert.equal(answer.error.code, -32601, method);
  assert.equal(answer.error.data.kind, 'unknown_method', method);
}

const callsBefore = coreCalls;
const outside = path.join(repo, 'devdocs/map_studio/briefs/mm6_cd2/L4'); // a real project, outside this test's roots
for (const key of ['devdocs/map_studio/briefs/mm6_cd2/L4', outside, `${example}/../goblinwatch_vault`, '../../etc',
  `${example}/`, 'openyamm-studio/examples', 'root0/../../..', '']) {
  const answer = await ask('project.open', { project: key });
  assert.equal(answer.error?.code, -32000, key);
  assert.equal(answer.error.data.kind, 'not_a_project', key);
}
assert.equal((await ask('pins.import_inbox', { inbox: '/tmp', projects: [example] })).error.data.kind, 'not_a_project');
assert.equal((await ask('pins.import_inbox', { inbox: 'default', projects: [outside] })).error.data.kind, 'not_a_project');
assert.equal(coreCalls, callsBefore, 'a refused key never reaches the core');

const listed = (await ask('host.projects', {})).result.projects;
assert.deepEqual(listed.map((project) => project.key), ['openyamm-studio/examples/gatehouse_cellars',
  'openyamm-studio/examples/goblinwatch_vault', 'openyamm-studio/examples/new_sorpigal_wells',
  'openyamm-studio/examples/s6_breakwater', 'openyamm-studio/examples/s6_loft', 'openyamm-studio/examples/s6_overlay_goblinwatch',
  'openyamm-studio/examples/s8a_isle_extras', 'openyamm-studio/examples/s8b_meadow',
  'openyamm-studio/examples/shapes_gallery']);
assert.equal(listed[0].id, 'studio01');
assert.equal(listed[0].kind, 'indoor');

// project.new names a folder that holds no project yet under a root (the jail's resolveNew): refused elsewhere.
const roots = (await ask('host.projects', {})).result.roots;
assert.deepEqual(roots, ['openyamm-studio/examples', 'root1']);
const callsBeforeNew = coreCalls;
for (const key of ['root1/../escape', 'root1/Bad Name', 'root1', example, '/tmp/crypt', 'root7/crypt', 'devdocs/crypt']) {
  const answer = await ask('project.new', { project: key, id: 'crypt01', name: 'Crypt' });
  assert.equal(answer.error?.data?.kind, 'not_a_project', key);
}
assert.equal(coreCalls, callsBeforeNew, 'a refused new folder never reaches the core');
const made = await ask('project.new', { project: 'root1/crypt', id: 'crypt01', name: 'Crypt', world: 'mm6', stats_id: 9401 });
assert.ok(made.result, JSON.stringify(made.error));
assert.ok((await ask('host.projects', {})).result.projects.some((project) => project.key === 'root1/crypt'));
assert.equal((await ask('project.new', { project: 'root1/crypt', id: 'crypt02', name: 'Again' })).error?.data?.kind, 'not_a_project');

const hello = await ask('session.hello', {});
assert.equal(hello.result.host.mode, 'local');
assert.equal(hello.result.host.assets, true);
assert.ok(hello.result.methods.includes('project.open'));

const opened = await ask('project.open', { project: example });
assert.match(opened.result.revision, /^[0-9a-f]{32}$/);
assert.equal(opened.result.files['project.yml'].tree.id, 'studio01');
assert.ok(!JSON.stringify(opened.result).includes(realpathSync(repo)), 'no absolute paths in an answer');
// A typed refusal of the core is forwarded as it is.
const noFile = await ask('project.read', { project: example, file: 'sketch.yml' });
assert.equal(noFile.error.data.kind, 'no_such_file');
assert.equal(noFile.error.data.file, 'sketch.yml');
const badParams = await ask('project.read', { project: example });
assert.equal(badParams.error.code, -32602);

// The mesh route serves what the core's view.mesh wrote (when this core has the method).
if (hello.result.methods.includes('view.mesh')) {
  const mesh = await ask('view.mesh', { project: example });
  if (mesh.result) {
    const name = path.basename(mesh.result.file);
    const bytes = await get(`/mesh/${encodeURIComponent(example)}/${name}`, auth);
    assert.equal(bytes.status, 200);
    assert.equal(bytes.body.length, mesh.result.bytes);
    assert.equal(bytes.headers['cache-control'], 'private, max-age=31536000, immutable');
    console.log(`view.mesh: ${mesh.result.counts.triangles} triangles, ${mesh.result.bytes} bytes served`);
  } else {
    console.log(`view.mesh refused: ${mesh.error.data.kind} (${mesh.error.message})`);
  }
}

// S5c: the token as the web app sends it, a subprotocol (never in the URL), from the page's own origin and from a
// hosted page's origin named with --allow-origin (pairing); any other origin and a wrong token are refused.
const opens = (protocols, origin) => new Promise((resolve) => {
  const client = new WebSocket(`ws://127.0.0.1:${port}/rpc`, protocols, { origin });
  client.once('open', () => { const chosen = client.protocol; client.close(); resolve(chosen); });
  client.once('error', () => resolve(null));
});
const hex = Buffer.from(token, 'utf8').toString('hex');
assert.equal(await opens(['oymap', `oymap.token.${hex}`], `http://127.0.0.1:${port}`), 'oymap');
assert.equal(await opens(['oymap', `oymap.token.${hex}`], 'https://studio.example.test'), 'oymap');
assert.equal(await opens(['oymap', `oymap.token.${hex}`], 'https://evil.example'), null);
assert.equal(await opens(['oymap', 'oymap.token.00'], `http://127.0.0.1:${port}`), null);
// The byte routes answer the paired origin's CORS (and its older private-network preflight), and no other origin's.
const preflight = await new Promise((resolve, reject) => {
  const request = http.request({ host: '127.0.0.1', port, path: '/tex/mm6/6dirttyl', method: 'OPTIONS', headers: { Host: `127.0.0.1:${port}`,
    Origin: 'https://studio.example.test', 'Access-Control-Request-Private-Network': 'true' } }, (response) => { response.resume(); resolve(response); });
  request.on('error', reject);
  request.end();
});
assert.equal(preflight.headers['access-control-allow-origin'], 'https://studio.example.test');
assert.equal(preflight.headers['access-control-allow-private-network'], 'true');
assert.equal((await get('/tex/mm6/6dirttyl', { ...auth, Origin: 'https://evil.example' })).headers['access-control-allow-origin'], undefined);

socket.close();
await host.close();

// The command itself: `host.mjs studio` prints its address with the token in the fragment.
const child = spawn(process.execPath, [path.resolve(here, '../src/host.mjs'), 'studio', '--port', String(port + 1),
  '--oymap', oymap, '--token', 'printed', '--discovery', path.join(mount, 'host.json'), '--inbox', path.join(mount, 'inbox')]);
const line = await new Promise((resolve) => child.stdout.once('data', (data) => resolve(String(data).trim())));
assert.equal(line, `oymap studio: http://127.0.0.1:${port + 1}/#token=printed`);
child.kill();

console.log(`host: all checks passed in ${Math.round(performance.now() - started)} ms`);
process.exit(0);
