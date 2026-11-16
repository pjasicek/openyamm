// The host's live side (S5_BROWSER_EDITOR.md 2.4.3, F4; S5a3): two browsers and agents on one host. Checks the
// presence notices, the watcher (an agent's `oymap pins` and `oymap edit`, an edit with a text editor, a file that
// does not parse; nothing for .oymap/ and build/), pins through the socket with a picture and the picture route,
// the MCP tools over Streamable HTTP and through the stdio relay (`host.mjs relay`), and the game's inbox imported
// live. Works on a scratch copy of an example project.  node test/live.test.mjs
import assert from 'node:assert/strict';
import { execFileSync, spawn } from 'node:child_process';
import { cpSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import http from 'node:http';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import zlib from 'node:zlib';
import WebSocket from 'ws';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { startStudio, watchedPath } from '../src/studio.mjs';

const started = performance.now();
const here = path.dirname(fileURLToPath(import.meta.url));
const studioDir = path.resolve(here, '../..');
const repo = path.resolve(studioDir, '..');
const assets = path.join(repo, 'assets_dev');
const oymap = process.env.OYMAP ?? path.join(studioDir, 'build-s4/oymap');
const token = 'live-' + Math.random().toString(36).slice(2);
const port = 25000 + Math.floor(Math.random() * 5000);

// The watcher's filter.
assert.equal(watchedPath('rooms.yml'), true);
assert.equal(watchedPath('review/pins.yml'), true);
assert.equal(watchedPath('.oymap/history/0001/entry.yml'), false);
assert.equal(watchedPath('.oymap'), false);
assert.equal(watchedPath('build/source/x.glb'), false);
assert.equal(watchedPath('builds.yml'), true);

// A scratch root with a copy of an example project (without its .oymap and build).
const scratch = mkdtempSync(path.join(tmpdir(), 'oymap-live-'));
const root = path.join(scratch, 'projects');
const project = path.join(root, 'cellars');
cpSync(path.join(studioDir, 'examples/gatehouse_cellars'), project, { recursive: true,
  filter: (source) => !/\/(\.oymap|build)(\/|$)/.test(source) });
const inbox = path.join(scratch, 'inbox');
const discovery = path.join(scratch, 'host.json');
const host = await startStudio({ background: false, port, token, repo, assets, mount: null, roots: [root], web: path.join(scratch, 'no-web'),
  rpcDir: path.join(studioDir, 'schema/rpc'), oymap, game: path.join(repo, 'build/game/openyamm'), inbox, discovery,
  log: process.env.OYMAP_HOST_LOG ? (line) => console.error(`host: ${line}`) : undefined });
const key = host.jail.keyOf(project);
assert.match(key, /^root0\/cellars$/);
assert.equal(JSON.parse(readFileSync(discovery, 'utf8')).port, port);

// A browser: its answers and its notices.
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
    // The first notice (from `from` on) that `test` accepts, within `ms`.
    next: (test, ms = 4000, from = 0) => new Promise((resolve, reject) => {
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
        reject(new Error(`no such notice within ${ms} ms; got ${JSON.stringify(notices.slice(from).map((n) => n.method))}`));
      }, ms);
      watchers.push(look);
      look();
    }),
  };
}

const a = await browser();
const b = await browser();
await a.next((notice) => notice.method === 'client_joined' && notice.params.client.kind === 'browser'
  && notice.params.client.id !== undefined);
const subscribed = await a.ask('host.subscribe', { project: key });
assert.match(subscribed.result.revision, /^[0-9a-f]{32}$/);
assert.equal(subscribed.result.counter, 0);
assert.equal(subscribed.result.clients.filter((client) => client.kind === 'browser').length, 2);
assert.equal((await a.ask('host.subscribe', { project: '../../etc' })).error.data.kind, 'not_a_project');
const clients = (await a.ask('host.clients', {})).result.clients;
assert.equal(clients.find((client) => client.project === key)?.kind, 'browser');

// An agent's `oymap pins` on the command line: the watcher announces the counter.
let mark = a.notices.length;
let t0 = performance.now();
execFileSync(oymap, ['pins', 'add', project, '--text', 'The torch flickers.', '--on', 'light:entry', '--by', 'agent:cli']);
let notice = await a.next((n) => n.method === 'pins_changed', 4000, mark);
assert.equal(notice.params.project, key);
assert.equal(notice.params.counter, 1);
console.log(`pins from the command line announced in ${Math.round(performance.now() - t0)} ms`);

