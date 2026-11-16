// S5b2, the items S5b1 carried (devdocs/map_studio/S5.md, "S5b1 part two and S5b1 exit"): plan handles on lifts,
// movers, plates, ladders, flights, beams and parapets; the 3D view's travel scrubber; fixes beyond the five kinds in
// the Issues drawer; History's ghost outdoors; the plan's section view. Each driven by gestures in the browser on
// copies of projects in output/s5b2_carried/ (the Sunken Chapel of S5b1 part two's exit test, a broken copy of it,
// mm8_d05 L4, mm6_oute3 L4), checked from the store, a screenshot of each in output/s5b2_carried_shots/.
//   npm run build && node scripts/s5b2_carried_shots.mjs
import { cpSync, readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, relative } from 'node:path';
import { repo, sleep, stampFolder, startRun, studio } from './exit_common.mjs';

const out = join(repo, 'output', 's5b2_carried_shots');
const runRoot = stampFolder('carried', 's5b2_carried');
const copy = (from, name) =>
{
    cpSync(from, join(runRoot, name), { recursive: true, filter: (path) => !path.includes('/.oymap') && !path.includes('/build') });
    return join(runRoot, name);
};
const chapel = copy(join(repo, 'output', 's5b1p2', 'web', 'runs', '2026-11-15T03-40-50-609Z-hand', 'sunken_chapel'), 'chapel');
const broken = copy(chapel, 'chapel_issues');
const d05 = copy(join(repo, 'devdocs', 'map_studio', 'briefs', 'mm8_d05', 'L4'), 'd05');
const oute3 = copy(join(repo, 'devdocs', 'map_studio', 'briefs', 'mm6_oute3', 'L4'), 'oute3');

// The broken copy: a room drawn clockwise, an opening wider than its wall, a light standing in the next room, a typo.
const rewrite = (file, pairs) =>
{
    let text = readFileSync(file, 'utf8');
    for (const [from, to] of pairs)
    {
        if (!text.includes(from))
        {
            throw new Error(`${file}: no ${from}`);
        }
        text = text.replace(from, to);
    }
    writeFileSync(file, text);
};
rewrite(join(broken, 'rooms.yml'), [
    ['outline: [[832, 960], [1344, 960], [1344, 1472], [832, 1472]]', 'outline: [[832, 960], [832, 1472], [1344, 1472], [1344, 960]]'],
    ['    to: room:space_2_1\n    along: 0.5\n    width: 192', '    to: room:space_2_1\n    along: 0.5\n    width: 900'],
]);
rewrite(join(broken, 'objects.yml'), [['  - id: light:space_6_1_2\n    room: room:space_6_1\n    at: [3456, 208]', '  - id: light:space_6_1_2\n    room: room:space_6_1\n    at: [2176, 320]']]);
rewrite(join(broken, 'wiring.yml'), [['toggles: [door:door_1]', 'toggles: [door:dor_1]']]);

// The outdoor copy: two entries made through the core before the browser opens it (an agent's edits): the volcano's
// peak lowered, a building moved.
const oymap = join(studio, 'build-s4', 'oymap');
const call = (method, params) => JSON.parse(execFileSync(oymap, ['call', method, JSON.stringify(params), '--assets', join(repo, 'assets_dev')], { encoding: 'utf8', maxBuffer: 256 << 20 }));
const peak = call('edit.apply', { project: oute3, author: 'agent:s5b2', label: 'the volcano lowered', ops: [
    { op: 'patch', file: 'sketch.yml', patch: [{ op: 'test', path: '/heights/points/point1/h', value: 4064 }, { op: 'replace', path: '/heights/points/point1/h', value: 2600 }] }] });
const moved = call('edit.apply', { project: oute3, author: 'agent:s5b2', label: 'the temple moved east', ops: [
    { op: 'set', id: 'thing:building_2', file: 'sketch.yml', fields: { at: [47.5, 64] } }] });

const run = await startRun({ out, prefix: 'carried', roots: [runRoot] });
const { page, check, shot, shotOf, settled, click, drag, key, frame } = run;
run.results.run = runRoot;
check('the outdoor copy: two entries made through the core', peak.result?.applied === true && moved.result?.applied === true,
    JSON.stringify([peak.error ?? peak.result?.changes, moved.error ?? moved.result?.changes]));

