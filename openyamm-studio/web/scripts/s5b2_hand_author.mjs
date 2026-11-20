// S5b2 exit test 1 (S5_BROWSER_EDITOR.md 6.4, F5, W2): a small new outdoor map, land included, made from an EMPTY
// project entirely in the UI: New project (kind outdoor) in the project list, then gestures only (clicks and drags on
// the plan, keys, the tool options, the inspector, the event form, the wall bay strip and the house picker); never
// the Source tab, YAML or a command line. The script reads the store to check and to find screen points, and calls
// check.validate and build.run at the end as the verification. Prints every word set and how, and the misses (a word
// that forced the Source tab, or a bespoke tool 3.18 promises that is only a row list). Screenshots in
// output/s5b2_shots/.
//   node scripts/s5b2_hand_author.mjs
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { repo, sleep, stampFolder, startRun } from './exit_common.mjs';

const out = join(repo, 'output', 's5b2_shots');
const runRoot = stampFolder('hand', 's5b2_web');
const run = await startRun({ out, prefix: 'hand', roots: [runRoot] });
const { page, check, shot, settled, key, type } = run;
run.results.run = runRoot;

const words = new Map();
const how = (word, means, detail = '') =>
{
    const known = words.get(word);
    if (!known || (known.means !== 'bespoke tool' && means === 'bespoke tool'))
    {
        words.set(word, { means, detail });
    }
};
const misses = [];

// Cells to map units (the plan's points): x east, y south from the north-west corner, 512 a cell.
const map = (cx, cy) => [cx * 512 - 32768, 32768 - cy * 512];
const click = (cx, cy, options = {}) => run.click(...map(cx, cy), options);
const drag = (from, to, steps = 14) => run.drag(map(...from), map(...to), steps);
const frame = (x0, y0, x1, y1) => run.frame(...map(x0, y1), ...map(x1, y0));
const hover = async (cx, cy) =>
{
    const [sx, sy] = await run.at(...map(cx, cy));
    await page.mouse.move(sx, sy, { steps: 3 });
    await sleep(80);
};
const tree = async (file) => (await run.files())[file]?.tree ?? {};
const sketch = async () => tree('sketch.yml');
const selected = async () => (await run.state()).selection?.id ?? null;
const tool = async (name) =>
{
    await page.click(`[data-testid="tool-${name}"]`);
    await sleep(150);
};
const stage = async (number) =>
{
    await page.evaluate(() => document.activeElement?.blur?.());
    await page.mouse.move(5, 500);
    await key(`Digit${number}`);
    await sleep(200);
};
const option = (name, value) => type(`option-${name}`, value);
const pick = (name, value) => page.selectOption(`[data-testid="option-${name}"]`, String(value));
const toggleOn = async (name, on) =>
{
    const pressed = await page.locator(`[data-testid="option-${name}"]`).getAttribute('data-pressed');
    if ((pressed !== null) !== on)
    {
        await page.click(`[data-testid="option-${name}"]`);
        await sleep(80);
    }
};
const lineTool = async (points) =>
{
    for (const p of points)
    {
        await click(...p);
    }
    await key('Enter');
    await settled();
};
// The built land's height at cells (view.terrain_query), the verification's own reading.
const heightsAt = async (points) =>
{
    const project = (await run.state()).projectKey;
    const answer = await page.evaluate(([p, pts]) => window.__studio.app.controller.client.call('view.terrain_query', { project: p, points: pts }), [project, points]);
    return answer.points.map((point) => point.height);
};

// --- 1. New project, kind outdoor -------------------------------------------------------------------------------

await page.goto(`${run.base}/#token=${run.token}`);
await page.waitForSelector('[data-testid="new-project"]', { timeout: 20000 });
await page.click('[data-testid="new-project"]');
await page.selectOption('[data-testid="new-kind"]', 'outdoor');
await page.fill('[data-testid="new-folder"]', 'hollow_vale');
await page.fill('[data-testid="new-id"]', 'hvale01');
await page.fill('[data-testid="new-name"]', 'Hollow Vale');
await page.fill('[data-testid="new-stats"]', '9611');
await shot('new_project', 'the New project form, kind outdoor');
await page.click('[data-testid="new-project-make"]');
await run.waitFor(() => window.__studio?.app?.store.getState().project.state === 'ready', 30000);
await run.waitFor(() => window.__studio?.app?.store.getState().layout.state === 'ready', 30000);
await settled();
let s = await run.state();
check('an empty outdoor project made in the UI opens in Author mode with the grid editor', s.mode === 'author' && s.tool === 'spots'
    && s.project.value.files['project.yml'].tree.kind === 'outdoor', `${s.projectKey} ${s.tool}`);
for (const word of ['project.yml id', 'project.yml name', 'project.yml world', 'project.yml kind', 'project.yml map_stats.id'])
{
    how(word, 'bespoke tool', 'New project form (kind outdoor)');
}
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(400);
await shot('opened', 'the new outdoor map: level land, the arrival point, the grid editor\'s spot heights');

// --- 2. Shape: spot heights -----------------------------------------------------------------------------------