// Nothing for .oymap/ and build/.
mark = a.notices.length;
mkdirSync(path.join(project, '.oymap'), { recursive: true });
mkdirSync(path.join(project, 'build/source'), { recursive: true });
writeFileSync(path.join(project, '.oymap/scratch.txt'), 'x');
writeFileSync(path.join(project, 'build/source/x.glb'), 'x');
await new Promise((resolve) => setTimeout(resolve, 700));
assert.equal(a.notices.slice(mark).length, 0, 'no notice for .oymap/ and build/');

// An agent's `oymap edit`: the revision with its entry's author and label.
mark = a.notices.length;
t0 = performance.now();
const ops = path.join(scratch, 'ops.json');
writeFileSync(ops, JSON.stringify([{ op: 'set', id: 'light:entry', fields: { radius: 950 } }]));
execFileSync(oymap, ['edit', project, '--ops', ops, '--author', 'agent:cli', '--label', 'brighter entry', '--assets', assets]);
notice = await a.next((n) => n.method === 'revision_changed', 6000, mark);
assert.equal(notice.params.author, 'agent:cli');
assert.equal(notice.params.label, 'brighter entry');
assert.ok(notice.params.changes.some((line) => line.includes('light:entry')), JSON.stringify(notice.params.changes));
assert.equal(notice.params.previous, subscribed.result.revision);
console.log(`an agent's oymap edit announced in ${Math.round(performance.now() - t0)} ms`);
assert.equal(b.notices.filter((n) => n.method === 'revision_changed').length, 0, 'only subscribers hear a project');

// A text editor's change: recorded as outside.
mark = a.notices.length;
const objectsFile = path.join(project, 'objects.yml');
writeFileSync(objectsFile, readFileSync(objectsFile, 'utf8').replace('radius: 1100', 'radius: 1150'));
notice = await a.next((n) => n.method === 'revision_changed', 6000, mark);
assert.equal(notice.params.author, 'outside');
assert.ok(notice.params.changes.some((line) => line.includes('light:hall_east')), JSON.stringify(notice.params.changes));

// A file that does not parse, and again when it parses.
mark = a.notices.length;
const wiringFile = path.join(project, 'wiring.yml');
const wiring = readFileSync(wiringFile, 'utf8');
writeFileSync(wiringFile, wiring + '\n  - [unclosed\n');
notice = await a.next((n) => n.method === 'project_unreadable', 6000, mark);
assert.match(notice.params.message, /wiring/);
mark = a.notices.length;
writeFileSync(wiringFile, wiring);
await a.next((n) => n.method === 'revision_changed', 6000, mark);

// The other browser pins with a picture; the first hears it at once.
const png = (() => {
  const chunk = (type, data) => {
    const length = Buffer.alloc(4);
    length.writeUInt32BE(data.length);
    const crc = Buffer.alloc(4);
    crc.writeUInt32BE(zlib.crc32(Buffer.concat([Buffer.from(type), data])) >>> 0);
    return Buffer.concat([length, Buffer.from(type), data, crc]);
  };
  const header = Buffer.alloc(13);
  header.writeUInt32BE(1, 0);
  header.writeUInt32BE(1, 4);
  header[8] = 8;
  header[9] = 2;
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk('IHDR', header),
    chunk('IDAT', zlib.deflateSync(Buffer.from([0, 255, 0, 0]))), chunk('IEND', Buffer.alloc(0))]);
})();
await b.ask('host.subscribe', { project: key });
mark = a.notices.length;
const added = await b.ask('pins.add', { project: key, text: 'This wall is too dark.', on: 'room:hall', file: 'rooms.yml',
  at: [100, 200, 0], author: 'user', source: 'studio',
  pose: { position: [0, 0, 0], yaw_radians: 1.5708, pitch_degrees: -10 },
  picture: { media_type: 'image/png', base64: png.toString('base64') } });
assert.equal(added.result.pin.picture, '.oymap/pins/pictures/p2.png');
notice = await a.next((n) => n.method === 'pins_changed', 2000, mark);
assert.equal(notice.params.action, 'add');
assert.equal(notice.params.pin, 'pin:p2');
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
const picture = await get(`/picture/${encodeURIComponent(key)}/${encodeURIComponent(added.result.pin.picture)}`, auth);
assert.equal(picture.status, 200);
assert.equal(picture.headers['content-type'], 'image/png');
assert.ok(picture.body.equals(png));
assert.equal((await get(`/picture/${encodeURIComponent(key)}/${encodeURIComponent(added.result.pin.picture)}`)).status, 401);
assert.equal((await get(`/picture/${encodeURIComponent(key)}/${encodeURIComponent('rooms.yml')}`, auth)).status, 404);
assert.equal((await get(`/picture/${encodeURIComponent(key)}/${encodeURIComponent('.oymap/pins/pictures/../../rooms.yml')}`, auth)).status, 404);
assert.equal((await get(`/picture/${encodeURIComponent('../x')}/${encodeURIComponent(added.result.pin.picture)}`, auth)).status, 404);
assert.equal((await b.ask('pins.add', { project: key, text: 'x', picture: { media_type: 'image/png', base64: 'AAAA' } }))
  .error.data.kind, 'bad_request');