const files = async () => run.files();
const objectOf = async (list, id) => ((await files())['objects.yml']?.tree[list] ?? []).find((entry) => entry.id === id);
const roomOf = async (id) => ((await files())['rooms.yml']?.tree.rooms ?? []).find((room) => room.id === id);
const selected = async () => (await run.state()).selection?.id ?? null;
const open = async (folder) =>
{
    await page.goto(`${run.base}/?project=${encodeURIComponent(relative(repo, folder))}#token=${run.token}`);
    await run.waitFor(() => window.__studio?.app?.store.getState().layout.state === 'ready', 90000);
    await settled(90000);
};
const author = async () =>
{
    await page.click('[data-testid="mode-author"]');
    await settled();
    await page.click('[data-testid="tool-select"]');
    await sleep(150);
};
const select = (id, file) => page.evaluate(([i, f]) => window.__studio.app.store.setState({ selection: i ? { id: i, file: f } : null }), [id, file]);

// --- 1. Plan handles ----------------------------------------------------------------------------------------------------

await open(chapel);
await author();
const entriesBefore = (await run.state()).history.value.entries.length;
await frame(800, -256, 1920, 960);
await click(992, 32);
check('handles: a click selects the lift', (await selected()) === 'lift:space_2_1_1', await selected());
await shot('lift_selected', 'Select on the lift of the nave: its box with corner handles');
await drag([1088, 128], [1152, 192]);
await settled();
let lift = await objectOf('lifts', 'lift:space_2_1_1');
check('handles: the lift\'s corner dragged resizes it (one patch of at and size)', JSON.stringify(lift.at) === '[1024,64]' && JSON.stringify(lift.size) === '[256,256]', JSON.stringify(lift));
await drag([1024, 64], [960, 64]);
await settled();
lift = await objectOf('lifts', 'lift:space_2_1_1');
check('handles: the lift dragged inside moves it', JSON.stringify(lift.at) === '[960,64]' && JSON.stringify(lift.size) === '[256,256]', JSON.stringify(lift));
await shot('lift_sized', 'the lift resized by its north-east corner (192 to 256) and moved west by a drag inside it');

await click(1400, 256);
check('handles: a click on the beam\'s line selects the beam', (await selected()) === 'room:space_2_1/beams/beam1', await selected());
await drag([1792, 256], [1792, 320]);
await settled();
const nave = async () => roomOf('room:space_2_1');
check('handles: the beam\'s end dragged (a point handle)', JSON.stringify((await nave()).beams[0].path) === '[[896,256],[1792,320]]', JSON.stringify((await nave()).beams[0].path));
await shot('beam', 'the beam selected by its line; its east end dragged north by 64 (point handles at both ends)');

await click(1600, 380);
check('handles: a click on the flight selects it', (await selected()) === 'room:space_2_1/flights/flight1', await selected());
await drag([1600, 464], [1600, 512]);
await settled();
check('handles: the flight\'s top end dragged', JSON.stringify((await nave()).flights[0].to) === '[1600,512]', JSON.stringify((await nave()).flights[0]));
await shot('flight', 'the flight selected; its top end dragged onto the gallery by 64');

await click(1640, 832);
check('handles: a click on the parapet selects it', (await selected()) === 'room:space_2_1/parapets/parapet1', await selected());
await drag([1640, 832], [1640, 768]);
await settled();
check('handles: the parapet dragged by its line moves whole', JSON.stringify((await nave()).parapets[0].path) === '[[1472,768],[1792,768]]', JSON.stringify((await nave()).parapets[0].path));
await shot('parapet', 'the parapet selected by its line and dragged whole 64 south (it is put back after)');
await drag([1640, 768], [1640, 832]);
await settled();

await click(1744, 440);
check('handles: a click selects the ladder', (await selected()) === 'ladder:space_2_1_1', await selected());
const upp = await page.evaluate(() => window.__studio.plan.unitsPerPixel());
// The facing handle stands 34 pixels along its facing (90: north).
await drag([1744, 446 + 34 * upp], [1744 - 60 * upp, 446]);
await settled();
const ladder = await objectOf('ladders', 'ladder:space_2_1_1');
check('handles: the ladder turned by its facing handle (90 to 180)', ladder.facing === 180, JSON.stringify(ladder));
await shot('ladder', 'the ladder selected: its foot and its facing handle, turned to face west');
await drag([1744 - 34 * upp, 446], [1744, 446 + 60 * upp]);
await settled();

