// S5b1 exit test 1, the hand author (S5_BROWSER_EDITOR.md 6.4, F5, W1): a small new dungeon from an EMPTY project made
// in the UI (New project), built entirely by gestures in the real app: clicks and drags on the plan, keys, the tool
// options, the inspector's fields and the event form, the Library's drag and drop, the switch board. Never the
// Source tab, never YAML, never a command line (the script reads the store to check and to find screen points, and
// calls check.validate and build.run at the end as the verification). Prints every word it set and how, and every
// word it could not set without the Source tab. A screenshot after each step, in output/s5b1_shots/exit/.
//   node scripts/s5b1_hand_author.mjs
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { repo, sleep, stampFolder, startRun } from './exit_common.mjs';

const out = process.env.S5_SHOTS ?? join(repo, 'output', 's5b1_shots', 'exit');
const runRoot = stampFolder('hand', process.env.S5_RUNS ?? 's5b1');
const run = await startRun({ out, prefix: 'hand', roots: [runRoot] });
const { page, check, shot, settled, click, drag, key, frame, type } = run;
run.results.run = runRoot;

// Every word set, and how: a bespoke tool, an inspector field, a generic row list; and the words the Source tab alone
// could set (or nothing in the UI).
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

const rooms = async () => (await run.files())['rooms.yml'].tree.rooms ?? [];
const objects = async (list) => (await run.files())['objects.yml']?.tree[list] ?? [];
const events = async () => (await run.files())['wiring.yml']?.tree.events ?? [];
const selected = async () => (await run.state()).selection?.id ?? null;
const tool = async (name) =>
{
    await page.click(`[data-testid="tool-${name}"]`);
    await sleep(120);
};
const stage = async (number) =>
{
    await page.mouse.move(5, 500);
    await key(`Digit${number}`);
    await sleep(150);
};
const option = (name, value) => type(`option-${name}`, value);
// A field of the inspector shown, from "+ add field" when the object does not write it yet.
const ensureField = async (name, label) =>
{
    const field = page.locator(`[data-testid="field-${name}"]`);
    if (await field.count() > 0)
    {
        return 'inspector field';
    }
    await page.click('[data-testid="add-field"]');
    await sleep(300);
    await shot(`add_field_${name}`, `the inspector's + add field, for ${name}`);
    await page.locator('[role="menuitem"]').filter({ has: page.locator('span', { hasText: new RegExp(`^${label}$`, 'i') }) }).first().click();
    await settled();
    return 'inspector field (+ add field)';
};

// --- 0. The panel gallery's part 2 cards, light and dark ----------------------------------------------------------

for (const theme of ['light', 'dark'])
{
    const gallery = await page.context().newPage();
    await gallery.emulateMedia({ colorScheme: theme });
    await gallery.goto(`${run.base}/gallery.html?theme=${theme}#token=${run.token}`);
    await gallery.waitForSelector('figure[data-card]');
    await sleep(1500);
    const heading = gallery.locator('h2', { hasText: 'Author mode, part 2' });
    const blocks = heading.locator('xpath=following-sibling::div[position() <= 2]');
    for (let i = 0; i < await blocks.count(); ++i)
    {
        const file = `hand_00_gallery_${i + 1}_${theme}.png`;
        await blocks.nth(i).screenshot({ path: join(out, file) });
        run.results.steps[file] = `the panel gallery's part 2 cards (${theme})`;
    }
    await gallery.close();
}

// --- 1. New project ----------------------------------------------------------------------------------------------

await page.goto(`${run.base}/#token=${run.token}`);
await page.waitForSelector('[data-testid="new-project"]', { timeout: 20000 });
await page.click('[data-testid="new-project"]');
await page.fill('[data-testid="new-folder"]', 'sunken_chapel');
await page.fill('[data-testid="new-id"]', 'hchap01');
await page.fill('[data-testid="new-name"]', 'The Sunken Chapel');
await page.fill('[data-testid="new-stats"]', '9431');
await shot('new_project', 'the New project form: folder, map id, name, map table row');
await page.click('[data-testid="new-project-make"]');
await run.waitFor(() => window.__studio?.app?.store.getState().project.state === 'ready', 20000);
await settled();
let s = await run.state();
check('an empty project made in the UI opens in Author mode', s.mode === 'author' && (await rooms()).length === 0, s.projectKey);
for (const word of ['project.yml id', 'project.yml name', 'project.yml world', 'project.yml map_stats.id'])
{
    how(word, 'bespoke tool', 'New project form');
}
await shot('empty', 'the empty project: no rooms, the Room tool active');

