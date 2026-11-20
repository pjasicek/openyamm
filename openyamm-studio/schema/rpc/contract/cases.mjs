// The RPC contract suite's calls (S5_BROWSER_EDITOR.md 2.3, "Contract test"): run in order against each backend on
// its own fresh copy of each fixture. A step is
//   { name, method, params, expect: 'result' | <error kind>, save?, differs?, touch? }
// `params` may be a function of the state (`$` holds the project folder and what earlier steps saved). `save` takes
// values out of a result for later steps. `differs` lists JSON pointers in which the backends may answer differently
// (anything else must be the same bytes). `touch` is an edit made outside the tool, the same on every backend.

import { fileURLToPath } from 'node:url';

const at = (state) => ({ project: state.project });

// A pin as the game's `pin <text>` writes it into its inbox (game/debug/PinInbox.cpp), naming its project when the
// map was installed with a <stem>.studio.yml.
const gamePin = (project, map, stem, text) => [
  'format: 1', 'source: game', 'author: user', 'created: "2026-11-14T19:00:00"', `text: "${text}"`, 'world: "mm6"',
  `map: "${map}"`, 'pose:', '  position: [1024.000, 256.500, 0.000]', '  yaw_radians: 1.571', '  pitch_degrees: -3.000',
  '  heading_yaw_units: 512', `picture: "${stem}.png"`,
  ...(project ? [`project: "${project}"`, 'revision: "0123456789abcdef0123456789abcdef"', 'lock_hash: "none"'] : []),
  ''].join('\n');

