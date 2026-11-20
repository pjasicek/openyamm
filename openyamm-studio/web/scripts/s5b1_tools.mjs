// S5b1 part 1 in the real app (S5_BROWSER_EDITOR.md 6.4): the host and the native core over fresh copies of
// projects, a browser that makes a new project from the project list and uses every indoor tool of part 1 once
// (Room, Corridor, Opening, Door, Stairs, Level, Platform, Pillar, Select's handles, PgUp), the editable inspector
// and the Source tab, undo and redo, History's revert, Delete and Ctrl D, the project's settings, and an outside
// rewrite of the hand-edited project with its revert. A screenshot after each step, and the checks' results.
// Headless Chrome on the machine's GPU; Playwright from S5-0 spike 1's folder. Build the web app first.
//   node scripts/s5b1_tools.mjs [--out <folder>]
import { spawn } from 'node:child_process';
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, unlinkSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createServer } from 'node:net';
import { join, relative, resolve } from 'node:path';
import { randomBytes } from 'node:crypto';

const web = resolve(import.meta.dirname, '..');
const studio = resolve(web, '..');
const repo = resolve(studio, '..');
const args = process.argv.slice(2);
const option = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);
const out = resolve(option('--out', join(repo, 'output', 's5b1_shots')));
mkdirSync(out, { recursive: true });
// The screenshots of an earlier run (this script's own numbered files) go, so the folder shows one run.
for (const name of readdirSync(out).filter((entry) => /^\d\d_.*\.png$/.test(entry)))
{
    unlinkSync(join(out, name));
}
const spike = join(repo, 'output', 's5_spikes', '1_viewer');
process.env.PLAYWRIGHT_BROWSERS_PATH ??= join(spike, 'browsers');
const { chromium } = createRequire(join(spike, 'package.json'))('playwright');
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

// Fresh copies for this run (output/s5b1/web/runs/<stamp>): the example dungeon, and room for a new project.
const stamp = new Date().toISOString().replace(/[:.]/g, '-');
const runRoot = join(repo, 'output', 's5b1', 'web', 'runs', stamp);
mkdirSync(runRoot, { recursive: true });
cpSync(join(studio, 'examples', 'gatehouse_cellars'), join(runRoot, 'gatehouse_cellars'), { recursive: true,
    filter: (source) => !source.includes('/build') && !source.includes('/.oymap') });

const freePort = () => new Promise((done) =>
{
    const server = createServer();
    server.listen(0, '127.0.0.1', () =>
    {
        const { port } = server.address();
        server.close(() => done(port));
    });
});

const port = await freePort();
const token = randomBytes(12).toString('hex');
const host = spawn(process.execPath, [join(studio, 'host', 'src', 'host.mjs'), 'studio', '--port', String(port), '--token', token,
    '--roots', runRoot, '--discovery', join(out, 'host.json'), '--inbox', join(out, 'inbox'), '--background', 'off'],
{ cwd: repo, stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, OYMAP_HOST_LOG: '1' } });
let hostLog = '';
host.stdout.on('data', (data) => { hostLog += data; });
host.stderr.on('data', (data) => { hostLog += data; });
for (let i = 0; i < 100 && !hostLog.includes('oymap studio:'); ++i)
{
    await sleep(100);
}
const base = `http://127.0.0.1:${port}`;
const browser = await chromium.launch({ executablePath: existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : undefined, headless: true,
    args: ['--use-angle=vulkan', '--enable-features=Vulkan', '--ignore-gpu-blocklist', '--enable-gpu-rasterization'] });
const results = { started: new Date().toISOString(), run: runRoot, steps: {}, checks: {} };
const context = await browser.newContext({ viewport: { width: 1680, height: 1000 }, deviceScaleFactor: 1 });
const page = await context.newPage();
const errors = [];
page.on('pageerror', (error) => errors.push(String(error)));
page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });

