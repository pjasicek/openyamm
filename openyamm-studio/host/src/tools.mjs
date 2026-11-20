// The MCP tools of Map Studio (devdocs/map_studio/PLAN.md section 8): thin calls into the oymap core. Workflow-level,
// not one per command: open, look, edit, check, build, play. Results are short JSON with ids an agent can use in the
// next call; long lists are cut with a count of what was left out.
//
// Every tool is on the request list (S5_BROWSER_EDITOR.md 2.3, D2; S5a2, S5a3): map_open (project.status,
// project.open, check.validate), map_new (project.new), map_query (project.query), map_edit (edit.apply),
// map_history (edit.history, edit.undo, edit.redo), map_validate (check.validate), map_overview (check.audit),
// map_flow (check.flow_event, check.solve), map_render (view.render), map_assets (assets.search), map_api
// (session.schema, assets.script_reference; "commands" is the serve's own list of command lines), map_build
// (build.run, build.install), map_pins (pins.*) and map_playtest (game.playtest, a host method answered here: the
// core never starts the game). Each calls the typed methods through the core's session, whose asset root is the
// host's (serve --assets) and whose mount of builds is set by session.configure before a method that reads or
// writes it. A typed refusal becomes an isError result naming data.kind and its fields.
// `run` (argv to a command line) is left only in map_exec's `oymap(command, ...)`, the escape hatch for the commands
// that still have no method (OYMAP_ESCAPE below: export, flow of every handler at once, things on a shipped map,
// install into a scratch asset root, scene-roundtrip and the two legacy builds); a command that has a method is
// refused with the method's name (S5a5 gave compare, metrics, probe, import, fmt, render-sketch and pins tour theirs).
// Its `call(method, params)` is the request list.
import { execFile } from 'node:child_process';
import { access, readFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import { z } from 'zod';

const text = (value) => ({ content: [{ type: 'text', text: typeof value === 'string' ? value : JSON.stringify(value, null, 1) }] });

// The command lines map_exec's `oymap()` still runs: those with no method of the request list (S5a5). Every other
// command is refused with the method that does its work.
export const OYMAP_ESCAPE = new Set(['export', 'flow', 'things', 'install', 'scene-roundtrip', 'build-map', 'compile-indoor']);
export const COMMAND_METHODS = {
  audit: 'check.audit', solve: 'check.solve', metrics: 'check.metrics', probe: 'check.probe', compare: 'compare.run',
  render: 'view.render', 'render-sketch': 'view.render_sketch', import: 'project.import', fmt: 'project.fmt',
  validate: 'check.validate', build: 'build.run', new: 'project.new', query: 'project.query', status: 'project.status',
  edit: 'edit.apply', undo: 'edit.undo', redo: 'edit.redo', record: 'project.record', lock: 'project.lock_prune',
  pins: 'pins.* (pins.tour for a tour)', assets: 'assets.search', 'script-reference': 'assets.script_reference',
  'event-functions': 'assets.script_reference', schema: 'session.schema',
};
// map_exec's oymap(command, ...args): the command line when it has no method, else a refusal naming the method.
export function escapeHatch(core, command, args) {
  if (OYMAP_ESCAPE.has(command)) return core.run(command, args);
  const method = COMMAND_METHODS[command];
  return Promise.resolve({ exit: 2, stdout: '', stderr: method
    ? `oymap ${command} has a method of the request list: use call("${method}", ...)`
    : `oymap ${command} is not run from map_exec (commands without a method: ${[...OYMAP_ESCAPE].join(', ')})` });
}
// The MCP App viewer's resource (S6 item A).
const VIEWER_URI = 'ui://openyamm/viewer';
const VIEWER_MIME = 'text/html;profile=mcp-app';
const VIEWER_FILE = path.join(path.dirname(fileURLToPath(import.meta.url)), 'viewer.html');
const failure = (message) => ({ isError: true, content: [{ type: 'text', text: message }] });
const cut = (list, limit) => (list.length > limit ? [...list.slice(0, limit), `... ${list.length - limit} more`] : list);

// Issues of the request list, errors first, then warnings, then notes (stable within each).
const SEVERITY_ORDER = { error: 0, warning: 1, note: 2 };
const bySeverity = (issues) => [...issues].sort((a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3));
const issueLine = (issue) => `${issue.severity} ${issue.file}: ${issue.path}: ${issue.message}`;
// A typed refusal of a method as the fields of a tool's answer: {ok: false, error: <data.kind>, message, ...data}.
const refusalFields = (error) => {
  const { kind, ...data } = error.data ?? {};
  if (Array.isArray(data.issues)) data.issues = bySeverity(data.issues);
  if (Array.isArray(data.new_issues)) data.new_issues = bySeverity(data.new_issues).map(issueLine);
  return { ok: false, error: kind ?? 'failed', message: error.message, ...data };
};
const refused = (error, extra = {}) => ({ isError: true, ...text({ ...extra, ...refusalFields(error) }) });

const escapePointer = (key) => key.replaceAll('~', '~0').replaceAll('/', '~1');
const isMap = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);