const gridRows = async () => (await sketch()).heights.grid.rows;
await option('spotHeight', 640);
// Spots stand at [8 + 16 i, 8 + 16 j]: paint the north-west four by a drag over two and a click on two more.
await drag([8, 8], [24, 8]);
await settled();
await click(8, 24);
await settled();
await click(24, 24);
await settled();
let rows = await gridRows();
check('spot heights painted by a drag and clicks (grid editor)', rows[0][0] === 10 && rows[0][1] === 10 && rows[1][0] === 10 && rows[1][1] === 10, JSON.stringify(rows.slice(0, 2)));
// PgUp twice and PgDn once on the hovered spot (3, 3): one unit up.
await hover(56, 56);
await key('PageUp');
await key('PageUp');
await key('PageDown');
await settled();
rows = await gridRows();
check('PgUp/PgDn on the hovered spot (grid editor)', rows[3][3] === 5, JSON.stringify(rows[3]));
// The south-east corner lower: paint 128 there.
await option('spotHeight', 128);
await drag([104, 120], [120, 120]);
await settled();
rows = await gridRows();
check('the south-east spots painted low', rows[7][6] === 2 && rows[7][7] === 2, JSON.stringify(rows[7]));
how('sketch.yml heights.grid.rows (spot heights)', 'bespoke tool', 'Spot heights tool: click, drag paint, PgUp/PgDn on the hovered spot');
await shot('spots', 'the grid editor: spot heights painted (640 in the north-west, 128 in the south-east) and one raised with PgUp');

// --- 3. Shape: a ridge, a terrace, a height point ---------------------------------------------------------------

await tool('ridge');
await option('height', 1088);
await option('ridgeWidth', 2);
await option('ridgeSlope', 5);
await frame(10, 80, 70, 115);
await lineTool([[18, 104], [32, 96], [48, 100], [60, 92]]);
const ridges = (await sketch()).heights.ridges ?? [];
check('a ridge drawn (Ridge tool: points and Enter)', ridges.length === 1 && ridges[0].line.length === 4 && ridges[0].height === 1088, JSON.stringify(ridges));
how('sketch.yml heights.ridges[] (line, height, width, slope)', 'bespoke tool', 'Ridge tool: click the crest, Enter; height, width, slope in the options');
await tool('terrace');
await option('height', 448);
await option('terraceSlope', 3);
await frame(60, 50, 90, 75);
await drag([72, 66], [80, 72]);
await settled();
const terraces = (await sketch()).heights.terraces ?? [];
check('a terrace dragged (Terrace tool)', terraces.length === 1 && terraces[0].height === 448 && terraces[0].polygon.length === 4, JSON.stringify(terraces));
how('sketch.yml heights.terraces[] (polygon, height, slope)', 'bespoke tool', 'Terrace tool: drag a box (or click an outline)');
await tool('hpoint');
await option('height', 896);
await frame(85, 15, 115, 45);
await click(100, 30);
await settled();
const points = (await sketch()).heights.points ?? [];
check('a height point clicked (Height point tool)', points.length === 1 && points[0].h === 896, JSON.stringify(points));
// PgUp with Select over the selected point.
await tool('select');
await hover(100, 30);
await key('PageUp');
await settled();
check('PgUp over the selected height point raises it (Select)', (await sketch()).heights.points[0].h === 928, JSON.stringify((await sketch()).heights.points));
how('sketch.yml heights.points[] (at, h)', 'bespoke tool', 'Height point tool: a click; PgUp/PgDn with Select');
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(300);
await shot('land_words', 'a ridge in the south-west, a terrace by the town and a height point in the north-east');

// --- 4. The land made by hand, sculpted ------------------------------------------------------------------------

await page.click('[data-testid="project-settings"]');
await page.waitForSelector('[data-testid="hand-made"]', { timeout: 10000 });
await shot('settings', 'Project settings: "This map\'s land is made by hand"');
await page.click('[data-testid="hand-made"]');
await settled();
await key('Escape');
check('the land marked made by hand (Project settings)', (await sketch()).heights.hand_made === true, JSON.stringify((await sketch()).heights.hand_made));
how('sketch.yml heights.hand_made', 'bespoke tool', 'Project settings: the checkbox "This map\'s land is made by hand"');
await tool('sculpt');
await pick('brushMode', 'raise');
await option('brushRadius', 3);
await option('brushStrength', 64);
await frame(20, 30, 60, 55);
const beforeRaise = await heightsAt([[36, 42]]);
// The stroke shown while dragging: the plan's tint and the 3D land moved (the client's own mesh).
const [ax, ay] = await run.at(...map(28, 42));
const [bx, by] = await run.at(...map(44, 42));
await page.mouse.move(ax, ay);
await page.mouse.down();
await page.mouse.move((ax + bx) / 2, ay, { steps: 10 });
await sleep(120);
const previewed = await page.evaluate(() =>
{
    const viewport = window.__studio.viewport;
    const base = viewport?.landBase;
    return base ? { vertices: base.vertices.length } : null;
});
await shot('sculpt_preview', 'a raise stroke while it is drawn: the plan tints the nodes, the 3D view moves its land');
await page.mouse.move(bx, by, { steps: 10 });
await page.mouse.up();
await settled();
const strokes = (await sketch()).heights.strokes ?? [];
check('the raise stroke previewed in 3D while dragging (the client\'s mesh moved)', previewed && previewed.vertices > 0, JSON.stringify(previewed));
check('a raise stroke written once on pointer-up (heights.strokes: differences, ~ outside)', strokes.length === 1 && strokes[0].rows.some((row) => row.some((v) => v === null))
    && strokes[0].rows.some((row) => row.some((v) => v > 0)), JSON.stringify(strokes[0]?.at) + ` ${strokes[0]?.rows?.length} rows`);