// --- 2. Shape: five rooms of different sizes and heights, a corridor, openings ----------------------------------

await frame(-256, -640, 4096, 1600);
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
};
await tool('room');
await drawRoom([[0, 0], [768, 0], [768, 640], [0, 640]], 0, 384);
how('rooms.yml rooms[].outline', 'bespoke tool', 'Room tool: corners on the plan');
how('rooms.yml rooms[].floor', 'bespoke tool', 'Room tool options');
how('rooms.yml rooms[].ceiling', 'bespoke tool', 'Room tool options');
how('objects.yml start.room', 'bespoke tool', 'the first room brings the start');
await shot('room_antechamber', 'Room tool: the antechamber (768 × 640, 384 high), with the party start');
await drawRoom([[832, -128], [1856, -128], [1856, 896], [832, 896]], 0, 512);
await drawRoom([[832, 960], [1344, 960], [1344, 1472], [832, 1472]], 0, 320);
await drawRoom([[1920, 0], [2432, 0], [2432, 640], [1920, 640]], 0, 448);
await drawRoom([[3072, -192], [3840, -192], [3840, 832], [3072, 832]], -256, 320);
await frame(-256, -640, 4096, 1600);
let list = await rooms();
check('five rooms of different sizes and heights', list.length === 5 && new Set(list.map((room) => room.ceiling - room.floor)).size >= 4, list.map((room) => `${room.id} ${room.ceiling - room.floor}`).join(', '));
const [ante, hall, store, stairs, crypt] = list.map((room) => room.id);
await shot('rooms', 'five rooms: antechamber, hall (512 high), store (320), stair hall (448), crypt (floor -256)');

await tool('corridor');
await option('width', 192);
await option('floor', -256);
await option('ceiling', 64);
await click(2496, 320);
await click(2752, 352);
await click(3008, 320);
await key('Enter');
await settled();
list = await rooms();
const corridor = list.find((room) => Array.isArray(room.path))?.id;
check('a corridor (a path with a width)', Boolean(corridor), corridor);
how('rooms.yml rooms[].path', 'bespoke tool', 'Corridor tool: points on the plan');
how('rooms.yml rooms[].width', 'bespoke tool', 'Corridor tool options');
await shot('corridor', 'Corridor tool: a bent passage 192 wide from the stair hall to the crypt');

await tool('stairs');
await option('rise', -256);
await option('steps', 8);
await drag([1990, 320], [2380, 320]);
await settled();
list = await rooms();
check('stairs: the stair hall falls 256 to the east in 8 steps', list.find((room) => room.id === stairs)?.slope?.to === -256, JSON.stringify(list.find((room) => room.id === stairs)?.slope));
how('rooms.yml rooms[].slope', 'bespoke tool', 'Stairs tool: a drag across the room');

await tool('opening');
await frame(-256, -640, 4096, 1600);
const openingDrags = [[[700, 320], [900, 320]], [[1100, 850], [1100, 1010]], [[1800, 320], [1980, 320]], [[2380, 320], [2540, 320]], [[2960, 320], [3140, 320]]];
for (const [from, to] of openingDrags)
{
    await drag(from, to);
    await settled();
}
let openings = (await run.files())['rooms.yml'].tree.openings ?? [];
check('an opening between each pair of rooms that connect (5)', openings.length === 5, openings.map((o) => `${o.from}→${o.to}`).join(', '));
how('rooms.yml openings[].from/to/along/width', 'bespoke tool', 'Opening tool: a drag across the wall');
how('rooms.yml openings[].height', 'bespoke tool', 'Opening tool options');
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(300);
await shot('openings', 'Opening tool: five doorways (teal) joining the rooms and the corridor');

