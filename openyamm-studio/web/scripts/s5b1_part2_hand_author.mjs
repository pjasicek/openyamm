// S5b1 part two, exit test 1 again (S5_BROWSER_EDITOR.md 6.4, F5, W1): a small new dungeon from an EMPTY project made
// in the UI, this time with every word part one listed as a miss: the plan (spaces, links, goals), the map's
// variables, a switch on a block's top, a lift, a mover, a plate, a floor of lava, a ladder, height points, a flight,
// a parapet, a beam and a ceiling level; and the rest of part two: placing in 3D, History's "show as it was", a fix
// from the Issues drawer, monsters, items and sounds from the Library, the map card's slots. Gestures only (clicks and
// drags on the plan and in 3D, keys, the tool options, the inspector, the event form, the switch board); never the
// Source tab, YAML or a command line (the script reads the store to check and to find screen points, and calls
// check.validate and build.run at the end as the verification). Prints every word set and how, and the words still
// forcing the Source tab. A screenshot after each step, in output/s5b1p2_shots/exit/.
//   node scripts/s5b1_part2_hand_author.mjs
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { repo, sleep, stampFolder, startRun } from './exit_common.mjs';

const out = join(repo, 'output', 's5b1p2_shots', 'exit');
const runRoot = stampFolder('hand', 's5b1p2');
const run = await startRun({ out, prefix: 'hand2', roots: [runRoot] });
const { page, check, shot, settled, click, drag, key, frame, type } = run;
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

