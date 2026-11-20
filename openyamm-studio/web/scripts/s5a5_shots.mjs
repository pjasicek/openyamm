// S5a5's screenshots (S5_BROWSER_EDITOR.md 4.13): the panel gallery (light and dark) and the app on copies of the
// projects: a rebuild's scorecard and its Compare view (original and rebuild, cameras locked, at a worst place), the
// compare's heat on the plan, an outdoor rebuild's Compare view with its regions, the flow graph, the Jobs panel with
// a running job cancelled, and a pins tour (the button, the job, its pictures, the picture in the pin's thread).
// Headless Chrome on the machine's GPU; Playwright from S5-0 spike 1's folder.
//   node scripts/s5a5_shots.mjs [--out <folder>] [--only <name>]
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
const out = resolve(option('--out', join(repo, 'output', 's5a5', 'shots')));
const only = option('--only', null);
mkdirSync(out, { recursive: true });
const spike = join(repo, 'output', 's5_spikes', '1_viewer');
process.env.PLAYWRIGHT_BROWSERS_PATH ??= join(spike, 'browsers');
const { chromium } = createRequire(join(spike, 'package.json'))('playwright');
const load = () => readFileSync('/proc/loadavg', 'utf8').split(' ').slice(0, 3).map(Number);
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

const freePort = () => new Promise((done) =>
{
    const server = createServer();
    server.listen(0, '127.0.0.1', () =>
    {
        const { port } = server.address();
        server.close(() => done(port));
    });
});

// The host over the copies (output/s5a5/projects, output/s5a5/pins): its own discovery file, inbox and play mounts.
const port = await freePort();
const token = randomBytes(12).toString('hex');
const roots = [join(repo, 'output', 's5a5', 'projects'), join(repo, 'output', 's5a5', 'pins')].join(',');
const host = spawn(process.execPath, [join(studio, 'host', 'src', 'host.mjs'), 'studio', '--port', String(port), '--token', token,
    '--roots', roots, '--discovery', join(out, 'host.json'), '--inbox', join(out, 'inbox')],
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
const results = { started: new Date().toISOString(), load_start: load(), shots: {} };

async function newPage(width = 1600, height = 960)
{
    const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(String(error)));
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    return { context, page, errors };
}

const shot = async (page, name, options = {}) =>
{
    await page.screenshot({ path: join(out, `${name}.png`), ...options });
    results.shots[name] = { load: load() };
};

async function waitFor(page, test, timeout, arg)
{
    const start = Date.now();
    while (Date.now() - start < timeout)
    {
        if (await page.evaluate(test, arg))
        {
            return true;
        }
        await sleep(150);
    }
    return false;
}

const state = (page) => page.evaluate(() => window.__studio.app.store.getState());
const setState = (page, value) => page.evaluate((s) => window.__studio.app.store.setState(s), value);
const app = (page, method, ...values) => page.evaluate(([m, v]) => window.__studio.app.controller[m](...v), [method, values]);

// Every background job of the open project done (the scorecard filled).
const filled = (page, timeout = 240000) => waitFor(page, () =>
{
    const s = window.__studio.app.store.getState();
    if (s.jobs.state !== 'ready' || s.project.state !== 'ready')
    {
        return false;
    }
    const mine = s.jobs.value.filter((job) => job.revision === s.project.value.revision && job.background);
    return mine.length > 0 && mine.every((job) => job.state !== 'queued' && job.state !== 'running')
        && mine.every((job) => !job.has_result || s.jobResults[job.id] !== undefined);
}, timeout);

async function open(page, key)
{
    await page.goto(`${base}/?project=${encodeURIComponent(key)}#token=${token}`);
    await waitFor(page, () =>
    {
        const s = window.__studio;
        return !!s?.marks.textured_full || s?.app?.store.getState().mesh.state === 'error';
    }, 90000);
}

// --- the gallery ---------------------------------------------------------------------------------------------------

