// The MCP server end to end, through the SDK's own client over standard input and output: the tools are listed, a
// project is opened, edited (with a refused change and an applied one), queried, undone, and a shipped map is read.
// Needs a built oymap and the repository's assets_dev.
import assert from 'node:assert/strict';
import { cp, mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const project = path.join(await mkdtemp(path.join(tmpdir(), 'oymap-mcp-')), 'cellars');
await cp(path.resolve(here, '../../examples/gatehouse_cellars'), project, { recursive: true,
  filter: (source) => !source.includes('.oymap') && !source.endsWith('/build') });

const mount = path.join(path.dirname(project), 'mount');
const client = new Client({ name: 'oymap-host-test', version: '0' });
await client.connect(new StdioClientTransport({ command: process.execPath,
  args: [path.resolve(here, '../src/host.mjs'), 'mcp', '--mount', mount,
    ...(process.env.OYMAP ? ['--oymap', process.env.OYMAP] : [])] }));
const call = async (name, args) => {
  const result = await client.callTool({ name, arguments: args });
  const first = result.content.find((part) => part.type === 'text');
  let data = first?.text;
  try { data = JSON.parse(first.text); } catch {}
  return { result, data };
};

const tools = (await client.listTools()).tools.map((tool) => tool.name).sort();
assert.deepEqual(tools, ['map_api', 'map_assets', 'map_build', 'map_edit', 'map_exec', 'map_flow', 'map_history',
  'map_new', 'map_open', 'map_overview', 'map_pins', 'map_playtest', 'map_query', 'map_render', 'map_validate',
  'map_view']);

// The MCP App viewer (S6 item A): the resource, the tool that names it, and its structured result.
const listedTools = (await client.listTools()).tools;
const viewTool = listedTools.find((tool) => tool.name === 'map_view');
assert.equal(viewTool._meta.ui.resourceUri, 'ui://openyamm/viewer');
const resources = (await client.listResources()).resources;
assert.deepEqual(resources.map((resource) => [resource.uri, resource.mimeType]),
  [['ui://openyamm/viewer', 'text/html;profile=mcp-app']]);
const page = (await client.readResource({ uri: 'ui://openyamm/viewer' })).contents[0];
assert.equal(page.mimeType, 'text/html;profile=mcp-app');
assert.match(page.text, /ui\/notifications\/tool-result/);
const viewed = await call('map_view', { project });
assert.equal(viewed.result.structuredContent.layout.rooms.length, 6);
assert.equal(viewed.data.rooms, 6);

const opened = await call('map_open', { project });
assert.equal(opened.data.card.id, 'studio01');
assert.equal(opened.data.issues.length, 0);

const refused = await call('map_edit', { project, ops: [{ op: 'door.add', value: { id: 'door:bad', opening: 'open:nowhere' } }] });
assert.equal(refused.result.isError, true);
assert.equal(refused.data.applied, false);

const edited = await call('map_edit', { project, expect_revision: opened.data.revision,
  ops: [{ op: 'light.add', value: { id: 'light:test', room: 'room:vault', radius: 400 } },
    { op: 'set', id: 'door:gate', fields: { speed: 64 } }] });
assert.equal(edited.data.applied, true);
assert.deepEqual(edited.data.changes.sort(), ['objects.yml: added light:test', 'objects.yml: door:gate changed speed (96 -> 64)']);

const stale = await call('map_edit', { project, expect_revision: opened.data.revision, ops: [{ op: 'remove', id: 'light:test' }] });
assert.equal(stale.result.isError, true);

assert.equal((await call('map_query', { project, id: 'door:gate' })).data.object.speed, 64);
assert.equal((await call('map_query', { project, id: 'door:nowhere' })).result.isError, true);
assert.equal((await call('map_query', { project, id: 'evt:gate_lever' })).data.number_of, 'events');
const dry = await call('map_edit', { project, dry_run: true, ops: [{ op: 'remove', id: 'light:test' }] });
assert.equal(dry.data.revision, edited.data.revision);
assert.notEqual(dry.data.revision_if_applied, edited.data.revision);
assert.equal((await call('map_query', { project, id: 'room:entry' })).result.isError, true);
assert.equal((await call('map_query', { project, id: 'room:entry', file: 'rooms.yml' })).data.file, 'rooms.yml');
assert.ok(Array.isArray((await call('map_query', { project, list: 'doors' })).data.items));
const undone = await call('map_history', { project, action: 'undo' });
assert.match(undone.data.changes.join('\n'), /undone: objects.yml: door:gate changed speed/);
assert.equal((await call('map_query', { project, id: 'door:gate' })).data.object.speed, 96);
assert.match((await call('map_history', { project, action: 'redo' })).data.changes.join('\n'), /redone/);
assert.equal((await call('map_query', { project, id: 'door:gate' })).data.object.speed, 64);
assert.equal((await call('map_history', { project, action: 'undo' })).data.ok, true);
const listed = await call('map_history', { project, action: 'list' });
assert.ok(listed.data.history.some((entry) => entry.undone && entry.changes.some((change) => change.includes('door:gate'))));
// The undo and redo above are the core's steps, not edits made outside the tool.
assert.deepEqual((await call('map_open', { project })).data.outside_changes, []);

// Pins are their own document: they never change the project's revision.
const revisionBeforePins = (await call('map_open', { project })).data.revision;
const pin = await call('map_pins', { project, action: 'add', text: 'The gate is too slow.', on: 'door:gate' });
assert.equal(pin.data.ok, true);
assert.equal(pin.data.pin.id, 'pin:p1');
assert.equal((await call('map_pins', { project, action: 'list' })).data.pins[0].status, 'open');
assert.equal((await call('map_pins', { project, action: 'claim', id: 'pin:p1', by: 'agent:test' })).data.pin.status, 'claimed');
assert.equal((await call('map_pins', { project, action: 'resolve', id: 'pin:p1', by: 'agent:test' })).result.isError, true);
const resolved = await call('map_pins', { project, action: 'resolve', id: 'pin:p1', by: 'agent:test', text: 'Faster now.' });
assert.equal(resolved.data.pin.status, 'resolved');
assert.equal(resolved.data.counter, 3);
assert.equal((await call('map_open', { project })).data.revision, revisionBeforePins);

const built = await call('map_build', { project, dry_run: true });
assert.equal(built.data.counts.doors, 4);

// The build is installed into the mount folder and read back from there as the game would read it; without
// `built` the assets do not have the map.
const installed = await call('map_build', { project, install: true });
assert.equal(installed.data.installed_into, mount);
assert.equal((await call('map_overview', { map: 'studio01.blv', world: 'mm6', built: true })).data.overview.doors, 4);
assert.equal((await call('map_overview', { map: 'studio01.blv', world: 'mm6' })).result.isError, true);
if (process.argv.includes('--play')) {
  const played = await call('map_playtest', { scenario: path.join(project, 'playtest.yml'), world: 'mm6' });
  assert.equal(played.data.passed, true);
  assert.equal((await call('map_playtest', { scenario: path.join(project, 'playtest.yml'), world: 'mm6', shipped: true })).data.passed, false);
}

const overview = await call('map_overview', { map: '6d01.blv', world: 'mm6' });
assert.equal(overview.data.overview.sectors, 59);
assert.ok(overview.data.findings.some((finding) => finding.includes('event 38')));
assert.match((await call('map_flow', { map: '6d01.blv', world: 'mm6', event: 23 })).data, /door 57 close/);
assert.equal((await call('map_flow', { map: '6d01.blv', world: 'mm6', event: 9999 })).data.error, 'no_such_object');
assert.equal((await call('map_overview', { map: 'nothing.blv', world: 'mm6' })).data.error, 'no_such_map');
const solved = await call('map_flow', { map: project });
assert.ok(solved.data.waves.length > 1);
assert.equal(solved.data.sector_rooms['1'] !== undefined, true);

// An overlay of a shipped map: a handler that calls a function the game does not have, or names a variable in
// quotes, is refused by the build with the reason; the corrected one builds and its script is returned.
const overlay = path.join(path.dirname(project), 'overlay');
// map_exec's command-line escape answers only commands without a method (S5a5): import has one now.
const refusedImport = await call('map_exec', { code: `const r = await oymap("import", "6d01.blv", "--world", "mm6", "--assets", assets, "--to", ${JSON.stringify(overlay)}); print(r.exit + " " + r.stderr);` });
assert.match(String(refusedImport.data), /^2 oymap import has a method of the request list: use call\("project\.import"/);
const imported = await call('map_exec', { code: `print(await call("project.import", {project: ${JSON.stringify(overlay)}, map: "6d01.blv", world: "mm6"}));` });
assert.match(JSON.stringify(imported.data), /written/);
const wrong = await call('map_edit', { project: overlay, ops: [
  { op: 'event.add', value: { id: 'evt:bad', preset: 'script', replaces: 'evt:e20', lua: 'evt.OpenTheDoor(57)\nevt.Set("MapVar2", 1)' } }] });
assert.equal(wrong.data.applied, true);
assert.ok(wrong.data.changes.includes('wiring.yml: added evt:bad'));
const refusedBuild = await call('map_build', { project: overlay });
assert.equal(refusedBuild.result.isError, true);
assert.ok(refusedBuild.data.issues.some((issue) => issue.message.includes('evt.OpenTheDoor is not a function of the game')));
assert.ok(refusedBuild.data.issues.some((issue) => issue.message.includes('where a variable selector')));
await call('map_edit', { project: overlay, ops: [{ op: 'set', id: 'evt:bad', fields: { lua: 'evt.SetDoorState(57, DoorAction.Open)' } }] });
const goodBuild = await call('map_build', { project: overlay });
assert.match(goodBuild.data.script, /evt\.SetDoorState\(57, DoorAction\.Open\)/);
assert.match((await call('map_api', { topic: 'lua' })).data, /SetDoorState/);
assert.match((await call('map_api', { topic: 'playtest' })).data, /new_game_flow/);
assert.equal((await call('map_api', { topic: 'schema', name: 'objects', section: 'placeholders' })).data.type, 'array');

// A project from nothing: one room and a start, read back without installing.
const fresh = path.join(path.dirname(project), 'fresh');
assert.match((await call('map_new', { project: fresh, id: 'fresh01', name: 'Fresh' })).data, /created/);
const firstRoom = await call('map_edit', { project: fresh, ops: [
  { op: 'room.add', value: { id: 'room:a', outline: [[0, 0], [512, 0], [512, 512], [0, 512]], floor: 0, ceiling: 384 } },
  { op: 'set_value', file: 'objects.yml', path: 'start', value: { room: 'room:a' } }] });
assert.equal(firstRoom.data.applied, true);
// Two sectors: the room and the map's reserved empty sector 0.
assert.equal((await call('map_overview', { map: fresh })).data.overview.sectors, 2);

const picture = await client.callTool({ name: 'map_render', arguments: { map: '6d01.blv', world: 'mm6', size: 256 } });
assert.equal(picture.content[0].type, 'image');
assert.ok(picture.content[0].data.length > 1000);

const torches = await call('map_assets', { query: 'torch', kind: 'decoration', limit: 3 });
assert.ok(torches.data.matches > 3);
assert.match((await call('map_api', { topic: 'ops' })).data, /set_value/);
const script = await call('map_exec', { code: 'const r = await call("project.status", { project: ' + JSON.stringify(project) + ' }); print(r.result.revision);' });
assert.match(String(script.data), /^[0-9a-f]{32}$/);
const viaCall = await call('map_exec', { code: 'const a = await call("project.query", { project: ' + JSON.stringify(project) + ' }); print(a.result.revision); const b = await call("session.configure", {}); print(b.error.data.kind);' });
assert.match(String(viaCall.data), /^[0-9a-f]{32}\nunknown_method$/);
const notThere = await call('map_playtest', { scenario: path.join(project, 'nothing.yml'), world: 'mm6' });
assert.equal(notThere.data.error, 'bad_request');

await client.close();

// The browser's endpoint: only with the pairing token, never for a page of another origin, and only the request
// list's exposed methods (the command-line bridge `run` is not one); host.test.mjs checks the rest.
const { spawn } = await import('node:child_process');
const { default: WebSocket } = await import('ws');
const port = 18000 + Math.floor(Math.random() * 2000);
// Its discovery file and inbox are the test's own (a running studio host's must not be touched).
const hostScratch = await mkdtemp(path.join(tmpdir(), 'oymap-mcp-host-'));
const hostProcess = spawn(process.execPath, [path.resolve(here, '../src/host.mjs'), 'serve', '--port', String(port),
  '--discovery', path.join(hostScratch, 'host.json'), '--inbox', path.join(hostScratch, 'inbox'),
  ...(process.env.OYMAP ? ['--oymap', process.env.OYMAP] : [])]);
const printed = await new Promise((resolve) => hostProcess.stdout.once('data', (data) => resolve(String(data).trim())));
const token = /#token=(\S+)/.exec(printed)[1];
const address = `ws://127.0.0.1:${port}/rpc?token=${token}`;
const open = (url, options) => new Promise((resolve) => {
  const socket = new WebSocket(url, options);
  socket.once('open', () => resolve(socket));
  socket.once('error', () => resolve(null));
});
assert.equal(await open(`ws://127.0.0.1:${port}/rpc`), null);
assert.equal(await open(`ws://127.0.0.1:${port}/rpc?token=wrong`), null);
assert.equal(await open(address, { origin: 'https://example.com' }), null);
const socket = await open(address, { origin: 'http://localhost:5173' });
assert.ok(socket);
// The answer to one call (notices, such as this socket's own client_joined, are passed over).
const ask = (id, method, params) => new Promise((resolve) => {
  const listen = (data) => {
    const message = JSON.parse(String(data));
    if (message.id !== id) return;
    socket.off('message', listen);
    resolve(message);
  };
  socket.on('message', listen);
  socket.send(JSON.stringify({ jsonrpc: '2.0', id, method, params }));
});
assert.equal((await ask(1, 'run', { command: 'status', args: [project, '--json'] })).error.code, -32601);
// project.open only reads (status would record a head under the example's .oymap).
const status = await ask(2, 'project.open', { project: 'openyamm-studio/examples/gatehouse_cellars' });
assert.match(status.result.revision, /^[0-9a-f]{32}$/);
socket.close();
hostProcess.kill();

console.log(`mcp: ${tools.length} tools, all checks passed`);