await frame(-128, -128, 896, 768);
await click(128, 512);
check('handles: a click selects the mover', (await selected()) === 'mover:space_1_1_1', await selected());
await drag([128, 512], [192, 448]);
await settled();
const mover = await objectOf('movers', 'mover:space_1_1_1');
check('handles: the mover dragged inside moves it', JSON.stringify(mover.at) === '[192,448]', JSON.stringify(mover));
await click(320, 512);
check('handles: a click selects the plate', (await selected()) === 'plate:space_1_1_1', await selected());
await drag([384, 576], [448, 576]);
await settled();
const plate = await objectOf('plates', 'plate:space_1_1_1');
check('handles: the plate\'s corner widens it', JSON.stringify(plate.size) === '[192,128]', JSON.stringify(plate));
await click(256, 256);
check('handles: a click selects the ceiling level', (await selected()) === 'room:space_1_1/ceiling_levels/ceiling_level1', await selected());
await shot('mover_plate', 'the entry: the mover moved, the plate widened by its east corner, the ceiling level selected (its outline\'s handles)');
const history = (await run.state()).history.value.entries;
// Ten gestures; a gesture and its undoing by hand with the same merge key fold into one entry (the parapet, the ladder).
check('handles: every gesture one history entry', history.length - entriesBefore >= 8, `${history.length - entriesBefore} new entries: ${history.map((entry) => entry.label).slice(-10).join(' | ')}`);

// --- 2. The travel scrubber ---------------------------------------------------------------------------------------------

const scrub = async (id, share, hold) =>
{
    await select(id, 'objects.yml');
    await page.waitForSelector('[data-testid="travel-range"]', { timeout: 15000 });
    await page.evaluate((i) => window.__studio.viewport.frameObject(i), id);
    await sleep(400);
    if (hold)
    {
        await page.locator('[data-testid="travel-scrubber"] input[type="checkbox"]').check();
    }
    const box = await page.locator('[data-testid="travel-range"]').boundingBox();
    const start = await page.evaluate(() => window.__studio.viewport.travelShare() ?? 0);
    await page.mouse.move(box.x + 8 + (box.width - 16) * start, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + 8 + (box.width - 16) * share, box.y + box.height / 2, { steps: 10 });
    await sleep(300);
};
await scrub('door:door_1', 0.6, false);
const doorShare = await page.evaluate(() => window.__studio.viewport.travelShare());
check('scrubber: the door raised while the slider is held (on the client)', doorShare > 0.4 && doorShare < 0.8, String(doorShare));
await shot('scrub_door', 'door:door_1 selected: the scrubber holds it 60 % open (blue), its closed place a faint ghost');
await page.mouse.up();
await sleep(300);
check('scrubber: let go, the door is back as the map starts it (closed)', (await page.evaluate(() => window.__studio.viewport.travelShare())) === null,
    String(await page.evaluate(() => window.__studio.viewport.travelShare())));
await scrub('door:door_2', 0.5, false);
await shot('scrub_hinged', 'door:door_2 (hinged) held half open: it turns about its hinge');
await page.mouse.up();
await scrub('lift:space_2_1_1', 1, true);
await page.mouse.up();
await sleep(300);
check('scrubber: with hold the lift stays raised as a view', (await page.evaluate(() => window.__studio.viewport.travelShare())) === 1,
    String(await page.evaluate(() => window.__studio.viewport.travelShare())));
const unwritten = await objectOf('lifts', 'lift:space_2_1_1');
check('scrubber: nothing written (the lift still starts down)', unwritten.state === undefined, JSON.stringify(unwritten));
await shot('scrub_lift', 'the lift raised its whole travel (256) and held there as a view; the files unchanged');
await select(null, null);

// --- 3. Fixes in the Issues drawer ------------------------------------------------------------------------------------------

await open(broken);
await author();
const issuesTab = page.getByRole('tab', { name: /^Issues\s*\d+$/ });
await issuesTab.click();
const issuesPanel = `[id="${await issuesTab.getAttribute('aria-controls')}"]`;
await run.waitFor(() => window.__studio.app.store.getState().validation?.state === 'ready', 60000);
const issues = async () => (await run.state()).validation.value.issues;
const fixOf = async (start) => (await issues()).find((issue) => (issue.fixes ?? []).some((fix) => fix.label.startsWith(start)));
await shotOf(issuesPanel, 'fixes_first', 'Issues: the clockwise room and the misspelt door, each with its fix');
const fixButton = (start) => page.locator('button', { hasText: start }).first();
const press = async (start) =>
{
    await fixButton(start).click();
    await settled();
    await run.waitFor(() => window.__studio.app.store.getState().validation?.state === 'ready', 60000);
    await sleep(300);
};
check('fixes: the clockwise room offers its reversal', Boolean(await fixOf('reverse the outline')));
check('fixes: the misspelt door offers the nearest door', Boolean(await fixOf('name door:door_1 instead')));
await press('reverse the outline');
await press('name door:door_1 instead');
check('fixes: reversed and renamed, both issues gone', !(await fixOf('reverse the outline')) && !(await fixOf('name door:door_1')),
    (await issues()).map((issue) => issue.message).join(' | '));