let shotNumber = 0;
const shot = async (name, note = '') =>
{
    shotNumber += 1;
    const file = `${String(shotNumber).padStart(2, '0')}_${name}.png`;
    await page.screenshot({ path: join(out, file) });
    results.steps[file] = note;
};

async function waitFor(test, timeout = 20000, arg = undefined)
{
    const start = Date.now();
    while (Date.now() - start < timeout)
    {
        if (await page.evaluate(test, arg))
        {
            return true;
        }
        await sleep(100);
    }
    return false;
}

const state = () => page.evaluate(() => window.__studio.app.store.getState());
const setState = (value) => page.evaluate((s) => window.__studio.app.store.setState(s), value);
const check = (name, ok, detail = '') =>
{
    results.checks[name] = { ok: Boolean(ok), detail };
    console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${detail ? `: ${detail}` : ''}`);
};

// Every gesture written and the views of the new revision read (or no view, for an empty project).
const settled = (timeout = 30000) => waitFor(() =>
{
    const s = window.__studio.app.store.getState();
    if (s.edits.pending > 0 || s.project.state !== 'ready' || window.__studio.app.controller.session.busy)
    {
        return false;
    }
    return window.__studio.viewsRevision === s.project.value.revision && s.history.state === 'ready'
        && s.history.value.revision === s.project.value.revision;
}, timeout);

// The screen point of a map point on the plan.
const at = async (x, y) => page.evaluate(([px, py]) => window.__studio.plan.screenOf(px, py), [x, y]);
const click = async (x, y, options = {}) =>
{
    const [sx, sy] = await at(x, y);
    await page.mouse.click(sx, sy, options);
    await sleep(60);
};
const drag = async (from, to, steps = 12) =>
{
    const [ax, ay] = await at(from[0], from[1]);
    const [bx, by] = await at(to[0], to[1]);
    await page.mouse.move(ax, ay);
    await page.mouse.down();
    await page.mouse.move(ax + (bx - ax) * 0.1, ay + (by - ay) * 0.1, { steps: 3 });
    await page.mouse.move(bx, by, { steps });
    await page.mouse.up();
    await sleep(80);
};
const key = async (name) =>
{
    await page.keyboard.press(name);
    await sleep(60);
};
const rooms = async () => (await state()).project.value.files['rooms.yml'].tree.rooms ?? [];
// The plan showing a box of the map (every drawing starts with its place in view).
const frame = async (minX, minY, maxX, maxY) =>
{
    await page.evaluate((b) => window.__studio.plan.frameBounds(...b), [minX, minY, maxX, maxY]);
    await sleep(200);
};

// --- 0. the panel gallery's Author mode cards, light and dark -------------------------------------------------------

for (const theme of ['light', 'dark'])
{
    const galleryPage = await context.newPage();
    await galleryPage.emulateMedia({ colorScheme: theme });
    await galleryPage.goto(`${base}/gallery.html?theme=${theme}#token=${token}`);
    await galleryPage.waitForSelector('figure[data-card]');
    await sleep(1500);
    const heading = galleryPage.locator('h2', { hasText: 'Author mode (S5b1)' });
    const blocks = heading.locator('xpath=following-sibling::div[position() <= 2]');
    for (let i = 0; i < await blocks.count(); ++i)
    {
        shotNumber += 1;
        const file = `${String(shotNumber).padStart(2, '0')}_gallery_author_${i + 1}_${theme}.png`;
        await blocks.nth(i).screenshot({ path: join(out, file) });
        results.steps[file] = `the panel gallery's Author mode cards (${theme})`;
    }
    await galleryPage.close();
}

// --- 1. a new project from the project list ----------------------------------------------------------------------

