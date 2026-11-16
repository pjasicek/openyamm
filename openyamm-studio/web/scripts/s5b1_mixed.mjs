// S5b1 exit test 2, the mixed test (S5_BROWSER_EDITOR.md 6.4, F6): an agent-made map (devdocs/xeen/briefs/xd01/L4,
// copied to a scratch folder) finished by hand in the real app: a room's corner moved with the Select tool, a wall's
// surface from the Library, two lights, a chest's contents, a light renamed, a decoration deleted. Then an agent
// works through the core (`oymap call edit.apply`, author agent:mixed): it adds objects and changes one object the
// person changed (its result's `hand_objects` names it). Then a generator-style rewrite of objects.yml from outside
// (the original file written back): the red notice in the UI and its one-step revert. Finally every hand edit is
// checked with output/s5b1/scripts/hand_edits_check.py. A screenshot after each step, in output/s5b1_shots/exit/.
//   node scripts/s5b1_mixed.mjs
import { execFileSync } from 'node:child_process';
import { cpSync, readFileSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { repo, sleep, stampFolder, startRun, studio } from './exit_common.mjs';

const out = process.env.S5_SHOTS ?? join(repo, 'output', 's5b1_shots', 'exit');
const runRoot = stampFolder('mixed', process.env.S5_RUNS ?? 's5b1');
const source = join(repo, 'devdocs', 'xeen', 'briefs', 'xd01', 'L4');
const folder = join(runRoot, 'xd01_l4');
cpSync(source, folder, { recursive: true, filter: (path) => !path.includes('/.oymap') && !path.includes('/build') });
const run = await startRun({ out, prefix: 'mixed', roots: [runRoot] });
const { page, check, shot, settled, click, drag, key, frame, type } = run;
run.results.run = folder;
const key_ = `${relative(repo, runRoot)}/xd01_l4`;
const edits = [];
const objects = async (list) => (await run.files())['objects.yml']?.tree[list] ?? [];
const rooms = async () => (await run.files())['rooms.yml'].tree.rooms ?? [];
const selected = async () => (await run.state()).selection?.id ?? null;
const tool = async (name) =>
{
    await page.click(`[data-testid="tool-${name}"]`);
    await sleep(120);
};

// --- 1. The agent's map, opened in Author mode ----------------------------------------------------------------------

await page.goto(`${run.base}/?project=${encodeURIComponent(key_)}#token=${run.token}`);
await run.waitFor(() => window.__studio?.app?.store.getState().layout.state === 'ready', 60000);
await page.click('[data-testid="mode-author"]');
await settled(60000);
let s = await run.state();
check('the agent-made map opens, not marked as edited by hand', s.project.state === 'ready' && !s.project.value.hand_edited, JSON.stringify(s.project.value.hand_edited ?? null));
await shot('opened', 'xd01 L4 (agent-made) in Author mode');

// --- 2. Finished by hand ---------------------------------------------------------------------------------------------

// A room's corner moved with the Select tool: the river sill's south-east corner out by a grid step.
await tool('select');
await frame(4480, 3648, 5184, 4352);
await click(4832, 4000);
check('a click selects the river sill', (await selected()) === 'room:river_sill', await selected());
await drag([4928, 4128], [4992, 4160]);
await settled();
const sill = (await rooms()).find((room) => room.id === 'room:river_sill');
const corner = sill.outline.findIndex((point) => point[0] === 4992 && point[1] === 4160);
check('the corner moved (a patch of one outline point)', corner >= 0, JSON.stringify(sill.outline));
edits.push({ file: 'rooms.yml', id: 'room:river_sill', pointer: `/outline/${corner}`, value: [4992, 4160], what: 'the river sill\'s corner moved by hand' });
await shot('corner', 'Select: the river sill\'s south-east corner dragged out (64, 32)');

// A wall's surface from the Library: the loading dock's south wall.
await page.click('[data-testid="tab-library"]');
await page.fill('[data-testid="library-search"]', 't6s1');
await page.waitForSelector('[data-testid="asset-t6s1bs"]', { timeout: 20000 });
await frame(0, -1280, 1536, -384);
await run.dropOnPlan('asset-t6s1bs', 768, -1080);
await settled();
const dock = (await rooms()).find((room) => room.id === 'room:loading_dock');
const wallIndex = (dock.walls ?? []).findIndex((wall) => wall.surface?.texture === 't6s1bs');
check('the dock\'s south wall takes t6s1bs (a walls entry)', wallIndex >= 0, JSON.stringify(dock.walls));
edits.push({ file: 'rooms.yml', id: 'room:loading_dock', pointer: `/walls/${wallIndex}/surface`, value: dock.walls[wallIndex].surface, what: 'a wall\'s surface from the Library' });
await shot('wall_surface', 'the Library: t6s1bs dropped on the loading dock\'s south wall');

// Two lights.
await page.mouse.move(5, 500);
await key('Digit6');
await tool('light');
await type('option-lightRadius', 640);
const lightsBefore = new Set((await objects('lights')).map((light) => light.id));
await click(400, -820);
await settled();
await click(1120, -820);
await settled();
const newLights = (await objects('lights')).filter((light) => !lightsBefore.has(light.id));
check('two lights added by hand', newLights.length === 2, JSON.stringify(newLights));
for (const light of newLights)
{
    edits.push({ file: 'objects.yml', id: light.id, pointer: '/at', value: light.at, what: `a light added by hand (${light.id})` });
}
await shot('lights', 'Light tool: two lights in the loading dock');

// A chest's contents: the stash's gold.
await tool('select');
await frame(384, 4256, 1024, 4768);
await click(688, 4556);
check('a click selects the stash chest', (await selected()) === 'chest:stash', await selected());
await type('field-gold', 450);
await settled();
check('the chest\'s gold changed in the inspector', (await objects('chests')).find((chest) => chest.id === 'chest:stash')?.gold === 450);
edits.push({ file: 'objects.yml', id: 'chest:stash', pointer: '/gold', value: 450, what: 'a chest\'s contents changed by hand' });
await shot('chest', 'the stash chest: gold 450 in the inspector');

// A light renamed (every reference follows).
// The lamp clicked on the plan (where the files put it).
const lamp = await page.evaluate(() => window.__studio.app.store.getState().project.value.files['objects.yml'].tree.lights.find((light) => light.id === 'light:feeding_lamp'));
const lampAt = await page.evaluate((id) =>
{
    const s = window.__studio.app.store.getState();
    const thing = s.layout.value.things.find((entry) => entry.id === id);
    return thing ? [thing.at[0], thing.at[1]] : null;
}, 'light:feeding_lamp') ?? lamp.at;
await frame(lampAt[0] - 384, lampAt[1] - 384, lampAt[0] + 384, lampAt[1] + 384);
await click(...lampAt);
check('the feeding lamp selected', (await selected()) === 'light:feeding_lamp', await selected());
await type('rename-id', 'light:feeding_lantern');
await settled();
const renamed = (await objects('lights')).find((light) => light.id === 'light:feeding_lantern');
check('the light renamed', Boolean(renamed) && !(await objects('lights')).some((light) => light.id === 'light:feeding_lamp'));
edits.push({ file: 'objects.yml', id: 'light:feeding_lantern', pointer: '/id', value: 'light:feeding_lantern', what: 'a light renamed by hand (new id)' });
edits.push({ file: 'objects.yml', id: 'light:feeding_lamp', pointer: '', value: null, what: 'the light\'s old id is gone' });
await shot('rename', 'the inspector: light:feeding_lamp renamed to light:feeding_lantern');

// A decoration deleted.
await frame(2304, 1728, 3072, 2368);
await click(2740, 2000);
check('a click selects the flour sacks', (await selected()) === 'deco:aisle_sacks_1', await selected());
await page.mouse.move(5, 500);
await key('Delete');
await settled();
check('the decoration deleted', !(await objects('decorations')).some((deco) => deco.id === 'deco:aisle_sacks_1'));
edits.push({ file: 'objects.yml', id: 'deco:aisle_sacks_1', pointer: '', value: null, what: 'a decoration deleted by hand' });
await shot('delete', 'Delete: the flour sacks in the hall aisle gone');
s = await run.state();
check('the first person\'s change marked the project as edited by hand', Boolean(s.project.value.hand_edited), JSON.stringify(s.project.value.hand_edited));

// --- 3. An agent adds through the core and changes an object the person changed --------------------------------

const oymap = join(studio, 'build-s4', 'oymap');
const call = (method, params) => JSON.parse(execFileSync(oymap, ['call', method, JSON.stringify(params), '--assets', join(repo, 'assets_dev')], { encoding: 'utf8', maxBuffer: 64 << 20 }));
const agent = call('edit.apply', { project: folder, author: 'agent:mixed', label: 'more light and a guard', ops: [
    { op: 'add', to: 'lights', file: 'objects.yml', value: { room: 'room:hall_aisle', at: [2368, 2368], radius: 512 } },
    { op: 'add', to: 'spawns', file: 'objects.yml', value: { room: 'room:hall_aisle', at: [2368, 1700], slot: 1 } },
    { op: 'set', id: 'chest:stash', file: 'objects.yml', fields: { trap_level: 2 } },
] });
run.results.agent = agent;
const result = agent.result ?? {};
check('the agent\'s operations are written', result.applied === true, JSON.stringify(agent.error ?? result.changes));
check('the agent\'s result names the hand-changed object it touched (hand_objects)', JSON.stringify(result.hand_objects ?? []).includes('chest:stash'), JSON.stringify(result.hand_objects));
check('the agent is told the project is edited by hand', Boolean(result.hand_edited), JSON.stringify(result.hand_edited?.message ?? ''));
await run.waitFor(() => (window.__studio.app.store.getState().project.value.files['objects.yml'].tree.spawns ?? []).some((spawn) => spawn.room === 'room:hall_aisle'), 20000);
await settled();
await frame(1856, 1280, 2880, 3456);
await shot('agent', 'the agent\'s light and spawn in the hall aisle arrive live (a note of the change)');

// --- 4. A generator rewrites objects.yml from outside -----------------------------------------------------------

writeFileSync(join(folder, 'objects.yml'), readFileSync(join(source, 'objects.yml')));
const noticed = await run.waitFor(() =>
{
    const st = window.__studio.app.store.getState();
    return st.history.state === 'ready' && st.history.value.entries.some((entry) => entry.kind === 'outside' && entry.notice?.length);
}, 30000);
await sleep(800);
check('the outside rewrite of the hand-edited project carries a red notice', noticed && await page.locator('[data-testid="outside-notice"]').count() > 0);
const noticeText = await page.locator('[data-testid="outside-notice"]').innerText().catch(() => '');
run.results.notice = noticeText;
check('the notice lists objects the person changed that it replaced', /chest:stash|light:feeding|deco:aisle_sacks_1|light:/.test(noticeText), noticeText.slice(0, 400));
await shot('notice', 'the red notice: the outside entry rewrote hand-edited work, with Revert entry');
await page.click('[data-testid="revert-notice"]');
await settled();
await sleep(500);
await shot('reverted', 'after the notice\'s one step: the rewrite reverted');

// --- 5. Every hand edit still there -------------------------------------------------------------------------------

writeFileSync(join(out, 'mixed_edits.json'), JSON.stringify(edits, null, 1));
let report = '';
let kept = false;
try
{
    report = execFileSync('python3', [join(repo, 'output', 's5b1', 'scripts', 'hand_edits_check.py'), folder, join(out, 'mixed_edits.json')], { encoding: 'utf8' });
    kept = true;
}
catch (error)
{
    report = String(error.stdout ?? error);
}
console.log(report);
run.results.hand_edits = report;
check('hand_edits_check.py: every hand edit still there', kept, report.split('\n').filter(Boolean).at(-1));
const after = (await objects('spawns')).some((spawn) => spawn.room === 'room:hall_aisle') && (await objects('chests')).find((chest) => chest.id === 'chest:stash')?.trap_level === 2;
check('the agent\'s additions and its change are back too', after);
await page.getByRole('tab', { name: /^History/ }).click();
await sleep(400);
await shot('history', 'History: the hand edits, the agent\'s entry, the outside rewrite and its revert');
const failed = await run.finish('s5b1_mixed');
process.exit(failed > 0 ? 1 : 0);