export const fixtures = [
  {
    name: 'gatehouse_cellars',
    source: 'examples/gatehouse_cellars',
    steps: [
      { name: 'hello', method: 'session.hello', params: {}, expect: 'result', differs: ['/result/backend'] },
      { name: 'hello with an unknown param', method: 'session.hello', params: { x: 1 }, expect: 'invalid_params' },
      { name: 'unknown method', method: 'project.nonexistent', params: {}, expect: 'unknown_method' },
      { name: 'open', method: 'project.open', params: at, expect: 'result' },
      { name: 'layout', method: 'view.layout', params: at, expect: 'result' },
      { name: 'mesh', method: 'view.mesh', params: at, expect: 'result' },
      { name: 'mesh again: kept', method: 'view.mesh', params: at, expect: 'result' },
      { name: 'open a missing folder', method: 'project.open', params: (s) => ({ project: `${s.project}/nothing` }),
        expect: 'not_a_project' },
      { name: 'layout of a missing folder', method: 'view.layout', params: (s) => ({ project: `${s.project}/nothing` }),
        expect: 'not_a_project' },
      { name: 'read rooms.yml', method: 'project.read', params: (s) => ({ ...at(s), file: 'rooms.yml' }),
        expect: 'result' },
      { name: 'read a file the project lacks', method: 'project.read',
        params: (s) => ({ ...at(s), file: 'review/pins.yml' }), expect: 'no_such_file' },
      { name: 'read a file the format lacks', method: 'project.read', params: (s) => ({ ...at(s), file: 'x.yml' }),
        expect: 'invalid_params' },
      { name: 'status, first sight', method: 'project.status', params: at, expect: 'result',
        save: (r, s) => { s.r0 = r.revision; } },
      { name: 'pins, none', method: 'pins.list', params: at, expect: 'result' },
      { name: 'add a pin', method: 'pins.add', expect: 'result', differs: ['/result/pin/created'],
        params: (s) => ({ ...at(s), text: 'The gate reads as a wall.', on: 'door:gate', author: 'user',
          map: 'studio01.blv', world: 'mm6',
          pose: { position: [512.5, 256, 0], yaw_radians: 1.5708, pitch_degrees: -3, heading_yaw_units: 512 } }) },
      { name: 'a pin on an id the project lacks', method: 'pins.add', expect: 'bad_request',
        params: (s) => ({ ...at(s), text: 'Where?', on: 'door:nothing' }) },
      { name: 'a pin on an id two files share', method: 'pins.add', expect: 'bad_request',
        params: (s) => ({ ...at(s), text: 'Which?', on: 'room:entry' }) },
      { name: 'a pin on a point, by an agent', method: 'pins.add', expect: 'result', differs: ['/result/pin/created'],
        params: (s) => ({ ...at(s), text: 'A dark corner.', at: [100, 200, 0], author: 'agent:contract' }) },
      { name: 'status: pins leave the revision', method: 'project.status', params: at, expect: 'result',
        save: (r, s) => { s.r1 = r.revision; } },
      { name: 'pins, open', method: 'pins.list', params: (s) => ({ ...at(s), status: 'open' }), expect: 'result',
        differs: ['/result/pins/0/created', '/result/pins/1/created'] },
      { name: 'pins, resolved', method: 'pins.list', params: (s) => ({ ...at(s), status: 'resolved' }),
        expect: 'result' },
      { name: 'claim a pin', method: 'pins.claim', expect: 'result', differs: ['/result/pin/created'],
        params: (s) => ({ ...at(s), pin: 'pin:p1', by: 'agent:contract' }) },
      { name: 'claim it from another agent', method: 'pins.claim', expect: 'wrong_state',
        params: (s) => ({ ...at(s), pin: 'pin:p1', by: 'agent:other' }) },
      { name: 'claim a pin that is not there', method: 'pins.claim', expect: 'no_such_pin',
        params: (s) => ({ ...at(s), pin: 'pin:p9', by: 'agent:contract' }) },
      { name: 'accept a pin not resolved', method: 'pins.accept', expect: 'wrong_state',
        params: (s) => ({ ...at(s), pin: 'pin:p1' }) },
      { name: 'patch a corner, dry run', method: 'edit.apply', expect: 'result',
        params: (s) => ({ ...at(s), dry_run: true, expect_revision: s.r1, ops: [{ op: 'patch', id: 'room:entry',
          file: 'rooms.yml', patch: [{ op: 'test', path: '/outline/1', value: [768, 0] },
            { op: 'replace', path: '/outline/1', value: [832, 0] }] }] }) },
      { name: 'patch an id two files share', method: 'edit.apply', expect: 'bad_operation',
        params: (s) => ({ ...at(s), ops: [{ op: 'patch', id: 'room:entry',
          patch: [{ op: 'replace', path: '/ceiling', value: 400 }] }] }) },
      { name: 'patch whose test fails', method: 'edit.apply', expect: 'bad_operation',
        params: (s) => ({ ...at(s), ops: [{ op: 'patch', id: 'room:entry', file: 'rooms.yml',
          patch: [{ op: 'replace', path: '/ceiling', value: 400 }, { op: 'test', path: '/outline/0', value: [1, 1] }]
        }] }) },
      { name: 'patch an id', method: 'edit.apply', expect: 'bad_operation',
        params: (s) => ({ ...at(s), ops: [{ op: 'patch', id: 'door:gate',
          patch: [{ op: 'replace', path: '/id', value: 'door:other' }] }] }) },
      { name: 'patch the pins file', method: 'edit.apply', expect: 'bad_operation',
        params: (s) => ({ ...at(s), ops: [{ op: 'patch', file: 'review/pins.yml',
          patch: [{ op: 'add', path: '/notes', value: 'x' }] }] }) },
      { name: 'stale revision', method: 'edit.apply', expect: 'stale_revision',
        params: (s) => ({ ...at(s), expect_revision: '0123456789abcdef0123456789abcdef',
          ops: [{ op: 'remove', id: 'door:gate' }] }) },
      { name: 'a change that adds errors', method: 'edit.apply', expect: 'new_errors',
        params: (s) => ({ ...at(s), ops: [{ op: 'remove', id: 'room:entry', file: 'rooms.yml' }] }) },
      { name: 'no operations', method: 'edit.apply', expect: 'invalid_params',
        params: (s) => ({ ...at(s), ops: [] }) },
      { name: 'an operation the list does not have', method: 'edit.apply', expect: 'invalid_params',
        params: (s) => ({ ...at(s), ops: [{ op: 'teleport', id: 'door:gate', to: 'room:hall' }] }) },
      { name: 'patch the ceiling and a list by key', method: 'edit.apply', expect: 'result',
        save: (r, s) => { s.r2 = r.revision_after; },
        params: (s) => ({ ...at(s), expect_revision: s.r1, author: 'agent:contract', label: 'ceiling and names',
          ops: [
          { op: 'patch', id: 'room:entry', file: 'rooms.yml', patch: [
            { op: 'test', path: '/ceiling', value: 384 }, { op: 'replace', path: '/ceiling', value: 400 }] },
          { op: 'patch', file: 'rooms.yml', patch: [
            { op: 'replace', path: '/rooms/room:hall/name', value: 'Great hall' },
            { op: 'add', path: '/rooms/room:hall/notes', value: 'Renamed by the contract suite.' }] },
          { op: 'patch', file: 'project.yml', patch: [{ op: 'replace', path: '/name', value: 'The Gatehouse' }] }] }) },
      { name: 'move and copy', method: 'edit.apply', expect: 'result', save: (r, s) => { s.r3 = r.revision_after; },
        params: (s) => ({ ...at(s), expect_revision: s.r2, ops: [
          { op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [
            { op: 'copy', from: '/name', path: '/label' }, { op: 'move', from: '/label', path: '/notes' }] }] }) },
      { name: 'set', method: 'edit.apply', expect: 'result',
        params: (s) => ({ ...at(s), expect_revision: s.r3, ops: [
          { op: 'set', id: 'room:hall', file: 'rooms.yml', fields: { notes: 'Set by the contract suite.' } }] }) },
      { name: 'mesh after the edits: the new revision', method: 'view.mesh', params: at, expect: 'result' },
      { name: 'open after the edits: the trees read back', method: 'project.open', params: at, expect: 'result',
        differs: ['/result/files/review~1pins.yml'] },
      { name: 'resolve the pin after the change', method: 'pins.resolve', expect: 'result',
        differs: ['/result/pin/created', '/result/pin/replies/0/created'],
        params: (s) => ({ ...at(s), pin: 'pin:p1', by: 'agent:contract', text: 'Gave the gate a frame.' }) },
      { name: 'resolve it without saying what was done', method: 'pins.resolve', expect: 'invalid_params',
        params: (s) => ({ ...at(s), pin: 'pin:p2', by: 'agent:contract', text: '' }) },
      { name: 'reopen it', method: 'pins.reopen', expect: 'result',
        differs: ['/result/pin/created', '/result/pin/replies/0/created', '/result/pin/replies/1/created'],
        params: (s) => ({ ...at(s), pin: 'pin:p1', text: 'It still reads as a wall from the hall.' }) },
      { name: 'reply without a status change', method: 'pins.reply', expect: 'result',
        differs: ['/result/pin/created', '/result/pin/replies/0/created', '/result/pin/replies/1/created',
          '/result/pin/replies/2/created'],
        params: (s) => ({ ...at(s), pin: 'pin:p1', by: 'agent:contract', text: 'Looking at it from the hall.' }) },
      { name: 'resolve again', method: 'pins.resolve', expect: 'result',
        differs: ['/result/pin/created', ...[0, 1, 2, 3].map((n) => `/result/pin/replies/${n}/created`)],
        params: (s) => ({ ...at(s), pin: 'pin:p1', by: 'agent:contract', text: 'A lintel over it now.' }) },
      { name: 'accept', method: 'pins.accept', expect: 'result',
        differs: ['/result/pin/created', ...[0, 1, 2, 3, 4].map((n) => `/result/pin/replies/${n}/created`)],
        params: (s) => ({ ...at(s), pin: 'pin:p1' }) },
      { name: 'decline the other', method: 'pins.decline', expect: 'result',
        differs: ['/result/pin/created', '/result/pin/replies/0/created'],
        params: (s) => ({ ...at(s), pin: 'pin:p2', by: 'agent:contract', text: 'The corner is lit by the torch.' }) },
      { name: 'status, nothing outside', method: 'project.status', params: at, expect: 'result' },
      { name: 'an edit outside the tool', touch: { file: 'rooms.yml', from: 'name: Store room', to: 'name: Larder' } },
      { name: 'status, the outside edit', method: 'project.status', params: at, expect: 'result' },
      { name: 'record the outside edit', method: 'project.record', expect: 'result',
        params: (s) => ({ ...at(s), author: 'agent:contract', label: 'hand edit of the store room' }) },
      { name: 'record again: nothing new', method: 'project.record', expect: 'result',
        params: (s) => ({ ...at(s), author: 'agent:contract' }) },
      { name: 'record as nobody', method: 'project.record', expect: 'invalid_params',
        params: (s) => ({ ...at(s), author: 'outside' }) },
      { name: 'prune the lock, dry run', method: 'project.lock_prune', expect: 'result',
        params: (s) => ({ ...at(s), dry_run: true }) },
      { name: 'validate without assets', method: 'check.validate', params: (s) => ({ ...at(s), use_assets: false }),
        expect: 'result' },
      { name: 'validate', method: 'check.validate', params: at, expect: 'result' },
      { name: 'build, dry run', method: 'build.run', params: (s) => ({ ...at(s), dry_run: true }), expect: 'result' },
      { name: 'things', method: 'check.things', params: at, expect: 'result' },
      { name: 'pins after', method: 'pins.list', params: at, expect: 'result',
        differs: ['/result/pins/0/created', '/result/pins/1/created',
          ...[0, 1, 2, 3, 4, 5].map((n) => `/result/pins/0/replies/${n}/created`), '/result/pins/1/replies/0/created'] },
      { name: 'the game pins two things', write: (s) => [
        { path: `${s.project}_inbox/20261114-190000-studio01.yml`, text: gamePin(s.project, 'studio01.blv',
          '20261114-190000-studio01', 'The lever is hard to see.') },
        { path: `${s.project}_inbox/20261114-190000-studio01.png`, text: 'PNG stand-in' },
        { path: `${s.project}_inbox/20261114-190100-6d01.yml`, text: gamePin('', '6d01.blv',
          '20261114-190100-6d01', 'A shipped map nobody rebuilt.') },
        { path: `${s.project}_inbox/20261114-190100-6d01.png`, text: 'PNG stand-in' }] },
      { name: 'import the inbox, dry run', method: 'pins.import_inbox', expect: 'result',
        params: (s) => ({ inbox: `${s.project}_inbox`, projects: [s.project], dry_run: true }) },
      { name: 'import the inbox', method: 'pins.import_inbox', expect: 'result',
        params: (s) => ({ inbox: `${s.project}_inbox`, projects: [s.project] }) },
      { name: 'import it again: nothing new', method: 'pins.import_inbox', expect: 'result',
        params: (s) => ({ inbox: `${s.project}_inbox`, projects: [s.project] }) },
      { name: 'import from no inbox', method: 'pins.import_inbox', expect: 'bad_request',
        params: (s) => ({ inbox: `${s.project}_nothing`, projects: [s.project] }) },
      { name: 'the game pin, open', method: 'pins.list', params: (s) => ({ ...at(s), status: 'open' }),
        expect: 'result' },
      { name: 'a room that does not lower, from outside', touch: { file: 'rooms.yml', from: 'ceiling: 320',
        to: 'ceiling: 0' } },
      { name: 'validate: an error', method: 'check.validate', params: at, expect: 'result' },
      { name: 'layout: the last one, stale', method: 'view.layout', params: at, expect: 'result' },
      { name: 'mesh: the last one, stale', method: 'view.mesh', params: at, expect: 'result' },
      { name: 'build: refused', method: 'build.run', params: (s) => ({ ...at(s), dry_run: true }),
        expect: 'has_errors' },
    ],
  },
  {
    // S5a3, the pin loop: a pin from the studio with its picture as bytes, an agent's change and its answer with
    // pictures, keeping a picture, accepting; the history with times; a file that does not parse, reported and not
    // recorded; the view with every face owned.
    name: 'pin_loop',
    source: 'examples/gatehouse_cellars',
    steps: [
      { name: 'status, first sight', method: 'project.status', params: at, expect: 'result' },
      { name: 'a pin from the studio with its picture', method: 'pins.add', expect: 'result',
        differs: ['/result/pin/created'],
        params: (s) => ({ ...at(s), text: 'The hall is too dark.', on: 'room:hall', file: 'rooms.yml', at: [412, 980, 0],
          author: 'user', source: 'studio', map: 'studio01.blv', world: 'mm6',
          pose: { position: [400, 700, 0], yaw_radians: 1.5708, pitch_degrees: -10, heading_yaw_units: 512 },
          picture: { media_type: 'image/jpeg', base64: '/9j/4AAQSkZJRgABAQ==' } }) },
      { name: 'a picture that is no picture', method: 'pins.add', expect: 'bad_request',
        params: (s) => ({ ...at(s), text: 'x', picture: { media_type: 'image/png', base64: 'R0lGODlh' } }) },
      { name: 'a picture that is not base64', method: 'pins.add', expect: 'bad_request',
        params: (s) => ({ ...at(s), text: 'x', picture: { media_type: 'image/png', base64: 'a%b=' } }) },
      { name: 'claim it', method: 'pins.claim', expect: 'result', differs: ['/result/pin/created'],
        params: (s) => ({ ...at(s), pin: 'pin:p1', by: 'agent:contract' }) },
      { name: 'the agent changes the map', method: 'edit.apply', expect: 'result',
        params: (s) => ({ ...at(s), ops: [{ op: 'set', id: 'light:hall_east', fields: { radius: 1300 } }],
          author: 'agent:contract', label: 'a brighter hall' }) },
      { name: 'resolve with pictures', method: 'pins.resolve', expect: 'result',
        differs: ['/result/pin/created', '/result/pin/replies/0/created'],
        params: (s) => ({ ...at(s), pin: 'pin:p1', by: 'agent:contract', text: 'Raised the east light to 1300.',
          pictures: [{ media_type: 'image/png', base64: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC' }] }) },
      { name: 'keep the picture', method: 'pins.keep', expect: 'result',
        differs: ['/result/pin/created', '/result/pin/replies/0/created'],
        params: (s) => ({ ...at(s), pin: 'pin:p1' }) },
      { name: 'keep a pin that is not there', method: 'pins.keep', expect: 'no_such_pin',
        params: (s) => ({ ...at(s), pin: 'pin:p9' }) },
      { name: 'the person accepts', method: 'pins.accept', expect: 'result',
        differs: ['/result/pin/created', '/result/pin/replies/0/created', '/result/pin/replies/1/created'],
        params: (s) => ({ ...at(s), pin: 'pin:p1' }) },
      { name: 'history', method: 'edit.history', params: at, expect: 'result', differs: ['/result/entries/0/time'] },
      { name: 'history, the latest one', method: 'edit.history', params: (s) => ({ ...at(s), limit: 1 }),
        expect: 'result', differs: ['/result/entries/0/time'] },
      { name: 'a file half written', touch: { file: 'wiring.yml', from: 'events:\n  - id: evt:exit',
        to: 'events:\n  - [unclosed\n  - id: evt:exit' } },
      { name: 'status: the file named, nothing recorded', method: 'project.status', params: at, expect: 'result' },
      { name: 'the file whole again', touch: { file: 'wiring.yml', from: 'events:\n  - [unclosed\n  - id: evt:exit',
        to: 'events:\n  - id: evt:exit' } },
      { name: 'status: readable', method: 'project.status', params: at, expect: 'result' },
      { name: 'history: no entry for it', method: 'edit.history', params: at, expect: 'result',
        differs: ['/result/entries/0/time'] },
      { name: 'mesh: every face owned', method: 'view.mesh', params: at, expect: 'result' },
    ],
  },
  {
    name: 'shapes_gallery',
    source: 'examples/shapes_gallery',
    steps: [
      { name: 'open', method: 'project.open', params: at, expect: 'result' },
      { name: 'validate', method: 'check.validate', params: at, expect: 'result' },
      { name: 'build, dry run', method: 'build.run', params: (s) => ({ ...at(s), dry_run: true }), expect: 'result' },
      { name: 'things', method: 'check.things', params: at, expect: 'result' },
    ],
  },
  {
    name: 'goblinwatch_vault',
    source: 'examples/goblinwatch_vault',
    steps: [
      { name: 'open', method: 'project.open', params: at, expect: 'result' },
      { name: 'validate', method: 'check.validate', params: at, expect: 'result' },
      { name: 'build, dry run', method: 'build.run', params: (s) => ({ ...at(s), dry_run: true }), expect: 'result' },
      { name: 'things', method: 'check.things', params: at, expect: 'result' },
    ],
  },
  {
    // S6 item O: an overlay that changes a shipped map's scene (a pulsing light, a placed sound, a spawn point more
    // and one less), described for the plan and built from the base map's own scene.
    name: 's6_overlay_goblinwatch',
    source: 'examples/s6_overlay_goblinwatch',
    steps: [
      { name: 'open', method: 'project.open', params: at, expect: 'result' },
      { name: 'validate', method: 'check.validate', params: at, expect: 'result' },
      { name: 'the scene things on the base map', method: 'view.overlay', params: at, expect: 'result' },
      { name: 'build, dry run', method: 'build.run', params: (s) => ({ ...at(s), dry_run: true }), expect: 'result' },
      { name: 'build', method: 'build.run', params: (s) => ({ ...at(s), dry_run: false }), expect: 'result' },
      { name: 'the lock keeps the new numbers', method: 'project.read', params: (s) => ({ ...at(s), file: 'ids.lock.yml' }),
        expect: 'result' },
    ],
  },
  {
    // S6 items D, W, L, C: destructibles, a water volume, a ladder, a night sound and a cinematic in a new map.
    name: 's6_breakwater',
    source: 'examples/s6_breakwater',
    steps: [
      { name: 'open', method: 'project.open', params: at, expect: 'result' },
      { name: 'validate', method: 'check.validate', params: at, expect: 'result' },
      { name: 'build, dry run', method: 'build.run', params: (s) => ({ ...at(s), dry_run: true }), expect: 'result' },
      { name: 'layout', method: 'view.layout', params: at, expect: 'result' },
      { name: 'no overlay', method: 'view.overlay', params: at, expect: 'bad_request' },
    ],
  },
];

// The asset root the suite runs with (run.mjs reads the same option): a method's params name the mount beside it.
const assetsOption = (() => {
  const index = process.argv.indexOf('--assets');
  return index >= 0 ? process.argv[index + 1] : fileURLToPath(new URL('../../../../assets_dev', import.meta.url));
})();

// The methods of the MCP tools that ran command lines until S5a3: queries, undo and redo, the reading methods on a
// project and on a shipped map, the picture, the catalogue, a new project, and install into the session's mount
// (the session is set back to the asset root alone at the end, as the other fixtures expect it).
fixtures.push({
  name: 'tool_methods',
  source: 'examples/gatehouse_cellars',
  steps: [
    { name: 'schemas', method: 'session.schema', params: {}, expect: 'result' },
    { name: 'one schema', method: 'session.schema', params: { name: 'pins' }, expect: 'result' },
    { name: 'a schema that is not there', method: 'session.schema', params: { name: 'nothing' }, expect: 'bad_request' },
    { name: 'query: the summary', method: 'project.query', params: at, expect: 'result' },
    { name: 'query an id', method: 'project.query', params: (s) => ({ ...at(s), id: 'door:gate' }), expect: 'result' },
    { name: 'query an id two files share', method: 'project.query', params: (s) => ({ ...at(s), id: 'room:entry' }),
      expect: 'bad_request' },
    { name: 'query it in one file', method: 'project.query',
      params: (s) => ({ ...at(s), id: 'room:entry', file: 'rooms.yml' }), expect: 'result' },
    { name: 'query a list', method: 'project.query', params: (s) => ({ ...at(s), list: 'doors' }), expect: 'result' },
    { name: 'query an id the project lacks', method: 'project.query',
      params: (s) => ({ ...at(s), id: 'door:nothing' }), expect: 'no_such_object' },
    { name: 'query a missing folder', method: 'project.query', params: (s) => ({ project: `${s.project}/nothing` }),
      expect: 'not_a_project' },
    { name: 'flow of one event', method: 'check.flow_event', params: (s) => ({ map: s.project, event: 1 }),
      expect: 'result' },
    { name: 'flow of an event without a handler', method: 'check.flow_event',
      params: (s) => ({ map: s.project, event: 999 }), expect: 'no_such_object' },
    { name: 'solve the project', method: 'check.solve', params: (s) => ({ map: s.project }), expect: 'result' },
    { name: 'solve a map that is not there', method: 'check.solve',
      params: { map: 'nothing.blv', world: 'mm6' }, expect: 'no_such_map' },
    { name: 'solve in a world that is not there', method: 'check.solve',
      params: { map: '6d01.blv', world: 'mm77' }, expect: 'bad_request' },
    { name: 'audit the project', method: 'check.audit', params: (s) => ({ map: s.project }), expect: 'result' },
    { name: 'audit the builds without a mount', method: 'check.audit',
      params: (s) => ({ map: s.project, built: true }), expect: 'no_mount' },
    { name: 'draw the project', method: 'view.render', params: (s) => ({ map: s.project, size: 160 }),
      expect: 'result' },
    { name: 'draw it from above at an angle', method: 'view.render',
      params: (s) => ({ map: s.project, size: 160, view: 'iso', labels: false }), expect: 'result' },
    { name: 'search decorations', method: 'assets.search', params: { query: 'torch', kind: 'decoration', limit: 3 },
      expect: 'result' },
    { name: 'search textures', method: 'assets.search', params: { query: 't1w11', kind: 'texture', limit: 5 },
      expect: 'result' },
    { name: 'search in a world that is not there', method: 'assets.search', params: { query: 'x', world: 'mm77' },
      expect: 'bad_request' },
    { name: 'the script reference', method: 'assets.script_reference', params: {}, expect: 'result' },
    { name: 'nothing to undo yet', method: 'edit.undo', params: at, expect: 'nothing_to_undo' },
    { name: 'an edit to undo', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...at(s), author: 'agent:contract', ops: [{ op: 'set', id: 'door:gate', fields: { speed: 80 } }] }) },
    { name: 'undo it', method: 'edit.undo', params: at, expect: 'result' },
    { name: 'the gate as before', method: 'project.query', params: (s) => ({ ...at(s), id: 'door:gate' }),
      expect: 'result' },
    { name: 'redo it', method: 'edit.redo', params: at, expect: 'result' },
    { name: 'nothing to redo', method: 'edit.redo', params: at, expect: 'nothing_to_undo' },
    { name: 'status: the steps are not outside edits', method: 'project.status', params: at, expect: 'result' },
    // S5b1: a person's change marks the project; a person's undo takes only the person's change; any entry can be
    // reverted; rename and keys; effective values; protect; migrate.
    { name: 'a person moves a pillar by its key', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...at(s), author: 'user', rebase: true, allow_errors: true, merge_key: 'speed',
        ops: [{ op: 'set', id: 'door:gate', fields: { speed: 70 } }] }) },
    { name: 'an agent renames the gate', method: 'edit.apply', expect: 'result', save: (r, s) => { s.renamed = r.sequence; },
      params: (s) => ({ ...at(s), author: 'agent:contract', ops: [{ op: 'rename', from: 'door:gate', to: 'door:main_gate' }] }) },
    { name: 'an agent adds a light without an id', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...at(s), author: 'agent:contract', ops: [{ op: 'add', to: 'lights', value: { room: 'room:hall', offset: [0, 0] } }] }) },
    // The person's change was to door:gate, which the agent renamed since: a conflict, left alone.
    { name: 'the person undoes their own change only', method: 'edit.undo', params: (s) => ({ ...at(s), author: 'user' }),
      expect: 'result' },
    { name: 'revert the rename', method: 'edit.revert', expect: 'result',
      params: (s) => ({ ...at(s), author: 'user', sequence: s.renamed }) },
    { name: 'revert an entry that is not there', method: 'edit.revert', expect: 'nothing_to_undo',
      params: (s) => ({ ...at(s), author: 'user', sequence: 999 }) },
    { name: 'effective values of a room', method: 'project.resolve', expect: 'result',
      params: (s) => ({ ...at(s), id: 'room:hall', file: 'rooms.yml' }) },
    { name: 'resolve an id that is not there', method: 'project.resolve', expect: 'no_such_object',
      params: (s) => ({ ...at(s), id: 'room:nothing' }) },
    { name: 'clear the mark', method: 'project.protect', params: (s) => ({ ...at(s), clear: true }), expect: 'result' },
    { name: 'protect again', method: 'project.protect', params: at, expect: 'result' },
    { name: 'migrate, dry run', method: 'project.migrate', params: (s) => ({ ...at(s), dry_run: true }), expect: 'result' },
    { name: 'history with the revert entries', method: 'edit.history', params: at, expect: 'result',
      differs: Array.from({ length: 12 }, (_, index) => `/result/entries/${index}/time`) },
    { name: 'a new project', method: 'project.new', expect: 'result',
      params: (s) => ({ project: `${s.project}_new`, id: 'crypt01', name: 'The Crypt', stats_id: 9401 }) },
    { name: 'a new project where one is', method: 'project.new', expect: 'bad_request',
      params: (s) => ({ project: `${s.project}_new`, id: 'crypt01', name: 'The Crypt' }) },
    { name: 'open the new project', method: 'project.open', params: (s) => ({ project: `${s.project}_new` }),
      expect: 'result' },
    { name: 'install without a mount', method: 'build.install', params: at, expect: 'no_mount' },
    { name: 'build into the project', method: 'build.run', params: (s) => ({ ...at(s), dry_run: false }),
      expect: 'result' },
    { name: 'a mount for the session', method: 'session.configure', expect: 'result',
      params: (s) => ({ asset_root: assetsOption, mount: `${s.project}_mount` }) },
    { name: 'install into the mount', method: 'build.install', params: at, expect: 'result' },
    { name: 'audit the installed build', method: 'check.audit',
      params: { map: 'studio01.blv', world: 'mm6', built: true }, expect: 'result' },
    { name: 'flow of the installed build', method: 'check.flow_event',
      params: { map: 'studio01.blv', world: 'mm6', built: true, event: 1 }, expect: 'result' },
    { name: 'the shipped maps lack it', method: 'check.solve', params: { map: 'studio01.blv', world: 'mm6' },
      expect: 'no_such_map' },
    { name: 'the mount taken away', method: 'session.configure', params: { asset_root: assetsOption },
      expect: 'result' },
    { name: 'a host method is not the core\'s', method: 'game.playtest',
      params: { scenario: 'x.yml', world: 'mm6' }, expect: 'unknown_method' },
  ],
});

