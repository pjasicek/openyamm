// Walk mode and Play here, driven in headless Chrome (S5a4; S5_BROWSER_EDITOR.md 3.6, 2.10): starts the host on a
// free port, opens projects, enters walk mode with G, walks with the keyboard (WASD, Shift, Space), takes and gives
// back the pointer (Esc, Esc), toggles a hinged door, measures the worker's load and step times, and plays one
// project in the game (minimised, closed after a few seconds by the launcher) to see the camera follow the game's
// exit pose. Screenshots and a JSON of the numbers, each with the load average beside it.
//
//   node scripts/walk.mjs [--out <folder>] [--only <name>] [--no-play] [--chrome <binary>]
// Playwright comes from S5-0 spike 1's folder (output/s5_spikes/1_viewer), as scripts/shots.mjs takes it.
import { spawn } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createServer } from 'node:net';
import { join, resolve } from 'node:path';
import { randomBytes } from 'node:crypto';

const web = resolve(import.meta.dirname, '..');
const studio = resolve(web, '..');
const repo = resolve(studio, '..');
const args = process.argv.slice(2);
const option = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);
const out = resolve(option('--out', join(repo, 'output', 's5a4_shots')));
const only = option('--only', null);
const play = !args.includes('--no-play');
const chromePath = option('--chrome', '/usr/bin/google-chrome');
mkdirSync(out, { recursive: true });

const spike = join(repo, 'output', 's5_spikes', '1_viewer');
process.env.PLAYWRIGHT_BROWSERS_PATH ??= join(spike, 'browsers');
const { chromium } = createRequire(join(spike, 'package.json'))('playwright');

const load = () => readFileSync('/proc/loadavg', 'utf8').split(' ').slice(0, 3).map(Number);
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

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

const port = await freePort();
const token = randomBytes(12).toString('hex');
// The game Play here starts makes no sound in a scripted run (memory "silent game runs").
const host = spawn(process.execPath, [join(studio, 'host', 'src', 'host.mjs'), 'studio', '--port', String(port), '--token', token,
    '--discovery', join(out, 'host.json'), '--inbox', join(out, 'inbox')],
    { cwd: repo, stdio: ['ignore', 'pipe', 'pipe'], env: { ...process.env, SDL_AUDIODRIVER: 'dummy', OYMAP_HOST_LOG: '1' } });
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

const browser = await chromium.launch({ executablePath: existsSync(chromePath) ? chromePath : undefined, headless: true,
    args: ['--use-angle=vulkan', '--enable-features=Vulkan', '--ignore-gpu-blocklist', '--enable-gpu-rasterization'] });
const results = { started: new Date().toISOString(), load_start: load(), projects: {} };

async function waitFor(page, test, timeout, arg)
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

const shot = (page, name) => page.screenshot({ path: join(out, `${name}.png`) });
const walkState = (page) => page.evaluate(() =>
{
    const state = window.__studio.app.store.getState();
    return { walk: state.walk.state, kind: state.walk.kind, pose: state.walk.pose, message: state.walk.message,
        locked: state.walk.locked ?? false, status: document.querySelector('[data-testid="walk-status"]')?.textContent ?? null };
});
const percentiles = (values) =>
{
    const sorted = [...values].sort((a, b) => a - b);
    const at = (q) => +(sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * q))] ?? 0).toFixed(3);
    return { n: sorted.length, p50: at(0.5), p95: at(0.95), p99: at(0.99), max: +(sorted.at(-1) ?? 0).toFixed(3) };
};

// Each project: where walk mode starts (the camera's eye and facing), and what to do there.
const projects = [
    { name: 'shapes', key: 'openyamm-studio/examples/shapes_gallery', camera: { eye: [1500, 1664, 416], yaw: 0, pitch: -0.05 },
        door: 'door:closet', play: { commands: ['tp 2300 1664 256 3.1416 -5'], seconds: 6 } },
    { name: 'darkmoor', key: 'devdocs/map_studio/briefs/mm6_cd2/L4' },
    { name: 'harmondale', key: 'devdocs/map_studio/briefs/mm7_7out02/L4', camera: { eye: [-2000, 3000, 1400], yaw: 0.5, pitch: -0.1 },
        play: { seconds: 6 } },
    { name: 'xd02', key: 'devdocs/xeen/briefs/xd02/L4' },
];