if (!only || only === 'gallery')
{
    for (const theme of ['light', 'dark'])
    {
        const { context, page, errors } = await newPage(1500, 900);
        await page.emulateMedia({ colorScheme: theme });
        await page.goto(`${base}/gallery.html?theme=${theme}#token=${token}`);
        await page.waitForSelector('figure[data-card]');
        await sleep(1500);
        await shot(page, `gallery_${theme}`, { fullPage: true });
        results.shots[`gallery_${theme}`].errors = errors;
        await context.close();
    }
}

// --- a rebuild: the scorecard, Compare, the plan's heat, the flow graph -------------------------------------------

if (!only || only === 'fortress')
{
    const { context, page, errors } = await newPage();
    const t0 = Date.now();
    await open(page, 'root0/mm6_6d16');
    const ok = await filled(page);
    results.fortress = { filled: ok, wall_ms: Date.now() - t0 };
    await setState(page, { drawerTab: 'scorecard' });
    await sleep(500);
    await shot(page, 'fortress_scorecard');
    await app(page, 'enterCompare');
    await waitFor(page, () => !!window.__studio.marks.original_textured, 60000);
    await sleep(800);
    await shot(page, 'fortress_compare');
    // The worst place: both cameras there.
    const worst = await page.evaluate(() =>
    {
        const s = window.__studio.app.store.getState();
        const job = s.jobs.value.find((entry) => entry.kind === 'compare' && entry.state === 'done');
        return s.jobResults[job.id].worst[0];
    });
    await app(page, 'goToPlace', worst.at, worst.yaw_radians);
    await sleep(1200);
    await shot(page, 'fortress_compare_worst');
    results.fortress.cameras = await page.evaluate(() => [window.__studio.original.camera(), window.__studio.viewport.camera()]);
    await setState(page, { viewMode: 'plan', compareHeat: true, drawerTab: 'scorecard' });
    await sleep(800);
    await shot(page, 'fortress_plan_heat');
    await setState(page, { viewMode: 'flow' });
    await sleep(800);
    await shot(page, 'fortress_flow');
    results.fortress.errors = errors;
    await context.close();
}

// --- a new dungeon (scale bands) and its flow graph ------------------------------------------------------------

if (!only || only === 'xd04')
{
    const { context, page, errors } = await newPage();
    await open(page, 'root0/xd04');
    results.xd04 = { filled: await filled(page) };
    await setState(page, { drawerTab: 'scorecard' });
    await sleep(500);
    await shot(page, 'xd04_scorecard');
    await setState(page, { viewMode: 'flow', drawerTab: 'scorecard' });
    await sleep(1000);
    await page.evaluate(() => window.__studio.app.controller.select({ id: 'room:hoist_room', file: 'rooms.yml' }, true));
    await sleep(800);
    await shot(page, 'xd04_flow');
    results.xd04.errors = errors;
    await context.close();
}

// --- an outdoor rebuild: its scorecard (compare, town feel) and Compare view with the regions -----------------

if (!only || only === 'harmondale')
{
    const { context, page, errors } = await newPage();
    await open(page, 'root0/mm7_7out02');
    results.harmondale = { filled: await filled(page) };
    await setState(page, { drawerTab: 'scorecard' });
    await sleep(500);
    await shot(page, 'harmondale_scorecard');
    await app(page, 'enterCompare');
    await waitFor(page, () => !!window.__studio.marks.original_textured, 90000);
    const worst = await page.evaluate(() =>
    {
        const s = window.__studio.app.store.getState();
        const job = s.jobs.value.find((entry) => entry.kind === 'compare' && entry.state === 'done');
        return s.jobResults[job.id].worst[0];
    });
    await app(page, 'goToPlace', worst.at);
    await sleep(2500);
    await shot(page, 'harmondale_compare');
    await setState(page, { viewMode: 'plan', compareHeat: true });
    await sleep(1000);
    await shot(page, 'harmondale_plan_heat');
    results.harmondale.errors = errors;
    await context.close();
}