// S5a5: the scorecard's checks from one walk (check.audit with `solve`), compare.run against the card's original,
// the original's mesh for the Compare view, the pins tour's shots, and the reading commands that left map_exec's
// command line (check.metrics, check.probe, project.fmt, project.import, view.render_sketch's refusal indoors).
fixtures.push({
  name: 'scorecard_methods',
  source: 'examples/gatehouse_cellars',
  steps: [
    { name: 'audit with the solve', method: 'check.audit', params: (s) => ({ map: s.project, reach: true, solve: true }),
      expect: 'result' },
    { name: 'compare with the card\'s original', method: 'compare.run', params: (s) => ({ map: s.project }), expect: 'result' },
    { name: 'compare with another original', method: 'compare.run', params: (s) => ({ map: s.project, original: '6d16.blv' }),
      expect: 'result' },
    { name: 'compare with a map that is not there', method: 'compare.run',
      params: (s) => ({ map: s.project, original: 'nothing.blv' }), expect: 'no_such_map' },
    { name: 'compare an indoor rebuild with an outdoor map', method: 'compare.run',
      params: (s) => ({ map: s.project, original: 'oute3.odm' }), expect: 'bad_request' },
    { name: 'the original\'s mesh', method: 'view.original_mesh', params: at, expect: 'result' },
    { name: 'the original\'s mesh again: kept', method: 'view.original_mesh', params: at, expect: 'result' },
    { name: 'metrics of the project', method: 'check.metrics', params: (s) => ({ map: s.project }), expect: 'result' },
    { name: 'a probe from the entry into the hall', method: 'check.probe',
      params: (s) => ({ map: s.project, from: [384, 384, 0], to: [384, 1400, 0], doors_open: true }), expect: 'result' },
    { name: 'a probe of a point list too short', method: 'check.probe',
      params: (s) => ({ map: s.project, from: [384, 384], to: [384, 1400, 0] }), expect: 'invalid_params' },
    { name: 'the sketch picture of an indoor project', method: 'view.render_sketch', params: at, expect: 'bad_request' },
    { name: 'fmt, check only', method: 'project.fmt', params: (s) => ({ ...at(s), check: true }), expect: 'result' },
    { name: 'a pin with a pose', method: 'pins.add', expect: 'result', differs: ['/result/pin/created'],
      params: (s) => ({ ...at(s), text: 'Picture it in the game.', at: [384, 384, 0], author: 'user', map: 'studio01.blv',
        world: 'mm6', pose: { position: [384.5, 384, 0], yaw_radians: 1.5708, pitch_degrees: -10, heading_yaw_units: 512 } }) },
    { name: 'a pin without one', method: 'pins.add', expect: 'result', differs: ['/result/pin/created'],
      params: (s) => ({ ...at(s), text: 'Somewhere.', at: [100, 100, 0], author: 'user' }) },
    { name: 'the pins tour', method: 'pins.tour', params: at, expect: 'result' },
    { name: 'the pins tour of accepted pins: none', method: 'pins.tour', params: (s) => ({ ...at(s), status: ['accepted'] }),
      expect: 'result' },
    { name: 'a shipped map as an overlay project', method: 'project.import',
      params: (s) => ({ project: `${s.project}_overlay`, map: '6d01.blv', world: 'mm6' }), expect: 'result' },
    { name: 'again into the same folder', method: 'project.import',
      params: (s) => ({ project: `${s.project}_overlay`, map: '6d01.blv', world: 'mm6' }), expect: 'bad_request' },
  ],
});