// A level in the hall, pillars and a dais in the crypt (a room selected by a click, then the block tools).
await tool('select');
await frame(768, -256, 1920, 960);
await click(1100, 200);
check('a click selects the hall', (await selected()) === hall, await selected());
await tool('level');
await drag([1472, 448], [1792, 832]);
await settled();
how('rooms.yml rooms[].levels[]', 'bespoke tool', 'Level tool: a box in the selected room');
await tool('select');
await frame(3008, -256, 3904, 896);
await click(3200, 0);
await tool('pillar');
await drag([3264, 0], [3328, 64]);
await settled();
await drag([3264, 576], [3328, 640]);
await settled();
await tool('platform');
await option('platformRise', 48);
await drag([3584, 192], [3776, 448]);
await settled();
list = await rooms();
const cryptRoom = list.find((room) => room.id === crypt);
check('pillars and a dais in the crypt, a level in the hall', cryptRoom?.pillars?.length === 2 && cryptRoom?.platforms?.length === 1 && list.find((room) => room.id === hall)?.levels?.length === 1,
    JSON.stringify({ pillars: cryptRoom?.pillars?.length, platforms: cryptRoom?.platforms?.length }));
how('rooms.yml rooms[].pillars[]', 'bespoke tool', 'Pillar tool');
how('rooms.yml rooms[].platforms[]', 'bespoke tool', 'Platform tool (rise in the options)');
await shot('blocks', 'the crypt with two pillars and a dais (Platform, 48 high)');

// --- 3. Build: two doors, the lever, a chest, the exit -------------------------------------------------------------

await stage(3);
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(300);
await tool('door');
await page.click('[data-testid="door-portcullis"]');
openings = (await run.files())['rooms.yml'].tree.openings;
const layoutOpenings = (await run.state()).layout.value.openings;
const middleOf = (from, to) =>
{
    const opening = openings.find((o) => o.from === from && o.to === to);
    const placed = layoutOpenings.find((o) => o.id === opening?.id);
    return placed?.a ? [(placed.a[0] + placed.b[0]) / 2, (placed.a[1] + placed.b[1]) / 2] : null;
};
const storeDoorAt = middleOf(hall, store);
const cryptDoorAt = middleOf(corridor, crypt) ?? middleOf(crypt, corridor);
await click(...storeDoorAt);
await settled();
await page.click('[data-testid="door-wooden"]');
await click(...cryptDoorAt);
await settled();
const doors = await objects('doors');
check('two doors: a portcullis to the store and a wooden door to the crypt', doors.length === 2 && doors.some((door) => door.kind === 'slide_up') && doors.some((door) => door.kind === 'hinged'), JSON.stringify(doors));
how('objects.yml doors[] (opening, kind)', 'bespoke tool', 'Door tool: a click on an opening, kind from the presets');
const portcullis = doors.find((door) => door.kind === 'slide_up')?.id;
const cryptDoor = doors.find((door) => door.kind === 'hinged')?.id;
await shot('doors', 'Door tool: the portcullis (store) and the wooden door (crypt), red on the plan');

await tool('switch');
await page.selectOption('[data-testid="option-switchKind"]', 'lever');
await frame(768, -256, 1920, 1536);
await click(1500, 893);
await settled();
const lever = (await objects('switches'))[0];
check('Switch tool: a lever on the hall\'s north wall', lever?.kind === 'lever' && lever.wall !== undefined && typeof lever.along === 'number', JSON.stringify(lever));
how('objects.yml switches[] (room, wall, along, kind)', 'bespoke tool', 'Switch tool: a click on a wall, kind in the options');
await shot('lever', 'Switch tool: the lever on the hall\'s north wall, beside the store\'s portcullis');