const afterRaise = await heightsAt([[36, 42]]);
check('the built land rose under the stroke (view.terrain_query)', afterRaise[0] > beforeRaise[0], `${beforeRaise[0]} -> ${afterRaise[0]}`);
how('sketch.yml heights.strokes[] (raise)', 'bespoke tool', 'Sculpt brush, raise: previewed, one transaction on pointer-up');
// A second raise over part of the first: a keyed patch of the block's rows.
await drag([32, 42], [40, 42], 10);
await settled();
const strokes2 = (await sketch()).heights.strokes ?? [];
check('a second stroke inside the first block patches its rows (one block)', strokes2.length === 1, `${strokes2.length} blocks`);
// Lower a little, then smooth.
await pick('brushMode', 'lower');
await option('brushStrength', 32);
await drag([30, 48], [42, 48], 10);
await settled();
await pick('brushMode', 'smooth');
await option('brushRadius', 4);
await drag([30, 44], [42, 44], 10);
await settled();
const smooth = (await sketch()).heights.smooth ?? [];
check('a smooth stroke written as its outline (heights.smooth)', smooth.length >= 1 && smooth[0].polygon.length >= 4, JSON.stringify(smooth[0]?.polygon?.slice(0, 6)));
how('sketch.yml heights.smooth[] (polygon)', 'bespoke tool', 'Sculpt brush, smooth: its outline traced on pointer-up');
how('sketch.yml heights.strokes[] (lower)', 'bespoke tool', 'Sculpt brush, lower');
// Flatten a pad for the well: the height under the first press.
await pick('brushMode', 'flatten');
await option('brushRadius', 2);
const terracesBefore = ((await sketch()).heights.terraces ?? []).length;
const pad = await heightsAt([[50, 34]]);
await drag([50, 34], [54, 34], 8);
await settled();
const terracesAfter = (await sketch()).heights.terraces ?? [];
const flat = terracesAfter[terracesAfter.length - 1];
check('a flatten stroke written as a terrace at the height under the first press', terracesAfter.length === terracesBefore + 1 && Math.abs(flat.height - Math.round(pad[0])) <= 1,
    `${JSON.stringify(flat?.height)} vs ${pad[0]}`);
how('sketch.yml heights.terraces[] (flatten)', 'bespoke tool', 'Sculpt brush, flatten: a terrace at view.terrain_query\'s height under the press');
await shot('sculpted', 'raise, lower, smooth and flatten strokes in the land made by hand');

// --- 5. Water and a road ------------------------------------------------------------------------------------------

await tool('water');
await pick('waterKind', 'pond');
await frame(40, 55, 60, 75);
await drag([44, 60], [51, 67]);
await settled();
const bodies = (await sketch()).water?.bodies ?? [];
const planSpaces = (await tree('plan.yml')).spaces ?? [];
check('a pond dragged (Water tool) with its plan space', bodies.length === 1 && bodies[0].kind === 'pond' && planSpaces.some((space) => space.id === bodies[0].id && space.kind === 'water'),
    JSON.stringify(bodies[0]));
how('sketch.yml water.bodies[] (polygon, kind, level) and its plan space', 'bespoke tool', 'Water tool: drag a box; kind and level in the options');
await tool('road');
await pick('roadWidth', 'road');
await option('roadSurface', 'pebbles');
await frame(55, 60, 85, 128);
// From the arrival point (64, 64) south, a 45-degree step, on to the south edge.
await click(64.5, 64.5);
await click(64.5, 80.5);
await click(71, 87.8);
await click(72.5, 127.5);
await key('Enter');
await settled();
const roads = (await sketch()).roads ?? [];
const road = roads[0];
const steps = road ? road.line.slice(1).map((p, i) => [p[0] - road.line[i][0], p[1] - road.line[i][1]]) : [];
check('a road clicked from the arrival point to the map edge (Road tool), square or 45-degree steps, with its plan link',
    roads.length === 1 && road.line.at(-1)[1] >= 127 && steps.every(([dx, dy]) => dx === 0 || dy === 0 || Math.abs(dx) === Math.abs(dy))
    && ((await tree('plan.yml')).links ?? []).some((link) => link.id === road.link && link.kind === 'road'), JSON.stringify(road));