// S5a4, walk mode: a recorded walk replayed in both cores must give the same poses, bit for bit (the walk's yaw
// through the core's own sin and cos; S5-0 spike 3). Indoors on the shapes gallery: into the hinged door of its
// closet (a rotating mover), the door opened, through it, the door shut behind, turns, runs, jumps and strafes.
// Outdoors on Harmondale's rebuild: a fall onto the land, a walk with turns and jumps, and the map's east bound.
const walkFrames = (count, make) => Array.from({ length: count }, (unused, index) => make(index));
const indoorWalk = [
  ...walkFrames(30, () => [0, 0, 1 / 60]),
  ...walkFrames(90, (i) => [0, 1, i % 3 === 0 ? 0.017 : 1 / 60]),
  ...walkFrames(90, () => [0, 1, 1 / 60]),
  ...walkFrames(120, (i) => [i * 0.031, 1 | 16, 1 / 60]),
  ...walkFrames(60, (i) => [3.7 + Math.sin(i / 7) * 0.4, 4 | (i % 30 === 0 ? 32 : 0), 1 / 60]),
  ...walkFrames(120, (i) => [Math.PI + i * 0.0123, 2 | (i % 40 === 5 ? 32 : 0), 0.0165 + (i % 5) * 0.0004]),
  ...walkFrames(90, (i) => [Math.PI, 1 | 8, 1 / 60]),
];
const outdoorWalk = [
  ...walkFrames(120, () => [0.5, 0, 1 / 60]),
  ...walkFrames(240, (i) => [0.5 + Math.sin(i / 20) * 0.8, 1 | (i % 50 === 10 ? 32 : 0), 1 / 60]),
  ...walkFrames(240, (i) => [2.2 + i * 0.01, 1 | 16 | (i % 70 === 3 ? 32 : 0), 0.0166 + (i % 3) * 0.0003]),
  ...walkFrames(120, (i) => [4.0, 2 | 4, 1 / 60]),
];
const decorations = () => `${assetsOption}/engine/data_tables/decoration_data.txt`;

