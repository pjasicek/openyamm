// The pin loop of S5a3, run end to end on a copy (S5_BROWSER_EDITOR.md 6.4, W7): a person pins in the browser (P on
// the 3D view, with its camera and picture, and on the plan) and a scripted agent answers live, through MCP over the
// stdio relay (`host.mjs relay`, as `oymap mcp`) and through `oymap pins` on the command line; the browser shows each
// answer at once (the host's notices), the person accepts; a pin from the game's inbox arrives with its picture,
// "go to" puts the camera at its pose, the agent answers it with a picture. Screenshots of each step and the times
// from an agent's call to the browser showing it, with the load average beside them.
//
//   node scripts/loop.mjs [--out <folder>] [--project <brief folder>] [--chrome <binary>]
// Playwright comes from S5-0 spike 1's folder (output/s5_spikes/1_viewer), as in shots.mjs.
import { execFileSync, spawn } from 'node:child_process';
import { cpSync, copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createServer } from 'node:net';
import { join, resolve } from 'node:path';
import { randomBytes } from 'node:crypto';
import { pathToFileURL } from 'node:url';

const web = resolve(import.meta.dirname, '..');
const studio = resolve(web, '..');
const repo = resolve(studio, '..');
const args = process.argv.slice(2);
const option = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);
const stamp = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
const out = resolve(option('--out', join(repo, 'output', 's5a3_loop', stamp)));
const source = resolve(option('--project', join(repo, 'devdocs/map_studio/briefs/mm6_6d18/L4')));
const chromePath = option('--chrome', '/usr/bin/google-chrome');
const oymap = join(studio, 'build-s4', 'oymap');
const assets = join(repo, 'assets_dev');
// A picture the game took of the Forge (S5a1's run, the `pin` command's own screenshot) and an after picture.
const gamePicture = join(repo, 'output/studio_s5a1/forge/.oymap/pins/pictures/p1.png');
const afterPicture = join(repo, 'output/studio_s5a1/after/01-p1.png');

const shots = join(out, 'shots');
const projects = join(out, 'projects');
const project = join(projects, 'forge');
const inbox = join(out, 'inbox');
mkdirSync(shots, { recursive: true });
mkdirSync(inbox, { recursive: true });
cpSync(source, project, { recursive: true, filter: (path) => !/\/(\.oymap|build)(\/|$)/.test(path.slice(source.length)) });

const spike = join(repo, 'output', 's5_spikes', '1_viewer');
process.env.PLAYWRIGHT_BROWSERS_PATH ??= join(spike, 'browsers');
const { chromium } = createRequire(join(spike, 'package.json'))('playwright');
const sdk = (path) => import(pathToFileURL(join(studio, 'host/node_modules/@modelcontextprotocol/sdk/dist/esm', path)).href);
const { Client } = await sdk('client/index.js');
const { StdioClientTransport } = await sdk('client/stdio.js');

const load = () => readFileSync('/proc/loadavg', 'utf8').split(' ').slice(0, 3).map(Number);
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));
const log = [];
const say = (line) => { log.push(line); console.log(line); };

async function freePort()
{
    return new Promise((done) =>
    {
        const server = createServer();
        server.listen(0, '127.0.0.1', () =>
        {
            const { port } = server.address();
            server.close(() => done(port));
        });
    });
}

// --- the host ------------------------------------------------------------------------------------------------------

const port = await freePort();
const token = randomBytes(12).toString('hex');
const discovery = join(out, 'host.json');
const host = spawn(process.execPath, [join(studio, 'host', 'src', 'host.mjs'), 'studio', '--port', String(port), '--token', token,
    '--roots', projects, '--inbox', inbox, '--discovery', discovery, '--oymap', oymap],
{ cwd: repo, stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, OYMAP_HOST_LOG: '1' } });
let hostLog = '';
host.stdout.on('data', (data) => { hostLog += data; });
host.stderr.on('data', (data) => { hostLog += data; });
for (let i = 0; i < 100 && !hostLog.includes('oymap studio:'); ++i)
{
    await sleep(100);
}
if (!hostLog.includes('oymap studio:'))
{
    host.kill();
    throw new Error(`the host did not start:\n${hostLog}`);
}
const base = `http://127.0.0.1:${port}`;
// On a failure, what the host said last.
process.on('exit', (code) => { if (code) console.error(`host log:\n${hostLog.split('\n').slice(-30).join('\n')}`); host.kill(); });