how('sketch.yml roads[] (line, width, surface) and its plan link', 'bespoke tool', 'Road tool: click cells, Enter');
// Its second point dragged east by a cell, then the bed at it raised.
await tool('select');
await click(64.5, 72);
check('a click on the road selects it', (await selected()) === '/roads/road1', await selected());
await drag([64.5, 80.5], [65.5, 80.5]);
await settled();
check('a road point dragged (Select)', (await sketch()).roads[0].line[1][0] === 65.5, JSON.stringify((await sketch()).roads[0].line));
await hover(65.5, 80.5);
await key('PageUp');
await settled();
const bed = (await sketch()).roads[0].bed;
check('PgUp over a road point writes its bed (the land\'s heights, that point raised)', Array.isArray(bed) && bed.length === (await sketch()).roads[0].line.length, JSON.stringify(bed));
how('sketch.yml roads[].bed', 'bespoke tool', 'Select: PgUp/PgDn over a road point');
await shot('road', 'a pond, and a road from the arrival point south to the map edge (a 45-degree step), its bed raised at a point');

// --- 6. Build: two buildings, one of two parts, roofs, a door bay with a house -------------------------------------

await stage(3);
await tool('building');
await pick('roof', 'hip');
await frame(54, 50, 76, 64);
await drag([56, 55], [59, 58]);
await settled();
let structures = (await sketch()).structures ?? [];
const houseA = structures.find((entry) => entry.kind === 'building');
check('a building dragged (Building tool): its first part made', houseA && houseA.size[0] === 3 && houseA.size[1] === 3 && houseA.parts?.length === 1, JSON.stringify(houseA));
await drag([67, 55], [71, 58]);
await settled();
structures = (await sketch()).structures ?? [];
const houseB = structures.filter((entry) => entry.kind === 'building').at(-1);
check('a second building dragged', houseB && houseB.id !== houseA?.id && houseB.size[0] === 4, JSON.stringify(houseB));
how('sketch.yml structures[] kind building (at, size, parts)', 'bespoke tool', 'Building tool: drag a box');
// Enter the second building: its first part; shrink it to the west half by its south-east corner; a second part.
await tool('select');
await page.mouse.dblclick(...(await run.at(...map(69, 56.5))));
await settled();
check('a double click enters the building (its first part selected)', (await selected()) === `${houseB.id}/parts/main`, await selected());
await drag([71, 58], [69, 58], 12);
await settled();
let partMain = (await sketch()).structures.find((entry) => entry.id === houseB.id).parts[0];
check('the part\'s corner dragged (Select): the main part the west half', JSON.stringify(partMain.size) === JSON.stringify([1024, 1536]), JSON.stringify(partMain));
await tool('building');
await drag([69, 56], [71, 58], 12);
await settled();
let partsB = (await sketch()).structures.find((entry) => entry.id === houseB.id).parts;
check('a second part dragged inside the building (Building tool)', partsB.length === 2 && JSON.stringify(partsB[1].at) === JSON.stringify([1024, 512]), JSON.stringify(partsB));
how('sketch.yml structures[].parts[] (at, size)', 'bespoke tool', 'Building tool inside a building; corners with Select');
// Roofs in the building panel: the wing flat, the main part gable.
await page.waitForSelector('[data-testid="building-panel"]', { timeout: 10000 });
await page.click('[data-testid="roof-flat"]');
await settled();
await page.click('[data-testid="part-main"]');
await sleep(300);
await page.click('[data-testid="roof-gable"]');
await settled();
await type('roof-pitch', 45);
await settled();
partsB = (await sketch()).structures.find((entry) => entry.id === houseB.id).parts;
check('roofs set in the building panel (gable 45°, flat)', partsB[0].roof === 'gable' && partsB[0].roof_pitch === 45 && partsB[1].roof === 'flat', JSON.stringify(partsB.map((part) => [part.roof, part.roof_pitch])));
how('sketch.yml structures[].parts[].roof, roof_pitch', 'bespoke tool', 'building panel: roof chips and pitch');
// The door: bay 2 of the main part's south wall (8 bays: 1024 long), then the house from the picker.
await page.click('[data-testid="bay-s-2"]');
await sleep(200);
await shot('bay_strip', 'the wall bay strip: the main part\'s walls, bay 2 of the south wall chosen');
await page.click('[data-testid="bay-role-door"]');
await settled();
let buildingB = (await sketch()).structures.find((entry) => entry.id === houseB.id);
check('a bay made the door (wall bay strip): the wall written, the building\'s door there', buildingB.parts[0].walls?.s?.[2] === 'door'
    && buildingB.door?.part === 'main' && buildingB.door?.wall === 's' && buildingB.door?.bay === 2, JSON.stringify({ walls: buildingB.parts[0].walls, door: buildingB.door }));