fixtures.push({
  name: 'walk_indoor',
  source: 'examples/shapes_gallery',
  steps: [
    { name: 'a step before any walk', method: 'walk.step', params: { yaw_radians: 0, buttons: 1, seconds: 0.016 },
      expect: 'bad_request' },
    { name: 'build into the project', method: 'build.run', params: (s) => ({ ...at(s), dry_run: false }),
      expect: 'result' },
    { name: 'load a map that is not there', method: 'walk.load', expect: 'bad_request',
      params: (s) => ({ map: `${s.project}/build/nothing.blv`, state: `${s.project}/build/studio02.walk.yml`,
        decorations: decorations() }) },
    { name: 'load the walk', method: 'walk.load', expect: 'result',
      params: (s) => ({ map: `${s.project}/build/studio02.blv`, state: `${s.project}/build/studio02.walk.yml`,
        decorations: decorations() }) },
    { name: 'stand at the closet door', method: 'walk.place', params: { eye: [1700, 1664, 420] }, expect: 'result' },
    { name: 'walk into the shut door', method: 'walk.step', expect: 'result',
      params: { yaw_radians: 0, buttons: 1, seconds: 1 / 60, frames: 90 } },
    { name: 'toggle a door the map lacks', method: 'walk.toggle', params: { door: 'door:nothing' },
      expect: 'no_such_object' },
    { name: 'open the hinged door', method: 'walk.toggle', params: { door: 'door:closet' }, expect: 'result' },
    { name: 'walk through it', method: 'walk.step', expect: 'result',
      params: { yaw_radians: 0, buttons: 1, seconds: 1 / 60, frames: 90 } },
    { name: 'shut it again', method: 'walk.toggle', params: { door: 'door:closet' }, expect: 'result' },
    { name: 'the recorded walk', method: 'walk.replay', expect: 'result',
      params: { eye: [1700, 1664, 420], frames: indoorWalk, trace_every: 60,
        toggles: [{ frame: 120, door: 'door:closet' }, { frame: 300, door: 'door:closet' },
          { frame: 400, door: 'lift:gallery' }] } },
    { name: 'a replay toggling a door the map lacks', method: 'walk.replay', expect: 'no_such_object',
      params: { eye: [1700, 1664, 420], frames: [[0, 1, 0.016]], toggles: [{ frame: 0, door: 'door:nothing' }] } },
  ],
});