const tree = async (file) => (await run.files())[file]?.tree ?? {};
const rooms = async () => (await tree('rooms.yml')).rooms ?? [];
const roomOf = async (id) => (await rooms()).find((room) => room.id === id);
const objects = async (list) => (await tree('objects.yml'))[list] ?? [];
const events = async () => (await tree('wiring.yml')).events ?? [];
const plan = async (list) => (await tree('plan.yml'))[list] ?? [];
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
const ensureField = async (name, label) =>
{
    if (await page.locator(`[data-testid="field-${name}"]`).count() > 0)
    {
        return;
    }
    await page.click('[data-testid="add-field"]');
    await sleep(300);
    await page.locator('[role="menuitem"]').filter({ has: page.locator('span', { hasText: new RegExp(`^${label}$`, 'i') }) }).first().click();
    await settled();
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
const allFrame = async () =>
{
    await page.evaluate(() => window.__studio.plan.frameAll());
    await sleep(300);
};

// --- 1. New project -------------------------------------------------------------------------------------------------

await page.goto(`${run.base}/#token=${run.token}`);
await page.waitForSelector('[data-testid="new-project"]', { timeout: 20000 });
await page.click('[data-testid="new-project"]');
await page.fill('[data-testid="new-folder"]', 'sunken_chapel');
await page.fill('[data-testid="new-id"]', 'hchap02');
await page.fill('[data-testid="new-name"]', 'The Sunken Chapel');
await page.fill('[data-testid="new-stats"]', '9432');
await page.click('[data-testid="new-project-make"]');
await run.waitFor(() => window.__studio?.app?.store.getState().project.state === 'ready', 20000);
await settled();
let s = await run.state();
check('an empty project made in the UI opens in Author mode', s.mode === 'author' && (await rooms()).length === 0, s.projectKey);
for (const word of ['project.yml id', 'project.yml name', 'project.yml world', 'project.yml map_stats.id'])
{
    how(word, 'bespoke tool', 'New project form');
}

// --- 2. Plan: spaces (bubbles), names, links, goals ------------------------------------------------------------------

await stage(1);
await frame(-512, -1024, 4096, 2200);
await shot('plan_empty', 'Plan stage: the Space, Plan link and Goal tools on an empty plan');
await tool('space');
await pick('spaceSize', 'S');
// The store's bubble stands off its room on purpose: the room drawn later realises nothing and the Issues drawer's
// fix makes it the store's room.
const bubbles = [['ante', [384, 320], 'room'], ['hall', [1344, 384], 'room'], ['store', [1088, 1800], 'room'], ['stairs', [2176, 320], 'room'],
    ['passage', [2752, 336], 'corridor'], ['crypt', [3456, 320], 'room']];
for (const [, at, kind] of bubbles)
{
    await pick('spaceKind', kind);
    await click(...at);
    await settled();
}
let spaces = await plan('spaces');
check('six planned spaces made by clicks (Space tool)', spaces.length === 6 && spaces.every((space) => Array.isArray(space.at)), spaces.map((space) => `${space.id} ${space.kind} ${JSON.stringify(space.at)}`).join(', '));
how('plan.yml spaces[] (kind, size, at)', 'bespoke tool', 'Space tool: a click on the plan, kind and size in the options');
// The space whose bubble is nearest a point (the Space tool puts a bubble on the 64 grid).
const spaceAt = async (x, y) => (await plan('spaces')).map((space) => ({ id: space.id, d: Math.hypot(space.at[0] - x, space.at[1] - y) }))
    .sort((a, b) => a.d - b.d)[0]?.id;
const ids = {};
for (const [name, at] of bubbles)
{
    ids[name] = await spaceAt(...at);
}
// A bubble dragged: the stair hall's a little further east.
await drag([2176, 320], [2240, 320]);
await settled();
check('a bubble moved by a drag (Space tool)', (await plan('spaces')).find((space) => space.id === ids.stairs)?.at?.[0] === 2240, JSON.stringify((await plan('spaces')).find((space) => space.id === ids.stairs)?.at));
how('plan.yml spaces[].at (moved)', 'bespoke tool', 'Space tool: drag a bubble');
// Names in the inspector.
await tool('select');
for (const [name, at] of [['ante', [384, 320]], ['crypt', [3456, 320]]])
{
    await click(...at);
    check(`a click on a bubble selects the space (${name})`, (await selected()) === ids[name], await selected());
    await ensureField('name', 'Name');
    await type('field-name', name === 'ante' ? 'Antechamber' : 'Crypt of the Abbot');
    await settled();
}
how('plan.yml spaces[].name', 'inspector field', '+ add field, a text');
await tool('planlink');
const linkDrags = [[[384, 320], [1344, 384], 'open'], [[1344, 384], [1088, 1800], 'portcullis'], [[1344, 384], [2240, 320], 'open'],
    [[2240, 320], [2752, 336], 'stairs'], [[2752, 336], [3456, 320], 'door']];
for (const [from, to, kind] of linkDrags)
{
    await pick('planLinkKind', kind);
    await drag(from, to);
    await settled();
}
const links = await plan('links');
check('five plan links made by drags between bubbles (Plan link tool)', links.length === 5 && links.some((link) => link.kind === 'portcullis'), links.map((link) => `${link.from}→${link.to} ${link.kind}`).join(', '));
how('plan.yml links[] (from, to, kind)', 'bespoke tool', 'Plan link tool: a drag from bubble to bubble, kind in the options');
await tool('goal');
await pick('goalKind', 'kill');
await option('goalWhat', 'the goblin chief');
await click(3456, 320);
await settled();
await pick('goalKind', 'reach');
await option('goalWhat', 'the crypt');
await click(3456, 320);
await settled();
const goals = await plan('goals');
check('two goals on the crypt (Goal tool)', goals.length === 2 && goals.every((goal) => goal.space === ids.crypt), JSON.stringify(goals));
how('plan.yml goals[] (space, kind, what)', 'bespoke tool', 'Goal tool: a click on a bubble, kind and what in the options');
// A link's lock in the inspector: the passage door wants the chapel open.
await tool('select');
await click((2752 + 3456) / 2, (336 + 320) / 2);
const doorLink = links.find((link) => link.kind === 'door');
check('a click on a link selects it', (await selected()) === doorLink?.id, await selected());
await ensureField('purpose', 'Purpose');
await type('field-purpose', 'the crypt door, barred until the lever in the hall opens the chapel');
await settled();
how('plan.yml links[].purpose', 'inspector field', '+ add field');
// The plan's own words with nothing selected: its purpose, and a key (a list of objects with ids: op add, the core's id).
await page.evaluate(() => window.__studio.app.store.setState({ selection: null }));
await page.waitForSelector('[data-testid="file-form"]', { timeout: 10000 });
await ensureField('purpose', 'Purpose');
await type('field-purpose', 'The abbot\'s crypt under the old chapel: kill the goblin chief who nests there.');
await settled();
await ensureField('keys', 'Keys');
if (await page.locator('[data-testid="add-row-keys"]').count() === 0)
{
    await page.click('[data-testid="block-keys"]');
}
await page.click('[data-testid="add-row-keys"]');
await settled();
const keys = await plan('keys');
check('the file inspector: the plan\'s purpose and a key (its id from the core)', (await tree('plan.yml')).purpose?.startsWith('The abbot') && keys.length === 1 && /^key:/.test(keys[0].id ?? ''),
    JSON.stringify({ purpose: (await tree('plan.yml')).purpose, keys }));
if (keys.length === 1)
{
    // The row opened, its "+ add field", How.
    await page.locator('[data-testid="file-form"] button', { hasText: keys[0].id }).first().click();
    await sleep(300);
    // The row's own "+ add field" (the form has one per object): the one whose menu offers How.
    const adders = page.locator('[data-testid="file-form"] [data-testid="add-field"]');
    for (let i = 0; i < await adders.count(); ++i)
    {
        await adders.nth(i).click();
        await sleep(250);
        const item = page.locator('[role="menuitem"]').filter({ has: page.locator('span', { hasText: /^how$/i }) });
        if (await item.count() > 0)
        {
            await item.first().click();
            await settled();
            break;
        }
        await key('Escape');
    }
    await type('field-keys.0.how', 'the lever in the hall opens the chapel');
    await settled();
}
check('the key says how it is found', (await plan('keys'))[0]?.how === 'the lever in the hall opens the chapel', JSON.stringify(await plan('keys')));
how('plan.yml purpose, keys[] (and the other file words: height_bands, states ...)', 'inspector field', 'the file inspector with nothing selected: + add field, + add row');
await shot('plan', 'Plan: six bubbles (the store\'s off to the south), five links by kind, two goals on the crypt; the plan\'s own words in the inspector');

// --- 3. Shape: rooms over the bubbles realise their spaces -----------------------------------------------------------

await stage(2);
const drawRoom = async (corners, floor, ceiling) =>
{
    const xs = corners.map((c) => c[0]);
    const ys = corners.map((c) => c[1]);
    await frame(Math.min(...xs) - 192, Math.min(...ys) - 192, Math.max(...xs) + 192, Math.max(...ys) + 192);
    await option('floor', floor);
    await option('ceiling', ceiling);
    for (const corner of corners)
    {
        await click(...corner);
    }
    await key('Enter');
    await settled();
    const status = await page.locator('[data-testid="edit-status"]').textContent();
    console.log(`room ${JSON.stringify(corners[0])}: ${status} · hint ${(await run.state()).hint}`);
};
await tool('room');
await drawRoom([[0, 0], [768, 0], [768, 640], [0, 640]], 0, 384);
await drawRoom([[832, -128], [1856, -128], [1856, 896], [832, 896]], 0, 512);
await drawRoom([[832, 960], [1344, 960], [1344, 1472], [832, 1472]], 0, 320);
await drawRoom([[1920, 0], [2432, 0], [2432, 640], [1920, 640]], 0, 448);
await drawRoom([[3072, -192], [3840, -192], [3840, 832], [3072, 832]], -256, 320);
let list = await rooms();
const roomAtCorner = (x, y) => list.find((room) => Array.isArray(room.outline) && room.outline[0][0] === x && room.outline[0][1] === y)?.id;
const [ante, hall, store, stairs, crypt] = [roomAtCorner(0, 0), roomAtCorner(832, -128), roomAtCorner(832, 960), roomAtCorner(1920, 0), roomAtCorner(3072, -192)];
check('rooms drawn over bubbles realise their spaces', list.find((room) => room.id === ante)?.space === ids.ante && list.find((room) => room.id === crypt)?.space === ids.crypt
    && list.find((room) => room.id === hall)?.space === ids.hall && list.find((room) => room.id === stairs)?.space === ids.stairs, list.map((room) => `${room.id}:${room.space ?? '-'}`).join(', '));
how('rooms.yml rooms[].space', 'bespoke tool', 'Room tool: a room drawn over a planned bubble realises it');
check('the store, drawn away from its bubble, realises nothing yet', !list.find((room) => room.id === store)?.space, JSON.stringify(list.find((room) => room.id === store)));
await tool('corridor');
await option('width', 192);
await option('floor', -256);
await option('ceiling', 64);
await frame(1800, -256, 3200, 900);
await lineTool([[2496, 320], [2752, 352], [3008, 320]]);
list = await rooms();
const corridor = list.find((room) => Array.isArray(room.path))?.id;
check('the corridor through the passage bubble realises it', list.find((room) => room.id === corridor)?.space === ids.passage, JSON.stringify(list.find((room) => room.id === corridor)));
await tool('stairs');
await option('rise', -256);
await option('steps', 8);
await drag([1990, 320], [2380, 320]);
await settled();
await tool('opening');
await allFrame();
for (const [from, to] of [[[700, 320], [900, 320]], [[1100, 850], [1100, 1010]], [[1800, 320], [1980, 320]], [[2380, 320], [2540, 320]], [[2960, 320], [3140, 320]]])
{
    await drag(from, to);
    await settled();
}
check('five openings', ((await tree('rooms.yml')).openings ?? []).length === 5, String(((await tree('rooms.yml')).openings ?? []).length));

// The fix from the Issues drawer: the store becomes the room of its planned space.
await page.getByRole('tab', { name: /^Issues \d/ }).click();
await page.getByRole('button', { name: 'Check again' }).click();
await run.waitFor(() => window.__studio.app.store.getState().validation.state === 'ready', 30000);
await sleep(300);
const fixButton = page.locator('button[data-testid^="fix-"]', { hasText: `make ${store} the room of ${ids.store}` });
const fixOffered = await fixButton.count() > 0;
check('the Issues drawer offers the core\'s fix for the store (no space)', fixOffered, fixOffered ? '' : await page.locator('[data-testid^="fix-"]').allTextContents().then((texts) => texts.join(' | ')));
await shot('issue_fix', 'Issues: "the room realises no space" with the core\'s fixes as buttons');
if (fixOffered)
{
    await fixButton.first().click();
    await settled();
}
check('the fix made the store the room of its space', (await roomOf(store))?.space === ids.store, JSON.stringify(await roomOf(store)));
how('Issues: a fix as operations (rooms[].space)', 'bespoke tool', 'Issues drawer: the core\'s fix button');

// A level, a sunken level, pillars, a dais (part one's tools).
await tool('select');
await frame(768, -256, 1920, 960);
await click(1100, 200);
await tool('level');
await option('levelRise', 64);
await drag([1472, 448], [1792, 832]);
await settled();
await tool('select');
await frame(3008, -256, 3904, 896);
await click(3200, 300);
await tool('pillar');
await drag([3264, 0], [3328, 64]);
await settled();
await drag([3264, 576], [3328, 640]);
await settled();
await tool('platform');
await option('platformRise', 48);
await drag([3584, 192], [3776, 448]);
await settled();
await tool('level');
await option('levelRise', -32);
await drag([3136, -160], [3392, -64]);
await settled();
let cryptRoom = await roomOf(crypt);
check('the crypt: two pillars, a dais, a sunken level', cryptRoom?.pillars?.length === 2 && cryptRoom?.platforms?.length === 1 && cryptRoom?.levels?.length === 1,
    JSON.stringify({ pillars: cryptRoom?.pillars?.length, platforms: cryptRoom?.platforms?.length, levels: cryptRoom?.levels }));

// Height points: the store's floor dips in the middle, its ceiling rises over the east half.
await tool('points');
await frame(768, 896, 1408, 1536);
await pick('pointsOn', 'floor');
await option('pointHeight', -32);
await click(1088, 1216);
await settled();
await page.mouse.move(...(await run.at(1088, 1216)));
await sleep(150);
await key('PageUp');
await settled();
let storeRoom = await roomOf(store);
check('Height points: a floor point made by a click and raised by PgUp (-32 to -16)', JSON.stringify(storeRoom?.floor_points) === JSON.stringify([[1088, 1216, -16]]), JSON.stringify(storeRoom?.floor_points));
await pick('pointsOn', 'ceiling');
await option('pointHeight', 48);
await click(1216, 1216);
await settled();
await drag([1216, 1216], [1232, 1200]);
await settled();
storeRoom = await roomOf(store);
check('Height points: a ceiling point made and dragged', JSON.stringify(storeRoom?.ceiling_points) === JSON.stringify([[1232, 1200, 368]]), JSON.stringify(storeRoom?.ceiling_points));
how('rooms.yml rooms[].floor_points', 'bespoke tool', 'Height points tool: click, PgUp/PgDn, drag');
how('rooms.yml rooms[].ceiling_points', 'bespoke tool', 'Height points tool (on the ceiling)');
await shot('points', 'Height points: the store\'s floor dip (-16) and ceiling crown (368) with their heights');

// A flight up to the hall's gallery, a parapet on its rim, a beam across the hall, a ceiling level in the antechamber.
await frame(768, -256, 1920, 960);
await tool('flight');
await drag([1600, 304], [1600, 464]);
await settled();
await tool('parapet');
await option('parapetHeight', 40);
await lineTool([[1488, 816], [1776, 816]]);
await tool('beam');
await option('beamWidth', 32);
await option('beamDepth', 32);
await lineTool([[896, 256], [1792, 256]]);
let hallRoom = await roomOf(hall);
check('a flight, a parapet and a beam in the hall', hallRoom?.flights?.length === 1 && hallRoom?.parapets?.[0]?.height === 40 && hallRoom?.beams?.[0]?.bottom === 448,
    JSON.stringify({ flights: hallRoom?.flights, parapets: hallRoom?.parapets, beams: hallRoom?.beams }));
how('rooms.yml rooms[].flights', 'bespoke tool', 'Flight tool: a drag from the low floor to the higher one');
how('rooms.yml rooms[].parapets', 'bespoke tool', 'Parapet tool: points on the plan, height in the options');
how('rooms.yml rooms[].beams', 'bespoke tool', 'Beam tool: points on the plan, width, depth and underside in the options');
await tool('select');
await frame(-128, -128, 896, 768);
await click(100, 100);
await tool('ceiling');
await option('ceilingRise', 128);
await drag([192, 192], [576, 448]);
await settled();
const anteRoom = await roomOf(ante);
check('a ceiling level in the antechamber (512)', anteRoom?.ceiling_levels?.[0]?.ceiling === 512, JSON.stringify(anteRoom?.ceiling_levels));
how('rooms.yml rooms[].ceiling_levels', 'bespoke tool', 'Ceiling level tool: a box, rise in the options');
await allFrame();
await shot('shape', 'Shape: every room realising its space, the hall\'s gallery with flight, parapet and beam, the crypt\'s blocks');

// --- 4. Build: doors, switches (one on the dais's top), a lift, a mover, a plate, lava, a ladder, the exit ----------

await stage(3);
await allFrame();
await tool('door');
await page.click('[data-testid="door-portcullis"]');
const openings = (await tree('rooms.yml')).openings;
const layoutOpenings = (await run.state()).layout.value.openings;
const middleOf = (from, to) =>
{
    const opening = openings.find((o) => (o.from === from && o.to === to) || (o.from === to && o.to === from));
    const placed = layoutOpenings.find((o) => o.id === opening?.id);
    return placed?.a ? [(placed.a[0] + placed.b[0]) / 2, (placed.a[1] + placed.b[1]) / 2] : null;
};
const storeDoorAt = middleOf(hall, store);
const cryptDoorAt = middleOf(corridor, crypt);
await click(...storeDoorAt);
await settled();
await page.click('[data-testid="door-wooden"]');
await click(...cryptDoorAt);
await settled();
const doors = await objects('doors');
const portcullis = doors.find((door) => door.kind === 'slide_up')?.id;
const cryptDoor = doors.find((door) => door.kind === 'hinged')?.id;
check('two doors', Boolean(portcullis && cryptDoor), JSON.stringify(doors));

await tool('switch');
await pick('switchKind', 'lever');
await frame(768, -256, 1920, 1536);
await click(1500, 893);
await settled();
const lever = (await objects('switches'))[0];
check('a lever on the hall\'s north wall', lever?.kind === 'lever', JSON.stringify(lever));
// A plate switch on the dais's top: the platform gets an id from the core first.
await pick('switchKind', 'plate');
await frame(3008, -256, 3904, 896);
await click(3680, 320);
await settled();
const daisSwitch = (await objects('switches')).find((entry) => entry.side === 'top');
cryptRoom = await roomOf(crypt);
check('Switch tool: a plate on the dais\'s top (block, side top, at), the dais named by the core', daisSwitch?.block === cryptRoom?.platforms?.[0]?.id && daisSwitch?.kind === 'plate'
    && Array.isArray(daisSwitch?.at), JSON.stringify({ daisSwitch, dais: cryptRoom?.platforms?.[0] }));
how('objects.yml switches[].block, side: top, at', 'bespoke tool', 'Switch tool: a click on a platform (its id given by the core, op name)');
await shot('dais_switch', 'Switch tool: a plate switch on the dais\'s top in the crypt');

// The lift in the hall's north-west corner.
await frame(768, -256, 1920, 960);
await tool('lift');
await option('liftTravel', 256);
await drag([896, -64], [1088, 128]);
await settled();
const lift = (await objects('lifts'))[0];
check('Lift tool: a lift in the hall (box, travel 256)', lift?.room === hall && lift?.travel === 256 && JSON.stringify(lift?.size) === '[192,192]', JSON.stringify(lift));
how('objects.yml lifts[] (room, at, size, travel)', 'bespoke tool', 'Lift tool: a box on the plan, travel in the options');
// A ladder up onto the gallery.
await tool('ladder');
await drag([1744, 380], [1744, 520]);
await settled();
const ladder = (await objects('ladders'))[0];
check('Ladder tool: a ladder from the hall floor up onto the gallery (64)', ladder?.room === hall && ladder?.height === 64 && ladder?.facing === 90, JSON.stringify(ladder));
how('objects.yml ladders[] (room, at, facing, height)', 'bespoke tool', 'Ladder tool: a drag from the foot up onto what it climbs');
await shot('lift_ladder', 'Build: the lift (blue) and the ladder up to the gallery');

// A mover and a plate in the antechamber.
await frame(-128, -128, 896, 768);
await tool('mover');
await option('moverHeight', 32);
await option('moverTravelZ', 128);
await drag([64, 448], [192, 576]);
await settled();
await tool('plate');
await drag([256, 448], [384, 576]);
await settled();
const mover = (await objects('movers'))[0];
const plate = (await objects('plates'))[0];
check('Mover and Plate tools: a rising block and a pressure plate in the antechamber', mover?.height === 32 && JSON.stringify(mover?.travel) === '[0,0,128]' && plate?.room === ante,
    JSON.stringify({ mover, plate }));
how('objects.yml movers[] (room, at, size, height, travel)', 'bespoke tool', 'Mover tool: a box, height and travel in the options');
how('objects.yml plates[] (room, at, size)', 'bespoke tool', 'Plate tool: a box');

// Lava in the crypt's sunken level.
await frame(3008, -256, 3904, 896);
await tool('floor');
await pick('floorKind', 'lava');
await click(3264, -112);
await settled();
const lava = (await objects('floors'))[0];
cryptRoom = await roomOf(crypt);
check('Floor tool: the sunken level named by the core and made lava', lava?.kind === 'lava' && lava?.of === cryptRoom?.levels?.[0]?.id, JSON.stringify({ lava, level: cryptRoom?.levels?.[0] }));
how('objects.yml floors[] (of, kind)', 'bespoke tool', 'Floor tool: a click on a level (its id from the core), kind in the options');
await shot('lava', 'Build: the crypt\'s sunken level as lava (its id given by the core)');

await tool('exit');
await option('new-neighbour', 'oute3');
await option('arrival-0', -9728);
await option('arrival-1', -11319);
await option('arrival-2', 160);
await page.click('[data-testid="add-neighbour"]');
await settled();
await frame(-256, -128, 832, 768);
await click(4, 320);
await settled();
check('the exit on the antechamber\'s west wall', (await objects('exits')).length === 1, JSON.stringify(await objects('exits')));

// --- 5. Wire: variables, the lever, the dais plate to the lift, the floor plate to the mover ----------------------

await stage(4);
await allFrame();
const layoutNow = (await run.state()).layout.value;
const leverThing = layoutNow.things.find((thing) => thing.id === lever.id);
check('view.layout places the lever on its wall (kind switch, facing into the room)', leverThing?.kind === 'switch' && leverThing.facing === 270 && leverThing.at[1] === 896, JSON.stringify(leverThing));
const daisThing = layoutNow.things.find((thing) => thing.id === daisSwitch?.id);
check('view.layout places the dais plate on the dais\'s top', daisThing?.kind === 'switch' && daisThing.at[2] > -256, JSON.stringify(daisThing));
await page.fill('[data-testid="variable-new"]', 'chapel_open');
await page.click('[data-testid="variable-add"]');
await settled();
await page.fill('[data-testid="variable-new"]', 'chapel_opn');
await page.click('[data-testid="variable-add"]');
await settled();
check('two variables declared on the switch board', JSON.stringify((await tree('wiring.yml')).variables) === '["chapel_open","chapel_opn"]', JSON.stringify((await tree('wiring.yml')).variables));
// One taken out again.
await page.locator('[data-testid="variable-chapel_opn"] button[title^="take"]').click();
await settled();
check('a variable taken out', JSON.stringify((await tree('wiring.yml')).variables) === '["chapel_open"]', JSON.stringify((await tree('wiring.yml')).variables));
how('wiring.yml variables', 'bespoke tool', 'switch board: + variable, rename, ×');
await shot('variables', 'Wire: the map\'s variables above the switch board');

// The lever toggles the portcullis (L), and its event sets the variable.
await tool('select');
await frame(768, -256, 1920, 1536);
await click(leverThing.at[0], leverThing.at[1]);
check('a click selects the lever', (await selected()) === lever.id, await selected());
await key('KeyL');
await click(...storeDoorAt);
await settled();
await key('Escape');
let leverEvent = (await events()).find((event) => event.source === lever.id);
check('L: the lever toggles the portcullis', leverEvent?.toggles?.includes(portcullis), JSON.stringify(leverEvent));
await click(leverThing.at[0], leverThing.at[1]);
await page.click(`text=${leverEvent.id}`);
await sleep(300);
await page.click('[data-testid="add-sets"]');
await settled();
leverEvent = (await events()).find((event) => event.source === lever.id);
check('the event form: the lever sets chapel_open (picked by name)', leverEvent?.sets?.map_var === 'chapel_open', JSON.stringify(leverEvent));
how('wiring.yml events[].sets {map_var: <variable>}', 'bespoke tool', 'event form: + sets, the variable picked by name');
await page.click('[data-testid="field-once"]');
await settled();

// The crypt door opens only once the chapel is open.
await allFrame();
await click(...cryptDoorAt);
await page.click('[data-testid="new-event-door"]');
await settled();
await page.selectOption('[data-testid="add-condition"]', 'map_var');
await settled();
await ensureField('locked_text', 'Locked text').catch(() => undefined);
if (await page.locator('[data-testid="field-locked_text"]').count() > 0)
{
    await type('field-locked_text', 'The crypt door is barred. Somewhere a lever must open the chapel.');
    await settled();
}
const doorEvent = (await events()).find((event) => event.source === cryptDoor && event.preset === 'door');
check('the crypt door\'s event is locked by the variable', doorEvent?.condition?.map_var === 'chapel_open' && typeof doorEvent?.locked_text === 'string', JSON.stringify(doorEvent));
how('wiring.yml events[].condition {map_var: <variable>}', 'bespoke tool', 'event form: + condition map variable, picked by name');
await shot('door_condition', 'the crypt door\'s event: locked until chapel_open is set, with its locked text');

// The dais plate raises the lift (L across the map).
await frame(768, -256, 3904, 960);
await click(daisThing.at[0], daisThing.at[1]);
check('a click selects the dais switch', (await selected()) === daisSwitch.id, await selected());
await key('KeyL');
await click(992, 32);
await settled();
await key('Escape');
const daisEvent = (await events()).find((event) => event.source === daisSwitch.id);
check('L: the dais switch toggles the lift', daisEvent?.toggles?.includes(lift.id), JSON.stringify(daisEvent));
// The floor plate moves the mover (a step event).
await frame(-128, -128, 896, 768);
await click(320, 512);
check('a click selects the plate', (await selected()) === plate.id, await selected());
await key('KeyL');
await click(128, 512);
await settled();
await key('Escape');
const plateEvent = (await events()).find((event) => event.source === plate.id);
check('L: the plate moves the mover when stepped on (trigger step)', plateEvent?.trigger === 'step' && plateEvent?.toggles?.includes(mover.id), JSON.stringify(plateEvent));
how('wiring.yml events[] of a plate and a block switch (toggles a lift, a mover)', 'bespoke tool', 'L: the link gesture onto a lift or a mover');
await page.click('[data-testid="view-board"]').catch(() => undefined);
await sleep(400);
await shot('board', 'the switch board: the lever, the dais plate and the floor plate across the doors, lift and mover');
await page.click('[data-testid="view-board"]').catch(() => undefined);
await sleep(300);

// --- 6. Populate: spawns with the card's slots, a monster and an item from the Library -----------------------------

await stage(5);
await frame(3008, -256, 3904, 896);
await tool('spawn');
await run.waitFor(() => (document.querySelector('[data-testid="option-spawnSlot"]')?.closest('label')?.textContent ?? '').includes('BGoblin'), 10000);
const slotLabel = await page.locator('[data-testid="option-spawnSlot"]').locator('xpath=ancestor::label').textContent();
check('the Spawn tool names the map card\'s slots (project.resolve card)', slotLabel.includes('1 BRat') && slotLabel.includes('2 BGoblin'), slotLabel);
await pick('spawnSlot', 2);
await click(3456, 640);
await settled();
const spawn = (await objects('spawns'))[0];
await tool('select');
await click(3456, 640);
await run.waitFor(() => Boolean(document.querySelector('[data-testid="slot-note"]')), 10000);
const slotNote = await page.locator('[data-testid="slot-note"]').textContent().catch(() => '');
check('the inspector names the spawn\'s slot from the map card', slotNote.includes('BGoblin'), slotNote);
how('objects.yml spawns[].slot (with the card\'s monster)', 'bespoke tool', 'Spawn tool options and the inspector name the slot\'s monster');
await shot('spawn_slot', 'the spawn point\'s slot 2: BGoblin, from map_stats.txt row of 6d01.blv');
await page.click('[data-testid="tab-library"]');
await page.click('[data-testid="library-monster"]');
await page.fill('[data-testid="library-search"]', 'goblin');
await page.waitForSelector('[data-testid="asset-monster-271"]', { timeout: 15000 });
await shot('library_monsters', 'the Library\'s monsters: goblins by row number, level and hit points');
await run.dropOnPlan('asset-monster-271', 3300, 400);
await settled();
const goblin = (await objects('monsters'))[0];
check('a goblin dragged from the Library (monster 271)', goblin?.monster === 271, JSON.stringify(goblin));
how('objects.yml monsters[] (monster by number)', 'bespoke tool', 'Library: Monsters, a drag onto the plan');
await page.click('[data-testid="library-item"]');
await page.fill('[data-testid="library-search"]', 'potion');
await page.waitForSelector('[data-testid^="asset-"]', { timeout: 15000 });
const itemRow = await page.locator('[data-testid^="asset-"]').first().getAttribute('data-testid');
await frame(768, 896, 1408, 1536);
await run.dropOnPlan(itemRow, 960, 1360);
await settled();
const item = (await objects('items'))[0];
check('an item dragged from the Library', typeof item?.item === 'number', JSON.stringify(item));
how('objects.yml items[] (item by number)', 'bespoke tool', 'Library: Items, a drag onto the plan');

// --- 7. Dress: a sound from the Library, a torch and a light placed in 3D, textures ------------------------------

await stage(6);
await page.click('[data-testid="library-sound"]');
await page.fill('[data-testid="library-search"]', 'drip');
await page.waitForSelector('[data-testid="asset-waterdrip"]', { timeout: 15000 });
await frame(3008, -256, 3904, 896);
await run.dropOnPlan('asset-waterdrip', 3700, 700);
await settled();
const sound = (await objects('sounds'))[0];
check('a sound dragged from the Library (waterdrip)', sound?.sound === 'waterdrip', JSON.stringify(sound));
how('objects.yml sounds[] (sound)', 'bespoke tool', 'Library: Sounds, a drag onto the plan');
await tool('light');
await option('lightRadius', 768);
for (const at of [[384, 320], [1344, 384], [3328, 320]])
{
    await click(...at);
    await settled();
}
// Placing in 3D: the crypt framed in the 3D view with the cutaway, a light on its floor and a torch on its east wall.
await page.locator('header [aria-label="Views"] button', { hasText: 'Split' }).click();
await sleep(400);
await tool('select');
await click(3200, 300);
await page.mouse.move(...(await run.at(3200, 300)));
await key('KeyF');
await page.locator('button', { hasText: /^cutaway$/ }).click().catch(() => undefined);
await sleep(2500);
const in3d = async (x, y, z) => page.evaluate(([px, py, pz]) =>
{
    const view = window.__studio.viewport;
    const at = view.clientOf(px, py, pz);
    const pick = at ? view.pickClient(at[0], at[1]) : null;
    return { at, owner: pick?.owner ?? null, point: pick?.point ?? null };
}, [x, y, z]);
await tool('light');
const floorAim = await in3d(3456, 200, -256);
const lightsBefore = (await objects('lights')).length;
if (floorAim.at)
{
    await page.mouse.click(floorAim.at[0], floorAim.at[1]);
    await settled();
}
check('placing in 3D: a light by a click on the crypt\'s floor in the 3D view', (await objects('lights')).length === lightsBefore + 1, JSON.stringify(floorAim));
await tool('decoration');
await option('decoration', 'torch01');
const wallAim = await in3d(3840, 320, -100);
const decorationsBefore = (await objects('decorations')).length;
if (wallAim.at)
{
    await page.mouse.click(wallAim.at[0], wallAim.at[1]);
    await settled();
}
const torch = (await objects('decorations')).at(-1);
check('placing in 3D: a torch on the crypt\'s east wall by a click on it in the 3D view', (await objects('decorations')).length === decorationsBefore + 1 && torch?.wall !== undefined, JSON.stringify({ wallAim, torch }));
how('objects.yml lights[], decorations[] placed in 3D', 'bespoke tool', 'placing tools: a click on a floor or a wall in the 3D view');
await shot('placed_3d', 'placing in 3D: a light on the crypt\'s floor and a torch on its east wall, clicked in the 3D view');
// Textures from the Library, as in part one.
await page.click('[data-testid="library-texture"]');
await page.fill('[data-testid="library-search"]', 't1w');
await page.waitForSelector('[data-testid^="asset-t1w"]', { timeout: 15000 });
const wallTexture = await page.locator('[data-testid^="asset-t1w"]').nth(2).getAttribute('data-testid');
await run.dropOnPlan(wallTexture, 3080, 320);
await settled();

// --- 8. Test: History's ghost, the checks, the build --------------------------------------------------------------

await stage(7);
await page.getByRole('tab', { name: /^History/ }).click();
await sleep(500);
const history = (await run.state()).history.value.entries;
// The crypt's entry: before it the map had no crypt (the ghost shows the rooms of then over the current).
const beamEntry = [...history].reverse().find((entry) => (entry.changes ?? []).some((change) => change.includes(`added ${crypt}`)));
check('History has the crypt\'s entry', Boolean(beamEntry), history.map((entry) => entry.label).slice(0, 30).join(' | '));
await allFrame();
if (beamEntry)
{
    await page.click(`[data-testid="ghost-${beamEntry.sequence}"]`);
    await run.waitFor(() => Boolean(window.__studio.app.store.getState().ghost?.layout), 20000);
}
const ghost = (await run.state()).ghost;
check('History: "show as it was" draws the state before an entry (view.layout_at): four rooms, no crypt', ghost?.layout?.rooms?.length === 4
    && !ghost.layout.rooms.some((room) => room.id === crypt), JSON.stringify({ sequence: ghost?.sequence, rooms: ghost?.layout?.rooms?.map((room) => room.id) }));
how('History: show as it was', 'bespoke tool', 'History drawer: the button on an entry');
await sleep(1500);
await page.evaluate(() => window.__studio.app.store.setState({ selection: null }));
await page.mouse.move(...(await run.at(1800, 300)));
await key('KeyF');
await sleep(2000);
await shot('ghost', 'History: the map as it was before the crypt was drawn (four rooms), dashed amber over the plan and as lines in 3D');
if (beamEntry)
{
    await page.click(`[data-testid="ghost-${beamEntry.sequence}"]`);
}
const validate = await page.evaluate((project) => window.__studio.app.controller.client.call('check.validate', { project }), (await run.state()).projectKey);
const errorsLeft = validate.issues.filter((issue) => issue.severity === 'error');
check('check.validate: no errors', errorsLeft.length === 0, errorsLeft.map((issue) => `${issue.code} ${issue.file} ${issue.path}: ${issue.message}`).join(' | ') || `${validate.issues.length} issues (warnings and notes)`);
run.results.validate = validate.issues;
let build = null;
try
{
    build = await page.evaluate((project) => window.__studio.app.controller.client.call('build.run', { project, dry_run: false }), (await run.state()).projectKey);
}
catch (error)
{
    build = { error: String(error) };
}
run.results.build = build;
check('build.run (not dry) builds the map', build && !build.error && build.files?.length > 0, JSON.stringify(build).slice(0, 500));
await page.getByRole('tab', { name: /^Issues \d/ }).click();
await page.getByRole('button', { name: 'Check again' }).click();
await sleep(2500);
await allFrame();
await key('Escape');
await page.mouse.move(...(await run.at(1800, 300)));
await key('KeyF');
await sleep(2500);
await shot('final', 'the finished dungeon: plan, 3D (cutaway) and the Issues drawer');
await stage(1);
await allFrame();
await shot('final_plan', 'the Plan stage over the finished dungeon: every bubble realised (green), links and goals');

console.log('\nWORDS SET, AND HOW');
for (const [word, entry] of [...words.entries()].sort())
{
    console.log(`  ${entry.means.padEnd(16)} ${word}${entry.detail ? `  (${entry.detail})` : ''}`);
}
console.log('\nWORDS THE UI COULD NOT SET WITHOUT THE SOURCE TAB (or at all)');
for (const miss of misses)
{
    console.log(`  ${miss.word}: ${miss.why}`);
}
run.results.words = Object.fromEntries(words);
run.results.misses = misses;
writeFileSync(join(out, 'hand2_words.json'), JSON.stringify({ words: Object.fromEntries(words), misses }, null, 1));
const failed = await run.finish('s5b1_part2_hand_author');
process.exit(failed > 0 ? 1 : 0);
