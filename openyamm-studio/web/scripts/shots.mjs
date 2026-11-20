// Screenshots and measurements of the web app (S5_BROWSER_EDITOR.md 4.13, 2.13): starts the host on a free port
// with a token of its own, opens the panel gallery and the app on a set of projects in headless Chrome (the
// machine's GPU through Vulkan; `--swiftshader` for the CI's software GPU), writes PNGs and a JSON of the numbers,
// each with the load average beside it.
//
//   node scripts/shots.mjs [--out <folder>] [--swiftshader] [--only <name>] [--chrome <binary>]
// Playwright comes from S5-0 spike 1's folder (output/s5_spikes/1_viewer), not from web/'s own dependencies.
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
const out = resolve(option('--out', join(repo, 'output', 's5a2_shots')));
const only = option('--only', null);
const swiftshader = args.includes('--swiftshader');
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

// --- the host ------------------------------------------------------------------------------------------------------

const port = await freePort();
const token = randomBytes(12).toString('hex');
// The host's discovery file and inbox are this run's (a running studio host's must not be touched).
const host = spawn(process.execPath, [join(studio, 'host', 'src', 'host.mjs'), 'studio', '--port', String(port), '--token', token,
    '--discovery', join(out, 'host.json'), '--inbox', join(out, 'inbox')],
    { cwd: repo, stdio: ['ignore', 'pipe', 'pipe'] });
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

// --- the browser ---------------------------------------------------------------------------------------------------

const launch = swiftshader
    ? { executablePath: existsSync(chromePath) ? chromePath : undefined, headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] }
    : { executablePath: existsSync(chromePath) ? chromePath : undefined, headless: true, args: ['--use-angle=vulkan', '--enable-features=Vulkan', '--ignore-gpu-blocklist', '--enable-gpu-rasterization'] };
const browser = await chromium.launch(launch);
const results = { started: new Date().toISOString(), gpu: swiftshader ? 'swiftshader' : 'vulkan', load_start: load(), gallery: {}, projects: {} };

async function newPage(width = 1600, height = 900)
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
    const file = join(out, `${name}.png`);
    await page.screenshot({ path: file, ...options });
    return file;
};

// --- the gallery ---------------------------------------------------------------------------------------------------

if (!only || only === 'gallery')
{
    for (const theme of ['light', 'dark'])
    {
        const { context, page, errors } = await newPage(1400, 900);
        await page.goto(`${base}/gallery.html?theme=${theme}#token=${token}`);
        await page.waitForSelector('figure[data-card]');
        await sleep(1500);
        await shot(page, `gallery_${theme}`, { fullPage: true });
        results.gallery[theme] = { errors, load: load() };
        await context.close();
    }
}

// --- the app on projects -------------------------------------------------------------------------------------------

const projects = [
    { name: 'darkmoor', key: 'devdocs/map_studio/briefs/mm6_cd2/L4', room: 'room:s002', inspect: [] },
    { name: 'harmondale', key: 'devdocs/map_studio/briefs/mm7_7out02/L4', building: true, inspect: [] },
    { name: 'erathia', key: 'devdocs/map_studio/briefs/mm7_7out03/L4', building: true, inspect: [] },
    { name: 'xd01', key: 'devdocs/xeen/briefs/xd01/L4', inspect: ['room:breeding_pens'] },
    { name: 'mm8_out06', key: 'devdocs/map_studio/briefs/mm8_out06/L4', inspect: ['thing:building_42', 'thing:mad_necromancers_lab'] },
    { name: 'mm7_7d06', key: 'devdocs/map_studio/briefs/mm7_7d06/L4', inspect: ['room:moon_nave'] },
];

async function waitFor(page, test, timeout)
{
    const start = Date.now();
    while (Date.now() - start < timeout)
    {
        if (await page.evaluate(test))
        {
            return true;
        }
        await sleep(100);
    }
    return false;
}

const setState = (page, state) => page.evaluate((s) => window.__studio.app.store.setState(s), state);