fixtures.push({
  name: 'walk_outdoor',
  source: '../devdocs/map_studio/briefs/mm7_7out02/L4',
  steps: [
    { name: 'build into the project', method: 'build.run', params: (s) => ({ ...at(s), dry_run: false }),
      expect: 'result', differs: ['/result/warnings'] },
    { name: 'load without the terrain pack', method: 'walk.load', expect: 'bad_request',
      params: (s) => ({ map: `${s.project}/build/calib_harmondale.odm`,
        state: `${s.project}/build/calib_harmondale.walk.yml`, decorations: decorations() }) },
    { name: 'load the walk', method: 'walk.load', expect: 'result',
      params: (s) => ({ map: `${s.project}/build/calib_harmondale.odm`,
        state: `${s.project}/build/calib_harmondale.walk.yml`, decorations: decorations(),
        terrain: `${s.project}/build/calib_harmondale.walk.terrain` }) },
    { name: 'a door outdoors', method: 'walk.toggle', params: { door: 'door:nothing' }, expect: 'bad_request' },
    { name: 'the recorded walk', method: 'walk.replay', expect: 'result',
      params: { eye: [-2000, 3000, 3000], frames: outdoorWalk, trace_every: 60 } },
    { name: 'at the east bound', method: 'walk.place', params: { eye: [22800, 0, 3000] }, expect: 'result' },
    { name: 'walk east past it', method: 'walk.step', expect: 'result',
      params: { yaw_radians: 0, buttons: 1 | 16, seconds: 1 / 60, frames: 240 } },
  ],
});

// The read-only calls run on a project named with --project (no recorded answers: native and wasm must agree).
export const readOnlySteps = [
  { name: 'open', method: 'project.open', params: at, expect: 'result' },
  { name: 'read project.yml', method: 'project.read', params: (s) => ({ ...at(s), file: 'project.yml' }),
    expect: 'result' },
  { name: 'validate without assets', method: 'check.validate', params: (s) => ({ ...at(s), use_assets: false }),
    expect: 'result' },
  { name: 'validate', method: 'check.validate', params: at, expect: 'result' },
  { name: 'build, dry run', method: 'build.run', params: (s) => ({ ...at(s), dry_run: true }), expect: 'result' },
  { name: 'things', method: 'check.things', params: at, expect: 'result' },
  { name: 'pins', method: 'pins.list', params: at, expect: 'result' },
  { name: 'layout', method: 'view.layout', params: at, expect: 'result' },
  { name: 'mesh', method: 'view.mesh', params: at, expect: 'result' },
];