// --- the browser ---------------------------------------------------------------------------------------------------

const browser = await chromium.launch({ executablePath: existsSync(chromePath) ? chromePath : undefined, headless: true,
    args: ['--use-angle=vulkan', '--enable-features=Vulkan', '--ignore-gpu-blocklist', '--enable-gpu-rasterization'] });
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
const page = await context.newPage();
const pageErrors = [];
page.on('pageerror', (error) => pageErrors.push(String(error)));
page.on('console', (message) => { if (message.type() === 'error') pageErrors.push(message.text()); });
const results = { started: new Date().toISOString(), load_start: load(), project: source, steps: [] };

let shotNumber = 0;
const shot = async (name) =>
{
    const file = join(shots, `${String(++shotNumber).padStart(2, '0')}_${name}.png`);
    await page.screenshot({ path: file });
    say(`  shot ${file}`);
    return file;
};
const state = (select) => page.evaluate(select);
async function waitFor(test, timeout = 15000, argument = undefined)
{
    const start = Date.now();
    while (Date.now() - start < timeout)
    {
        if (await page.evaluate(test, argument))
        {
            return Date.now() - start;
        }
        await sleep(20);
    }
    throw new Error(`waited ${timeout} ms for ${test}`);
}
// The time from an agent's step to the browser showing it.
async function timed(name, act, shown, timeout = 15000, argument = undefined)
{
    const loadAt = load();
    const start = Date.now();
    const answer = await act();
    const acted = Date.now() - start;
    const waited = await waitFor(shown, timeout, argument);
    const entry = { step: name, agent_ms: acted, shown_ms: acted + waited, load: loadAt };
    results.steps.push(entry);
    say(`${name}: the agent's call ${acted} ms, shown in the browser ${entry.shown_ms} ms after it began (load ${loadAt[0]})`);
    return answer;
}
const pinsOf = () => state(() => { const s = window.__studio.app.store.getState(); return s.pins.state === 'ready' ? s.pins.value.pins : []; });

// The project's key as the host lists it.
await page.goto(`${base}/#token=${token}`);
await waitFor(() => window.__studio?.app?.store.getState().projects.state === 'ready', 15000);
const key = await state(() => window.__studio.app.store.getState().projects.value.find((p) => p.id === 'cal6d18').key);
say(`project copy ${project} (key ${key}); host ${base}`);
await page.goto(`${base}/?project=${encodeURIComponent(key)}#token=${token}`);
await waitFor(() => !!window.__studio?.marks.textured_full, 90000);
await waitFor(() => window.__studio.app.store.getState().validation.state !== 'loading', 30000);
await sleep(300);
await shot('opened');

// The person: a room in 3D, the pointer on its wall, P.
const room = 'room:machine';
await page.evaluate((id) => window.__studio.app.controller.select({ id, file: 'rooms.yml' }, true), room);
await sleep(600);
await page.evaluate(() => window.__studio.app.controller.select(null));
const canvas = await page.$('canvas.oy-viewport-canvas');
const box = await canvas.boundingBox();
await page.mouse.move(box.x + box.width * 0.5, box.y + box.height * 0.45);
await sleep(300);
const hovered = await state(() => window.__studio.viewport.lastHover);
say(`hovered in 3D: ${JSON.stringify(hovered)}`);
await page.keyboard.press('p');
await waitFor(() => !!document.querySelector('[data-testid="pin-composer"] textarea'));
await page.keyboard.type('The machine room is too dark to read the levers: more light over the gears.');
await sleep(200);
await shot('composer_3d');
const t0 = Date.now();
await page.keyboard.press('Control+Enter');
await waitFor(() => window.__studio.app.store.getState().pinDraft === null && window.__studio.app.store.getState().pins.state === 'ready'
    && window.__studio.app.store.getState().pins.value.pins.length > 0, 15000);
results.pin_add_ms = Date.now() - t0;
const studioPin = (await pinsOf()).at(-1);
say(`the person's pin: ${JSON.stringify({ id: studioPin.id, on: studioPin.on, file: studioPin.file, at: studioPin.at, pose: studioPin.pose, picture: studioPin.picture })}`);
await sleep(500);
await shot('pinned_3d');

// The agent, through the relay (`oymap mcp`), as Claude Code would.
const agent = new Client({ name: 'loop-agent', version: '1' });
await agent.connect(new StdioClientTransport({ command: process.execPath,
    args: [join(studio, 'host/src/host.mjs'), 'relay', '--discovery', discovery, '--oymap', oymap], stderr: 'pipe' }));
