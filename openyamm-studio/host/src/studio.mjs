// `host.mjs studio`: the browser editor's local host (S5_BROWSER_EDITOR.md 2.2, 2.4.3, 2.11, 2.12; F4). One HTTP
// server on 127.0.0.1 serves the web app's static files, the byte routes (textures, meshes, pin pictures), on /rpc
// the request list as JSON-RPC 2.0 over WebSocket, and on /mcp the MCP tools over Streamable HTTP (agents reach it
// through `oymap mcp`, the stdio relay: host.mjs relay). Browsers and MCP sessions share one `oymap serve` child
// (lane I), so what an agent changes the browser shows at once. The host holds no document state: it remembers per
// watched project only the last revision and pins counter it announced.
//
// Security, on every request: the Host header must be 127.0.0.1:<port> or localhost:<port> (421 otherwise; DNS
// rebinding); the WebSocket needs the pairing token and an allowed Origin (or none, for non-browser clients): the web
// app sends the token as a subprotocol (`oymap.token.<hex of its bytes>`, never in a URL), agents' and tests' clients
// as ?token=; every byte route and /mcp need `Authorization: Bearer <token>` (401), never a token in a query string.
// Pairing (S5c, S5_BROWSER_EDITOR.md 2.12): a hosted page on its own origin, named with --allow-origin, may connect
// and read the byte routes (CORS) once the person gave it the token and the browser's local-network permission.
// Only the catalogue's methods marked `exposed` are forwarded from a browser; a project is named by its key from
// host.projects and mapped by the path jail (projects.mjs).
//
// Routes:
//   GET /, /index.html, /gallery.html, /assets/...   the web app (web/dist); no token
//   GET /health                                       "ok" (the relay's check that a host runs); no token
//   GET /tex/<world>/<name>[?from=<level>]            a cooked texture: its 120-byte header and the un-framed blocks of
//                                                     levels from..last (textures.mjs); X-Texture-Scale, -From, -Levels
//   GET /mesh/<encoded key>/<name>                    <project>/.oymap/view/<name>, written by the core's view.mesh
//   GET /picture/<encoded key>/<encoded path>         a pin's picture: .oymap/pins/pictures/<f> or review/pictures/<f>
//   GET /walk/<encoded key>/<name>                    walk mode's files (S5a4): the built map, <stem>.walk.yml and
//                                                     <stem>.walk.terrain from <project>/build/, and
//                                                     decoration_data.txt from the asset root; house_data.txt from
//                                                     it too (the outdoor door's house picker, S5b2)
//   GET /job/<encoded key>/<revision>/<job>/<path>    a job's picture (png, jpg) or its log.txt, under
//                                                     <project>/.oymap/jobs/<revision>/<job>/
//   GET /core/oymap_worker.mjs, /core/oymap_worker.wasm  the WebAssembly core for the browser's worker; no token
//   ws  /rpc (and /)                                  JSON-RPC 2.0, with the notices below
//   POST, GET, DELETE /mcp                            MCP Streamable HTTP (one session per agent)
//
// Host methods (answered here, not by the core):
//   host.projects {}             -> {projects: [{key, name, id, kind, world, root}], roots: [key of each root]}: a new
//                                   project's folder (project.new) is named <root key>/<folder>
//   host.subscribe {project|null} -> {revision, counter, clients}: this browser has that project open; the host
//                                   watches its folder and sends it the project's notices
//   host.clients {}              -> {clients: [{id, kind: browser|mcp, name, project, since}]}
//   host.walk_prepare {project}  -> {kind, map, files: {map, state, terrain?, decorations}}: builds the project and
//                                   names the byte routes of what walk mode's worker loads (walk.load)
//   game.play_here {project, pose, visible?, commands?, seconds?} -> {run, map, world, kind}: builds, installs into the
//                                   project's own mount (output/studio_host/play_mounts/<key>) and starts the game at
//                                   the pose (play.mjs); game_started now, game_exited when it closes
//   jobs.start {project, kind, params?} -> {job}   a job on its lane (jobs.mjs: checks, compare, scale_bands,
//                                   town_feel, building_shots, pins_tour, playtest); job_progress and job_done follow
//   jobs.list {project} -> {jobs}   the project's jobs, newest first, without their results
//   jobs.status {project, job} -> {job}   one job with its result (its kind's output schema, jobs.rpc.json)
//   jobs.cancel {project, job} -> {job}   a queued job dropped, a running one killed (lane J's child, or its processes)
// Background checks: when a browser opens a project and a few seconds after each change, the host queues the
// project's background jobs for its revision (jobs.mjs, backgroundKinds) unless they ran already.
// session.hello is the core's answer with `host: {mode: "local", game, assets, version}` added.
//
// Notices (JSON-RPC notifications, no id; to every browser that subscribed to the project, client_* to all):
//   revision_changed {project, revision, previous, author, label, changes, entry}   the project's source changed:
//                     an edit through the host (browser or agent), or a change found on disk by the watcher
//                     (recorded first by project.status as an `outside` entry, or already in the history when an
//                     agent's `oymap edit` wrote it)
//   project_unreadable {project, message}   a file of the project does not parse (the browser keeps its last trees)
//   pins_changed {project, counter, pin?, action?, by?}   the pins document changed (never the revision)
//   client_joined {client}, client_left {client}
//   game_started {project, run, map, world}, game_exited {project, run, map, world, code, exit: {world, map, pose}|null}
//                     Play here's game: the exit pose is where the party stood when it closed (the camera follows)
//   job_progress {project, job}, job_done {project, job}   a job of the project queued, running (its last line), and
//                     finished (done, failed or cancelled); `job` is its summary (jobs.status gives the result)
//
// The watcher (the project's folder and its review/ folder, debounced 200 ms) watches only projects a browser has
// open, and ignores .oymap/ (history, view meshes, pins log and pictures written by the core) and build/ (the indoor
// dry build writes and removes its GLB there). The pins inbox (the game's `pin` command) is watched too: new pins are imported into their
// projects at once and announced with pins_changed.
import { randomUUID } from 'node:crypto';
import { createReadStream, existsSync, mkdirSync, readdirSync, readFileSync, realpathSync, statSync, unlinkSync, watch,
  writeFileSync } from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { WebSocketServer } from 'ws';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { isInitializeRequest } from '@modelcontextprotocol/sdk/types.js';