// S5b1 part two: pins on keyed sub-objects (a pillar, a flight: by their keys, written or derived; a key the list
// lacks refused), op name (a platform's id from the core; a second name refused), switches and exits in view.layout
// (the gallery's), the map card's slots in project.resolve, check.validate's fixes on a broken reference (and the fix
// applied), History's "show as it was" (view.layout_at), and assets.search's monsters, items and sounds.
fixtures.push({
  name: 'authoring_part2',
  source: 'examples/shapes_gallery',
  steps: [
    { name: 'open', method: 'project.open', params: at, expect: 'result' },
    { name: 'layout: switches and exits at their faces', method: 'view.layout', params: at, expect: 'result' },
    { name: 'a pin on a pillar by its derived key', method: 'pins.add', expect: 'result', differs: ['/result/pin/created'],
      params: (s) => ({ ...at(s), text: 'The pillar is too thin.', on: 'room:cave/pillars/pillar1', author: 'user' }) },
    { name: 'a pin on a flight by its key', method: 'pins.add', expect: 'result', differs: ['/result/pin/created'],
      params: (s) => ({ ...at(s), text: 'The steps are steep.', on: 'room:climb_top/flights/flight1', author: 'agent:contract' }) },
    { name: 'a pin on a key the list lacks', method: 'pins.add', expect: 'bad_request',
      params: (s) => ({ ...at(s), text: 'Which pillar?', on: 'room:cave/pillars/pillar9' }) },
    { name: 'pins on keyed sub-objects', method: 'pins.list', params: at, expect: 'result',
      differs: ['/result/pins/0/created', '/result/pins/1/created'] },
    { name: 'name a platform (its id from the core)', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...at(s), ops: [{ op: 'name', id: 'room:climb_top', path: '/platforms/platform1' }], author: 'user' }) },
    { name: 'name it again', method: 'edit.apply', expect: 'bad_operation',
      params: (s) => ({ ...at(s), ops: [{ op: 'name', id: 'room:climb_top', path: '/platforms/platform1' }], author: 'user' }) },
    { name: 'the map card', method: 'project.resolve', params: (s) => ({ ...at(s), card: true }), expect: 'result' },
    { name: 'a spawn point with the card\'s slots', method: 'project.resolve', params: (s) => ({ ...at(s), id: 'spawn:pass_shelf' }),
      expect: 'result' },
    { name: 'resolve without id or card', method: 'project.resolve', params: at, expect: 'invalid_params' },
    { name: 'an event naming a switch the project lacks', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...at(s), allow_errors: true, author: 'user',
        ops: [{ op: 'add', to: 'events', file: 'wiring.yml', value: { id: 'evt:orphan', preset: 'text', source: 'switch:none', text: 'x' } }] }) },
    { name: 'validate: the issue with its fixes', method: 'check.validate', params: at, expect: 'result',
      save: (r, s) => { s.fix = r.issues.find((issue) => issue.message.includes('switch:none'))?.fixes?.at(-1)?.ops; } },
    { name: 'apply the fix', method: 'edit.apply', expect: 'result', params: (s) => ({ ...at(s), ops: s.fix, author: 'user' }) },
    { name: 'as it was before entry 2', method: 'view.layout_at', params: (s) => ({ ...at(s), sequence: 2 }), expect: 'result' },
    { name: 'as it was after entry 2', method: 'view.layout_at', params: (s) => ({ ...at(s), sequence: 2, side: 'after' }), expect: 'result' },
    { name: 'an entry the history lacks', method: 'view.layout_at', params: (s) => ({ ...at(s), sequence: 99 }), expect: 'bad_request' },
    { name: 'monsters', method: 'assets.search', params: { query: 'goblin', kind: 'monster', limit: 4 }, expect: 'result' },
    { name: 'items', method: 'assets.search', params: { query: 'potion', kind: 'item', limit: 4 }, expect: 'result' },
    { name: 'sounds', method: 'assets.search', params: { query: 'door', kind: 'sound', limit: 4 }, expect: 'result' },
  ],
});

// S5b2: outdoor authoring. A new outdoor project (project.new kind outdoor: level spot heights, the arrival in the
// middle) is edited by keyed patches into sketch.yml (a ridge appended, its line by its key, a key the list lacks
// refused); a sculpt patch with a raise stroke and a smoothed area inside it; a stroke outside every patch (an error
// the view build leaves out of nothing: the land is no object, so the commit is refused); the land marked as made by
// hand; view.terrain_query's heights, slopes and profile; a structure the build cannot build left out of the view; and
// on Harmondale a building part patched by its id.
const fresh = (s) => ({ project: `${s.project}/fresh` });
fixtures.push({
  name: 'outdoor_authoring',
  source: '../devdocs/map_studio/briefs/mm7_7out02/L4',
  steps: [
    { name: 'a new outdoor project', method: 'project.new', expect: 'result',
      params: (s) => ({ ...fresh(s), id: 'meadow01', name: 'Contract Meadow', world: 'mm6', kind: 'outdoor' }) },
    { name: 'open it', method: 'project.open', params: fresh, expect: 'result', save: (r, s) => { s.f0 = r.revision; } },
    { name: 'it validates', method: 'check.validate', params: fresh, expect: 'result' },
    { name: 'a ridge appended', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...fresh(s), author: 'user', ops: [{ op: 'patch', file: 'sketch.yml', patch: [
        { op: 'add', path: '/heights/ridges', value: [{ line: [[40, 60], [80, 60]], height: 640, slope: 3 }] }] }] }) },
    { name: 'its line by its key', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...fresh(s), author: 'user', ops: [{ op: 'patch', file: 'sketch.yml', patch: [
        { op: 'replace', path: '/heights/ridges/ridge1/line/1', value: [84, 62] }] }] }) },
    { name: 'a key the list lacks', method: 'edit.apply', expect: 'bad_operation',
      params: (s) => ({ ...fresh(s), author: 'user', ops: [{ op: 'patch', file: 'sketch.yml', patch: [
        { op: 'replace', path: '/heights/ridges/ridge9/height', value: 1 }] }] }) },
    { name: 'a patch, a raise stroke and a smoothed area', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...fresh(s), author: 'user', ops: [{ op: 'patch', file: 'sketch.yml', patch: [
        { op: 'add', path: '/heights/patches', value: [{ polygon: [[50, 50], [70, 50], [70, 70], [50, 70]] }] },
        { op: 'add', path: '/heights/strokes', value: [{ at: [58, 58], rows: [[2, 2, 2], [2, 4, 2], [2, 2, 2]] }] },
        { op: 'add', path: '/heights/smooth', value: [{ polygon: [[52, 52], [68, 52], [68, 68], [52, 68]], passes: 2 }] }] }] }) },
    { name: 'a stroke outside every patch', method: 'edit.apply', expect: 'new_errors',
      params: (s) => ({ ...fresh(s), author: 'user', ops: [{ op: 'patch', file: 'sketch.yml', patch: [
        { op: 'add', path: '/heights/strokes/-', value: { at: [20, 20], rows: [[3]] } }] }] }) },
    { name: 'the heights and slopes there', method: 'view.terrain_query', expect: 'result',
      params: (s) => ({ ...fresh(s), points: [[59, 59], [60, 60.5], [30, 30]], line: { from: [40, 60], to: [84, 62], step: 4 } }) },
    { name: 'the land marked as made by hand', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...fresh(s), author: 'user', ops: [{ op: 'patch', file: 'sketch.yml', patch: [
        { op: 'add', path: '/heights/hand_made', value: true },
        { op: 'add', path: '/heights/strokes/-', value: { at: [20, 20], rows: [[3]] } }] }] }) },
    { name: 'a structure it cannot build', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...fresh(s), author: 'user', allow_errors: true, ops: [
        { op: 'add', to: 'structures', file: 'sketch.yml', value: { id: 'thing:well', kind: 'well', at: [60, 66] } },
        { op: 'add', to: 'structures', file: 'sketch.yml', value: { id: 'thing:span', kind: 'bridge', line: [[70, 60], [76, 60]], height: 64, kerb: 900 } }] }) },
    { name: 'the view leaves it out', method: 'view.layout', params: fresh, expect: 'result' },
    { name: 'a terrain query indoors', method: 'view.terrain_query', expect: 'not_a_project',
      params: (s) => ({ project: `${s.project}/nothing`, points: [[1, 1]] }) },
    { name: 'open Harmondale', method: 'project.open', params: at, expect: 'result', save: (r, s) => {
      s.hall = r.files['sketch.yml'].tree.structures.find((t) => t.kind === 'building' && Array.isArray(t.parts) && t.parts[0].id); } },
    { name: 'a building part by its id', method: 'edit.apply', expect: 'result',
      params: (s) => ({ ...at(s), author: 'agent:contract', ops: [{ op: 'patch', id: s.hall.id, file: 'sketch.yml', patch: [
        { op: 'test', path: `/parts/${s.hall.parts[0].id}/wall_height`, value: s.hall.parts[0].wall_height },
        { op: 'replace', path: `/parts/${s.hall.parts[0].id}/wall_height`, value: s.hall.parts[0].wall_height + 32 }] }] }) },
  ],
});