await waitFor(() => window.__studio.app.store.getState().clients.some((c) => c.kind === 'mcp'));
await sleep(200);
await shot('agent_connected');
const tool = async (name, input) =>
{
    const answer = await agent.callTool({ name, arguments: input });
    const text = answer.content.find((part) => part.type === 'text')?.text ?? '';
    if (answer.isError)
    {
        throw new Error(`${name}: ${text}`);
    }
    try
    {
        return JSON.parse(text);
    }
    catch
    {
        return text;
    }
};
const opened = await tool('map_open', { project });
say(`agent: map_open: revision ${opened.revision}; people: ${opened.people}`);
const open = await tool('map_pins', { project, action: 'list', status: 'open' });
const job = open.pins.find((pin) => pin.source === 'studio');
say(`agent: the open studio pin ${job.id} on ${job.on}: "${job.text}"`);
await page.evaluate((id) => window.__studio.app.controller.selectPin(id), job.id);
await timed('claim through MCP', () => tool('map_pins', { project, action: 'claim', id: job.id, by: 'agent:loop' }),
    (id) => window.__studio.app.store.getState().pins.value?.pins.find((p) => p.id === id)?.status === 'claimed', 15000, job.id);
await sleep(200);
await shot('claimed_live');

// The fix: a light over the gears, in the room the pin is on, with the revision the agent read.
const edited = await timed('edit through MCP (the browser refreshes)', () => tool('map_edit', { project, expect_revision: opened.revision,
    ops: [{ op: 'add', to: 'lights', value: { id: 'light:machine_gears', room: job.on ?? room, height: 384, radius: 1400, color: [255, 214, 160] } }] }),
(revision) => window.__studio.app.store.getState().project.value?.revision !== revision && !!window.__studio.marks.refreshed, 20000,
opened.revision);
say(`agent: map_edit: ${JSON.stringify(edited.changes)} -> ${edited.revision}; people: ${edited.people}`);
await sleep(400);
await shot('agent_edit_live');

// The answer with a picture, through the command line (the watcher announces it).
const picture = join(out, 'agent_after.png');
copyFileSync(afterPicture, picture);
await timed('resolve with a picture through `oymap pins`', async () => execFileSync(oymap, ['pins', 'resolve', project, job.id, '--by', 'agent:loop',
    '--text', 'Added light:machine_gears (radius 1400) over the gears; rebuilt; the after picture is the game\'s.', '--picture', picture]),
(id) => window.__studio.app.store.getState().pins.value?.pins.find((p) => p.id === id)?.status === 'resolved', 15000, job.id);
await waitFor(() => [...document.querySelectorAll('[data-testid="pin-thread"] img')].length >= 2, 10000).catch(() => undefined);
await sleep(400);
await shot('resolved_live_with_picture');

// The person accepts.
await page.click('[data-testid="pin-thread"] button[data-action="accept"]');
await waitFor((id) => window.__studio.app.store.getState().pins.value?.pins.find((p) => p.id === id)?.status === 'accepted', 10000, job.id);
const seen = await tool('map_pins', { project, action: 'list', status: 'accepted' });
say(`agent sees accepted: ${seen.pins.map((p) => p.id).join(', ')}`);
await page.evaluate(() => window.__studio.app.store.setState({ pinFilter: 'all' }));
await sleep(300);
await shot('accepted');

// A pin from the game: the `pin` command's file and picture land in the inbox; the host files it at once.
const stem = '20261114-230000-cal6d18';
copyFileSync(gamePicture, join(inbox, `${stem}.png`));
const tg = Date.now();
writeFileSync(join(inbox, `${stem}.yml`), [
    '# A pin from the game\'s console (`pin <text>`); `oymap pins import <inbox>` files it into its project.',
    'format: 1', 'source: game', 'author: user', 'created: "2026-11-14T23:00:00"', 'text: "the door ahead should open from this side"',
    'world: "mm6"', 'map: "cal6d18.blv"', 'pose:', '  position: [-2778.129, 764.537, 1152.000]', '  yaw_radians: 3.655',
    '  pitch_degrees: 8.594', '  heading_yaw_units: 1191', `picture: "${stem}.png"`, ''].join('\n'));