// The operations of map_edit in the request list's form (edit.apply takes add, set, remove and patch):
// "door.add" is add to "door" (the core takes a collection's singular), "door.set" is set; set_value becomes a patch
// of its file, made from the file's tree so that the maps on the way are made as set_value makes them, and a
// removal of something absent is left out (as set_value leaves it).
async function toRequestListOps(core, project, ops) {
  const trees = new Map();
  const treeOf = async (file) => {
    if (!trees.has(file)) {
      const answer = await core.call('project.read', { project, file });
      trees.set(file, answer.result?.tree && isMap(answer.result.tree) ? structuredClone(answer.result.tree) : {});
    }
    return trees.get(file);
  };
  const translated = [];
  for (const op of ops) {
    const name = typeof op?.op === 'string' ? op.op : '';
    const dot = name.indexOf('.');
    if (dot > 0) {
      const verb = name.slice(dot + 1);
      if (verb === 'add') translated.push({ op: 'add', to: op.to ?? name.slice(0, dot), value: op.value });
      else translated.push({ ...op, op: verb });
      continue;
    }
    if (name !== 'set_value' || typeof op.file !== 'string' || typeof op.path !== 'string') {
      translated.push(op);
      continue;
    }
    const keys = op.path.split('.');
    const tree = await treeOf(op.file);
    let node = tree;
    let depth = 0;
    while (depth < keys.length - 1 && isMap(node[keys[depth]])) node = node[keys[depth++]];
    const pointer = '/' + keys.slice(0, depth + 1).map(escapePointer).join('/');
    if (op.value === null) {
      if (depth === keys.length - 1 && keys[depth] in node) {
        translated.push({ op: 'patch', file: op.file, patch: [{ op: 'remove', path: pointer }] });
        delete node[keys[depth]];
      }
      continue;
    }
    // From the first key that is not a map on the way: the rest of the way as nested maps around the value.
    let value = structuredClone(op.value);
    for (let index = keys.length - 1; index > depth; --index) value = { [keys[index]]: value };
    translated.push({ op: 'patch', file: op.file, patch: [{ op: 'add', path: pointer, value }] });
    node[keys[depth]] = structuredClone(value);
  }
  return translated;
}

export const INSTRUCTIONS =
  'Map Studio edits OpenYAMM maps as projects (folders of YAML). Loop: map_open a project (map_new makes an empty one), map_edit it with ' +
  'operations, read the diff and new issues it returns, map_validate, map_build, map_playtest. Shipped maps and projects ' +
  'are read with map_overview, map_flow and map_render; a shipped map is changed through an overlay project ' +
  '(map_api topic "import"). Every edit returns the new revision; pass it as expect_revision to notice changes made ' +
  'by someone else. map_api explains operations, schemas and commands. Never edit generated Lua or files under ' +
  'build/; change the project.';

// The scenario lines a playtest returns: what its steps log, its failures and its verdict.
const PLAYTEST_LINE = /^(PLAY|FAIL|ASSERT fail|Scenario|WALK done|CLICK)/;

// game.playtest (schema/rpc/game.rpc.json), a host method: the host starts the game, never a core. Answers like a
// core's method: {result: {passed, log}} or {error: {code, message, data: {kind}}}.
export async function playtest({ scenario, world, shipped }, { game, assets, mount }) {
  const failed = (kind, message, code = -32000) => ({ error: { code, message, data: { kind } } });
  if (typeof scenario !== 'string' || scenario.length === 0 || typeof world !== 'string' || !/^[a-z0-9_]+$/.test(world)) {
    return failed('invalid_params', 'game.playtest takes a scenario path and a world', -32602);
  }
  try {
    await access(scenario);
  } catch {
    return failed('bad_request', `no scenario file ${scenario}`);
  }
  try {
    await access(game);
  } catch {
    return failed('failed', 'the game is not built (the host was started without a game binary)', -32603);
  }
  const runFolder = path.join(path.dirname(mount), 'playtest_run');
  await mkdir(runFolder, { recursive: true });
  await mkdir(mount, { recursive: true });
  const output = await new Promise((resolve) => {
    execFile(game, ['--asset-root', assets, ...(shipped ? [] : ['--extra-mount', mount]), '--world', world,
      '--headless-run-scenario', path.resolve(scenario), '--scenario-no-color'],
    { cwd: runFolder, timeout: 600000, maxBuffer: 64 << 20 },
    (error, stdout, stderr) => resolve(`${stdout ?? ''}\n${stderr ?? ''}`));
  });
  const lines = output.split('\n').filter((line) => PLAYTEST_LINE.test(line));
  return { result: { passed: /^Scenario passed/m.test(output), log: cut(lines, 60) } };
}

// check.flow_event's answer as `oymap flow --event` prints it.
const flowText = (flow) => [`event ${flow.event} "${flow.title}"`, ...flow.paths.map((route) => {
  const tests = route.tests.length === 0 ? ' always'
    : route.tests.map((test) => ` [${test.taken ? '' : 'not '}${test.what}]`).join('');
  const effects = route.effects.map((effect) => ` ${effect};`).join('');
  const nothing = route.effects.length === 0 && !route.error ? ' nothing' : '';
  return `  when${tests}:${effects}${nothing}${route.error ? ` (stopped: ${route.error})` : ''}`;
})].join('\n') + '\n';