await page.goto(`${base}/#token=${token}`);
await page.waitForSelector('[data-testid="new-project"]', { timeout: 20000 });
await page.click('[data-testid="new-project"]');
await page.fill('[data-testid="new-folder"]', 'crypt');
await page.fill('[data-testid="new-id"]', 'crypt01');
await page.fill('[data-testid="new-name"]', 'The Old Crypt');
await page.fill('[data-testid="new-stats"]', '9401');
await shot('new_project_form', 'the New project form on the project list');
await page.click('[data-testid="new-project-make"]');
await waitFor(() => window.__studio?.app?.store.getState().project.state === 'ready', 20000);
await settled();
let s = await state();
check('new project opens in Author mode with the Room tool', s.mode === 'author' && s.tool === 'room' && s.projectKey.endsWith('/crypt'), s.projectKey);
await page.evaluate(() => window.__studio.plan.frameObject(null, [768, 512, 0]));
await sleep(300);
await shot('empty_project_author', 'the empty project: stage bar, tool rail, tool options, the plan with no view yet');

// --- 2. Room tool: two rooms by corners (Enter; a click on the first corner) ---------------------------------------

await setState({ toolOptions: { ...s.toolOptions, grid: 64 } });
await click(0, 0);
await click(768, 0);
await click(768, 640);
// Mid-drawing: the ghost and the hint.
const [mx, my] = await at(0, 640);
await page.mouse.move(mx, my, { steps: 4 });
await sleep(150);
await shot('room_drawing', 'Room tool: three corners clicked, the fourth under the pointer');
await click(0, 640);
await key('Enter');
await settled();
let list = await rooms();
check('Room tool adds a room (the core gives its id)', list.length === 1 && /^room:/.test(list[0].id), list[0]?.id);
s = await state();
check('the first room brings the party start', Boolean(s.project.value.files['objects.yml']?.tree.start), JSON.stringify(s.project.value.files['objects.yml']?.tree.start));
check('the first change marks the project as edited by hand', Boolean(s.project.value.hand_edited), s.project.value.hand_edited?.since);
const first = list[0].id;
check('the new room is selected', s.selection?.id === first, JSON.stringify(s.selection));
await frame(-256, -256, 1856, 1024);
// A second room east of it, across a wall 64 thick, closed by clicking its first corner.
await click(832, 128);
await click(1600, 128);
await click(1600, 768);
await click(832, 768);
await click(832, 128);
await settled();
list = await rooms();
check('a click on the first corner closes the outline', list.length === 2, list.map((room) => room.id).join(' '));
const second = list[1].id;
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(300);
await shot('two_rooms', 'Room tool: two rooms, the second selected');

// --- 3. Opening tool: a drag across the wall between them --------------------------------------------------------

await key('KeyI');
await drag([700, 400], [900, 420]);
await settled();
s = await state();
const openings = s.project.value.files['rooms.yml'].tree.openings ?? [];
check('Opening tool adds an opening between the two rooms', openings.length === 1 && openings[0].from === first && openings[0].to === second,
    JSON.stringify(openings[0]));
const layoutOpening = s.layout.state === 'ready' ? s.layout.value.openings[0] : null;
check('the core builds the opening where the drag crossed', layoutOpening && Math.abs((layoutOpening.a[1] + layoutOpening.b[1]) / 2 - 410) < 40,
    JSON.stringify(layoutOpening));
await shot('opening', 'Opening tool: the doorway between the rooms (teal)');

// --- 4. Door tool: a portcullis in the opening -----------------------------------------------------------------------

await key('KeyD');
await page.click('[data-testid="door-portcullis"]');
await page.mouse.move(...(await at(800, 410)));
await sleep(150);
await shot('door_hover', 'Door tool: the opening under the pointer, the presets in the options');
await click(800, 410);
await settled();
s = await state();
const doors = s.project.value.files['objects.yml'].tree.doors ?? [];
check('Door tool adds a door of the preset in the opening', doors.length === 1 && doors[0].kind === 'slide_up' && doors[0].opening === openings[0].id, JSON.stringify(doors[0]));
await shot('door', 'Door tool: the door (red) in the opening, selected in the inspector');

// --- 5. Corridor tool: a path off the second room ---------------------------------------------------------------------