await tool('chest');
await page.selectOption('[data-testid="option-chestKind"]', 'ch3');
await click(1088, 1300);
await settled();
const chest = (await objects('chests'))[0];
check('Chest tool: a chest in the store with its open event', chest?.kind === 'ch3' && (await events()).some((event) => event.preset === 'chest' && event.source === chest.id), JSON.stringify(chest));
how('objects.yml chests[] (room, at, kind)', 'bespoke tool', 'Chest tool: a click on the floor, kind in the options');
how('wiring.yml events[] preset chest', 'bespoke tool', 'Chest tool: its open event with it');
// Its facing by the handle (Select), its contents in the inspector.
await tool('select');
await frame(832, 960, 1344, 1472);
// The facing handle stands 30 pixels from the thing in its facing (east when none is written).
const handle = await page.evaluate(([x, y]) => [x + 30 * window.__studio.plan.unitsPerPixel(), y], chest.at);
await drag(handle, [chest.at[0], chest.at[1] + 120]);
await settled();
check('the chest turned by its facing handle', (await objects('chests'))[0].facing === 90, String((await objects('chests'))[0].facing));
how('objects.yml chests[].facing', 'bespoke tool', 'Select: the facing handle');
await ensureField('gold', 'Gold');
await type('field-gold', 350);
await settled();
await ensureField('items', 'Items');
let chestNow = (await objects('chests'))[0];
if (!Array.isArray(chestNow.items) || chestNow.items.length === 0)
{
    // The list's section opens; its "+ add item" row.
    if (await page.locator('[data-testid="add-row-items"]').count() === 0)
    {
        await page.click('[data-testid="block-items"]');
    }
    await page.click('[data-testid="add-row-items"]');
    await settled();
}
await type('field-items.0', 101);
await settled();
chestNow = (await objects('chests'))[0];
check('the chest\'s contents set in the inspector (gold, an item)', chestNow.gold === 350 && chestNow.items?.[0] === 101, JSON.stringify({ gold: chestNow.gold, items: chestNow.items }));
how('objects.yml chests[].gold', 'inspector field', '+ add field, a number');
how('objects.yml chests[].items', 'inspector field', '+ add field, the row list of item numbers');
await shot('chest', 'the chest (ch3) turned to face north, its gold and item in the inspector');

await tool('exit');
await option('new-neighbour', 'oute3');
// The arrival on New Sorpigal's map (outside the dungeon's mouth): a place on the other map.
await option('arrival-0', -9728);
await option('arrival-1', -11319);
await option('arrival-2', 160);
await page.click('[data-testid="add-neighbour"]');
await settled();
how('project.yml neighbours[] (to, kind, arrival)', 'bespoke tool', 'Exit tool options: + neighbour, arriving at');
await frame(-256, -128, 832, 768);
await click(4, 320);
await settled();
const exit = (await objects('exits'))[0];
check('Exit tool: a way out on the antechamber\'s west wall, with its event', exit?.to && (await events()).some((event) => event.preset === 'exit' && event.source === exit.id), JSON.stringify(exit));
how('objects.yml exits[] (room, wall, along, to)', 'bespoke tool', 'Exit tool: a click on a wall');
how('wiring.yml events[] preset exit', 'bespoke tool', 'Exit tool: its event with it');
await shot('exit', 'Exit tool: the way out to oute3 on the antechamber\'s west wall');

// --- 4. Wire: the lever to the portcullis with L; the event form; the wooden door's event; the switch board --------

await stage(4);
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(300);
await tool('select');
const leverPlace = (await objects('switches'))[0];
// The lever stands on the hall's north wall (y 896) at its `along` from the wall's start corner (counter-clockwise: east to west).
const leverPoint = [1856 - (1856 - 832) * leverPlace.along, 896];
await frame(768, -256, 1920, 1536);
await click(...leverPoint);
check('a click on the plan selects the lever', (await selected()) === lever.id, await selected());
await key('KeyL');
await page.mouse.move(...(await run.at(storeDoorAt[0], storeDoorAt[1])), { steps: 4 });
await sleep(200);
await shot('link_aim', 'L on the lever: the link follows the pointer to the portcullis');
await click(...storeDoorAt);
await settled();
await key('Escape');
let leverEvent = (await events()).find((event) => event.source === lever.id);
check('L and a click make the lever\'s switch event toggling the portcullis', leverEvent?.preset === 'switch' && leverEvent.toggles?.includes(portcullis), JSON.stringify(leverEvent));
how('wiring.yml events[] preset switch, source, toggles', 'bespoke tool', 'L: the link gesture');
await shot('linked', 'the link drawn dashed gold from the lever to the portcullis');