export function registerTools(server, context) {
  const { core, assets, game, mount } = context;
  // Who else has a project open, when the tools run inside the studio host (F4, presence): a line for the results of
  // map_open, map_edit and map_pins, or nothing.
  const people = (project) => {
    const line = context.presence?.(project);
    return line ? { people: line } : {};
  };
  // The agent's name in history entries and pin threads: agent:<its MCP client's name> inside the studio host (the
  // name its client gives, cut to what an author may hold), else agent:mcp.
  const agentName = () => {
    const name = context.agent?.();
    return name ? `agent:${String(name).replace(/^agent:/, '').replace(/[^A-Za-z0-9_.-]+/g, '-').slice(0, 64) || 'mcp'}`
      : 'agent:mcp';
  };
  // The session's mount of builds (build.install writes it, `built` reads it), set before each method that needs it:
  // the core may have been started again since (it keeps no state but its caches).
  const withMount = () => core.call('session.configure', { asset_root: assets, mount });
  // A reading method's call, with the mount set first when the builds are read.
  const read = async (method, params) => {
    if (params.built) await withMount();
    return core.call(method, params);
  };
  const MAP = 'File name of a shipped map (6d01.blv, oute3.odm) with `world`, or the path of a project folder without it: the project is built privately and read as the game would read it (an overlay project: its base map with the overlay in front).';
  const guard = (handler) => async (input) => {
    try {
      return await handler(input);
    } catch (error) {
      return failure(error.message);
    }
  };
  const tool = (name, config, handler) => server.registerTool(name, config, guard(handler));
  const readOnly = { readOnlyHint: true, openWorldHint: false };
  const always = { 'anthropic/alwaysLoad': true };

  tool('map_open', {
    title: 'Open a map project',
    description: 'Opens a project folder: its revision, map card, the ids of everything in it, edits made outside the tool since it was last read, and its validation issues. Start here.',
    inputSchema: { project: z.string().describe('Path of the project folder (holds project.yml).') },
    annotations: readOnly, _meta: always,
  }, async ({ project }) => {
    const status = await core.call('project.status', { project });
    if (status.error) return refused(status.error);
    const opened = await core.call('project.open', { project });
    if (opened.error) return refused(opened.error);
    const checks = await core.call('check.validate', { project });
    if (checks.error) return refused(checks.error);
    // The map card's own words (not its lists), and the ids of each file's lists.
    const card = {};
    for (const [key, value] of Object.entries(opened.result.files['project.yml']?.tree ?? {})) {
      if (key !== 'format' && (value === null || typeof value !== 'object')) card[key] = value;
    }
    const files = {};
    for (const [file, entry] of Object.entries(opened.result.files)) {
      if (file === 'ids.lock.yml') continue;
      for (const [list, items] of Object.entries(entry.tree ?? {})) {
        if (!Array.isArray(items)) continue;
        files[file] ??= {};
        files[file][list] = items.filter((item) => isMap(item) && typeof item.id === 'string').map((item) => item.id);
      }
    }
    return text({
      handle: `${project}@${status.result.revision}`, revision: status.result.revision, card,
      files, outside_changes: status.result.outside_changes,
      issues: cut(bySeverity(checks.result.issues).map(issueLine), 20), ...people(project),
      // The hand-edit mark (S5_BROWSER_EDITOR.md 2.8): agents change such a project only through operations.
      ...(opened.result.hand_edited ? { hand_edited: opened.result.hand_edited } : {}),
    });
  });

  // The MCP App viewer (devdocs/map_studio/S6_PLAN.md item A): one page that draws map_view's structured result,
  // for clients that show MCP Apps (Claude Desktop, claude.ai, VS Code, Cursor); others read the text.
  server.registerResource('map-viewer', VIEWER_URI, {
    title: 'Map Studio viewer',
    description: 'Draws a project\'s plan (rooms, openings, things; an overlay\'s scene things on its base map) from map_view.',
    mimeType: VIEWER_MIME,
  }, async () => ({
    contents: [{ uri: VIEWER_URI, mimeType: VIEWER_MIME, text: await readFile(VIEWER_FILE, 'utf8'),
      _meta: { ui: { prefersBorder: true } } }],
  }));

  tool('map_view', {
    title: 'View a project\'s plan',
    description: 'A project\'s plan as data, drawn by the Map Studio viewer where the client shows MCP Apps: rooms with their outlines, openings and placed things (from the project\'s own lowering), or for an overlay project the base map\'s scene things (pulsing lights, ambient sounds, destructibles, water volumes, spawn points, ladders) with what the overlay does to each (kept, changed, removed) and its additions (also monsters, with their actor numbers after the base map\'s, and floor items), and the base map\'s cinematics kept or replaced and the overlay\'s added. Read only.',
    inputSchema: { project: z.string().describe('Path of the project folder (holds project.yml).') },
    annotations: readOnly,
    _meta: { ui: { resourceUri: VIEWER_URI }, 'ui/resourceUri': VIEWER_URI },
  }, async ({ project }) => {
    const opened = await core.call('project.open', { project });
    if (opened.error) return refused(opened.error);
    const card = opened.result.files['project.yml']?.tree ?? {};
    const structured = { title: card.name ?? card.id ?? path.basename(project), subtitle: '' };
    if (card.base) {
      await withMount();
      const overlay = await core.call('view.overlay', { project });
      if (overlay.error) return refused(overlay.error);
      structured.overlay = overlay.result;
      structured.subtitle = `overlay of ${overlay.result.base} (${overlay.result.world}, ${overlay.result.profile})`;
      const states = {};
      for (const thing of overlay.result.things) states[thing.state] = (states[thing.state] ?? 0) + 1;
      // What the overlay touches, each with its id, place and label (an added monster's actor number among them).
      const touched = overlay.result.things.filter((thing) => thing.state !== 'kept')
        .map((thing) => `${thing.id} ${thing.state} at [${thing.at.join(', ')}]: ${thing.label}`);
      return { ...text({ base: overlay.result.base, profile: overlay.result.profile, scene_keys: overlay.result.scene_keys,
        things: states, touched, cinematics: overlay.result.cinematics ?? [],
        issues: overlay.result.issues.map((issue) => `${issue.file}: ${issue.path}: ${issue.message}`) }),
      structuredContent: structured };
    }
    const layout = await core.call('view.layout', { project });
    if (layout.error) return refused(layout.error);
    structured.layout = layout.result;
    structured.subtitle = `${layout.result.kind} map, ${layout.result.world}`;
    return { ...text({ kind: layout.result.kind, world: layout.result.world, rooms: layout.result.rooms?.length ?? 0,
      openings: layout.result.openings?.length ?? 0, things: layout.result.things?.length ?? 0 }),
    structuredContent: structured };
  });

  tool('map_new', {
    title: 'Create a project',
    description: 'Creates an empty indoor project folder to draw a new dungeon into: a map card, one masonry theme, no rooms yet (so it reports one issue until the first room exists). Then use map_edit: rooms, openings and the start in one first edit (the start is {op: "set_value", file: "objects.yml", path: "start", value: {room}}; without it the edit is refused), reading map_api topic "schema" with `section` (name "rooms", section "rooms" or "openings"; the whole schema is long): outlines of any simple shape, corridor paths, slopes and stairs, pillars, platforms), then objects (start, lights, doors, switches, chests, spawns), then wiring events. For changing a shipped map use an overlay project instead (map_api topic "import").',
    inputSchema: { project: z.string().describe('Folder to create.'), id: z.string().describe('The map file stem, lower case, such as crypt01 (builds crypt01.blv).'),
      name: z.string().describe('The map\'s name as the player reads it.'), world: z.string().optional().describe('Default mm6.'),
      stats_id: z.number().int().optional().describe('Number of the map\'s row in the map table; each new map needs its own (default: the first free one of the world\'s declared range, else of the studio\'s 9400 to 9999: mod.map_number).') },
    annotations: { readOnlyHint: false, destructiveHint: false, openWorldHint: false },
  }, async ({ project, id, name, world, stats_id }) => {
    // A free map number when none is given (S6 item M): the asset root's rows and the world's range decide it.
    let proposed = null;
    if (stats_id === undefined) {
      const number = await core.call('mod.map_number', { world: world ?? 'mm6' });
      if (number.result) proposed = number.result;
    }
    const answer = await core.call('project.new', { project, id, name, world: world ?? 'mm6',
      stats_id: stats_id ?? proposed?.number });
    if (answer.error) return refused(answer.error);
    return text(`created ${project}${proposed ? ` (map number ${proposed.number}, the first free one of ${proposed.from}'s ${proposed.range.join(' to ')})` : ''}. ${answer.result.next}`);
  });

  tool('map_overview', {
    title: 'Overview of a shipped or installed map',
    description: 'A map as the game reads it (geometry, scene with overlays, event script with overlays): counts (chests are the old chest records, loot_containers the scene\'s; a map built by the studio has the latter), wiring findings (events bound to a face but without a handler, doors a script moves that the map lacks, script calls the game does not have), optionally the walkable reach. Shipped maps have findings of their own: compare with and without `built` before blaming a build. For a project use map_open.',
    inputSchema: {
      map: z.string().describe(MAP),
      world: z.string().optional().describe('World id: mm6, mm7, mm8, mm9.'),
      reach: z.boolean().optional().describe('Also walk the map from the party start (indoor; seconds).'),
      built: z.boolean().optional().describe('Read with the installed builds in front (after map_build with install).'),
    },
    annotations: readOnly, _meta: always,
  }, async ({ map, world, reach, built }) => {
    const answer = await read('check.audit', { map, world, reach, built });
    if (answer.error) return refused(answer.error);
    const data = answer.result;
    const order = { error: 0, warning: 1, info: 2 };
    const findings = [...data.findings].sort((a, b) => order[a.severity] - order[b.severity]);
    return text({ ...data, findings: cut(findings.map((f) => `${f.severity} ${f.code}: ${f.message}`), 30) });
  });

  tool('map_edit', {
    title: 'Edit a project',
    description: 'Applies operations to a project as one transaction: all or nothing. Returns the semantic diff, the issues the change introduces and fixes, and the new revision. A change that introduces issues is refused unless allow_issues. Operations: {op:"add", to:"doors", value:{id,...}} (or op:"door.add"), {op:"set", id, fields:{...}} (null removes a field), {op:"remove", id}; set and remove take `file` when the id is in more than one file (a plan space and its room share one), {op:"set_value", file, path, value}. Collections: doors lights switches chests spawns decorations exits placeholders (objects.yml), events (wiring.yml), rooms openings themes (rooms.yml). Pins: map_pins. A dry run or a refused change leaves `revision` as it was and gives `revision_if_applied`. See map_api topic "ops".',
    inputSchema: {
      project: z.string(),
      ops: z.array(z.record(z.any())).describe('The operations, in order.'),
      dry_run: z.boolean().optional().describe('Check and report without writing.'),
      expect_revision: z.string().optional().describe('Apply only if the project is still at this revision.'),
      allow_issues: z.boolean().optional(),
    },
    annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false }, _meta: always,
  }, async ({ project, ops, dry_run, expect_revision, allow_issues }) => {
    const translated = await toRequestListOps(core, project, ops);
    if (translated.length === 0) {
      return text({ ok: true, applied: false, dry_run: Boolean(dry_run), changes: [], errors: [], outside_changes: [],
        new_issues: [], fixed_issues: 0, note: 'nothing to change (set_value of null on a key that is not there)' });
    }
    const answer = await core.call('edit.apply', { project, ops: translated, dry_run, expect_revision,
      allow_errors: allow_issues, author: agentName() });
    if (answer.error) {
      const fields = refusalFields(answer.error);
      if (fields.error === 'new_errors') fields.revision_if_applied = fields.revision_after;
      if (fields.error === 'stale_revision') fields.revision_now = fields.revision;
      return { isError: true, ...text({ applied: false, dry_run: Boolean(dry_run), ...fields, errors: [answer.error.message] }) };
    }
    const result = answer.result;
    const data = { ok: true, applied: result.applied, dry_run: Boolean(dry_run), revision_before: result.revision_before,
      // The project's revision now: unchanged by a dry run or a change that changed nothing.
      revision: result.applied ? result.revision_after : result.revision_before };
    if (!result.applied && result.revision_after !== result.revision_before) data.revision_if_applied = result.revision_after;
    return text({ ...data, changes: result.changes, errors: [], outside_changes: result.outside_changes,
      new_issues: bySeverity(result.new_issues).map(issueLine), fixed_issues: result.fixed_issues.length,
      ...(result.ids_allocated ? { ids_allocated: result.ids_allocated } : {}),
      ...(result.notes ? { notes: result.notes } : {}),
      ...(result.hand_edited ? { hand_edited: result.hand_edited.message } : {}),
      ...(result.hand_objects ? { hand_objects: `you changed ${result.hand_objects.length} object(s) a person edited last: ${result.hand_objects.join(', ')}` } : {}),
      ...(result.outside_notice ? { outside_notice: result.outside_notice } : {}),
      ...people(project) });
  });

  tool('map_validate', {
    title: 'Check a project',
    description: 'Validates a project: schemas, references between files, and for a new indoor map the geometry rules of the build. Returns the issues with severity, file, path and message, errors first; `ok` means no issue of severity error (only errors stop a build; warnings and notes do not).',
    inputSchema: { project: z.string() },
    annotations: readOnly, _meta: always,
  }, async ({ project }) => {
    const answer = await core.call('check.validate', { project });
    if (answer.error) return refused(answer.error);
    // `ok`: no issue of severity error (warnings and notes do not stop a build).
    const data = { ok: answer.result.ok, issues: cut(bySeverity(answer.result.issues), 40) };
    if (answer.result.notes.length > 0) data.notes = answer.result.notes;
    return text(data);
  });

  tool('map_query', {
    title: 'Read part of a project',
    description: 'Reads one object by id (id: "door:gate") or one list (list: "doors") of a project, as stored; `file` where the id is in more than one file (a plan space and its room share one). For an id the build has numbered, also its engine number (`number`: the event number map_flow takes, a door\'s id).',
    inputSchema: { project: z.string(), id: z.string().optional(), list: z.string().optional(), file: z.string().optional() },
    annotations: readOnly,
  }, async ({ project, id, list, file }) => {
    const answer = await core.call('project.query', { project, id, list, file });
    if (answer.error) return refused(answer.error);
    return text(answer.result);
  });

  tool('map_flow', {
    title: 'What a map\'s events do, and the order it opens up',
    description: 'For a shipped map or a project (give its folder as `map`). With `event` (a number; map_query gives the number of a project\'s evt: id): what that handler tests and does on each way its tests can come out, every call with all its arguments. "door 5 close" and "open" are the engine\'s two door states, not what the player sees: which of them clears the way depends on the door, and the solve tells. Without `event`: the lock-and-key solve of an indoor map: the steps in which it opens up from the party start (`waves`), which events open what, which items each step needs, what is never reached, and `niches_not_reached` (sectors too small or too low to stand in: alcoves, door pockets, slots under a grating). Sectors are numbers (0 is the map\'s reserved empty sector); for a project `sector_rooms` names the room of each.',
    inputSchema: { map: z.string().describe(MAP), world: z.string().optional(), event: z.number().int().optional(), built: z.boolean().optional() },
    annotations: readOnly,
  }, async ({ map, world, event, built }) => {
    if (event !== undefined) {
      const flow = await read('check.flow_event', { map, world, event, built });
      return flow.error ? refused(flow.error) : text(flowText(flow.result));
    }
    const answer = await read('check.solve', { map, world, built });
    if (answer.error) return refused(answer.error);
    const data = answer.result;
    return text({ ...data, waves: data.waves.map((wave) => ({ ...wave, opened_by: cut(wave.opened_by, 40) })),
      never_reached: cut(data.never_reached, 20) });
  });

  tool('map_render', {
    title: 'Labelled picture of a map',
    description: 'Draws a shipped map or a project (give its folder as `map`) from its data: plan (top down) or iso. Indoor: sectors numbered and coloured, doors red with their numbers (d12), portals green, S the party start, yellow dots spawn points. Outdoor: terrain by height, buildings numbered (b7), clickable faces orange.',
    inputSchema: { map: z.string().describe(MAP), world: z.string().optional(), view: z.enum(['plan', 'iso']).optional(),
      size: z.number().int().min(256).max(1568).optional(), built: z.boolean().optional() },
    annotations: readOnly,
  }, async ({ map, world, view, size, built }) => {
    const answer = await read('view.render', { map, world, view: view ?? 'plan', size: size ?? 1024, built });
    if (answer.error) return refused(answer.error);
    const { png_base64: data, width, height } = answer.result;
    return { content: [{ type: 'image', data, mimeType: 'image/png' },
      { type: 'text', text: `size (${width} x ${height})` }] };
  });

  tool('map_assets', {
    title: 'Search the asset catalogue',
    description: 'Finds decorations (by internal name or hint, with radius and height in world units) and face textures (with their sizes in texels) whose name contains every word of the query. Names are short and old ("statue", "torch01", "wtrdr"): search one plain word first. Use the names in objects.yml and rooms.yml; when nothing fits, add a placeholder (objects.yml placeholders) instead of a wrong asset.',
    inputSchema: { query: z.string(), world: z.string().optional(), kind: z.enum(['decoration', 'texture']).optional(),
      limit: z.number().int().min(1).max(100).optional() },
    annotations: readOnly,
  }, async ({ query, world, kind, limit }) => {
    const answer = await core.call('assets.search', { query, world: world ?? 'mm6', kind, limit: limit ?? 20 });
    return answer.error ? refused(answer.error) : text(answer.result);
  });

  tool('map_api', {
    title: 'How to use Map Studio',
    description: 'Reference text: topic "ops" (operations and collections), "schema" with name (project, plan, rooms, objects, wiring, atmosphere, pins, common, ids_lock) and optionally `section` (one list of it, such as "lights"), "commands" (the oymap commands behind these tools), "import" (changing a shipped map through an overlay project), "lua" (what a script preset may call), "playtest" (how to write a scenario).',
    inputSchema: { topic: z.enum(['ops', 'schema', 'commands', 'import', 'lua', 'playtest']), name: z.string().optional(),
      section: z.string().optional() },
    annotations: readOnly,
  }, async ({ topic, name, section }) => {
    if (topic === 'schema') {
      const answer = await core.call('session.schema', name ? { name } : {});
      if (answer.error) return failure(answer.error.message);
      if (!name) return text(answer.result.schemas.map((entry) => `${entry.name}  ${entry.title}`).join('\n'));
      const schema = answer.result.schema;
      if (!section) return text(schema);
      const part = schema.properties?.[section] ?? schema.$defs?.[section];
      return part ? text(part)
        : failure(`${name} has no section ${section}; it has: ${Object.keys(schema.properties ?? {}).join(', ')}`);
    }
    if (topic === 'lua') {
      const answer = await core.call('assets.script_reference', { world: name ?? 'mm6' });
      if (answer.error) return refused(answer.error);
      const { functions, reference } = answer.result;
      return text(`${LUA_HELP}\n\n${reference.trim()}\n\nFunctions of the game (called as evt.<name>):\n${functions.join(' ')}`);
    }
    if (topic === 'playtest') return text(PLAYTEST_HELP);
    if (topic === 'commands') return text(await core.request('commands', {}));
    if (topic === 'import') return text(IMPORT_HELP);
    return text(OPS_HELP);
  });

  tool('map_build', {
    title: 'Build a project',
    description: 'Compiles a project: a new indoor map to BLV, scene and Lua; an overlay project (with `base`) to its overlays of the base map (a Lua overlay checked against the base map\'s script, a scene overlay checked by the game\'s reader, a cinematics overlay checked by the game\'s parser). With `install`, copies the result into the mount folder of builds (never assets_dev): map_overview, map_flow and map_render read it with `built: true`, and map_playtest plays it.',
    inputSchema: { project: z.string(), install: z.boolean().optional().describe('Install into the mount folder.'),
      dry_run: z.boolean().optional() },
    annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  }, async ({ project, install, dry_run }) => {
    const answer = await core.call('build.run', { project, dry_run: Boolean(dry_run) });
    if (answer.error) return refused(answer.error);
    const data = { ok: true, ...answer.result };
    // An overlay's generated script, to read what the wiring became (never to edit).
    const script = (data.files ?? []).find((file) => file.endsWith('.lua'));
    if (script && !dry_run) {
      const lua = await readFile(path.join(project, 'build', script), 'utf8');
      data.script = lua.length > 6000 ? lua.slice(0, 6000) + `\n-- ... ${lua.length - 6000} more characters` : lua;
    }
    if (install && !dry_run) {
      await withMount();
      const installed = await core.call('build.install', { project });
      if (installed.error) return refused(installed.error);
      return text({ ...data, installed_into: mount, installed: installed.result.installed });
    }
    return text(data);
  });

  tool('map_playtest', {
    title: 'Play a scenario in the game',
    description: 'Runs a headless scenario file in the game with the installed builds mounted in front of the assets, and returns its log lines, the failure with its Lua error, and whether it passed. map_api topic "playtest" has a scenario to start from and the helpers of its Lua steps. Run it with `shipped: true` too and compare the logs. Takes up to a few minutes.',
    inputSchema: { scenario: z.string().describe('Path of the scenario .yml.'), world: z.string(),
      shipped: z.boolean().optional().describe('Play the shipped maps only, without the installed builds (to compare).') },
    annotations: { readOnlyHint: true, openWorldHint: false },
  }, async ({ scenario, world, shipped }) => {
    const answer = await playtest({ scenario, world, shipped }, { game, assets, mount });
    return answer.error ? refused(answer.error) : text(answer.result);
  });

  tool('map_pins', {
    title: 'Review pins',
    description: 'Notes a person pinned to the map, in the game (`pin <text>`, imported by the studio host or `oymap pins import`) or in the studio\'s browser (P on the plan or the 3D view), and their threads (review/pins.yml, its own document: pins never change the project revision). action "list" returns them with the pins counter (status filters: open, claimed, resolved, accepted, declined; each pin has its `pose` as the game\'s `loc` gives it and its `picture`); "add" pins a note (text, and `on` an object id, `file` where the id is in two files); "claim" takes an open pin before working on it; "reply" adds to its thread; "resolve" says what was changed (text required) and marks it resolved; "decline" closes it with the reason. reply, resolve and decline take `pictures`: paths of PNG or JPEG files on this machine (the fix seen in the game: `oymap pins tour` gives the poses). The person accepts or reopens; with the studio open in a browser the person sees each answer at once.',
    inputSchema: { project: z.string(), action: z.enum(['list', 'add', 'claim', 'reply', 'resolve', 'decline']),
      id: z.string().optional(), text: z.string().optional(), on: z.string().optional(), file: z.string().optional(),
      status: z.enum(['open', 'claimed', 'resolved', 'accepted', 'declined']).optional(),
      pictures: z.array(z.string()).max(4).optional().describe('PNG or JPEG files to attach to a reply, resolve or decline.'),
      by: z.string().optional().describe('agent:<name>; default agent:mcp') },
    annotations: { readOnlyHint: false, destructiveHint: false, openWorldHint: false },
  }, async ({ project, action, id, text: note, on, file, status, pictures, by }) => {
    const author = by ?? agentName();
    let answer;
    if (action === 'list') answer = await core.call('pins.list', { project, status });
    else if (action === 'add') answer = await core.call('pins.add', { project, text: note ?? '', on, file, author });
    else if (action === 'claim') answer = await core.call('pins.claim', { project, pin: id, by: author });
    else {
      // The pictures go to the core as bytes (the request list takes no paths).
      const attached = [];
      for (const picture of pictures ?? []) {
        const bytes = await readFile(picture);
        attached.push({ media_type: /\.jpe?g$/i.test(picture) ? 'image/jpeg' : 'image/png', base64: bytes.toString('base64') });
      }
      answer = await core.call(`pins.${action}`, { project, pin: id, by: author, text: note,
        ...(attached.length > 0 ? { pictures: attached } : {}) });
    }
    return answer.error ? refused(answer.error) : text({ ok: true, ...answer.result, ...people(project) });
  });

  tool('map_history', {
    title: 'History of a project',
    description: 'action "list": the project\'s revision and its changes (transactions and edits made outside the tool), newest last. "undo" reverts your own latest change as a new entry (object by object; what someone changed since is left alone and listed as a conflict); "redo" reverts your latest undo.',
    inputSchema: { project: z.string(), action: z.enum(['list', 'undo', 'redo']) },
    annotations: { readOnlyHint: false, destructiveHint: true, openWorldHint: false },
  }, async ({ project, action }) => {
    if (action === 'list') {
      const answer = await core.call('edit.history', { project, limit: 15 });
      if (answer.error) return refused(answer.error);
      return text({ revision: answer.result.revision, count: answer.result.count, history: answer.result.entries });
    }
    // An agent's undo and redo are its own (S5b1: revert entries; a person's changes are never undone by it).
    const answer = await core.call(`edit.${action}`, { project, author: agentName() });
    return answer.error ? refused(answer.error) : text({ ok: true, ...answer.result });
  });

  tool('map_exec', {
    title: 'Run a script against the core',
    description: 'Runs JavaScript with `await call(method, params)` (a method of the request list, as the other tools use them: project.open, project.query, edit.apply, check.audit, check.solve, check.flow_event, check.metrics, check.probe, compare.run, view.render, view.render_sketch, project.import, project.fmt, pins.tour, assets.search, mod.pack, mod.list, mod.map_number, world.view ...; returns {result} or {error: {message, data: {kind}}}), `await oymap(command, ...args)` (a command line, only for the commands with no method: export, flow (every handler at once), things (a shipped map), install (into a scratch asset root, --root), scene-roundtrip, build-map, compile-indoor; returns {exit, stdout, stderr}; add "--json" and JSON.parse stdout; any other command answers exit 2 naming its method) and `print(value)`. For bulk work that would take many tool calls: audits over many maps, generated operations. Returns what was printed. The session has the asset root already; for `oymap` pass it as "--assets", assets. A map is the file name of a shipped map with its world, or a project folder; `export` takes a path. The script has no file or network access of its own.',
    inputSchema: { code: z.string().describe('The body of an async function.') },
    annotations: { readOnlyHint: false, openWorldHint: false },
  }, async ({ code }) => {
    const printed = [];
    const sandbox = vm.createContext({
      // The session's asset root and mount are the host's: a script may not change them.
      call: (method, params) => (method === 'session.configure'
        ? Promise.resolve({ error: { code: -32601, message: 'session.configure is the host\'s', data: { kind: 'unknown_method' } } })
        : method === 'game.playtest' ? playtest(params ?? {}, { game, assets, mount })
          : core.call(method, params ?? {})),
      oymap: (command, ...args) => escapeHatch(core, String(command), args),
      print: (value) => printed.push(typeof value === 'string' ? value : JSON.stringify(value)),
      assets, JSON, Math, Promise,
    });
    const script = new vm.Script(`(async () => {\n${code}\n})()`, { filename: 'map_exec.js' });
    await Promise.race([script.runInContext(sandbox, { timeout: 5000 }),
      new Promise((_, reject) => setTimeout(() => reject(new Error('map_exec ran longer than 120 seconds')), 120000))]);
    const output = printed.join('\n');
    return text(output.length > 8000 ? output.slice(0, 8000) + `\n... ${output.length - 8000} more characters` : output);
  });
}

const OPS_HELP = `Operations (map_edit ops, in order, one transaction):
  {"op":"add","to":"<collection>","value":{"id":"<kind>:<name>", ...}}   or  {"op":"<singular>.add","value":{...}}
  {"op":"set","id":"<id>","fields":{"key":value,"other":null}}            null removes the field; ids are not changed
  {"op":"remove","id":"<id>"}
  set and remove take "file":"<name>" too, needed when the id is in more than one file: ids are unique per file, and
  a plan's space shares its id with the room that realises it (plan.yml, rooms.yml)
  {"op":"set_value","file":"project.yml","path":"map_stats.treasure_level","value":2}   for what is not in a list
Collections: objects.yml: doors lights switches chests spawns decorations exits placeholders; wiring.yml: events;
rooms.yml: rooms openings themes; plan.yml: spaces links entrances goals keys points_of_interest landmarks set_pieces
states; project.yml: neighbours. Pins are not operations: map_pins (or oymap pins).
Ids are <kind>:<name>, lower case (door:gate, evt:lever, room:vault). Place things by relation: an object in a room
(room, and offset from its centre or at [x, y]) or on a wall (wall: north|east|south|west, along: 0..1, height).
Every field is described in its schema: map_api topic "schema", name "objects" (or rooms, wiring, plan, project).`;

const IMPORT_HELP = `Changing a shipped map: an overlay project.
  1. map_exec:  print(await call("project.import", {project: "<folder>", map: "6d01.blv", world: "mm6"}))
     writes project.yml (base: the map), a derived plan and ids.lock.yml with the map's own doors (door:d12),
     events (evt:e20) and sectors (room:s3).
  2. map_flow with event to read what a handler does today.
  3. map_edit: add wiring events that take a base event's place:
     {"op":"event.add","value":{"id":"evt:my_lever","replaces":"evt:e20","preset":"switch",
       "condition":{"not":{"map_var":2}},"opens":["door:d57"],"closes":["door:d55"],
       "texture":{"cog":-2011,"name":"t1swdu"},"sets":{"map_var":2}}}
     Presets: door (door, action), switch (opens, closes, toggles), chest (container), teleport (to, direction),
     exit (to a neighbour), text, script (lua: the handler body; map_api topic "lua"). Map variables are numbers
     in an overlay. A handler's order: condition (when it fails: else_effects, locked_text, stop), doors, texture,
     sets, effects, text, lua. Conditions: item, qbit, map_var, gold: {at_least | below}, stat: {name: <selector
     such as BaseLuck or MightBonus>, at_least}, award, autonote, not, any, all. Effects (lists of single steps):
     {gold: 100}, {add | subtract | set: {var: <selector name or {map_var: n}>, value}}, {autonote: n}, {qbit: n},
     {give_item | take_item: id}, {text}, {lua}. A text preset with condition, effects, else_effects, text and
     locked_text covers wells, fountains and shrines without a script.
     Only the handler is replaced: timers, load events, titles and chest links of the event stay.
  4. The scene (objects.yml \`scene\`; map_view shows the base map's things and their ids): {op: "patch", file:
     "objects.yml", patch: [...]} adds lights, sounds, spawns, destructibles, water, ladders ({id: ladder:x, position:
     [x, y, z] of its foot, facing, height}), monsters ({id: monster:x, position, monster}) and floor items ({id:
     item:x, position, item}) at absolute places; changes [{of: <lock id>, ...}] and removals [<lock id>] the base
     map's own (a base ladder moves by \`offset\`). Added monsters stand after the base map's actors (map_view gives
     each its actor number), so the base map's scripts keep theirs. wiring.yml \`cinematics\` become
     <stem>_<project id>.cinematics.yml: one named as a base cinematic (ids.lock.yml \`cinematics\`) replaces it, others
     are added; cues name base events by their lock ids (evt:e31014).
  5. map_build with install, then map_flow with built: true, and map_playtest (with and without shipped: true).`;

const LUA_HELP = `Prefer presets: a text, switch or door preset with condition, effects and else_effects says gold, stats,
variables, autonotes, items and texts without Lua (map_api topic "schema", name "wiring"). A script preset's \`lua\`
is the body of the handler in the Lua of the game's generated map scripts, for what no preset covers. The surest
guide is the shipped handler: map_flow shows every call with all its arguments. Common calls:
  evt.SetDoorState(doorId, DoorAction.Open | DoorAction.Close | DoorAction.Trigger)
  evt.StatusText("text")      evt.SetTexture(cog, "texture")      evt.OpenChest(containerId)
  evt.MoveToMap(x, y, z, direction, look, speed, house, icon, "map.odm" or "")
  IsAtLeast(selector, value)  SetValue(selector, value)  AddValue(selector, value)  SubtractValue(selector, value)
  SetAutonote(n)  SetQBit(QBit(n))  HasItem(id)  GiveItem(id)  RemoveItem(id)
A selector is MapVar(n), QBit(n) or one of the names listed below (Gold, HP, SP, BaseLuck ...). The build runs
every handler and refuses a call to a function the game does not have and a selector that is not a number (a
name in quotes, or a name that does not exist). It cannot check argument counts or meanings: compare map_flow of
the shipped and the built handler, and play both. The lists below are read from the game's own support script.`;

const PLAYTEST_HELP = `A scenario is a YAML file; map_playtest runs it headless. Start from this:
  id: my.playtest
  title: What it shows
  world: mm6
  mode: faithful
  steps:
    - new_game_flow: {start_map: 6d01.blv}          # a new party on that map (without start_map there is no map)
    - setup_shortcut: {kind: immortal, value: true}
    - play_lua:
        source: |
          log("doors: " .. door_state(57) .. " " .. door_state(58))
          click(20); wait(6)                         -- event 20, as if its face were clicked
          log("after 20: " .. door_state(57))
    - assert: {party_position: {x: 9000, y: 1916, radius: 200}}
play_lua helpers: click(event), wait(seconds), log(text) (the PLAY lines of the result), door_state(id) (open,
closed, opening, closing), status() (the status line; read it right after the click, before any wait, or it is
empty), qbit(id), has_item(id), item_count(id), gold(), party() (the selected member, names, Might, conditions),
experience(index), conditions(index), mapvar(name) (named variables only: numbered ones cannot be read),
loot_chest(event), open_door(event, door), take_chest(), close(). Luck, HP, SP and autonotes cannot be read in a
playtest; compare those through map_flow.
walk_to: {x, y, z, radius, timeout_seconds} walks there in a straight line or by the map's paths; z is the floor's height at the target (give several walk_to steps round corners and through doorways). assert: {party_position: {x, y, radius, z_min, z_max}}. Other steps: load_map, console. The full list is tests/scenarios/README.md in the repository.
Log what should be the same, then run the scenario twice, with and without shipped: true, and compare the logs. A
log that is the same proves little by itself: change one thing on purpose once and see the log change.`;