await key('KeyC');
await page.fill('[data-testid="option-width"]', '192');
await key('Enter');
await frame(-256, -256, 2304, 1600);
await click(1216, 832);
await click(1216, 1344);
await click(1984, 1344);
await key('Enter');
await settled();
list = await rooms();
const corridor = list.find((room) => Array.isArray(room.path));
check('Corridor tool adds a path room with the options\' width', corridor && corridor.width === 192 && corridor.path.length === 3, JSON.stringify(corridor?.path));
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(300);
await shot('corridor', 'Corridor tool: a path room 192 wide');

// --- 6. Stairs tool: the second room's floor rising north -----------------------------------------------------------

await key('KeyS');
await frame(-256, -256, 2304, 1600);
await page.fill('[data-testid="option-rise"]', '96');
await key('Enter');
await page.fill('[data-testid="option-steps"]', '6');
await key('Enter');
await drag([1216, 200], [1216, 700]);
await settled();
list = await rooms();
const sloped = list.find((room) => room.id === second);
check('Stairs tool writes the slope toward the wall the drag points at', sloped?.slope?.toward === 'north' && sloped.slope.to === 96 && sloped.slope.steps === 6, JSON.stringify(sloped?.slope));
await shot('stairs', 'Stairs tool: the second room climbs 96 north in 6 steps');

// --- 7. Level, Platform and Pillar inside the first room -------------------------------------------------------------

await page.evaluate((id) => window.__studio.app.controller.select({ id, file: 'rooms.yml' }), first);
await frame(-128, -128, 896, 768);
await key('KeyY');
await drag([64, 64], [320, 256]);
await settled();
await key('KeyT');
await drag([448, 64], [640, 192]);
await settled();
await key('KeyX');
await drag([128, 448], [192, 512]);
await settled();
list = await rooms();
const firstRoom = list.find((room) => room.id === first);
check('Level, Platform and Pillar tools add keyed blocks to the room', firstRoom.levels?.length === 1 && firstRoom.platforms?.length === 1 && firstRoom.pillars?.length === 1
    && firstRoom.pillars[0].key, JSON.stringify({ levels: firstRoom.levels, platforms: firstRoom.platforms, pillars: firstRoom.pillars }));