// The event form: the lever acts once and says so.
await click(...leverPoint);
await page.click(`text=${leverEvent.id}`);
await sleep(300);
await page.click('[data-testid="field-once"]');
await settled();
await page.selectOption('[data-testid="add-effects"]', 'text');
await settled();
await type('field-effects.0.text', 'Chains rattle: the portcullis rises.');
await settled();
await page.selectOption('[data-testid="add-effects"]', 'gold');
await settled();
await type('field-effects.1.gold', 5);
await settled();
leverEvent = (await events()).find((event) => event.source === lever.id);
check('the event form: once, a status line and gold as effect rows', leverEvent.once === true && leverEvent.effects?.[0]?.text && leverEvent.effects?.[1]?.gold === 5, JSON.stringify(leverEvent));
how('wiring.yml events[].once', 'bespoke tool', 'event form');
how('wiring.yml events[].effects', 'bespoke tool', 'event form: step rows by word, each value its own field');
await shot('event_form', 'the event form of the lever: preset switch, toggles the portcullis, once, two steps');
await run.shotOf('[data-testid="event-form"]', 'event_form_close', 'the event form close up');

// The portcullis says it does not move by hand: its own text event (+ text) with the event form.
await page.click(`[data-testid="board-row-${leverEvent.id}"]`).catch(() => undefined);
await frame(768, -256, 1920, 1536);
await click(...storeDoorAt);
check('a click selects the portcullis', (await selected()) === portcullis, await selected());
await page.click('[data-testid="new-event-text"]');
await settled();
await type('field-text', 'The portcullis will not move. A lever must raise it.');
await settled();
how('wiring.yml events[] preset text, text', 'bespoke tool', '+ text on the door, the event form');
// The wooden door opens by a click: + door; its hint.
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(200);
await click(...cryptDoorAt);
check('a click selects the wooden door', (await selected()) === cryptDoor, await selected());
await page.click('[data-testid="new-event-door"]');
await settled();
await type('field-title', 'Crypt door');
await settled();
const doorEvent = (await events()).find((event) => event.source === cryptDoor && event.preset === 'door');
check('the wooden door\'s door event with its hint', doorEvent?.title === 'Crypt door', JSON.stringify(doorEvent));
how('wiring.yml events[].title', 'bespoke tool', 'event form');
await shot('door_event', 'the wooden door\'s event in the event form (preset door, title)');

// The switch board: a cell clicked twice and back, then the board as it ends.
await page.click('[data-testid="view-board"]');
await sleep(300);
const cell = `[data-testid="cell-${leverEvent.id}-${cryptDoor}"]`;
await page.click(cell);
await settled();
let afterCell = (await events()).find((event) => event.id === leverEvent.id);
check('a board cell adds the crypt door to the lever\'s event (toggles)', afterCell.toggles?.includes(cryptDoor), JSON.stringify(afterCell.toggles));
await shot('board', 'the switch board: the lever toggles the portcullis and (one click) the crypt door');
for (let i = 0; i < 3; ++i)
{
    await page.click(cell);
    await settled();
}
afterCell = (await events()).find((event) => event.id === leverEvent.id);
check('three more clicks cycle it back to none', !(afterCell.toggles ?? []).includes(cryptDoor) && !(afterCell.opens ?? []).includes(cryptDoor) && !(afterCell.closes ?? []).includes(cryptDoor), JSON.stringify(afterCell));
how('wiring.yml events[].opens/closes/toggles', 'bespoke tool', 'switch board cells, the event form\'s chips');
await page.click('[data-testid="view-board"]');
await sleep(300);

// --- 5. Populate: spawns, a monster, the start moved -------------------------------------------------------------

