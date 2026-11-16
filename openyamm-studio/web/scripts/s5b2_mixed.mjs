// S5b2 exit test 2, the mixed test outdoors (S5_BROWSER_EDITOR.md 6.4, F6, 3.18 "Land by hand"): an outdoor project an
// agent makes (project.new and edit.apply through `oymap call`, author agent:maker, a ridge in heights.ridges, a road,
// a building, trees) is finished by hand in the real app: a sculpt patch drawn over the ridge, a raise stroke and a
// smooth stroke in it, a building added, a road's point moved. Then an agent adds and changes through operations
// (edit.apply as agent:mixer), moving the ridge under the sculpted patch among them. Every hand edit must still be
// there, the strokes still in heights.strokes and heights.smooth, the built land at the stroke its difference over the
// moved ridge (view.terrain_query against a copy without the strokes), and the project must validate and build.
// Screenshots in output/s5b2_shots/.
//   node scripts/s5b2_mixed.mjs
import { execFileSync } from 'node:child_process';
import { cpSync, rmSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { repo, sleep, stampFolder, startRun, studio } from './exit_common.mjs';

const out = join(repo, 'output', 's5b2_shots');
const runRoot = stampFolder('mixed', 's5b2_web');
const folder = join(runRoot, 'agent_vale');
const oymap = join(studio, 'build-s4', 'oymap');
const assets = join(repo, 'assets_dev');
const call = (method, params) =>
{
    const text = execFileSync(oymap, ['call', method, JSON.stringify(params), '--assets', assets], { encoding: 'utf8', maxBuffer: 64 << 20 });
    const answer = JSON.parse(text);
    if (answer.error)
    {
        throw new Error(`${method}: ${answer.error.message}`);
    }
    return answer.result;
};
const agentEdit = (project, ops, author, label) => call('edit.apply', { project, ops, author, label, rebase: true });

// --- 0. The agent's map ------------------------------------------------------------------------------------------

call('project.new', { project: folder, kind: 'outdoor', id: 'amix01', name: 'Agent Vale', world: 'mm6', stats_id: 9612 });
const RIDGE = [[20, 40], [60, 40]];
let made = agentEdit(folder, [
    { op: 'patch', file: 'sketch.yml', patch: [{ op: 'add', path: '/heights/ridges', value: [{ line: RIDGE, height: 832, width: 2, slope: 6 }] }] },
    { op: 'add', to: 'links', file: 'plan.yml', value: { from: 'zone:land', to: 'zone:land', kind: 'road' } },
    { op: 'add', to: 'structures', file: 'sketch.yml', value: { kind: 'building', at: [56, 70], size: [3, 2], parts: [{ id: 'main', roof: 'hip' }] } },
    { op: 'add', to: 'scatter', file: 'sketch.yml', value: { decoration: 'tree12', count: 12, spacing: 2, polygon: [[80, 20], [96, 20], [96, 34], [80, 34]] } },
], 'agent:maker', 'the agent\'s base');
const link = made.ids_allocated.find((entry) => entry.startsWith('plan.yml#link:')).split('#')[1];
agentEdit(folder, [{ op: 'patch', file: 'sketch.yml', patch: [{ op: 'add', path: '/roads', value: [{ link, line: [[64.5, 64.5], [64.5, 90.5], [80.5, 90.5]], width: 'road', surface: 'pebbles' }] }] }],
    'agent:maker', 'a road south');

const run = await startRun({ out, prefix: 'mixed', roots: [runRoot] });
const { page, check, shot, settled, key, type } = run;
run.results.run = folder;
const projectKey = `${relative(repo, runRoot)}/agent_vale`;
const map = (cx, cy) => [cx * 512 - 32768, 32768 - cy * 512];
const click = (cx, cy, options = {}) => run.click(...map(cx, cy), options);
const drag = (from, to, steps = 14) => run.drag(map(...from), map(...to), steps);
const frame = (x0, y0, x1, y1) => run.frame(...map(x0, y1), ...map(x1, y0));
const sketch = async () => (await run.files())['sketch.yml']?.tree ?? {};
const selected = async () => (await run.state()).selection?.id ?? null;
const tool = async (name) =>
{
    await page.click(`[data-testid="tool-${name}"]`);
    await sleep(150);
};
const option = (name, value) => type(`option-${name}`, value);
const pick = (name, value) => page.selectOption(`[data-testid="option-${name}"]`, String(value));
const query = (project, points) => call('view.terrain_query', { project, points }).points.map((point) => point.height);

// --- 1. The agent's map, opened in Author mode -------------------------------------------------------------------

await page.goto(`${run.base}/?project=${encodeURIComponent(projectKey)}#token=${run.token}`);
await run.waitFor(() => window.__studio?.app?.store.getState().layout.state === 'ready', 60000);
await page.click('[data-testid="mode-author"]');
await settled(60000);
let s = await run.state();
check('the agent-made outdoor map opens, not marked as edited by hand', s.project.state === 'ready' && !s.project.value.hand_edited, JSON.stringify(s.project.value.hand_edited ?? null));
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(400);
await shot('opened', 'the agent\'s map (a ridge, a road, a building, trees) in Author mode');

// --- 2. Finished by hand -------------------------------------------------------------------------------------------

await page.mouse.move(5, 500);
await key('Digit2');
await tool('patch');
await frame(20, 25, 60, 55);
await drag([30, 32], [50, 50]);
await settled();
const patches = (await sketch()).heights.patches ?? [];
check('a sculpt patch drawn over the ridge (Patch tool, 20 x 18 cells)', patches.length === 1 && patches[0].polygon.length === 4, JSON.stringify(patches));
// A patch too big is refused in the browser.
await drag([10, 10], [60, 60]);
await settled();
check('a patch over 32 cells is refused', ((await sketch()).heights.patches ?? []).length === 1, `${((await sketch()).heights.patches ?? []).length} patches`);
await tool('sculpt');
await pick('brushMode', 'raise');
await option('brushRadius', 2);
await option('brushStrength', 96);
// Outside the patch the brush does nothing (land the sketch describes).
await drag([10, 60], [16, 60], 8);
await settled();
check('outside a patch the brush writes nothing (described land)', ((await sketch()).heights.strokes ?? []).length === 0, JSON.stringify((await sketch()).heights.strokes ?? null));
await drag([41, 46], [47, 46], 12);
await settled();
const strokes = (await sketch()).heights.strokes ?? [];
check('a raise stroke inside the patch (heights.strokes)', strokes.length === 1, JSON.stringify(strokes[0]?.at));
// The smooth stroke across the ridge's crest (north to south), apart from the raise stroke.
await pick('brushMode', 'smooth');
await option('brushRadius', 2);
await drag([34, 35], [34, 48], 12);
await settled();
const smooth = (await sketch()).heights.smooth ?? [];
check('a smooth stroke inside the patch (heights.smooth)', smooth.length >= 1, JSON.stringify(smooth.map((entry) => entry.polygon.length)));
await shot('sculpted', 'a patch over the agent\'s ridge: a raise stroke south of it, a smooth stroke across its crest');
await page.mouse.move(5, 500);
await key('Digit3');
await tool('building');
await frame(60, 55, 85, 75);
await drag([70, 60], [73, 63]);
await settled();
const handBuilding = ((await sketch()).structures ?? []).filter((entry) => entry.kind === 'building').at(-1);
check('a building added by hand (Building tool)', handBuilding && JSON.stringify(handBuilding.at) === '[70,60]', JSON.stringify(handBuilding));
await tool('select');
await frame(55, 60, 90, 95);
await click(70, 90.5);
check('a click selects the agent\'s road', (await selected()) === '/roads/road1', await selected());
await drag([80.5, 90.5], [80.5, 86.5]);
await settled();
const movedRoad = (await sketch()).roads[0].line;
check('the road\'s last point moved by hand (Select)', JSON.stringify(movedRoad[2]) === '[80.5,86.5]', JSON.stringify(movedRoad));
s = await run.state();
check('the project is marked edited by hand', Boolean(s.project.value.hand_edited), JSON.stringify(s.project.value.hand_edited ?? null));
await shot('finished', 'finished by hand: a building beside the agent\'s, the road\'s end moved north');
const hand = await sketch();
const handStrokes = JSON.stringify(hand.heights.strokes);
const handSmooth = JSON.stringify(hand.heights.smooth);
const handPatches = JSON.stringify(hand.heights.patches);

// --- 3. An agent adds and changes through operations, moving the ridge under the patch ----------------------------

const before = call('project.open', { project: folder });
const agent = agentEdit(folder, [
    { op: 'patch', file: 'sketch.yml', patch: [{ op: 'replace', path: '/heights/ridges/ridge1/line', value: [[20, 42], [60, 42]] }] },
    { op: 'add', to: 'structures', file: 'sketch.yml', value: { kind: 'well', at: [62, 66] } },
    { op: 'patch', id: 'scatter:scatter_1', file: 'sketch.yml', patch: [{ op: 'replace', path: '/count', value: 16 }] },
], 'agent:mixer', 'the agent moves the ridge, adds a well, thickens the trees');
run.results.agent = { revision_before: before.revision, revision_after: agent.revision_after, hand_objects: agent.hand_objects, changes: agent.changes };
check('the agent\'s operations are applied (edit.apply as agent:mixer)', agent.applied !== false && agent.revision_after !== before.revision, JSON.stringify(agent.changes ?? agent).slice(0, 300));
check('the agent is told the project is edited by hand', agent.hand_edited === true || Boolean(agent.hand_edited), JSON.stringify(agent.hand_edited));
await run.waitFor((revision) => window.__studio.app.store.getState().project.value?.revision === revision, 30000, agent.revision_after);
await settled();
const after = await sketch();
check('the ridge moved under the sculpted patch (the agent\'s patch of /heights/ridges/ridge1/line)', JSON.stringify(after.heights.ridges[0].line) === '[[20,42],[60,42]]', JSON.stringify(after.heights.ridges));
check('the strokes stay in heights.strokes, unchanged', JSON.stringify(after.heights.strokes) === handStrokes, JSON.stringify(after.heights.strokes)?.slice(0, 200));
check('the smoothed area stays in heights.smooth, unchanged', JSON.stringify(after.heights.smooth) === handSmooth, JSON.stringify(after.heights.smooth)?.slice(0, 200));
check('the patch stays', JSON.stringify(after.heights.patches) === handPatches, JSON.stringify(after.heights.patches));
check('the hand-made building stays', (after.structures ?? []).some((entry) => entry.id === handBuilding.id && JSON.stringify(entry.at) === '[70,60]'), JSON.stringify((after.structures ?? []).map((entry) => entry.id)));
check('the road\'s point moved by hand stays', JSON.stringify(after.roads[0].line[2]) === '[80.5,86.5]', JSON.stringify(after.roads[0].line));
check('the agent\'s well is there', (after.structures ?? []).some((entry) => entry.kind === 'well'), '');
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(1200);
await frame(20, 25, 60, 55);
await shot('agent_after', 'after the agent: the ridge two cells further south under the patch, the strokes kept');

// --- 4. The built land: the stroke's difference over the moved ridge -----------------------------------------------

const copy = join(runRoot, 'agent_vale_without_strokes');
cpSync(folder, copy, { recursive: true, filter: (path) => !path.includes('/.oymap') && !path.includes('/build') });
agentEdit(copy, [{ op: 'patch', file: 'sketch.yml', patch: [{ op: 'remove', path: '/heights/strokes' }] }], 'agent:check', 'the same land without the strokes');
const block = after.heights.strokes[0];
const nodes = [];
block.rows.forEach((row, r) => row.forEach((value, c) =>
{
    if (value !== null)
    {
        nodes.push({ at: [block.at[0] + c, block.at[1] + r], value });
    }
}));
const withStrokes = query(folder, nodes.map((node) => node.at));
const without = query(copy, nodes.map((node) => node.at));
const unit = block.unit ?? 32;
const wrong = nodes.map((node, i) => ({ at: node.at, want: node.value * unit, got: withStrokes[i] - without[i] })).filter((entry) => Math.abs(entry.want - entry.got) > 0.5);
run.results.stroke_check = { nodes: nodes.length, wrong: wrong.slice(0, 20) };
check('the built land at every stroke node is the stroke\'s difference over the moved ridge (view.terrain_query, against a copy without the strokes)',
    nodes.length > 0 && wrong.length === 0, `${nodes.length} nodes, ${wrong.length} off: ${JSON.stringify(wrong.slice(0, 5))}`);
// The smoothed area follows the moved ridge: inside its outline the moved crest is lower and its slopes rounder
// than the same land without the smoothing (no ripple of the old crest: the smooth entry is an area, not
// differences), read column by column (the ridge runs east-west).
const smoothPoly = after.heights.smooth[0].polygon;
const xs = smoothPoly.map((p) => p[0]);
const ys = smoothPoly.map((p) => p[1]);
const columns = [];
for (let x = Math.ceil(Math.min(...xs)); x <= Math.floor(Math.max(...xs)); ++x)
{
    const column = [];
    for (let y = Math.ceil(Math.min(...ys)); y <= Math.floor(Math.max(...ys)); ++y)
    {
        column.push([x, y]);
    }
    columns.push(column);
}
const copy2 = join(runRoot, 'agent_vale_without_smooth');
cpSync(folder, copy2, { recursive: true, filter: (path) => !path.includes('/.oymap') && !path.includes('/build') });
agentEdit(copy2, [{ op: 'patch', file: 'sketch.yml', patch: [{ op: 'remove', path: '/heights/smooth' }] }], 'agent:check', 'the same land without the smoothing');
// The sum of the second differences down each column: how far the profile bends.
const bend = (project) => columns.reduce((sum, column) =>
{
    const heights = query(project, column);
    let total = 0;
    for (let i = 1; i + 1 < heights.length; ++i)
    {
        total += Math.abs(heights[i + 1] - 2 * heights[i] + heights[i - 1]);
    }
    return sum + total;
}, 0);
// The crest under the smooth stroke's middle line (x 34; the moved ridge's two nodes across, y 41 and 42).
const crest = (project) => query(project, [[34, 41], [34, 42]]).reduce((sum, value) => sum + value, 0) / 2;
const smoothWith = { bend: bend(folder), crest: crest(folder) };
const smoothWithout = { bend: bend(copy2), crest: crest(copy2) };
run.results.smooth_check = { columns: columns.length, with: smoothWith, without: smoothWithout };
check('the smoothed area is smoothed on the moved ridge: its crest lower and its profile bending less than the same land without it',
    smoothWith.crest < smoothWithout.crest && smoothWith.bend < smoothWithout.bend, `crest ${smoothWith.crest} vs ${smoothWithout.crest}; bend ${smoothWith.bend} vs ${smoothWithout.bend}`);
rmSync(copy, { recursive: true, force: true });
rmSync(copy2, { recursive: true, force: true });

// --- 5. Checks and the build ------------------------------------------------------------------------------------

const validate = call('check.validate', { project: folder });
const errors = validate.issues.filter((issue) => issue.severity === 'error');
check('check.validate: no errors', errors.length === 0, errors.map((issue) => `${issue.file} ${issue.path}: ${issue.message}`).join(' | ') || `${validate.issues.length} issues`);
let build;
try
{
    build = call('build.run', { project: folder, dry_run: false });
}
catch (error)
{
    build = { error: String(error) };
}
check('build.run builds the map', build && !build.error && build.files?.some((file) => file.endsWith('.odm')), JSON.stringify(build).slice(0, 300));
const history = call('edit.history', { project: folder, limit: 100 }).entries;
run.results.history = history.map((entry) => `${entry.sequence} ${entry.author} ${entry.label}`);
check('History holds the person\'s and the agents\' entries apart', history.some((entry) => entry.author === 'user') && history.some((entry) => entry.author === 'agent:mixer')
    && history.some((entry) => entry.author === 'agent:maker'), [...new Set(history.map((entry) => entry.author))].join(', '));
await page.mouse.move(5, 500);
await key('Digit7');
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(1500);
await shot('final', 'the mixed map: the agent\'s base, the hand edits and the agent\'s later operations together');
writeFileSync(join(out, 'mixed_result.json'), JSON.stringify(run.results, null, 1));
const failed = await run.finish('s5b2_mixed');
process.exit(failed > 0 ? 1 : 0);