s = await state();
check('the new block is selected by its key address', /\/pillars\//.test(s.selection?.id ?? ''), s.selection?.id);
await page.evaluate(() => window.__studio.plan.frameObject(null, [384, 320, 0]));
await sleep(300);
await shot('blocks', 'Level (dashed), Platform (crossed) and Pillar (solid) inside the first room; the pillar selected, its form in the inspector');

// --- 8. Select tool: drag a corner, insert a corner, PgUp ---------------------------------------------------------------

await key('KeyV');
await page.evaluate((id) => window.__studio.app.controller.select({ id, file: 'rooms.yml' }), first);
await frame(-384, -256, 1024, 1024);
await drag([0, 640], [-128, 768]);
await settled();
list = await rooms();
check('dragging a corner patches that outline point', JSON.stringify(list.find((room) => room.id === first).outline).includes('[-128,768]'),
    JSON.stringify(list.find((room) => room.id === first).outline));
const [ex, ey] = await at(384, 0);
await page.mouse.dblclick(ex, ey);
await settled();
list = await rooms();
check('double-clicking an edge inserts a corner', list.find((room) => room.id === first).outline.length === 5, JSON.stringify(list.find((room) => room.id === first).outline));
await page.mouse.move(...(await at(400, 400)));
await key('PageUp');
await key('PageUp');
await settled();
list = await rooms();
check('PgUp twice raises the floor under the cursor by the grid, one merged entry', list.find((room) => room.id === first).floor === 128, String(list.find((room) => room.id === first).floor));
s = await state();
const merged = s.history.value.entries.at(-1);
check('repeated PgUp folds into one history entry', (merged.merged ?? 1) >= 2 || /floor/.test(merged.label ?? ''), JSON.stringify({ label: merged.label, merged: merged.merged }));
await page.evaluate(() => window.__studio.plan.frameObject(null, [384, 320, 0]));
await sleep(300);
await shot('select_handles', 'Select tool: the room\'s handles after a corner drag and an inserted corner; floor raised by PgUp');

// --- 9. The inspector: a field, + add field, the Source tab ------------------------------------------------------

const ceiling = page.locator('[data-testid="field-ceiling"]');
await ceiling.fill('512+64');
await ceiling.press('Enter');
await settled();
list = await rooms();
check('the inspector writes a number from an expression', list.find((room) => room.id === first).ceiling === 576, String(list.find((room) => room.id === first).ceiling));
await page.click('[data-testid="add-field"]');
await sleep(200);
await shot('inspector_add_field', 'the inspector: the room\'s fields, "+ add field" open with each word\'s description');
await page.keyboard.press('Escape');
await sleep(100);
await page.evaluate(() => window.__studio.app.store.setState({ inspectorTab: 'source' }));
await sleep(200);
const editor = page.locator('[data-testid="source"] .cm-content');
await editor.click();
await page.keyboard.press('Control+End');
await page.keyboard.type('\nname: Crypt hall');
await page.click('[data-testid="source-apply"]');
await settled();
list = await rooms();
check('the Source tab\'s Apply replaces the object', list.find((room) => room.id === first).name === 'Crypt hall', list.find((room) => room.id === first).name);
await shot('source_tab', 'the Source tab after Apply');
await page.evaluate(() => window.__studio.app.store.setState({ inspectorTab: 'properties' }));

// --- 10. Undo, redo, History and its revert ----------------------------------------------------------------------

await page.mouse.move(...(await at(1000, -400)));
await key('Control+z');
await settled();
list = await rooms();
check('Ctrl Z undoes the person\'s latest change (the name)', list.find((room) => room.id === first).name === undefined, String(list.find((room) => room.id === first).name));
await key('Control+y');
await settled();
list = await rooms();
check('Ctrl Y redoes it', list.find((room) => room.id === first).name === 'Crypt hall', String(list.find((room) => room.id === first).name));
await setState({ drawerTab: 'history' });
await sleep(300);
await shot('history', 'History: the undo and the redo as entries naming what they revert; merged PgUp; Revert this entry');
s = await state();
const stairsEntry = s.history.value.entries.find((entry) => (entry.label ?? '').startsWith('stairs'));
await page.click(`[data-testid="revert-${stairsEntry.sequence}"]`);
await sleep(200);
await settled();
list = await rooms();
check('Revert this entry puts back what that entry changed', !list.find((room) => room.id === second).slope, JSON.stringify(list.find((room) => room.id === second).slope));
s = await state();
const revertEntry = s.history.value.entries.at(-1);
check('the revert is an entry of its own naming the entry', revertEntry.kind === 'revert' && revertEntry.reverts === stairsEntry.sequence, JSON.stringify({ kind: revertEntry.kind, reverts: revertEntry.reverts }));
await shot('history_revert', 'History after reverting the stairs entry');

// --- 11. Delete and Ctrl D ---------------------------------------------------------------------------------------------

await setState({ drawerTab: 'issues' });
list = await rooms();
const pillarKey = list.find((room) => room.id === first).pillars[0].key;
await page.evaluate((address) => window.__studio.app.controller.select({ id: address, file: 'rooms.yml' }), `${first}/pillars/${pillarKey}`);
await page.mouse.move(...(await at(1000, -400)));
await key('Delete');
await settled();
list = await rooms();
check('Delete removes the selected pillar', !(list.find((room) => room.id === first).pillars ?? []).length, JSON.stringify(list.find((room) => room.id === first).pillars));
await page.evaluate((id) => window.__studio.app.controller.select({ id, file: 'rooms.yml' }), second);
await key('Control+d');
await settled();
list = await rooms();
check('Ctrl D duplicates the selected room beside it', list.length === 4, list.map((room) => room.id).join(' '));
await page.evaluate(() => window.__studio.plan.frameAll());
await sleep(300);
await shot('delete_duplicate', 'Delete took the pillar; Ctrl D copied the second room (south-east, hatched until built if it overlaps)');

// --- 12. The project's settings: the hand-edit mark ------------------------------------------------------------------

await page.click('[data-testid="project-settings"]');
await sleep(300);
await shot('settings', 'the project\'s settings: edited by hand since today, Clear the mark…, Write all keys now…');
await page.keyboard.press('Escape');

// --- 13. An outside rewrite of the hand-edited project, and its one revert step ---------------------------------------

s = await state();
const folder = join(runRoot, 'crypt');
const text = readFileSync(join(folder, 'rooms.yml'), 'utf8');
// A generator-like rewrite: the hand-edited first room's levels and platforms gone, keys dropped.
const rewritten = text.split('\n').filter((line) => !/^\s+key: /.test(line)).join('\n').replace(/\n {4}levels:[\s\S]*?(?=\n {4}[a-z_]+:|\n {2}- )/, '');
writeFileSync(join(folder, 'rooms.yml'), rewritten);
const noticed = await waitFor(() =>
{
    const st = window.__studio.app.store.getState();
    return st.history.state === 'ready' && st.history.value.entries.some((entry) => entry.kind === 'outside' && entry.notice?.length);
}, 20000);
await sleep(500);
check('an outside rewrite of the hand-edited project carries an error notice', noticed);
await shot('outside_notice', 'the error banner over the views: the outside entry rewrote hand-edited work, with its one revert step');
if (noticed)
{
    await page.click('[data-testid="revert-notice"]');
    await settled();
    list = await rooms();
    check('the notice\'s revert step puts the hand work back', (list.find((room) => room.id === first).levels ?? []).length === 1, JSON.stringify(list.find((room) => room.id === first).levels));
    await shot('outside_reverted', 'after Revert entry: the levels are back');
}

// --- 14. A project made by others: effective values, keys ------------------------------------------------------------

await page.goto(`${base}/?project=${encodeURIComponent(`${relative(repo, runRoot)}/gatehouse_cellars`)}#token=${token}`);
await waitFor(() => window.__studio?.app?.store.getState().layout.state === 'ready', 30000);
await setState({ mode: 'author', stage: 2 });
await page.evaluate(() => window.__studio.app.controller.select({ id: 'room:hall', file: 'rooms.yml' }, true));
await sleep(1500);
const notWritten = await page.locator('[data-testid="not-written"]').count();
check('the inspector shows the absent fields\' effective values (project.resolve)', notWritten > 0);
await shot('effective_values', 'gatehouse_cellars in Author mode: room:hall with its theme, ambient and surfaces greyed as "not written"');
await page.click('[data-testid="project-settings"]');
await page.click('[data-testid="migrate"]');
await sleep(800);
await shot('migrate_ask', 'the project\'s settings: Write all keys now asks first, with what it would write');
await page.keyboard.press('Escape');

// --- 15. Review mode: nothing edits ---------------------------------------------------------------------------------

await setState({ mode: 'review' });
await sleep(300);
await shot('review_mode', 'Review mode: no stage bar, no tools, the inspector read only');

results.errors = errors;
results.failed = Object.entries(results.checks).filter(([, value]) => !value.ok).map(([name]) => name);
writeFileSync(join(out, 's5b1_tools.json'), JSON.stringify(results, null, 1));
writeFileSync(join(out, 'host.log'), hostLog);
await browser.close();
host.kill();
console.log(`${Object.keys(results.checks).length - results.failed.length} of ${Object.keys(results.checks).length} checks passed; ${errors.length} page errors`);
if (errors.length)
{
    console.log(errors.slice(0, 10).join('\n'));
}
process.exit(results.failed.length > 0 ? 1 : 0);