await stage(5);
await frame(3008, -256, 3904, 896);
await tool('spawn');
await page.selectOption('[data-testid="option-spawnSlot"]', '1');
await click(3456, 640);
await settled();
await page.selectOption('[data-testid="option-spawnSlot"]', '2');
await click(3456, 0);
await settled();
how('objects.yml spawns[] (room, at, slot, radius)', 'bespoke tool', 'Spawn tool: slot in the options');
await tool('monster');
await option('monster', '271');
await click(3680, 320);
await settled();
const monster = (await objects('monsters'))[0];
check('two spawn points and a goblin on the dais', (await objects('spawns')).length === 2 && monster?.monster === 271, JSON.stringify(monster));
how('objects.yml monsters[] (room, at, monster)', 'bespoke tool', 'Monster tool: the monster by number in the options');
// The goblin faces the door: the facing handle.
await tool('select');
await click(3680, 320);
const facingHandle = await page.evaluate(([x, y]) => [x + 30 * window.__studio.plan.unitsPerPixel(), y], monster.at);
await drag(facingHandle, [monster.at[0] - 200, monster.at[1]]);
await settled();
check('the goblin turned west by its facing handle', (await objects('monsters'))[0].facing === 180, String((await objects('monsters'))[0].facing));
how('objects.yml monsters[].facing', 'bespoke tool', 'Select: the facing handle');
// The goblin is a boss: its name and hit points in the inspector.
await ensureField('hp', 'Hp');
await type('field-hp', 60);
await settled();
how('objects.yml monsters[].hp', 'inspector field', '+ add field');
await shot('populate', 'Populate: two spawn points (slots 1, 2) and the goblin on the dais facing the door');
await tool('start');
await frame(-256, -128, 832, 768);
await click(256, 320);
await settled();
const start = (await run.files())['objects.yml'].tree.start;
check('Start tool: the party start moved by a click', start.room === ante && start.at?.[0] === 256, JSON.stringify(start));
how('objects.yml start.at', 'bespoke tool', 'Start tool');

// --- 6. Dress: lights, a torch from the Library, textures from the Library ----------------------------------------

await stage(6);
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(300);
await tool('light');
await option('lightRadius', 768);
for (const at of [[384, 320], [1344, 384], [3328, 320], [3600, 600]])
{
    await click(...at);
    await settled();
}
check('four lights', (await objects('lights')).length === 4, String((await objects('lights')).length));
how('objects.yml lights[] (room, at, radius)', 'bespoke tool', 'Light tool, radius in the options');
// One light's radius by its handle.
await tool('select');
await frame(-256, -128, 1408, 768);
await click(384, 320);
await drag([384 + 768, 320], [384 + 512, 320]);
await settled();
check('a light\'s radius set by its handle', (await objects('lights')).some((light) => light.radius === 512), JSON.stringify((await objects('lights')).map((light) => light.radius)));
how('objects.yml lights[].radius', 'bespoke tool', 'Select: the radius handle');
await shot('lights', 'Dress: a light selected with its radius handle (512)');

await page.click('[data-testid="tab-library"]');
await sleep(200);
await page.click('[data-testid="library-decoration"]');
await page.fill('[data-testid="library-search"]', 'torch');
await page.waitForSelector('[data-testid="asset-torch01"]', { timeout: 15000 });
await frame(3008, -256, 3904, 896);
await run.dropOnPlan('asset-torch01', 3456, 820);
await settled();
const torch = (await objects('decorations'))[0];
check('a torch dragged from the Library hangs on the crypt\'s north wall', torch?.decoration === 'torch01' && torch.wall !== undefined, JSON.stringify(torch));
how('objects.yml decorations[] (room, wall, along, height, decoration)', 'bespoke tool', 'Library: a decoration dropped near a wall');
await shot('torch', 'the Library\'s decorations: torch01 dropped on the crypt\'s north wall');