await shotOf(issuesPanel, 'fixes_next', 'Issues after two fixes: the opening wider than the wall its rooms share, with its two fixes');
check('fixes: the opening too wide offers to narrow it or make it full', Boolean(await fixOf('narrow it to')) && Boolean(await fixOf('make it `width: full`')));
await press('narrow it to');
check('fixes: the light standing in the next room offers that room, or a place inside its own', Boolean(await fixOf('give light:space_6_1_2 the room it stands in'))
    && Boolean(await fixOf('move light:space_6_1_2 inside')), (await issues()).map((issue) => issue.message).join(' | '));
await shotOf(issuesPanel, 'fixes_light', 'Issues: the light that stands in the next room, with its two fixes');
await press('give light:space_6_1_2 the room it stands in');
const left = (await issues()).filter((issue) => issue.severity === 'error');
check('fixes: no errors left', left.length === 0, left.map((issue) => issue.message).join(' | '));
await shot('fixes_done', 'the broken copy after four fixes from the Issues drawer: no errors, the plan drawn again');

// --- 4. History's ghost outdoors ---------------------------------------------------------------------------------------------

await open(oute3);
await page.getByRole('tab', { name: /^History\s*\d*$/ }).click();
await sleep(800);
const entries = (await run.state()).history.value.entries;
const lowered = entries.find((entry) => entry.label === 'the volcano lowered');
check('ghost outdoors: History lists the agent\'s entries', Boolean(lowered), entries.map((entry) => entry.label).join(' | '));
if (lowered)
{
    await page.click(`[data-testid="ghost-${lowered.sequence}"]`);
    await run.waitFor(() => Boolean(window.__studio.app.store.getState().ghost?.layout), 120000);
}
const ghost = (await run.state()).ghost;
check('ghost outdoors: view.layout_at answers for the outdoor project (land and models of then)', ghost?.layout?.kind === 'outdoor'
    && ghost.layout.land?.heights?.length === 128 * 128 && (ghost.layout.models?.length ?? 0) > 0,
    JSON.stringify({ kind: ghost?.layout?.kind, models: ghost?.layout?.models?.length }));
await page.evaluate(() => window.__studio.app.store.setState({ viewMode: 'plan' }));
await sleep(1200);
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(800);
await shot('ghost_outdoor', 'History: oute3 as it was before the volcano was lowered and the temple moved: the models of then dashed, the land changed since tinted (blue: sunk)');
await frame(-14336, -4096, -4096, 4096);
await shot('ghost_outdoor_near', 'the same, near the temple: its box of then (dashed) west of where it stands now');
await page.evaluate(() => window.__studio.app.store.setState({ viewMode: 'split' }));

// --- 5. The section view ---------------------------------------------------------------------------------------------------

await open(d05);
await select('room:trap_hall', 'rooms.yml');
await page.click('[data-testid="section-toggle"]');
await sleep(800);
const spans = () => page.evaluate(() => window.__studio.section ? true : false);
check('section: the panel opens with a view', await spans());
await frame(-1200, 600, 1400, 2200);
await sleep(500);
await shot('section_trap_hall', 'Section along the trap hall\'s long axis: its floor, the eight lift steps with their travel (dashed, arrows)');
await page.click('[data-testid="section-draw"]');
await frame(-5600, -4800, 600, 600);
await drag([-5300, -1340], [-500, -1340]);
await sleep(800);
await shot('section_pyramid', 'A cut drawn west to east across the pyramid: the lantern above it, the well and the tunnel below, stacked by height');
// A click in the section on the lantern selects it.
const lantern = await page.evaluate(() => window.__studio.section.screenOf(2300, 2500));
await page.mouse.click(lantern[0], lantern[1]);
await sleep(300);
check('section: a click in it selects what it hits (the lantern)', (await selected()) === 'room:lantern', await selected());
await shot('section_select', 'the lantern clicked in the section: selected in the plan and the section');

const failed = await run.finish('carried');
process.exit(failed > 0 ? 1 : 0);