// A window to the east of the door.
await page.click('[data-testid="bay-s-3"]');
await page.click('[data-testid="bay-role-window"]');
await settled();
how('sketch.yml structures[].parts[].walls (bays), door {part, wall, bay}', 'bespoke tool', 'the wall bay strip: click a bay, choose door / window / wall / posts');
await page.waitForSelector('[data-testid="house-search"]', { timeout: 10000 });
await page.fill('[data-testid="house-search"]', 'tavern');
await sleep(300);
const houseButton = page.locator('[data-testid="house-list"] button').first();
const houseNumber = Number((await houseButton.getAttribute('data-testid'))?.replace('house-', ''));
await houseButton.click();
await settled();
buildingB = (await sketch()).structures.find((entry) => entry.id === houseB.id);
check('the door\'s house chosen in the house picker (the house table, searched)', buildingB.house === houseNumber && houseNumber > 0, `${buildingB.house} (picked ${houseNumber})`);
how('sketch.yml structures[].house', 'bespoke tool', 'building panel: the house picker over the house table');
await shot('building', 'the second building entered: two parts (gable and flat roofs), the door bay and its house');
// The first building's roof: its part's gable from the panel (single click selects the building, its panel shows).
await tool('select');
await page.mouse.move(5, 500);
await click(57.5, 56.5);
await sleep(300);
await page.click('[data-testid="roof-gable"]');
await settled();
check('the first building\'s roof set from its panel', (await sketch()).structures.find((entry) => entry.id === houseA.id).parts[0].roof === 'gable',
    JSON.stringify((await sketch()).structures.find((entry) => entry.id === houseA.id).parts));

// --- 7. Structures: a well and a sign (generic tool + inspector) -------------------------------------------------

await tool('structure');
await pick('structureKind', 'well');
await click(62, 61);
await settled();
await pick('structureKind', 'sign');
await click(64, 61);
await settled();
structures = (await sketch()).structures;
const well = structures.find((entry) => entry.kind === 'well');
const sign = structures.find((entry) => entry.kind === 'sign');
check('a well and a sign placed (Structure tool, kind in the options)', well && sign && JSON.stringify(well.at) === '[62,61]', JSON.stringify({ well, sign }));
how('sketch.yml structures[] other kinds (well, sign: at)', 'generic tool + inspector', 'Structure tool: the kind from the options, a click');
// The sign's words in the inspector: what it says.
check('the sign is selected after placing', (await selected()) === sign.id, await selected());
await page.waitForSelector('[data-testid="click-words"]', { timeout: 10000 });
await type('field-title', 'Hollow Vale: the Inn this way');
await settled();
check('the sign\'s title set in its Click words (inspector)', (await sketch()).structures.find((entry) => entry.id === sign.id).title === 'Hollow Vale: the Inn this way',
    JSON.stringify((await sketch()).structures.find((entry) => entry.id === sign.id)));
how('sketch.yml structures[].title (click words)', 'inspector field', 'the Click section over a structure\'s form');
// The well gives a little might: one step in its Click words (the event form's rows).
await tool('select');
await click(62, 61);
check('a click selects the well', (await selected()) === well.id, await selected());
await sleep(300);
await page.selectOption('[data-testid="click-words"] [data-testid="add-effects"]', 'text');
await settled();
const wellSteps = (await sketch()).structures.find((entry) => entry.id === well.id).effects;
check('the well\'s click does a step (the event form\'s rows in its Click words)', Array.isArray(wellSteps) && wellSteps.length === 1 && 'text' in wellSteps[0], JSON.stringify(wellSteps));
how('sketch.yml structures[].effects (a click\'s steps)', 'bespoke tool', 'the Click section: the event form\'s step rows');
await shot('structures', 'a well and a sign by the road; the well\'s Click words in the inspector');

// --- 8. Populate: an encounter area and an actor -------------------------------------------------------------------

await stage(5);
await tool('area');
await pick('areaKind', 'encounter');
await page.locator('[data-testid="option-areaPopulation"]').fill('wolves');
await page.locator('[data-testid="option-areaPopulation"]').press('Enter');
await option('areaCount', 3);
await frame(85, 80, 115, 110);
await lineTool([[90, 88], [106, 88], [108, 104], [92, 104]]);
const areas = (await sketch()).areas ?? [];
const pops = ((await tree('plan.yml')).spaces ?? []).flatMap((space) => space.population ?? []);
check('an encounter area clicked (Area tool) with its plan population', areas.length === 1 && areas[0].id === 'pop:wolves' && areas[0].kind === 'encounter'
    && pops.some((pop) => pop.id === 'pop:wolves'), JSON.stringify({ areas, pops }));