for (const project of projects)
{
    if (only && only !== project.name)
    {
        continue;
    }
    const { context, page, errors } = await newPage();
    const entry = { key: project.key, load_open: load() };
    const navigation = Date.now();
    await page.goto(`${base}/?project=${encodeURIComponent(project.key)}#token=${token}`);
    const done = await waitFor(page, () =>
    {
        const s = window.__studio;
        const state = s?.app?.store.getState();
        return !!s?.marks.textured_full || state?.mesh.state === 'error' || state?.project.state === 'error';
    }, 90000);
    entry.wall_ms_to_done = Date.now() - navigation;
    const probe = await page.evaluate(() =>
    {
        const s = window.__studio;
        const state = s.app.store.getState();
        return {
            marks: s.marks, textures: s.textures, capabilities: s.capabilities, errors: s.errors,
            project: state.project.state, layout: state.layout.state, layoutError: state.layout.message,
            mesh: state.mesh.state, meshError: state.mesh.message,
            meshCounts: state.mesh.value?.counts, meshBytes: state.mesh.value?.bytes, groups: state.mesh.value?.groups?.length,
            issues: (state.validation.value?.issues ?? state.project.value?.issues ?? []).length,
        };
    });
    Object.assign(entry, { finished: done, ...probe });
    // Let the check finish so the issues drawer shows its result.
    await waitFor(page, () => window.__studio.app.store.getState().validation.state !== 'loading', 20000);
    entry.validate_ms = await page.evaluate(() => window.__studio.marks.validate_ms);
    await sleep(400);
    await shot(page, `${project.name}_split`);
    await setState(page, { viewMode: 'plan' });
    await sleep(400);
    await shot(page, `${project.name}_plan`);
    await setState(page, { viewMode: '3d' });
    await sleep(600);
    await shot(page, `${project.name}_3d`);

    // Hover and pick (2.13: under 16 ms, no core call): 500 picks at random points of the 3D view.
    entry.load_measure = load();
    const picks = await page.evaluate(() => window.__studio.viewport?.measurePicks(500) ?? []);
    if (picks.length)
    {
        const sorted = [...picks].sort((a, b) => a - b);
        entry.pick_ms = { p50: sorted[Math.floor(sorted.length * 0.5)], p95: sorted[Math.floor(sorted.length * 0.95)], max: sorted[sorted.length - 1] };
    }
    entry.frame = await page.evaluate(() => window.__studio.viewport?.measureFrameRate(120));
    const planDraw = await page.evaluate(() => (window.__studio.plan ? window.__studio.plan.drawNow() : null));
    entry.plan_draw_ms = planDraw;

    // Context loss: the view comes back from what it kept (4.4).
    const lost = await page.evaluate(() => window.__studio.viewport?.simulateContextLoss() ?? false);
    if (lost)
    {
        await sleep(800);
        entry.context_restores = await page.evaluate(() => window.__studio.viewport.contextRestores);
        await shot(page, `${project.name}_3d_after_context_loss`);
    }

    // Select something: a room or a building, through the store as a click would.
    await setState(page, { viewMode: 'split' });
    const target = await page.evaluate((wantBuilding) =>
    {
        const state = window.__studio.app.store.getState();
        const ids = state.project.value?.ids ?? [];
        const pick = wantBuilding ? ids.find((p) => p.list === 'structures' && /building/.test(p.id)) ?? ids.find((p) => p.list === 'structures')
            : ids.find((p) => p.list === 'rooms');
        return pick ?? null;
    }, !!project.building);
    if (target)
    {
        await page.evaluate((t) => window.__studio.app.controller.select({ id: t.id, file: t.file }, true), target);
        await sleep(800);
        await shot(page, `${project.name}_selected`);
        await setState(page, { inspectorTab: 'source' });
        await sleep(300);
        await shot(page, `${project.name}_source`);
        await setState(page, { inspectorTab: 'properties' });
        entry.selected = target.id;
    }
    await setState(page, { drawerTab: 'pins' });
    await sleep(200);
    await shot(page, `${project.name}_pins`);
    await setState(page, { drawerTab: 'issues' });

    // The inspector's render time in the browser (3.8): collapsed and with every section expanded.
    entry.inspector = [];
    for (const id of project.inspect)
    {
        for (const expanded of [false, true])
        {
            const times = [];
            for (let run = 0; run < 5; ++run)
            {
                await page.evaluate(() => window.__studio.app.controller.select(null));
                await sleep(50);
                await page.evaluate(() => { window.__studio.inspector = []; });
                if (expanded)
                {
                    await page.evaluate((i) => window.__studio.app.controller.select({ id: i }), id);
                    await waitFor(page, () => window.__studio.inspector.length > 0, 10000);
                    await page.evaluate(() => { window.__studio.inspector = []; });
                    await page.click('text=expand all');
                }
                else
                {
                    await page.evaluate((i) => window.__studio.app.controller.select({ id: i }), id);
                }
                await waitFor(page, () => window.__studio.inspector.length > 0, 10000);
                const recorded = await page.evaluate(() => window.__studio.inspector.at(-1));
                if (recorded)
                {
                    times.push(recorded.ms);
                }
                if (expanded)
                {
                    await page.click('text=expand all');
                }
            }
            times.sort((a, b) => a - b);
            entry.inspector.push({ id, expanded, median_ms: times[Math.floor(times.length / 2)], runs: times, load: load() });
        }
        await page.evaluate((i) => window.__studio.app.controller.select({ id: i }, true), id);
        await sleep(600);
        await shot(page, `${project.name}_inspector_${id.replace(/[^a-z0-9]+/g, '_')}`);
    }
    entry.page_errors = errors;
    results.projects[project.name] = entry;
    console.log(project.name, JSON.stringify({ marks: entry.marks, pick: entry.pick_ms, frame: entry.frame, mesh: entry.mesh, layout: entry.layout }));
    await context.close();
}

results.load_end = load();
results.host_log = hostLog.split('\n').slice(-30).join('\n');
writeFileSync(join(out, `measurements${swiftshader ? '_swiftshader' : ''}${only ? `_${only}` : ''}.json`), JSON.stringify(results, null, 1));
await browser.close();
host.kill();
console.log(`wrote ${out}`);