// S6, the second run: the world view of a project and of the briefs around it (world.view), and named mods in the
// request list: a free map number from the studio's band and then from the mod's declared range (mod.map_number),
// the project packed into a mod with its range (mod.pack, built first), the mods folder listed (mod.list), and the
// refusals (a mod without its folder, an id out of form, a project that is not one).
const modsOf = (s) => `${s.project}_mods`;
fixtures.push({
  name: 's6b_world_mods',
  source: 'examples/s6_breakwater',
  steps: [
    { name: 'the world of one project', method: 'world.view', params: (s) => ({ projects: [s.project] }), expect: 'result' },
    { name: 'the world of a project that is not one', method: 'world.view',
      params: (s) => ({ projects: [s.project, `${s.project}/nothing`] }), expect: 'result' },
    { name: 'a map number from the studio\'s band', method: 'mod.map_number',
      params: (s) => ({ world: 'mm6', projects: [s.project] }), expect: 'result' },
    { name: 'packed into a mod with its range', method: 'mod.pack', expect: 'result',
      params: (s) => ({ projects: [s.project], id: 'breakwater', out: modsOf(s), name: 'The Breakwater', maps: [9300, 9309] }) },
    { name: 'the mods folder', method: 'mod.list', params: (s) => ({ mods: modsOf(s) }), expect: 'result' },
    { name: 'a map number of the mod', method: 'mod.map_number',
      params: (s) => ({ world: 'mm6', mods: modsOf(s), mod: 'breakwater', projects: [s.project] }), expect: 'result' },
    { name: 'a mod named without its folder', method: 'mod.map_number', params: { world: 'mm6', mod: 'breakwater' },
      expect: 'bad_request' },
    { name: 'a mod the folder lacks', method: 'mod.map_number',
      params: (s) => ({ world: 'mm6', mods: modsOf(s), mod: 'nothing' }), expect: 'bad_request' },
    { name: 'a mod id out of form', method: 'mod.pack', expect: 'invalid_params',
      params: (s) => ({ projects: [s.project], id: 'Bad Id', out: modsOf(s) }) },
    { name: 'a project that is not one', method: 'mod.pack', expect: 'not_a_project',
      params: (s) => ({ projects: [`${s.project}/nothing`], id: 'none', out: modsOf(s) }) },
  ],
});

// S6, the second run: the Overlay tab's own tools on an overlay project (web/src/model/overlayEdit.ts writes these
// patches): a new pulsing light placed on the plan, the project's own light recoloured and moved by its id, a base
// spawn point taken out and the one taken out before put back, a change of a base thing that is not there refused by
// its test; the overlay described again, and built.
const overlayPatch = (s, patch) => ({ ...at(s), author: 'user', ops: [{ op: 'patch', file: 'objects.yml', patch }] });
fixtures.push({
  name: 's6b_overlay_tools',
  source: 'examples/s6_overlay_goblinwatch',
  steps: [
    { name: 'a light placed on the plan', method: 'edit.apply', expect: 'result', params: (s) => overlayPatch(s, [
      { op: 'add', path: '/scene/lights/-', value: { id: 'light:new_1', position: [7000, 3200, 160], color: [255, 200, 140],
        intensity: [0.6, 1], radius: [384, 640], frequency: 0.5 } }]) },
    { name: 'the project\'s light recoloured and moved', method: 'edit.apply', expect: 'result', params: (s) => overlayPatch(s, [
      { op: 'test', path: '/scene/lights/light:vault_glow/color', value: [120, 180, 255] },
      { op: 'replace', path: '/scene/lights/light:vault_glow/color', value: [255, 120, 60] },
      { op: 'test', path: '/scene/lights/light:vault_glow/position', value: [7456, 3164, 256] },
      { op: 'replace', path: '/scene/lights/light:vault_glow/position', value: [7400, 3100, 256] }]) },
    { name: 'a base spawn point taken out, the other put back', method: 'edit.apply', expect: 'result', params: (s) => overlayPatch(s, [
      { op: 'test', path: '/scene/removals/0', value: 'spawn:s1' }, { op: 'remove', path: '/scene/removals/0' },
      { op: 'add', path: '/scene/removals/-', value: 'spawn:s2' }]) },
    { name: 'a change whose test fails', method: 'edit.apply', expect: 'bad_operation', params: (s) => overlayPatch(s, [
      { op: 'test', path: '/scene/lights/light:vault_glow/color', value: [1, 2, 3] },
      { op: 'replace', path: '/scene/lights/light:vault_glow/color', value: [4, 5, 6] }]) },
    { name: 'the overlay described again', method: 'view.overlay', params: at, expect: 'result' },
    { name: 'built', method: 'build.run', params: (s) => ({ ...at(s), dry_run: false }), expect: 'result' },
  ],
});

// S8a: the Overlay tab's tools on an overlay project's ladders, monsters and items (the game's G1 and G5), and its
// cinematics overlay (G2): a ladder placed on the plan, the project's monster moved by its id, an item added, the
// overlay described (the monster's actor number after the base map's; book_sinking replaced), built. By an agent, so
// that no hand mark (with its date) is recorded.
const agentPatch = (s, patch) => ({ ...at(s), author: 'agent:contract', ops: [{ op: 'patch', file: 'objects.yml', patch }] });
fixtures.push({
  name: 's8a_overlay_tools',
  source: 'examples/s8a_isle_extras',
  steps: [
    { name: 'a ladder placed on the plan', method: 'edit.apply', expect: 'result', params: (s) => agentPatch(s, [
      { op: 'add', path: '/scene/ladders/-', value: { id: 'ladder:new_1', position: [1400, 3310, 656], facing: 'n',
        height: 342 } }]) },
    { name: 'the project\'s monster moved', method: 'edit.apply', expect: 'result', params: (s) => agentPatch(s, [
      { op: 'test', path: '/scene/monsters/monster:s8a_guard/position', value: [1800, 3500, 987] },
      { op: 'replace', path: '/scene/monsters/monster:s8a_guard/position', value: [1700, 3500, 990] }]) },
    { name: 'an item added', method: 'edit.apply', expect: 'result', params: (s) => agentPatch(s, [
      { op: 'add', path: '/scene/items/-', value: { id: 'item:new_1', position: [1500, 3450, 995], item: 1 } }]) },
    { name: 'the overlay described', method: 'view.overlay', params: at, expect: 'result' },
    { name: 'built', method: 'build.run', params: (s) => ({ ...at(s), dry_run: true }), expect: 'result' },
  ],
});