await page.click('[data-testid="library-texture"]');
await page.fill('[data-testid="library-search"]', 'd2ceil');
await page.waitForSelector('[data-testid="asset-d2ceil3"]', { timeout: 15000 }).catch(() => undefined);
const floorTexture = await page.locator('[data-testid^="asset-"]').first().getAttribute('data-testid');
await run.dropOnPlan(floorTexture, 3456, 320);
await settled();
await page.fill('[data-testid="library-search"]', 't1w');
await page.waitForSelector('[data-testid^="asset-t1w"]', { timeout: 15000 });
const wallTexture = (await page.locator('[data-testid^="asset-t1w"]').nth(2).getAttribute('data-testid'));
await run.dropOnPlan(wallTexture, 3080, 320);
await settled();
await click(3456, 100);
await page.fill('[data-testid="library-search"]', 'd2ceil');
await page.waitForSelector('[data-testid^="asset-d2ceil"]', { timeout: 15000 });
const ceilingTexture = await page.locator('[data-testid^="asset-d2ceil"]').nth(3).getAttribute('data-testid');
await page.locator(`[data-testid="lay-${ceilingTexture.slice(6)}"]`).click();
await page.click('[data-testid="lay-room-ceiling"]');
await settled();
list = await rooms();
const cryptNow = list.find((room) => room.id === crypt);
const themes = (await run.files())['rooms.yml'].tree.themes;
const cryptTheme = themes.find((theme) => theme.id === cryptNow.theme);
check('Library textures: the crypt\'s floor and ceiling (its own theme) and its west wall', Boolean(cryptTheme?.floor?.texture && cryptTheme?.ceiling?.texture) && (cryptNow.walls ?? []).some((wall) => wall.surface?.texture),
    JSON.stringify({ theme: cryptTheme, walls: cryptNow.walls }));
how('rooms.yml themes[] (floor, ceiling) and rooms[].theme', 'bespoke tool', 'Library: a texture dropped on a floor, "lay on" the ceiling');
how('rooms.yml rooms[].walls[].surface', 'bespoke tool', 'Library: a texture dropped near a wall');
await page.locator('header [aria-label="Views"] button', { hasText: 'Split' }).click();
// The crypt framed in both views (F), the selection put away (Esc) so its textures show.
await page.mouse.move(...(await run.at(3456, 100)));
await key('KeyF');
await key('Escape');
await sleep(2500);
await shot('textures', 'the crypt with its own floor, ceiling and west wall from the Library (plan and 3D)');

// --- 7. Test: the checklist, the checks, the build -----------------------------------------------------------------

await stage(7);
await page.click('[data-testid="tab-checklist"]');
await sleep(300);
await shot('checklist', 'the Checklist: the stages\' done-when and what the measure does not see');
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
await page.evaluate(() => window.__studio.plan.frameAll());
await shot('final', 'the finished dungeon: plan, 3D and the Issues drawer');

// --- the words --------------------------------------------------------------------------------------------------

misses.push({ word: 'plan.yml (spaces, links, goals, keys, height_bands)', why: 'no Plan tool (3.18 promises bubbles and links on an empty plan): the UI cannot add a plan.yml object at all; the Source tab only replaces a selected one' });
misses.push({ word: 'wiring.yml variables', why: 'a file-level word of wiring.yml: no inspector for a file\'s own words (an event names map variables by number meanwhile)' });
misses.push({ word: 'objects.yml switches[].block, side: top', why: 'the Switch tool places on walls only: a switch on a block\'s top needs the block to carry an id and the tool to aim at it' });
misses.push({ word: 'objects.yml lifts, movers, plates, floors, ladders', why: '3.18 "Generic: draw the block or line": no tool yet (only through the Source tab of an existing object)' });
misses.push({ word: 'rooms.yml floor_points, ceiling_points, flights, parapets, beams, ceiling_levels', why: 'no "Height points" tool or per-word tools beyond Level, Platform and Pillar (part 1 scope)' });
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
writeFileSync(join(out, 'hand_words.json'), JSON.stringify({ words: Object.fromEntries(words), misses }, null, 1));
const failed = await run.finish('s5b1_hand_author');
process.exit(failed > 0 ? 1 : 0);