// --- Jobs: a long check running, then cancelled ----------------------------------------------------------------

if (!only || only === 'jobs')
{
    const { context, page, errors } = await newPage();
    await open(page, 'root0/mm6_cd2');
    await filled(page, 300000);
    await app(page, 'startJob', 'checks');
    await waitFor(page, () => window.__studio.app.store.getState().jobs.value?.some((job) => job.kind === 'checks' && job.state === 'running' && !job.background), 60000);
    await setState(page, { drawerTab: 'jobs' });
    await sleep(1500);
    await shot(page, 'darkmoor_jobs_running');
    const running = await page.evaluate(() => window.__studio.app.store.getState().jobs.value.find((job) => job.state === 'running').id);
    const t0 = Date.now();
    await app(page, 'cancelJob', running);
    await waitFor(page, (id) => window.__studio.app.store.getState().jobs.value.find((job) => job.id === id)?.state === 'cancelled', 20000, running);
    results.jobs = { cancel_ms: Date.now() - t0 };
    await sleep(500);
    await shot(page, 'darkmoor_jobs_cancelled');
    results.jobs.errors = errors;
    await context.close();
}

// --- pins tour: the button, the job, the pictures, the picture in the thread ------------------------------------

if (!only || only === 'tour')
{
    const { context, page, errors } = await newPage();
    await open(page, 'root1/forge');
    await setState(page, { drawerTab: 'pins', pinFilter: 'all' });
    await sleep(800);
    await shot(page, 'forge_pins_before_tour');
    // Tours of earlier runs are on disk: this run's is the one that is not among them.
    const earlier = await page.evaluate(() => (window.__studio.app.store.getState().jobs.value ?? []).filter((job) => job.kind === 'pins_tour').map((job) => job.id));
    const t0 = Date.now();
    await page.click('[data-testid="pins-tour"]');
    const mine = (ids) => window.__studio.app.store.getState().jobs.value?.find((job) => job.kind === 'pins_tour' && !ids.includes(job.id));
    await waitFor(page, (ids) => (window.__studio.app.store.getState().jobs.value ?? []).some((job) => job.kind === 'pins_tour' && !ids.includes(job.id) && job.state === 'running'), 60000, earlier);
    await sleep(500);
    await shot(page, 'forge_pins_tour_running');
    const done = await waitFor(page, (ids) => (window.__studio.app.store.getState().jobs.value ?? []).some((job) => job.kind === 'pins_tour' && !ids.includes(job.id)
        && (job.state === 'done' || job.state === 'failed')), 300000, earlier);
    results.tour = { done, seconds: (Date.now() - t0) / 1000 };
    results.tour.job = await page.evaluate(`(${mine.toString()})(${JSON.stringify(earlier)})`);
    await sleep(1500);
    await setState(page, { drawerTab: 'pictures' });
    await sleep(1500);
    await shot(page, 'forge_pictures');
    const pinWithShot = await page.evaluate(() =>
    {
        const s = window.__studio.app.store.getState();
        const job = s.jobs.value.find((entry) => entry.kind === 'pins_tour' && entry.state === 'done');
        return job ? s.jobResults[job.id]?.shots.find((entry) => entry.picture)?.pin : null;
    });
    if (pinWithShot)
    {
        await setState(page, { drawerTab: 'pins', selectedPin: pinWithShot });
        await sleep(1500);
        await shot(page, 'forge_pin_thread_tour_picture');
    }
    results.tour.errors = errors;
    await context.close();
}

results.load_end = load();
writeFileSync(join(out, 's5a5_shots.json'), JSON.stringify(results, null, 1));
writeFileSync(join(out, 'host.log'), hostLog);
await browser.close();
host.kill();
console.log(JSON.stringify(results, null, 1).slice(0, 4000));