import { Core } from './core.mjs';
import { Jobs, jobSummary as jobSummaryOf } from './jobs.mjs';
import { playHere } from './play.mjs';
import { ProjectJail, readCard, readOriginal } from './projects.mjs';
import { TextureStore } from './textures.mjs';
import { INSTRUCTIONS, registerTools } from './tools.mjs';

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.wasm': 'application/wasm', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
  '.ico': 'image/x-icon', '.map': 'application/json', '.txt': 'text/plain; charset=utf-8',
};
const MESH_NAME = /^[0-9a-f]+-[0-9a-z]+-[0-9a-f]{12}\.mesh$/;
const PICTURE_PATH = /^(\.oymap\/pins\/pictures|review\/pictures)\/[A-Za-z0-9_.-]+\.(png|jpg)$/;
// A job's files: its pictures (in folders of its own) and its log.
const JOB_FILE = /^(?:[A-Za-z0-9_.-]+\/){0,3}[A-Za-z0-9_.-]+\.(png|jpg|txt)$/;
const JOB_ID = /^j[0-9a-z]+-[0-9a-f]+$/;
const REVISION = /^[0-9a-f]{12,64}$/;
// Walk mode's files beside a built map, and the worker's core.
const WALK_FILE = /^[A-Za-z0-9_-]+\.(blv|odm|walk\.yml|walk\.terrain)$/;
const CORE_FILES = new Set(['oymap_worker.mjs', 'oymap_worker.wasm']);
// The source files and the record (a change of either is a new view); the review document is announced apart.
const SOURCE_FILES = new Set(['project.yml', 'plan.yml', 'sketch.yml', 'rooms.yml', 'objects.yml', 'wiring.yml',
  'atmosphere.yml', 'ids.lock.yml']);
const PINS_FILE = 'review/pins.yml';
const DEBOUNCE_MS = 200;

// The catalogue's methods by full name, from schema/rpc/*.rpc.json: {exposed, writes}.
export function readCatalogue(rpcDir) {
  const methods = new Map();
  for (const name of readdirSync(rpcDir).filter((file) => file.endsWith('.rpc.json'))) {
    const document = JSON.parse(readFileSync(path.join(rpcDir, name), 'utf8'));
    for (const [method, entry] of Object.entries(document.methods ?? {})) {
      methods.set(`${document['x-group']}.${method}`, { exposed: entry.exposed === true, writes: entry.writes ?? 'none' });
    }
  }
  return methods;
}

// Whether a path the watcher reports (relative to the project, any separator) is the host's to look at.
export function watchedPath(relative) {
  const normal = relative.split(path.sep).join('/');
  return !(normal === '.oymap' || normal.startsWith('.oymap/') || normal === 'build' || normal.startsWith('build/'));
}

const rpcError = (code, kind, message, extra = {}) => ({ error: { code, message, data: { kind, ...extra } } });