// An agent over MCP (Streamable HTTP): present by its name, its answers announced at once.
mark = a.notices.length;
assert.equal((await new Promise((resolve) => {
  const request = http.request({ host: '127.0.0.1', port, path: '/mcp', method: 'POST',
    headers: { Host: `127.0.0.1:${port}`, 'Content-Type': 'application/json' } }, (response) => resolve(response.statusCode));
  request.end('{}');
})), 401);
const agent = new Client({ name: 'live-test-agent', version: '1' });
const agentTransport = new StreamableHTTPClientTransport(new URL(`http://127.0.0.1:${port}/mcp`),
  { requestInit: { headers: { Authorization: `Bearer ${token}` } } });
await agent.connect(agentTransport);
notice = await a.next((n) => n.method === 'client_joined' && n.params.client.kind === 'mcp', 4000, mark);
assert.equal(notice.params.client.name, 'agent:live-test-agent');
const toolNames = (await agent.listTools()).tools.map((tool) => tool.name);
assert.ok(toolNames.includes('map_pins'));
const claim = await agent.callTool({ name: 'map_pins', arguments: { project, action: 'claim', id: 'pin:p2', by: 'agent:live' } });
assert.ok(!claim.isError, JSON.stringify(claim.content));
assert.match(JSON.parse(claim.content[0].text).people, /a person has this project open in the studio \(2 browsers\).*pins\.add pin:p2/);
notice = await a.next((n) => n.method === 'pins_changed' && n.params.action === 'claim', 2000, mark);
assert.equal(notice.params.by, 'agent:live');
mark = a.notices.length;
await agentTransport.terminateSession();
await agent.close();
await a.next((n) => n.method === 'client_left' && n.params.client.kind === 'mcp', 4000, mark);

// The relay: `host.mjs relay` finds this host through the discovery file.
mark = a.notices.length;
const relayed = new Client({ name: 'relayed-agent', version: '1' });
await relayed.connect(new StdioClientTransport({ command: process.execPath,
  args: [path.join(studioDir, 'host/src/host.mjs'), 'relay', '--discovery', discovery, '--oymap', oymap],
  stderr: 'pipe' }));
notice = await a.next((n) => n.method === 'client_joined' && n.params.client.kind === 'mcp', 6000, mark);
assert.equal(notice.params.client.name, 'agent:relayed-agent');
const resolved = await relayed.callTool({ name: 'map_pins', arguments: { project, action: 'resolve', id: 'pin:p2',
  by: 'agent:live', text: 'Raised the hall light.' } });
assert.ok(!resolved.isError, JSON.stringify(resolved.content));
notice = await a.next((n) => n.method === 'pins_changed' && n.params.action === 'resolve', 2000, mark);
mark = a.notices.length;
await relayed.close();
await a.next((n) => n.method === 'client_left' && n.params.client.name === 'agent:relayed-agent', 4000, mark);

// The game's inbox: a pin written there is filed into its project and announced.
mark = a.notices.length;
mkdirSync(inbox, { recursive: true });
writeFileSync(path.join(inbox, '20261114-220000-studio01.png'), png);
writeFileSync(path.join(inbox, '20261114-220000-studio01.yml'), [
  'format: 1', 'source: game', 'author: user', 'created: "2026-11-14T22:00:00"', 'text: "The gate sticks."',
  'world: "mm6"', 'map: "studio01.blv"', 'pose:', '  position: [0.000, 0.000, 0.000]', '  yaw_radians: 0.000',
  '  pitch_degrees: 0.000', '  heading_yaw_units: 0', 'picture: "20261114-220000-studio01.png"', ''].join('\n'));
notice = await a.next((n) => n.method === 'pins_changed' && n.params.action === 'import', 6000, mark);
const listed = await a.ask('pins.list', { project: key });
const gamePin = listed.result.pins.find((pin) => pin.id === notice.params.pin);
assert.equal(gamePin.source, 'game');
assert.match(gamePin.picture, /^\.oymap\/pins\/pictures\/p\d+\.png$/);

// Leaving.
mark = a.notices.length;
b.socket.close();
await a.next((n) => n.method === 'client_left' && n.params.client.kind === 'browser', 4000, mark);
a.socket.close();
await host.close();
assert.throws(() => readFileSync(discovery), 'the discovery file goes with the host');
console.log(`live: all checks passed in ${Math.round(performance.now() - started)} ms (${host.counters.notices} notices, `
  + `${host.counters.watcherFlushes} watcher flushes)`);
process.exit(0);