for (const project of projects)
{
    if (only && only !== project.name)
    {
        continue;
    }
    const context = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(String(error)));
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    const missing = {};
    page.on('response', (response) =>
    {
        if (response.status() >= 400)
        {
            const route = new URL(response.url()).pathname.split('/')[1];
            missing[route] = (missing[route] ?? 0) + 1;
        }
    });
    const entry = { key: project.key, load_open: load(), errors, missing };
    results.projects[project.name] = entry;
    await page.goto(`${base}/?project=${encodeURIComponent(project.key)}#token=${token}`);
    entry.opened = await waitFor(page, () => !!window.__studio?.marks.textured_full
        || window.__studio?.app?.store.getState().mesh.state === 'error', 120000);
    await page.evaluate(() => window.__studio.app.store.setState({ viewMode: '3d' }));
    await sleep(300);
    if (project.camera)
    {
        await page.evaluate((camera) => window.__studio.viewport.setCamera(camera), project.camera);
    }
    else
    {
        // A dungeon: from its start, the camera at the eye over the start point (the layout's start).
        await page.evaluate(() =>
        {
            const layout = window.__studio.app.store.getState().layout.value;
            const start = layout?.start;
            if (start)
            {
                window.__studio.viewport.setCamera({ eye: [start.at[0], start.at[1], start.at[2] + 160],
                    yaw: ((start.facing ?? 0) * Math.PI) / 180, pitch: 0 });
            }
        });
    }
    await sleep(300);
    await shot(page, `${project.name}_0_before`);

    // G: walk mode.
    entry.load_walk = load();
    await page.locator('canvas.oy-viewport-canvas').hover();
    await page.keyboard.press('KeyG');
    entry.walk_on = await waitFor(page, () => ['on', 'error'].includes(window.__studio.app.store.getState().walk.state), 120000);
    entry.after_g = await walkState(page);
    entry.marks = await page.evaluate(() => ({ prepare: window.__studio.marks.walk_prepare_ms, ready: window.__studio.marks.walk_ready_ms }));
    entry.worker = await page.evaluate(() => { const t = window.__studio.walk?.timings; return t ? { coreMs: t.coreMs, fetchMs: t.fetchMs, loadMs: t.loadMs, bytes: t.bytes } : null; });
    if (entry.after_g.walk !== 'on')
    {
        await shot(page, `${project.name}_walk_failed`);
        await context.close();
        continue;
    }
    await sleep(500);
    await shot(page, `${project.name}_1_walk`);

    // The pointer: a click takes it (mouse look), Esc gives it back.
    await page.mouse.click(800, 450);
    await sleep(300);
    entry.locked_after_click = (await walkState(page)).locked;
    if (entry.locked_after_click)
    {
        await page.mouse.move(900, 450, { steps: 5 });
        await sleep(200);
    }
    // The browser's own Esc gives the pointer back (headless Chrome does not act on a scripted Esc there): as it would.
    await page.evaluate(() => document.exitPointerLock());
    await sleep(300);
    entry.locked_after_exit = (await walkState(page)).locked;
    entry.walk_after_pointer_back = (await walkState(page)).walk;

    // Walk: W for 1.5 s, then Shift+W (run) with a jump.
    const facing = project.camera?.yaw ?? (await page.evaluate(() => window.__studio.app.controller.viewport.camera().yaw));
    await page.evaluate((yaw) => window.__studio.walk.face(yaw, -0.05), facing);
    const startPose = (await walkState(page)).pose;
    await page.keyboard.down('KeyW');
    await sleep(1500);
    await page.keyboard.up('KeyW');
    await sleep(200);
    const walked = (await walkState(page)).pose;
    entry.walked = { from: startPose?.position, to: walked?.position, distance: startPose && walked
        ? Math.hypot(walked.position[0] - startPose.position[0], walked.position[1] - startPose.position[1]) : null };
    await shot(page, `${project.name}_2_walked`);
    await page.keyboard.down('Shift');
    await page.keyboard.down('KeyW');
    await sleep(400);
    await page.keyboard.press('Space');
    entry.jump_airborne = await waitFor(page, () => window.__studio.app.store.getState().walk.pose?.grounded === false, 1500);
    await sleep(800);
    await page.keyboard.up('KeyW');
    await page.keyboard.up('Shift');
    await sleep(600);
    entry.after_run = await walkState(page);
    await shot(page, `${project.name}_3_ran`);

    if (project.door)
    {
        // Into the hinged door shut, open it with a click at the middle of the view, through it.
        await page.evaluate(() => window.__studio.walk.placeAt({ eye: [1700, 1664, 416], yaw: 0, pitch: -0.05 }));
        await sleep(300);
        await page.keyboard.down('KeyW');
        await sleep(1200);
        await page.keyboard.up('KeyW');
        await sleep(200);
        entry.door_blocked_at = (await walkState(page)).pose.position;
        await shot(page, `${project.name}_4_door_shut`);
        entry.door_open = await page.evaluate((id) => window.__studio.walk.toggle(id), project.door);
        await sleep(300);
        await shot(page, `${project.name}_5_door_open`);
        await page.keyboard.down('KeyW');
        await sleep(1500);
        await page.keyboard.up('KeyW');
        await sleep(200);
        entry.through_door = await walkState(page);
        await shot(page, `${project.name}_6_through_door`);
    }

    entry.steps = percentiles(await page.evaluate(() => window.__studio.walk.timings.steps));
    entry.step_calls = percentiles(await page.evaluate(() => window.__studio.walk.timings.calls));
    entry.load_steps = load();

    if (play && project.play)
    {
        // Play here from the party's pose; the launcher closes the game after a few seconds and the camera follows.
        entry.load_play = load();
        const started = Date.now();
        await page.evaluate((options) => window.__studio.app.controller.playHere({ visible: false, ...options }), project.play);
        entry.play_started = await waitFor(page, () => window.__studio.app.store.getState().play.state === 'running', 120000);
        entry.play_started_ms = Date.now() - started;
        entry.play_exited = await waitFor(page, () => !!window.__studio.marks.game_exited, 300000);
        entry.play_total_ms = Date.now() - started;
        await sleep(500);
        entry.exit = await page.evaluate(() => ({ exitPose: window.__studio.exitPose ?? null,
            camera: window.__studio.app.controller.viewport.camera(), walk: window.__studio.app.store.getState().walk.pose ?? null,
            play: window.__studio.app.store.getState().play, notes: window.__studio.app.store.getState().notes.map((n) => n.text) }));
        await shot(page, `${project.name}_7_after_game`);
    }

    // The split view: the 3D half narrower than the game's 16:9, its field of view widened to the game's width and
    // the game's frame outlined.
    await page.evaluate(() => window.__studio.app.store.setState({ viewMode: 'split' }));
    await sleep(600);
    entry.split_fov = await page.evaluate(() => window.__studio.viewport.verticalFov());
    await shot(page, `${project.name}_9_split`);

    // Esc with the pointer given back: out of walk mode.
    await page.evaluate(() => document.exitPointerLock());
    await sleep(400);
    await page.keyboard.press('Escape');
    await sleep(400);
    entry.walk_after_escapes = (await walkState(page)).walk;
    await shot(page, `${project.name}_8_left`);
    await context.close();
}

results.load_end = load();
writeFileSync(join(out, 'walk.json'), `${JSON.stringify(results, null, 1)}\n`);
writeFileSync(join(out, 'host.log'), hostLog);
await browser.close();
host.kill();
console.log(JSON.stringify(results, null, 1));