export async function startStudio(options) {
  const { port, token, repo, web } = options;
  const catalogue = readCatalogue(options.rpcDir);
  const jail = new ProjectJail(repo, options.roots);
  const core = options.core ?? new Core(options.oymap, { assets: options.assets });
  const textures = new TextureStore([options.mount, options.assets], { cacheDir: options.textureCache ?? null });
  const version = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8')).version;
  const allowedHosts = new Set([`127.0.0.1:${port}`, `localhost:${port}`]);
  const allowedOrigins = new Set([`http://127.0.0.1:${port}`, `http://localhost:${port}`, 'http://localhost:5173',
    'http://127.0.0.1:5173', ...(options.allowOrigins ?? [])]);
  const inbox = options.inbox;
  const counters = { coreCalls: 0, notices: 0, watcherFlushes: 0, inboxImports: 0 };
  // Lane J (S5_BROWSER_EDITOR.md 2.4.3): a second core of the same binary for the jobs, never the browser's clicks.
  const coreJ = options.coreJ ?? new Core(options.oymap, { assets: options.assets });
  const playMounts = options.playMounts ?? path.join(repo, 'output', 'studio_host', 'play_mounts');
  const mountOfKey = (key) => path.join(playMounts, String(key).replace(/[^A-Za-z0-9_-]+/g, '_'));
  const log = options.log ?? (() => undefined);

  const security = {
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer',
  };
  const csp = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; "
    + "img-src 'self' blob: data:; font-src 'self' data:; "
    + `connect-src 'self' ws://127.0.0.1:${port} ws://localhost:${port}; worker-src 'self' blob:`;

  // --- clients and notices --------------------------------------------------------------------------------------

  // Every connected client: browsers (their socket) and MCP sessions (their transport). `project` is the key of
  // the project a browser has open.
  const clients = new Map();
  let nextClient = 1;
  const clientView = (client) => ({ id: client.id, kind: client.kind, name: client.name, project: client.project ?? null,
    since: client.since });
  const sendTo = (client, method, params) => {
    if (client.kind === 'browser' && client.socket.readyState === client.socket.OPEN) {
      client.socket.send(JSON.stringify({ jsonrpc: '2.0', method, params }));
      counters.notices += 1;
    }
  };
  const broadcast = (method, params) => {
    for (const client of clients.values()) sendTo(client, method, params);
  };
  const toProject = (key, method, params) => {
    for (const client of clients.values()) {
      // Each browser hears the project under the key it named it by.
      if (client.canonical === key) sendTo(client, method, { project: client.project, ...params });
    }
  };
  const join = (client) => {
    clients.set(client.id, client);
    log(`joined ${client.kind} ${client.name}`);
    broadcast('client_joined', { client: clientView(client) });
  };
  const leave = (client) => {
    if (!clients.delete(client.id)) return;
    broadcast('client_left', { client: clientView(client) });
    if (client.canonical) releaseProject(client.canonical);
  };

  // --- jobs (lane J and the processes: jobs.mjs) ------------------------------------------------------------------

  const infoOf = (key) => {
    const folder = jail.resolve(key);
    if (!folder) return { kind: '', world: '', reference: '', base: '' };
    const card = readCard(path.join(folder, 'project.yml'));
    return { ...card, ...readOriginal(path.join(folder, 'project.yml')) };
  };
  const jobs = new Jobs({ coreJ, coreI: core, repo, assets: options.assets, game: options.game, oymap: options.oymap,
    python: options.python, folderOf: (key) => jail.resolve(key), infoOf, mountOf: mountOfKey, log,
    runGame: options.runGame ?? path.join(repo, 'tools', 'run_game.sh'), env: options.gameEnv,
    blender: options.blender, bakeRoots: options.bakeRoots,
    notify: (key, method, params) => toProject(key, method, params) });
  const background = options.background !== false;

  // --- watched projects -----------------------------------------------------------------------------------------

  // By project key: {folder, revision, counter, watcher, timer, changed, users, unreadable}.
  const watched = new Map();

  // A project's one key, whatever it was named by (a browser's key, an agent's path, a link): the key of its real
  // folder. Watched projects and their notices go by it.
  const keyOfFolder = (folder) => {
    let real;
    try {
      real = realpathSync(path.resolve(folder));
    } catch {
      return null;
    }
    const key = jail.keyOf(real);
    return jail.resolve(key) ? key : null;
  };

  // What the core says the project is now; announces a new revision (with the history's latest entry: who changed
  // what) or a file that does not parse. `source` names who caused the check, for the log.
  const checkRevision = async (key, source) => {
    const state = watched.get(key);
    if (!state) return;
    const status = await core.call('project.status', { project: state.folder });
    const problem = status.error?.message
      ?? (status.result.unreadable?.length ? status.result.unreadable.map((file) => `${file.file}: ${file.message}`)
        .join('; ') : null);
    if (problem) {
      // The browser keeps its last good trees; the revision of the broken bytes is not announced.
      if (status.result) state.revision = status.result.revision;
      if (state.unreadable !== problem) {
        state.unreadable = problem;
        toProject(key, 'project_unreadable', { message: problem, files: status.result?.unreadable ?? [] });
      }
      return;
    }
    // A project that parses again is announced even at the revision it had (the browser drops its banner).
    const wasUnreadable = Boolean(state.unreadable);
    state.unreadable = null;
    if (status.result.revision === state.revision && !wasUnreadable) return;
    const previous = state.revision;
    state.revision = status.result.revision;
    const history = await core.call('edit.history', { project: state.folder, limit: 1 });
    const entry = history.result?.entries?.at(-1);
    const fromEntry = entry && entry.revision_after === status.result.revision;
    toProject(key, 'revision_changed', {
      revision: status.result.revision, previous,
      author: fromEntry ? entry.author : 'outside', label: fromEntry ? entry.label ?? '' : '',
      changes: fromEntry ? entry.changes : status.result.outside_changes, entry: fromEntry ? entry.sequence : null,
    });
    log(`revision_changed ${key} ${status.result.revision.slice(0, 8)} (${source})`);
    if (background) jobs.scheduleBackground(key);
  };

  const checkPins = async (key, extra = {}) => {
    const state = watched.get(key);
    if (!state) return;
    const answer = await core.call('pins.list', { project: state.folder });
    if (answer.error) return;
    if (answer.result.counter === state.counter) return;
    state.counter = answer.result.counter;
    toProject(key, 'pins_changed', { counter: state.counter, ...extra });
  };

  const flush = async (key) => {
    const state = watched.get(key);
    if (!state) return;
    state.timer = null;
    const changed = [...state.changed];
    state.changed.clear();
    counters.watcherFlushes += 1;
    log(`watcher ${key}: ${changed.join(' ')}`);
    // An unknown name (some platforms give none) is checked both ways.
    if (changed.some((name) => name === '' || SOURCE_FILES.has(name))) await checkRevision(key, 'watcher');
    if (changed.some((name) => name === '' || name === PINS_FILE || name === 'review')) await checkPins(key);
  };

  const watchProject = async (key) => {
    let state = watched.get(key);
    if (state) {
      state.users += 1;
      return state;
    }
    const folder = jail.resolve(key);
    state = { folder, revision: null, counter: null, watcher: null, reviewWatcher: null, timer: null, changed: new Set(),
      users: 1, unreadable: null };
    watched.set(key, state);
    // Two folder watches, not one recursive watch: the source files lie in the project's folder and the pins in
    // review/, and Node's recursive watch on Linux loses a file that a writer replaced by a rename (the core's
    // atomic writes), where a folder's own watch sees every rename into it.
    const note = (name) => {
      if (name && !watchedPath(name)) return;
      state.changed.add(name);
      if (state.timer) clearTimeout(state.timer);
      state.timer = setTimeout(() => void flush(key), DEBOUNCE_MS);
    };
    const watchReview = () => {
      if (state.reviewWatcher || !existsSync(path.join(folder, 'review'))) return;
      try {
        state.reviewWatcher = watch(path.join(folder, 'review'), (event, filename) =>
          note(filename ? `review/${filename}` : ''));
        state.reviewWatcher.on('error', () => undefined);
      } catch (error) {
        log(`cannot watch ${key}/review: ${error.message}`);
      }
    };
    try {
      state.watcher = watch(folder, (event, filename) => {
        const name = filename ? String(filename) : '';
        if (name === 'review') watchReview();
        note(name);
      });
      state.watcher.on('error', () => undefined);
      watchReview();
    } catch (error) {
      log(`cannot watch ${key}: ${error.message}`);
    }
    const status = await core.call('project.status', { project: folder });
    state.revision = status.result?.revision ?? null;
    if (status.error) state.unreadable = status.error.message;
    const pins = await core.call('pins.list', { project: folder });
    state.counter = pins.result?.counter ?? null;
    // The scorecard's background checks for the revision the project has now (soon: the browser's opening calls
    // go first on lane I, and lane J is another process).
    if (background && !state.unreadable) jobs.scheduleBackground(key, 1000);
    return state;
  };

  function releaseProject(key) {
    const state = watched.get(key);
    if (!state) return;
    state.users -= 1;
    if (state.users > 0) return;
    if (state.timer) clearTimeout(state.timer);
    state.watcher?.close();
    state.reviewWatcher?.close();
    watched.delete(key);
  }

  // After a call through the host that changed a project: announce it at once (the watcher would, 200 ms later; it
  // then finds nothing new).
  const afterWrite = async (key, method, params, answer) => {
    if (!key || !watched.has(key) || answer.error) return;
    const state = watched.get(key);
    if (method.startsWith('pins.') && method !== 'pins.list' && method !== 'pins.import_inbox') {
      if (answer.result.counter !== state.counter) {
        state.counter = answer.result.counter;
        toProject(key, 'pins_changed', { counter: state.counter, pin: answer.result.pin?.id ?? null,
          action: method.slice('pins.'.length), by: params.by ?? params.author ?? null });
      }
      return;
    }
    if (method === 'edit.apply') {
      const result = answer.result;
      if (result.applied && result.revision_after !== state.revision) {
        const previous = state.revision;
        state.revision = result.revision_after;
        toProject(key, 'revision_changed', { revision: result.revision_after, previous,
          author: params.author ?? 'agent', label: params.label ?? '', changes: result.changes, entry: null });
        if (background) jobs.scheduleBackground(key);
      }
      return;
    }
    await checkRevision(key, method);
  };

  // --- the pins inbox ---------------------------------------------------------------------------------------------

  let inboxTimer = null;
  let inboxRunning = false;
  const importInbox = async () => {
    inboxTimer = null;
    if (!inbox || !existsSync(inbox) || inboxRunning) return;
    inboxRunning = true;
    try {
      const folders = jail.list().map((project) => jail.resolve(project.key)).filter(Boolean);
      const answer = await core.call('pins.import_inbox', { inbox, projects: folders });
      counters.inboxImports += 1;
      for (const imported of answer.result?.imported ?? []) {
        const key = keyOfFolder(imported.project);
        log(`inbox: ${imported.file} -> ${key} ${imported.pin ?? ''}`);
        if (key && watched.has(key)) await checkPins(key, { pin: imported.pin ?? null, action: 'import', by: 'user' });
      }
    } finally {
      inboxRunning = false;
    }
  };
  const inboxSoon = () => {
    if (inboxTimer) clearTimeout(inboxTimer);
    inboxTimer = setTimeout(() => void importInbox(), 300);
  };
  // The inbox is the game's folder: the host never makes it. Until it exists, its parent is watched for it.
  let inboxWatcher = null;
  const watchInbox = () => {
    if (!inbox) return;
    try {
      if (!existsSync(inbox)) {
        inboxWatcher = watch(path.dirname(inbox), (event, filename) => {
          if (String(filename) !== path.basename(inbox) || !existsSync(inbox)) return;
          inboxWatcher.close();
          watchInbox();
          inboxSoon();
        });
      } else {
        inboxWatcher = watch(inbox, (event, filename) => {
          if (filename && /\.(yml|png)$/.test(String(filename))) inboxSoon();
        });
      }
      inboxWatcher.on('error', () => undefined);
    } catch (error) {
      log(`cannot watch the pins inbox: ${error.message}`);
    }
  };

  // --- MCP over Streamable HTTP ---------------------------------------------------------------------------------

  // The tools' core: the host's own, with each write announced to the browsers (the tools name projects by folder).
  const announcingCore = {
    call: async (method, params) => {
      const answer = await core.call(method, params);
      const entry = catalogue.get(method);
      if (entry && entry.writes !== 'none' && params?.project) {
        await afterWrite(keyOfFolder(params.project), method, params, answer);
      }
      return answer;
    },
    request: (...args) => core.request(...args),
    run: (...args) => core.run(...args),
    json: (...args) => core.json(...args),
    stop: () => undefined,
  };
  const mcpSessions = new Map();
  // For the tools' results: how many browsers have the project open, and the person's last change there.
  const presence = (folder) => {
    const key = keyOfFolder(folder);
    if (!key) return null;
    const browsers = [...clients.values()].filter((client) => client.kind === 'browser' && client.canonical === key).length;
    if (browsers === 0) return null;
    const state = watched.get(key);
    const last = state?.lastByUser;
    const ago = last ? ` ; the person last changed it ${Math.round((Date.now() - last.at) / 1000)} s ago (${last.what})` : '';
    return `a person has this project open in the studio (${browsers} browser${browsers > 1 ? 's' : ''}): pins and `
      + `changes show there at once${ago}`;
  };
  const handleMcp = async (request, response) => {
    if (request.headers.authorization !== `Bearer ${token}`) {
      return send(response, 401, 'the pairing token is needed');
    }
    const sessionId = request.headers['mcp-session-id'];
    let body;
    if (request.method === 'POST') {
      const chunks = [];
      for await (const chunk of request) chunks.push(chunk);
      try {
        body = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      } catch {
        return send(response, 400, 'not JSON');
      }
    }
    let session = sessionId ? mcpSessions.get(sessionId) : undefined;
    if (!session) {
      if (request.method !== 'POST' || sessionId || !isInitializeRequest(body)) {
        return send(response, sessionId ? 404 : 400, sessionId ? 'no such MCP session' : 'initialize first');
      }
      const client = { id: nextClient++, kind: 'mcp', name: 'agent', since: new Date().toISOString(), project: null };
      const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: () => randomUUID(),
        onsessioninitialized: (id) => mcpSessions.set(id, session),
      });
      const server = new McpServer({ name: 'openyamm-map-studio', version: '0.1.0' }, { instructions: INSTRUCTIONS });
      registerTools(server, { core: announcingCore, assets: options.assets, game: options.game,
        mount: options.toolsMount ?? options.mount, presence, agent: () => server.server.getClientVersion()?.name });
      session = { transport, server, client };
      transport.onclose = () => {
        if (transport.sessionId) mcpSessions.delete(transport.sessionId);
        leave(client);
      };
      // Present once the agent says it is ready (notifications/initialized), under the name its client gives.
      server.server.oninitialized = () => {
        client.name = `agent:${server.server.getClientVersion()?.name ?? 'mcp'}`;
        join(client);
      };
      await server.connect(transport);
      await transport.handleRequest(request, response, body);
      return undefined;
    }
    // An agent that vanished without ending its session (a killed relay) is seen by its event stream closing: a
    // client that does not open it again within a few seconds has left.
    if (request.method === 'GET') {
      session.streams = (session.streams ?? 0) + 1;
      response.on('close', () => {
        session.streams -= 1;
        setTimeout(() => {
          if (session.streams === 0 && mcpSessions.has(session.transport.sessionId)) void session.transport.close();
        }, 5000).unref();
      });
    }
    await session.transport.handleRequest(request, response, body);
    return undefined;
  };

  // --- HTTP -----------------------------------------------------------------------------------------------------

  // CORS only for the allowed origins (the Vite dev server on 5173 reads the byte routes across origins).
  const corsOf = (request) => {
    const origin = request.headers.origin;
    if (!origin || !allowedOrigins.has(origin)) return {};
    return { 'Access-Control-Allow-Origin': origin, 'Vary': 'Origin', 'Access-Control-Allow-Headers': 'Authorization',
      'Access-Control-Expose-Headers': 'X-Texture-Scale, X-Texture-From, X-Texture-Levels' };
  };

  function send(response, status, body, headers = {}) {
    response.writeHead(status, { 'Content-Type': 'text/plain; charset=utf-8', ...security, ...headers });
    response.end(body);
  }

  const serveFile = (response, file, type, headers) => {
    let info;
    try {
      info = statSync(file);
    } catch {
      return false;
    }
    if (!info.isFile()) return false;
    response.writeHead(200, { 'Content-Type': type, 'Content-Length': info.size, ...security, ...headers });
    createReadStream(file).pipe(response);
    return true;
  };

  const serveStatic = (request, response, pathname) => {
    if (!existsSync(web)) {
      return send(response, 404, `the web app is not built (${path.basename(web)} is missing): run the web build, `
        + 'cd openyamm-studio/web && npm run build');
    }
    let relative;
    try {
      relative = decodeURIComponent(pathname === '/' ? '/index.html' : pathname);
    } catch {
      return send(response, 400, 'bad path');
    }
    const file = path.resolve(web, '.' + relative);
    if (file !== web && !file.startsWith(web + path.sep)) return send(response, 404, 'not found');
    const type = TYPES[path.extname(file).toLowerCase()] ?? 'application/octet-stream';
    const headers = {
      // Hashed build files never change; pages are read again.
      'Cache-Control': relative.startsWith('/assets/') ? 'public, max-age=31536000, immutable' : 'no-cache' };
    if (type.startsWith('text/html')) headers['Content-Security-Policy'] = csp;
    if (!serveFile(response, file, type, headers)) return send(response, 404, 'not found');
    return undefined;
  };

  const server = http.createServer(async (request, response) => {
    if (!allowedHosts.has(request.headers.host)) return send(response, 421, 'wrong Host header');
    const cors = corsOf(request);
    const url = new URL(request.url, `http://${request.headers.host}`);
    const pathname = url.pathname;
    if (pathname === '/mcp') {
      try {
        return await handleMcp(request, response);
      } catch (error) {
        if (!response.headersSent) return send(response, 500, String(error.message ?? error));
        return undefined;
      }
    }
    if (request.method === 'OPTIONS') {
      // A browser's older private-network preflight (Chrome before its local-network permission) for an allowed origin.
      const privateNetwork = cors['Access-Control-Allow-Origin'] && request.headers['access-control-request-private-network']
        ? { 'Access-Control-Allow-Private-Network': 'true' } : {};
      return send(response, 204, '', { ...cors, ...privateNetwork, 'Access-Control-Allow-Methods': 'GET' });
    }
    if (request.method !== 'GET' && request.method !== 'HEAD') return send(response, 405, 'GET only', cors);
    if (pathname === '/health') return send(response, 200, 'ok');
    if (pathname.startsWith('/core/')) {
      const name = pathname.slice('/core/'.length);
      if (!options.coreWasm || !CORE_FILES.has(name)) return send(response, 404, 'not found');
      if (!serveFile(response, path.join(options.coreWasm, name), TYPES[path.extname(name)], { 'Cache-Control': 'no-cache',
        ...cors })) {
        return send(response, 404, 'the WebAssembly core is not built (openyamm-studio: ./build.sh wasm)');
      }
      return undefined;
    }
    const byteRoute = pathname.startsWith('/tex/') || pathname.startsWith('/mesh/') || pathname.startsWith('/picture/')
      || pathname.startsWith('/walk/') || pathname.startsWith('/job/');
    if (!byteRoute) return serveStatic(request, response, pathname);
    if (request.headers.authorization !== `Bearer ${token}`) return send(response, 401, 'the pairing token is needed', cors);
    try {
      let match;
      if ((match = /^\/tex\/([^/]+)\/([^/]+)$/.exec(pathname))) {
        const from = url.searchParams.has('from') ? Number(url.searchParams.get('from')) : 0;
        if (!Number.isInteger(from) || from < 0) return send(response, 400, 'from is a mip level, 0 or more', cors);
        const answer = await textures.answer(decodeURIComponent(match[1]), decodeURIComponent(match[2]).toLowerCase(), from);
        return send(response, answer.status, answer.body, { ...answer.headers, ...cors });
      }
      if ((match = /^\/mesh\/([^/]+)\/([^/]+)$/.exec(pathname))) {
        const folder = jail.resolve(decodeURIComponent(match[1]));
        const name = decodeURIComponent(match[2]);
        if (!folder || !MESH_NAME.test(name)) return send(response, 404, 'no such mesh', cors);
        if (!serveFile(response, path.join(folder, '.oymap', 'view', name), 'application/octet-stream',
          { 'Cache-Control': 'private, max-age=31536000, immutable', ...cors })) {
          return send(response, 404, 'no such mesh', cors);
        }
        return undefined;
      }
      if ((match = /^\/walk\/([^/]+)\/([^/]+)$/.exec(pathname))) {
        const folder = jail.resolve(decodeURIComponent(match[1]));
        const name = decodeURIComponent(match[2]);
        // The engine's decoration table (walk mode) and house table (the outdoor door's house picker, S5b2).
        const file = (name === 'decoration_data.txt' || name === 'house_data.txt') && options.assets
          ? path.join(options.assets, 'engine', 'data_tables', name)
          : folder && WALK_FILE.test(name) ? path.join(folder, 'build', name) : null;
        if (!file || !serveFile(response, file, 'application/octet-stream', { 'Cache-Control': 'no-cache', ...cors })) {
          return send(response, 404, 'no such walk file (host.walk_prepare builds them)', cors);
        }
        return undefined;
      }
      if ((match = /^\/job\/([^/]+)\/([^/]+)\/([^/]+)\/(.+)$/.exec(pathname))) {
        const folder = jail.resolve(decodeURIComponent(match[1]));
        const [revision, id] = [decodeURIComponent(match[2]), decodeURIComponent(match[3])];
        const relative = match[4].split('/').map((part) => decodeURIComponent(part)).join('/');
        if (!folder || !REVISION.test(revision) || !JOB_ID.test(id) || !JOB_FILE.test(relative)
          || relative.split('/').some((part) => part === '..' || part === '.')) {
          return send(response, 404, 'no such job file', cors);
        }
        const type = relative.endsWith('.png') ? 'image/png' : relative.endsWith('.jpg') ? 'image/jpeg'
          : 'text/plain; charset=utf-8';
        if (!serveFile(response, path.join(folder, '.oymap', 'jobs', revision, id, ...relative.split('/')), type,
          { 'Cache-Control': 'private, max-age=3600', ...cors })) {
          return send(response, 404, 'no such job file', cors);
        }
        return undefined;
      }
      if ((match = /^\/picture\/([^/]+)\/([^/]+)$/.exec(pathname))) {
        const folder = jail.resolve(decodeURIComponent(match[1]));
        const relative = decodeURIComponent(match[2]);
        if (!folder || !PICTURE_PATH.test(relative)) return send(response, 404, 'no such picture', cors);
        // A picture's name is its pin's and reply's: written once, never changed (a kept one moves to review/).
        if (!serveFile(response, path.join(folder, ...relative.split('/')),
          relative.endsWith('.png') ? 'image/png' : 'image/jpeg', { 'Cache-Control': 'private, max-age=3600', ...cors })) {
          return send(response, 404, 'the picture is not on this machine', cors);
        }
        return undefined;
      }
    } catch (error) {
      return send(response, 500, String(error.message ?? error), cors);
    }
    return send(response, 404, 'not found', cors);
  });

  // --- the request list over WebSocket ----------------------------------------------------------------------------

  // Maps the project keys of a browser's params onto folders; null when one is refused.
  const jailParams = (params, method) => {
    const mapped = { ...params };
    if ('project' in mapped) {
      // project.new names a folder that holds no project yet, under one of the roots.
      const folder = method === 'project.new' ? jail.resolveNew(mapped.project) : jail.resolve(mapped.project);
      if (!folder) return { refused: mapped.project };
      mapped.project = folder;
    }
    if (Array.isArray(mapped.projects)) {
      const folders = mapped.projects.map((key) => jail.resolve(key));
      const bad = folders.findIndex((folder) => !folder);
      if (bad >= 0) return { refused: mapped.projects[bad] };
      mapped.projects = folders;
    }
    // The pins inbox is the host's own folder: a browser names it "default".
    if ('inbox' in mapped) {
      if (mapped.inbox !== 'default' || !inbox) return { refused: String(mapped.inbox), inbox: true };
      mapped.inbox = inbox;
    }
    // So is the mods folder (mod.pack's `out`, mod.list's and mod.map_number's `mods`: S6 item M).
    for (const field of method.startsWith('mod.') ? ['out', 'mods'] : []) {
      if (!(field in mapped)) continue;
      if (mapped[field] !== 'default' || !options.mods) return { refused: String(mapped[field]), mods: true };
      mkdirSync(options.mods, { recursive: true });
      mapped[field] = options.mods;
    }
    return { params: mapped };
  };

  const refusedProject = (key) => {
    const what = `no project ${JSON.stringify(key)} in the host's project folders (host.projects lists them)`;
    return rpcError(-32000, 'not_a_project', what, { issues: [{ severity: 'error', code: 'project', file: '', path: '',
      message: what }] });
  };

  const answerOf = async (client, method, params) => {
    if (method === 'host.projects') return { result: { projects: jail.list(), roots: jail.rootKeys() } };
    if (method === 'host.clients') return { result: { clients: [...clients.values()].map(clientView) } };
    if (method === 'host.subscribe') {
      const key = params?.project ?? null;
      if (key !== null && !jail.resolve(key)) return refusedProject(key);
      const canonical = key === null ? null : keyOfFolder(jail.resolve(key));
      if (client.canonical && client.canonical !== canonical) releaseProject(client.canonical);
      const already = client.canonical === canonical && canonical !== null;
      client.project = key;
      client.canonical = canonical;
      if (key === null) return { result: { revision: null, counter: null, clients: [...clients.values()].map(clientView) } };
      const state = already ? watched.get(canonical) : await watchProject(canonical);
      return { result: { revision: state.revision, counter: state.counter, unreadable: state.unreadable,
        clients: [...clients.values()].map(clientView) } };
    }
    if (method.startsWith('jobs.')) return jobsAnswer(method, params ?? {});
    if (method === 'host.walk_prepare' || method === 'game.play_here') {
      const key = params?.project;
      const folder = typeof key === 'string' ? jail.resolve(key) : null;
      if (!folder) return refusedProject(key);
      if (method === 'host.walk_prepare') return walkPrepare(key, folder);
      const project = jail.list().find((entry) => entry.key === key) ?? jail.list().find((entry) => jail.resolve(entry.key) === folder);
      const canonical = keyOfFolder(folder);
      return playHere({ folder, world: project?.world ?? 'mm6', pose: params.pose, visible: params.visible === true,
        commands: params.commands ?? [], seconds: params.seconds }, {
        // Each project plays from a mount of its own: the shared one mixes worlds' rows (an MM7 map's travel row in
        // engine/data_tables stops an MM6 game from loading).
        core, repo, assets: options.assets, mount: mountOfKey(canonical ?? key),
        runs: options.playRuns ?? path.join(repo, 'output', 'studio_host', 'play'),
        runGame: options.runGame ?? path.join(repo, 'tools', 'run_game.sh'), env: options.gameEnv, log,
        onExit: ({ run, code, map, world, exitPose }) => {
          log(`play here ${run} closed (${code})${exitPose ? ` at ${exitPose.pose.position.join(' ')}` : ''}`);
          toProject(canonical, 'game_exited', { run, map, world, code, exit: exitPose });
        },
      }).then((answer) => {
        if (answer.result) toProject(canonical, 'game_started', { run: answer.result.run, map: answer.result.map,
          world: answer.result.world });
        return answer;
      });
    }
    const entry = catalogue.get(method);
    if (!entry || !entry.exposed) return rpcError(-32601, 'unknown_method', `unknown method '${method}'`);
    const given = params ?? {};
    if (typeof given !== 'object' || Array.isArray(given)) {
      return rpcError(-32602, 'invalid_params', 'the params are an object', { issues: [] });
    }
    const jailed = jailParams(given, method);
    if (jailed.refused !== undefined && jailed.mods) {
      return rpcError(-32000, 'bad_request', 'the mods folder is named "default" (the host\'s own folder)');
    }
    if (jailed.refused !== undefined) {
      if (!jailed.inbox) return refusedProject(jailed.refused);
      const what = 'the pins inbox is named "default" (the host\'s own folder)';
      return rpcError(-32000, 'not_a_project', what, { issues: [{ severity: 'error', code: 'project', file: '',
        path: '', message: what }] });
    }
    counters.coreCalls += 1;
    // mod.pack builds every project it packs: lane J's, so the browser's clicks do not wait behind it.
    const answer = await (method === 'mod.pack' ? coreJ : core).call(method, jailed.params);
    if (method === 'session.hello' && answer.result) {
      answer.result.host = { mode: 'local', game: Boolean(options.game && existsSync(options.game)),
        assets: Boolean(options.assets), version, jobs: true, python: jobs.python };
    }
    if (entry.writes !== 'none' && typeof jailed.params.project === 'string') {
      const canonical = keyOfFolder(jailed.params.project);
      const state = watched.get(canonical);
      if (state && !answer.error) {
        state.lastByUser = { at: Date.now(), what: answer.result?.pin?.id ? `${method} ${answer.result.pin.id}` : method };
      }
      await afterWrite(canonical, method, given, answer);
    }
    if (method === 'pins.import_inbox' && answer.result) {
      for (const imported of answer.result.imported) {
        const key = keyOfFolder(imported.project);
        if (key) await checkPins(key, { pin: imported.pin ?? null, action: 'import', by: 'user' });
      }
    }
    return answer;
  };

  // jobs.* (host methods: jobs.rpc.json): the project by its key, mapped by the jail; jobs go by the project's one key.
  const jobsAnswer = async (method, params) => {
    const key = typeof params.project === 'string' ? params.project : null;
    const folder = key ? jail.resolve(key) : null;
    if (!folder) return refusedProject(key);
    const canonical = keyOfFolder(folder);
    const badRequest = (message) => rpcError(-32000, 'bad_request', message);
    if (method === 'jobs.list') return { result: { jobs: jobs.list(canonical) } };
    if (method === 'jobs.start') {
      if (typeof params.kind !== 'string') return rpcError(-32602, 'invalid_params', 'jobs.start takes a kind', { issues: [] });
      const given = params.params ?? {};
      if (typeof given !== 'object' || Array.isArray(given)) {
        return rpcError(-32602, 'invalid_params', 'a job\'s params are an object', { issues: [] });
      }
      const started = await jobs.start(canonical, params.kind, given);
      if (started.invalid) return rpcError(-32602, 'invalid_params', started.error, { issues: [] });
      return started.error ? badRequest(started.error) : { result: { job: jobSummaryOf(started.job) } };
    }
    if (typeof params.job !== 'string') return rpcError(-32602, 'invalid_params', `${method} takes a job`, { issues: [] });
    if (method === 'jobs.status') {
      const job = jobs.status(canonical, params.job);
      return job ? { result: { job } } : rpcError(-32000, 'no_such_object', `no job ${params.job} of the project`);
    }
    if (method === 'jobs.cancel') {
      const job = jobs.cancel(canonical, params.job);
      return job ? { result: { job: jobSummaryOf(job) } }
        : rpcError(-32000, 'no_such_object', `no job ${params.job} of the project waits or runs`);
    }
    return rpcError(-32601, 'unknown_method', `unknown method '${method}'`);
  };

  // Walk mode (S5a4): the project built (its build folder holds the map and its movement state), and the byte routes of
  // what the browser's worker loads with walk.load.
  const walkPrepare = async (key, folder) => {
    const built = await core.call('build.run', { project: folder, dry_run: false });
    if (built.error) return built;
    const { kind, map, files } = built.result;
    if (kind === 'overlay') {
      return rpcError(-32000, 'bad_request', 'an overlay project changes a shipped map: walk mode walks new maps only');
    }
    const stem = map.replace(/\.(blv|odm)$/, '');
    if (!files.includes(`${stem}.walk.yml`)) {
      return rpcError(-32000, 'bad_request', 'the build wrote no movement state for walk mode (an outdoor map needs the '
        + 'asset root to read its tile tables)');
    }
    const route = (name) => `/walk/${encodeURIComponent(key)}/${encodeURIComponent(name)}`;
    return { result: { kind, map, files: { map: route(map), state: route(`${stem}.walk.yml`),
      ...(kind === 'outdoor' ? { terrain: route(`${stem}.walk.terrain`) } : {}), decorations: route('decoration_data.txt') } } };
  };

  // The token as the web app sends it: a subprotocol, beside the plain `oymap` the server answers with.
  const tokenProtocol = `oymap.token.${Buffer.from(token, 'utf8').toString('hex')}`;
  const protocolsOf = (request) => String(request.headers['sec-websocket-protocol'] ?? '').split(',')
    .map((value) => value.trim()).filter(Boolean);
  const sockets = new WebSocketServer({ noServer: true, maxPayload: 32 * 1024 * 1024,
    handleProtocols: (protocols) => (protocols.has('oymap') ? 'oymap' : false) });
  server.on('upgrade', (request, socket, head) => {
    const refuse = (status, text) => {
      socket.write(`HTTP/1.1 ${status} ${text}\r\nConnection: close\r\nContent-Length: 0\r\n\r\n`);
      socket.destroy();
    };
    if (!allowedHosts.has(request.headers.host)) return refuse(421, 'Misdirected Request');
    const url = new URL(request.url, 'http://127.0.0.1');
    if (url.pathname !== '/rpc' && url.pathname !== '/') return refuse(404, 'Not Found');
    if (url.searchParams.get('token') !== token && !protocolsOf(request).includes(tokenProtocol)) {
      return refuse(401, 'Unauthorized');
    }
    const origin = request.headers.origin;
    if (origin !== undefined && !allowedOrigins.has(origin)) return refuse(403, 'Forbidden');
    sockets.handleUpgrade(request, socket, head, (client) => sockets.emit('connection', client, request));
    return undefined;
  });
  sockets.on('connection', (socket) => {
    const client = { id: nextClient++, kind: 'browser', name: 'browser', socket, since: new Date().toISOString(),
      project: null };
    join(client);
    socket.on('close', () => leave(client));
    socket.on('message', async (data) => {
      let message;
      try {
        message = JSON.parse(data.toString());
      } catch {
        socket.send(JSON.stringify({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'not a JSON message',
          data: { kind: 'failed' } } }));
        return;
      }
      if (!message || typeof message !== 'object' || typeof message.method !== 'string') {
        socket.send(JSON.stringify({ jsonrpc: '2.0', id: message?.id ?? null, error: { code: -32600,
          message: 'not a JSON-RPC request', data: { kind: 'failed' } } }));
        return;
      }
      const answer = await answerOf(client, message.method, message.params);
      if (socket.readyState === socket.OPEN) socket.send(JSON.stringify({ jsonrpc: '2.0', id: message.id ?? null, ...answer }));
    });
  });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', resolve);
  });

  // Where `oymap mcp` (the relay) finds this host: its port and token, readable by this user only.
  if (options.discovery) {
    mkdirSync(path.dirname(options.discovery), { recursive: true });
    writeFileSync(options.discovery, JSON.stringify({ port, token, pid: process.pid, started: new Date().toISOString() }),
      { mode: 0o600 });
  }
  watchInbox();
  void importInbox();

  return {
    server, core, coreJ, jobs, textures, jail, counters, clients, watched,
    close: () => new Promise((resolve) => {
      for (const client of sockets.clients) client.terminate();
      for (const session of mcpSessions.values()) void session.transport.close();
      for (const key of [...watched.keys()]) {
        const state = watched.get(key);
        if (state.timer) clearTimeout(state.timer);
        state.watcher?.close();
        state.reviewWatcher?.close();
        watched.delete(key);
      }
      if (inboxTimer) clearTimeout(inboxTimer);
      inboxWatcher?.close();
      jobs.stop();
      coreJ.stop();
      if (options.discovery) {
        try {
          const kept = JSON.parse(readFileSync(options.discovery, 'utf8'));
          if (kept.pid === process.pid && kept.port === port) unlinkSync(options.discovery);
        } catch {
          // gone already
        }
      }
      core.stop();
      server.close(() => resolve());
      server.closeAllConnections();
    }),
  };
}