await waitFor(() => window.__studio.app.store.getState().pins.value?.pins.some((p) => p.source === 'game'), 20000);
results.game_pin_shown_ms = Date.now() - tg;
say(`the game's pin shown in the browser ${results.game_pin_shown_ms} ms after its file was written`);
const gamePin = (await pinsOf()).find((p) => p.source === 'game');
await page.evaluate(() => window.__studio.app.store.setState({ pinFilter: 'active' }));
await page.evaluate((id) => window.__studio.app.controller.selectPin(id), gamePin.id);
await waitFor(() => [...document.querySelectorAll('[data-testid="pin-thread"] img')].some((img) => img.complete && img.naturalWidth > 0), 10000);
await sleep(300);
await shot('game_pin_arrived');
await page.click('[data-testid="pin-thread"] button:has-text("Go to")');
await sleep(900);
await shot('go_to_game_pose');
results.camera_at_game_pose = await state(() => window.__studio.viewport.camera());

// The agent answers the game pin through MCP with a picture.
await timed('reply with a picture through MCP', async () =>
{
    await tool('map_pins', { project, action: 'claim', id: gamePin.id, by: 'agent:loop' });
    return tool('map_pins', { project, action: 'resolve', id: gamePin.id, by: 'agent:loop', pictures: [picture],
        text: 'The door now opens from this side too (door:d3 use from both faces); picture from the same pose.' });
}, (id) => window.__studio.app.store.getState().pins.value?.pins.find((p) => p.id === id)?.status === 'resolved', 15000, gamePin.id);
await waitFor(() => [...document.querySelectorAll('[data-testid="pin-thread"] img')].length >= 2, 10000).catch(() => undefined);
await sleep(400);
await shot('game_pin_answered');

// History: the agent's edit with its author.
await page.evaluate(() => window.__studio.app.store.setState({ drawerTab: 'history' }));
await sleep(500);
await shot('history');

// A pin on the plan.
await page.evaluate(() => window.__studio.app.store.setState({ viewMode: 'plan', drawerTab: 'pins' }));
await sleep(500);
// The pointer over a room's floor: the room framed in the plan, the pointer at the plan's middle.
await page.evaluate(() => window.__studio.app.controller.select({ id: 'room:alcove', file: 'rooms.yml' }, true));
await sleep(500);
await page.evaluate(() => window.__studio.app.controller.select(null));
const plan = await page.$('canvas.oy-plan-canvas');
const planBox = await plan.boundingBox();
await page.mouse.move(planBox.x + planBox.width * 0.5 + 40, planBox.y + planBox.height * 0.5 + 20);
await sleep(200);
await page.keyboard.press('p');
await waitFor(() => !!document.querySelector('[data-testid="pin-composer"] textarea'));
await page.keyboard.type('A torch on this wall would show the way on.');
await sleep(200);
await shot('composer_plan');
await page.keyboard.press('Control+Enter');
await waitFor(() => window.__studio.app.store.getState().pinDraft === null, 10000);
await sleep(400);
const planPin = (await pinsOf()).at(-1);
say(`the plan's pin: ${JSON.stringify({ id: planPin.id, on: planPin.on, file: planPin.file, at: planPin.at })}`);
await shot('pinned_plan');

// A file half written by a generator: the banner, then gone when it parses.
await page.evaluate(() => window.__studio.app.store.setState({ viewMode: 'split' }));
const wiring = join(project, 'wiring.yml');
const wiringText = readFileSync(wiring, 'utf8');
writeFileSync(wiring, `${wiringText}\n  - [unclosed\n`);
await waitFor(() => !!window.__studio.app.store.getState().unreadable, 10000);
await sleep(300);
await shot('file_does_not_parse');
writeFileSync(wiring, wiringText);
await waitFor(() => !window.__studio.app.store.getState().unreadable, 10000);

await agent.close();
await waitFor(() => !window.__studio.app.store.getState().clients.some((c) => c.kind === 'mcp'), 10000);
results.final_pins = (await pinsOf()).map((p) => ({ id: p.id, status: p.status, source: p.source, replies: p.replies?.length ?? 0 }));
results.page_errors = pageErrors;
results.load_end = load();
results.host_log = hostLog.split('\n').filter(Boolean).slice(-40);
results.log = log;
writeFileSync(join(out, 'loop.json'), JSON.stringify(results, null, 1));
await browser.close();
host.kill('SIGTERM');
say(`wrote ${out}`);