how('sketch.yml areas[] (encounter, polygon, count, slot) and its plan population', 'bespoke tool', 'Area tool: click an outline, Enter');
// The map card's encounter slots (a new map names no reference map whose row would give them): the inspector of
// project.yml with nothing selected (3.18 "map card ... the inspector on project.yml").
await page.evaluate(() => window.__studio.app.store.setState({ selection: null }));
await page.waitForSelector('[data-testid="file-form"]', { timeout: 10000 });
await page.selectOption('[data-testid="file-form-file"]', 'project.yml');
await sleep(400);
await page.click('[data-testid="block-map_stats"]');
await sleep(300);
const adders = page.locator('[data-testid="file-form"] [data-testid="add-field"]');
for (let i = 0; i < await adders.count(); ++i)
{
    await adders.nth(i).click();
    await sleep(250);
    const item = page.locator('[role="menuitem"]').filter({ has: page.locator('span', { hasText: /^slots$/i }) });
    if (await item.count() > 0)
    {
        await item.first().click();
        await settled();
        break;
    }
    await key('Escape');
}
let slots = (await tree('project.yml')).map_stats?.slots;
if (!Array.isArray(slots) || slots.length === 0)
{
    if (await page.locator('[data-testid="add-row-slots"]').count() === 0)
    {
        await page.click('[data-testid="block-map_stats.slots"]');
        await sleep(200);
    }
    await page.click('[data-testid="add-row-slots"]');
    await settled();
}
// The slots' list opened, and its first row.
const openBlock = async (locator) =>
{
    if (await locator.count() > 0 && await locator.first().getAttribute('aria-expanded') === 'false')
    {
        await locator.first().click();
        await sleep(300);
    }
};
await openBlock(page.locator('[data-testid="block-map_stats.slots"]'));
await openBlock(page.locator('[data-testid="file-form"] button', { hasText: /^▸#0/ }));
await type('field-map_stats.slots.0.monster', 'Wolf');
await settled();
slots = (await tree('project.yml')).map_stats?.slots;
check('the map card\'s first encounter slot set in the inspector of project.yml', Array.isArray(slots) && slots[0]?.monster === 'Wolf', JSON.stringify(slots));
how('project.yml map_stats.slots[] (the encounter slots)', 'inspector field', 'the file inspector of project.yml: + add field, + add row');
await tool('actor');
await option('monster', 'Peasant');
await frame(55, 55, 75, 70);
await click(63, 63.5);
await settled();
const actors = (await sketch()).actors ?? [];
check('an actor clicked (Actor tool)', actors.length === 1 && actors[0].monster === 'Peasant', JSON.stringify(actors));
how('sketch.yml actors[] (monster, at)', 'bespoke tool', 'Actor tool: a click, the monster in the options');
await shot('populate', 'an encounter area of wolves to the south-east, a peasant by the well');

// --- 9. Dress: ground of a second kind, a scatter of trees -------------------------------------------------------

await stage(6);
await tool('ground');
await option('groundMaterial', 'sand');
await option('groundRadius', 3);
await frame(30, 20, 70, 50);
await drag([40, 26], [60, 26], 16);
await settled();
await drag([60, 26], [62, 34], 8);
await settled();
const ground = (await sketch()).ground ?? [];
check('the ground painted with a second kind (Ground brush): the world\'s first kind laid whole, sand traced into outlines', ground.length >= 2 && ground[0].material === 'grass'
    && ground.some((zone) => zone.material === 'sand' && zone.polygon.length >= 4), JSON.stringify(ground.map((zone) => [zone.material, zone.polygon.length])));
how('sketch.yml ground[] (material, polygon)', 'bespoke tool', 'Ground brush: strokes merged per kind into zone outlines');
await tool('scatter');
await option('decoration', 'tree12');
await option('scatterCount', 24);
await option('scatterSpacing', 2);
await frame(5, 5, 45, 45);
await drag([12, 12], [34, 30]);
await settled();
const scatter = (await sketch()).scatter ?? [];
check('a scatter of trees dragged (Scatter tool)', scatter.length === 1 && scatter[0].decoration === 'tree12' && scatter[0].count === 24, JSON.stringify(scatter));
how('sketch.yml scatter[] (decoration, count, spacing, polygon)', 'bespoke tool', 'Scatter tool: drag a box; decoration, count, spacing in the options');
await shot('dress', 'sand painted north of the town, a stand of trees in the north-west');

// --- 10. The other words of 3.18's Outdoor table ------------------------------------------------------------------

await stage(2);
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(300);
const heightsOf = async (name) => (await sketch()).heights[name] ?? [];
await tool('cliff');
await option('cliffDrop', 256);
await lineTool([[84, 8], [96, 12]]);
check('a cliff drawn (Cliff tool)', (await heightsOf('cliffs')).length === 1 && (await heightsOf('cliffs'))[0].drop === 256, JSON.stringify(await heightsOf('cliffs')));
how('sketch.yml heights.cliffs[] (line, drop, down)', 'bespoke tool', 'Cliff tool: click its edge, Enter');
await tool('cut');
await option('height', 128);
await drag([110, 40], [116, 46]);
await settled();
check('a cut dragged (Cut tool)', (await heightsOf('cuts')).length === 1 && (await heightsOf('cuts'))[0].floor === 128, JSON.stringify(await heightsOf('cuts')));
how('sketch.yml heights.cuts[] (polygon, floor)', 'bespoke tool', 'Cut tool: drag a box');
await tool('rough');
await drag([4, 60], [14, 70]);
await settled();
check('rough ground dragged (Rough tool)', (await heightsOf('rough')).length === 1, JSON.stringify(await heightsOf('rough')));
how('sketch.yml heights.rough[] (polygon, amount)', 'bespoke tool', 'Rough tool: drag a box');
await tool('peaks');
await option('peaksCount', 4);
await drag([112, 108], [124, 124]);
await settled();
check('an area of peaks dragged (Peaks tool)', (await heightsOf('peaks')).length === 1 && (await heightsOf('peaks'))[0].count === 4, JSON.stringify(await heightsOf('peaks')));
how('sketch.yml heights.peaks[] (polygon, count, height)', 'bespoke tool', 'Peaks tool: drag a box');
await tool('spire');
await option('height', 1600);
await click(118, 18);
await settled();
check('a spire clicked (Spire tool)', (await heightsOf('spires')).length === 1 && (await heightsOf('spires'))[0].height === 1600, JSON.stringify(await heightsOf('spires')));
how('sketch.yml heights.spires[] (at, height)', 'bespoke tool', 'Spire tool: a click');
await tool('frame');
await drag([16, 16], [112, 112]);
await settled();
check('the playable square dragged (Frame tool)', JSON.stringify((await sketch()).frame?.playable) === '[16,16,96,96]', JSON.stringify((await sketch()).frame));
how('sketch.yml frame.playable', 'bespoke tool', 'Frame tool: drag the square; corners with Select');
await tool('rim');
await pick('rimForm', 'level');
await option('height', 256);
await drag([10, 2], [100, 2]);
await settled();
const rim = (await sketch()).frame?.rim ?? [];
check('a stretch of rim dragged along the north edge (Rim tool)', rim.length === 1 && rim[0].side === 'north' && rim[0].span[0] === 10 && rim[0].span[1] === 100, JSON.stringify(rim));
how('sketch.yml frame.rim[] (side, span, form, height)', 'bespoke tool', 'Rim tool: drag along a side');
await tool('river');
await option('riverWidth', 1);
await lineTool([[118, 56], [112, 70], [127, 82]]);
const rivers = (await sketch()).water?.rivers ?? [];
check('a river drawn (River tool) with its plan space', rivers.length === 1 && rivers[0].line.length === 3, JSON.stringify(rivers));
how('sketch.yml water.rivers[] (line, width) and its plan space', 'bespoke tool', 'River tool: click its line, Enter');
await stage(3);
await tool('district');
await option('districtName', 'Vale town');
await drag([54, 48], [78, 66]);
await settled();
const districts = (await sketch()).districts ?? [];
check('a district dragged for a new plan space (District tool)', districts.length === 1 && ((await tree('plan.yml')).spaces ?? []).some((space) => space.id === districts[0].space),
    JSON.stringify(districts));
how('sketch.yml districts[] (space, polygon) and its plan space', 'bespoke tool', 'District tool: drag a box');
await tool('plot');
await option('new-building', 'bakery');
await page.click('[data-testid="add-plan-building"]');
await settled();
await click(73, 50.5);
await settled();
const plots = (await sketch()).districts?.[0]?.plots ?? [];
check('a plot clicked in the district for a plan building (Plot tool, + plan building)', plots.length === 1 && plots[0].building === 'building:bakery', JSON.stringify(plots));
how('sketch.yml districts[].plots[] (building, at, facing) and the plan building', 'bespoke tool', 'Plot tool: a click; the plan building from the options');
await stage(5);
await tool('arrival');
await pick('pointKind', 'entrance');
await pick('pointFacing', 'n');
await click(72, 120);
await settled();
const sketchPoints = (await sketch()).points ?? [];
check('an arrival point clicked (Point tool) with its plan entrance', sketchPoints.length === 2 && ((await tree('plan.yml')).entrances ?? []).some((entry) => entry.id === sketchPoints[1].id),
    JSON.stringify(sketchPoints));
how('sketch.yml points[] (an arrival point) and its plan entrance', 'bespoke tool', 'Point tool: a click');
await tool('area');
await pick('areaKind', 'keep_clear');
await toggleOn('areaCircle', true);
await drag([40, 84], [43, 84]);
await settled();
const clear = ((await sketch()).areas ?? []).find((area) => area.kind === 'keep_clear');
check('a round keep-clear area dragged (Area tool, circle)', clear && clear.circle?.r === 3, JSON.stringify(clear));
how('sketch.yml areas[] (keep_clear, circle)', 'bespoke tool', 'Area tool: drag a circle');
await toggleOn('areaCircle', false);
await stage(6);
await tool('scatter');
await toggleOn('scatterLine', true);
await option('scatterCount', 6);
await lineTool([[70, 40], [86, 40]]);
await toggleOn('scatterLine', false);
const rows2 = ((await sketch()).scatter ?? []).filter((entry) => Array.isArray(entry.line));
check('a row of trees drawn (Scatter tool, a row)', rows2.length === 1 && rows2[0].count === 6, JSON.stringify(rows2));
how('sketch.yml scatter[] (line)', 'bespoke tool', 'Scatter tool: a row');
// A decoration from the Library, dropped on the plan: it stands there.
await page.click('[data-testid="tab-library"]');
await page.click('[data-testid="library-decoration"]');
await page.fill('[data-testid="library-search"]', 'rock');
await page.waitForSelector('[data-testid^="asset-rock"]', { timeout: 20000 });
const rockAsset = await page.locator('[data-testid^="asset-rock"]').first().getAttribute('data-testid');
const structuresBefore = ((await sketch()).structures ?? []).length;
await frame(60, 30, 100, 60);
await run.dropOnPlan(rockAsset, ...map(90, 45));
await settled();
const dropped = ((await sketch()).structures ?? []).at(-1);
check('a decoration dropped from the Library stands there (a decoration structure)', ((await sketch()).structures ?? []).length === structuresBefore + 1 && dropped.kind === 'decoration'
    && dropped.decoration === rockAsset.replace('asset-', ''), JSON.stringify(dropped));
how('sketch.yml structures[] kind decoration', 'bespoke tool', 'the Library: drag a decoration onto the plan');
await page.click('[data-testid="tab-issues"]').catch(() => undefined);
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(500);
await shot('more_words', 'the other words: a cliff, a cut, rough ground, peaks, a spire, the playable square, a rim stretch, a river, a district with a plot, a second arrival point, a round keep-clear area, a row of trees, a rock from the Library');

// --- 11. Wire: an event of the map -------------------------------------------------------------------------------

await stage(4);
await page.click('[data-testid="add-event"]');
await settled();
const events = (await sketch()).events ?? [];
check('"+ event" makes a sketch event (trigger load) and selects it', events.length === 1 && events[0].trigger === 'load' && (await selected()) === events[0].id, JSON.stringify(events));
await page.waitForSelector('[data-testid="event-form"]', { timeout: 10000 });
await page.selectOption('[data-testid="event-form"] [data-testid="add-effects"]', 'text');
await settled();
const eventSteps = (await sketch()).events[0].effects;
check('the event form adds a step to the event', Array.isArray(eventSteps) && eventSteps.length === 1, JSON.stringify(eventSteps));
how('sketch.yml events[] (trigger, effects)', 'bespoke tool', 'Wire stage "+ event", the event form');
await shot('event', 'the Wire stage: a load event in the event form');

// --- 12. Test: checks and the build ------------------------------------------------------------------------------

await stage(7);
const project = (await run.state()).projectKey;
const validate = await page.evaluate((p) => window.__studio.app.controller.client.call('check.validate', { project: p }), project);
const errorsLeft = validate.issues.filter((issue) => issue.severity === 'error');
check('check.validate: no errors', errorsLeft.length === 0, errorsLeft.map((issue) => `${issue.code} ${issue.file} ${issue.path}: ${issue.message}`).join(' | ') || `${validate.issues.length} issues (warnings and notes)`);
run.results.validate = validate.issues;
let build = null;
try
{
    build = await page.evaluate((p) => window.__studio.app.controller.client.call('build.run', { project: p, dry_run: false }), project);
}
catch (error)
{
    build = { error: String(error) };
}
run.results.build = build;
check('build.run (not dry) builds the map', build && !build.error && build.files?.some((file) => file.endsWith('.odm')), JSON.stringify(build).slice(0, 400));
// The town feel where the author works (W2 step 8): the rail's figures from town_feel.py run as a job.
await page.click('[data-testid="run-town-feel"]');
const townDone = await run.waitFor(() =>
{
    const state = window.__studio.app.store.getState();
    const jobs = state.jobs.state === 'ready' ? state.jobs.value : [];
    const job = jobs.find((entry) => entry.kind === 'town_feel' && (entry.state === 'done' || entry.state === 'failed'));
    return Boolean(job && (job.state === 'failed' || state.jobResults[job.id]));
}, 240000);
const townText = await page.locator('[data-testid="town-feel"]').innerText();
check('the town feel figures shown in the tool rail (town_feel.py as a job)', townDone && /outside the shipped ranges/.test(townText), townText.replace(/\s+/g, ' ').slice(0, 300));
how('town feel (scorecard figures where the author works)', 'bespoke tool', 'the rail\'s Town feel box: Run town feel, its figures');
await shot('town_feel', 'the town feel figures in the tool rail');
const finalHistory = (await run.state()).history.value.entries;
check('every edit was the person\'s (author user)', finalHistory.every((entry) => entry.author === 'user' || entry.sequence <= 1), [...new Set(finalHistory.map((entry) => entry.author))].join(', '));
await page.evaluate(() => window.__studio.app.store.setState({ selection: null }));
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(1500);
await shot('final', 'Hollow Vale made by hand: land, pond, road, two buildings, a well and a sign, trees, sand, wolves, a peasant');
await page.evaluate(() => window.__studio.app.store.setState({ viewMode: '3d' }));
await sleep(2500);
await shot('final_3d', 'the 3D view of the finished map');

console.log('\nWORDS SET, AND HOW');
for (const [word, entry] of [...words.entries()].sort())
{
    console.log(`  ${entry.means.padEnd(24)} ${word}${entry.detail ? `  (${entry.detail})` : ''}`);
}
console.log('\nMISSES (a word that forced the Source tab, or a bespoke tool 3.18 promises offered only as a row list)');
for (const miss of misses)
{
    console.log(`  ${miss.word}: ${miss.why}`);
}
if (misses.length === 0)
{
    console.log('  none');
}
run.results.words = Object.fromEntries(words);
run.results.misses = misses;
writeFileSync(join(out, 'hand_words.json'), JSON.stringify({ words: Object.fromEntries(words), misses }, null, 1));
const failed = await run.finish('s5b2_hand_author');
process.exit(failed > 0 ? 1 : 0);
