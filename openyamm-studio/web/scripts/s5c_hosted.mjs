#!/usr/bin/env node
// S5c, hosted mode, end to end against a local static origin (S5_BROWSER_EDITOR.md 6.4 S5c; 2.11 to 2.14): stages
// nothing itself (run stage_hosted.mjs first), serves the staged site with scripts/hosted_server.mjs, and in headless
// Chrome and Firefox (Playwright from S5-0 spike 1's folder):
//   slice    opens a player's install with the page's own folder input, opens the slice dungeon, builds it with the
//            Build button, exports the build and the mod folder with the Files menu, and compares the build with the
//            native core's build against the same install (extracted: tests/extract_install.py)
//   calib    opens assets_dev (a checkout) and the Xeen root, builds every calibration project in the page's worker
//            (one worker, one map at a time) and compares every output file and the lock with the native build
//   budgets  opening Darkmoor and Erathia, the indoor and outdoor commit, a brush stroke, walk mode's steps, the
//            checks job (Darkmoor's solve), the heap after each (2.13)
//   firstopen opening Darkmoor first and again in one page (the start of budgets, alone)
//   revisit  opening Darkmoor first on a second and third visit in the same browser profile (caches kept)
//   mm9      the largest MM9 region (thjorgardcity.blv) of the install as an overlay project: opened, its original's
//            mesh, its audit: the heap (PLAN 9's 1 GB)
//   folder   (Chrome) a project opened through the File System Access path (showDirectoryPicker answered with a
//            folder of the origin's private storage, the same handle type) and an edit written back into it
//   offline  (Chrome) the page and the core opening again with the static server stopped (the service worker)
//   pair     the page on https marked public pairing with a local `oymap studio` (--allow-origin): without the
//            local-network permission (Chrome refuses at once, Firefox waits for the prompt) and with it (paired,
//            the host's projects listed)
//
//   node scripts/s5c_hosted.mjs [--browsers chrome,firefox] [--parts slice,calib,budgets,mm9,folder,offline,pair]
//        [--out <folder>] [--version <staged version>] [--install <player's install>] [--install-tree <extracted>]
//        [--site <staged site, default openyamm-studio/hosted_site>] [--native <oymap for the references, default build-s4>]
// Writes <out>/results.json and PNGs. Every number has the load average beside it.
import { spawn, spawnSync } from 'node:child_process';
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createServer } from 'node:net';
import { basename, dirname, join, resolve } from 'node:path';
import { randomBytes } from 'node:crypto';
import { unzipSync } from '../node_modules/three/examples/jsm/libs/fflate.module.js';

const web = resolve(import.meta.dirname, '..');
const studio = resolve(web, '..');
const repo = resolve(studio, '..');
const args = process.argv.slice(2);
const option = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);
const out = resolve(option('--out', join(studio, 's5c_work', 'run')));
const browsers = option('--browsers', 'chrome,firefox').split(',');
const parts = new Set(option('--parts', 'slice,calib,budgets,mm9,folder,offline,pair').split(','));
const site = resolve(option('--site', join(studio, 'hosted_site')));
const version = option('--version', JSON.parse(readFileSync(join(site, 'studio', 'versions.json'), 'utf8')).latest);
const install = resolve(option('--install', join(repo, 'build-rehearsal', 'installs', 'windows', 'OpenYAMM')));
const installTree = resolve(option('--install-tree', join(studio, 's5c_work', 'install20_tree')));
const assetsDev = join(repo, 'assets_dev');
const xeenRoot = join(repo, 'output', 'studio_play', 'xeen_root');
const oymap = resolve(option('--native', join(studio, 'build-s4', 'oymap')));
const count = Number(option('--count', '40'));
// Extra Chrome switches for experiments (comma separated), e.g. --chrome-args=--js-flags=--no-wasm-lazy-compilation
const chromeArgs = option('--chrome-args', '').split(',').filter(Boolean);
// firstopen's asset root: assets_dev (as budgets) or the player's install (fewer files to hand to the page: quicker)
const firstOpenAssets = option('--firstopen-assets', 'assets_dev');
// budgets: also the person's own gestures through the app's edit session (timed to the 3D view drawing them)
const gestures = args.includes('--gestures');
mkdirSync(out, { recursive: true });

const spike = join(repo, 'output', 's5_spikes', '1_viewer');
process.env.PLAYWRIGHT_BROWSERS_PATH ??= join(spike, 'browsers');
const { chromium, firefox } = createRequire(join(spike, 'package.json'))('playwright');

const load = () => readFileSync('/proc/loadavg', 'utf8').split(' ').slice(0, 3).map(Number);
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));
const results = { version, started: new Date().toISOString(), load_start: load(), browsers: {}, native: {} };
const save = () => writeFileSync(join(out, 'results.json'), `${JSON.stringify(results, null, 1)}\n`);
const stats = (values) =>
{
    const sorted = [...values].sort((a, b) => a - b);
    const at = (q) => sorted[Math.min(sorted.length - 1, Math.max(0, Math.ceil(q * sorted.length) - 1))];
    return sorted.length ? { n: sorted.length, median: +at(0.5).toFixed(1), p95: +at(0.95).toFixed(1), p99: +at(0.99).toFixed(1), max: +sorted.at(-1).toFixed(1) } : null;
};

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

// --- the native references -----------------------------------------------------------------------------------------

function projectsOf()
{
    const list = [];
    for (const [briefs, root] of [[join(repo, 'devdocs', 'map_studio', 'briefs'), assetsDev], [join(repo, 'devdocs', 'xeen', 'briefs'), xeenRoot]])
    {
        for (const name of readdirSync(briefs).sort())
        {
            if (existsSync(join(briefs, name, 'L4', 'project.yml')))
            {
                list.push({ name, folder: join(briefs, name, 'L4'), root });
            }
        }
    }
    return list;
}

// A fresh copy of the project (no build, no .oymap) built by the native core into <work>/out.
function nativeBuild(name, folder, root)
{
    const work = join(out, 'native', basename(root), name);
    if (existsSync(join(work, 'rc')))
    {
        return { work, rc: Number(readFileSync(join(work, 'rc'), 'utf8')) };
    }
    mkdirSync(work, { recursive: true });
    cpSync(folder, join(work, 'proj'), { recursive: true, filter: (path) => !['build', '.oymap'].includes(basename(path)) || path === folder });
    const started = performance.now();
    const run = spawnSync(oymap, ['build', join(work, 'proj'), '--assets', root, '--out', join(work, 'out'), '--json'], { encoding: 'utf8', maxBuffer: 1 << 28 });
    writeFileSync(join(work, 'rc'), String(run.status));
    results.native[`${basename(root)}/${name}`] = { rc: run.status, ms: Math.round(performance.now() - started) };
    return { work, rc: run.status };
}

function readTree(folder, prefix = '', into = new Map())
{
    if (!existsSync(folder))
    {
        return into;
    }
    for (const entry of readdirSync(folder, { withFileTypes: true }))
    {
        const path = prefix ? `${prefix}/${entry.name}` : entry.name;
        if (entry.isDirectory())
        {
            readTree(join(folder, entry.name), path, into);
        }
        else
        {
            into.set(path, readFileSync(join(folder, entry.name)));
        }
    }
    return into;
}

// The browser's build (its build/ as a zip) and lock against the native --out folder: every file, byte for byte.
function compareBuild(nativeOut, buildZip, lockBytes)
{
    const native = readTree(nativeOut);
    const browser = new Map(Object.entries(unzipSync(buildZip)).filter(([path]) => !path.endsWith('/')));
    const problems = [];
    for (const [path, bytes] of native)
    {
        if (path === 'ids.lock.yml')
        {
            if (lockBytes && Buffer.compare(Buffer.from(lockBytes), bytes) !== 0)
            {
                problems.push('ids.lock.yml differs');
            }
            continue;
        }
        const other = browser.get(path);
        if (!other)
        {
            problems.push(`${path} missing in the browser's build`);
        }
        else if (Buffer.compare(Buffer.from(other), bytes) !== 0)
        {
            problems.push(`${path} differs`);
        }
    }
    for (const path of browser.keys())
    {
        if (!native.has(path) && path !== 'ids.lock.yml')
        {
            problems.push(`${path} only in the browser's build`);
        }
    }
    return { identical: problems.length === 0, files: native.size - (native.has('ids.lock.yml') ? 1 : 0), problems };
}

// --- the static origin and the host ----------------------------------------------------------------------------------

async function startServer(extra = [])
{
    const child = spawn(process.execPath, [join(web, 'scripts', 'hosted_server.mjs'), '--site', site, '--port', '0', ...extra], { stdio: ['ignore', 'pipe', 'inherit'] });
    const urls = [];
    await new Promise((done) =>
    {
        child.stdout.on('data', (data) =>
        {
            for (const match of String(data).matchAll(/hosted: (\S+)/g))
            {
                urls.push(match[1]);
            }
            if (urls.length >= (extra.includes('--https') ? 2 : 1))
            {
                done();
            }
        });
    });
    return { child, urls, stop: () => child.kill('SIGTERM') };
}

async function launch(which)
{
    if (which === 'firefox')
    {
        return firefox.launch({ headless: true, firefoxUserPrefs: { 'dom.webkitBlink.dirPicker.enabled': true } });
    }
    return chromium.launch({ executablePath: existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : undefined, headless: true,
        args: ['--use-angle=vulkan', '--enable-features=Vulkan', '--ignore-gpu-blocklist', ...chromeArgs] });
}

async function shot(page, which, name)
{
    await page.screenshot({ path: join(out, `${which}_${name}.png`) });
}

async function waitCore(page)
{
    await page.waitForFunction(() => window.__studio?.app?.store?.getState().connection === 'open', null, { timeout: 60000 });
}

async function openStart(page, url)
{
    await page.goto(`${url}studio/${version}/`);
    await page.waitForSelector('[data-testid=hosted-start]', { timeout: 60000 });
    await waitCore(page);
}

// The asset root through the page's own folder input (the upload picker; the browser reads the files in place).
async function openAssets(page, folder)
{
    const started = Date.now();
    await page.setInputFiles('[data-testid=install-input]', folder);
    await page.waitForFunction(() => !document.querySelector('[data-testid=hosted-busy]') && (document.querySelector('[data-testid=install-summary]') || document.querySelector('[data-testid=hosted-error]')), null, { timeout: 600000 });
    const error = await page.textContent('[data-testid=hosted-error]').catch(() => null);
    const summary = await page.evaluate(() => window.__studio.hosted.client.install);
    const pageMs = await page.evaluate(() => window.__studio.assetsOpenMs ?? null);
    const timing = await page.evaluate(() => Object.fromEntries(window.__studio.hosted.client.lastTiming));
    // automation_ms includes Playwright's own folder upload (it lists the folder for the input); page_ms is the page's
    // time from the input's files to the mounted root, worker its share.
    return { automation_ms: Date.now() - started, page_ms: pageMs, summary, worker: timing.open_assets ?? null, error, load: load() };
}

// A project folder as files of a test input (no UI), opened in the worker without views.
async function openProjectFiles(page, folder, name)
{
    await page.evaluate(() =>
    {
        if (!document.getElementById('s5c-project'))
        {
            const input = document.createElement('input');
            input.type = 'file';
            input.id = 's5c-project';
            input.webkitdirectory = true;
            input.style.display = 'none';
            document.body.appendChild(input);
        }
    });
    await page.setInputFiles('#s5c-project', folder);
    return page.evaluate(async (projectName) =>
    {
        const input = document.getElementById('s5c-project');
        const files = Array.from(input.files).map((file) => ({ path: file.webkitRelativePath || file.name, file }));
        const client = window.__studio.hosted.client;
        const started = performance.now();
        const opened = await client.openProject({ kind: 'files', files }, 'memory', projectName);
        return { opened, ms: performance.now() - started, files: files.length, timing: client.lastTiming.get('open_project') };
    }, name);
}

// Bytes from the page as base64 (Playwright passes strings, not typed arrays).
async function zipOf(page, key, what)
{
    const text = await page.evaluate(async ([projectKey, kind]) =>
    {
        const zip = await window.__studio.hosted.client.exportZip(projectKey, kind);
        let binary = '';
        for (let at = 0; at < zip.bytes.length; at += 0x8000)
        {
            binary += String.fromCharCode(...zip.bytes.subarray(at, at + 0x8000));
        }
        return btoa(binary);
    }, [key, what]);
    return new Uint8Array(Buffer.from(text, 'base64'));
}

async function workerStats(page)
{
    return page.evaluate(async () =>
    {
        const stats = await window.__studio.hosted.client.stats();
        return { heap_mb: Object.fromEntries(Object.entries(stats.heap).map(([k, v]) => [k, +(v / 1048576).toFixed(1)])),
            reads: stats.reads, textures: stats.textures };
    });
}

// --- parts -----------------------------------------------------------------------------------------------------------

// A copy of the slice dungeon (no build, no history): what the page opens, so the example is never written.
function sliceCopy()
{
    const copy = join(out, 'slice_copy');
    if (!existsSync(copy))
    {
        cpSync(join(studio, 'examples', 'gatehouse_cellars'), copy, { recursive: true, filter: (path) => !['build', '.oymap'].includes(basename(path)) || path.endsWith('gatehouse_cellars') });
    }
    return copy;
}

async function partSlice(browser, which, url, entry)
{
    const context = await browser.newContext({ viewport: { width: 1600, height: 900 }, acceptDownloads: true });
    const page = await context.newPage();
    page.on('pageerror', (error) => (entry.page_errors ??= []).push(error.message));
    const started = Date.now();
    await openStart(page, url);
    entry.start = { core_ms: Date.now() - started, worker: await page.evaluate(() => Object.fromEntries(window.__studio.hosted.client.lastTiming)) };
    await shot(page, which, '1_start');
    entry.install = await openAssets(page, install);
    entry.install_stats = await workerStats(page);
    await shot(page, which, '2_install');
    // The slice, through the page's project folder input (read only: a working copy in this browser).
    const copy = sliceCopy();
    const opening = Date.now();
    await page.setInputFiles('[data-testid=project-input]', copy);
    await page.waitForSelector('[data-testid=hosted-menu]', { timeout: 120000 });
    await page.waitForFunction(() => 'textured_full' in (window.__studio.marks ?? {}), null, { timeout: 120000 }).catch(() => undefined);
    entry.slice_open = { page_ms: Date.now() - opening, marks: await page.evaluate(() => window.__studio.marks), load: load() };
    await sleep(500);
    await shot(page, which, '3_slice');
    // Build with the button, then export the build and the mod folder through the Files menu (downloads).
    await page.click('[data-testid=hosted-build]');
    await page.waitForFunction(() => /^Built /.test(document.querySelector('[data-testid=hosted-note]')?.textContent ?? ''), null, { timeout: 120000 });
    entry.slice_build_note = await page.textContent('[data-testid=hosted-note]');
    const key = await page.evaluate(() => window.__studio.app.store.getState().projectKey);
    const download = async (testid) =>
    {
        await page.click('[data-testid=hosted-files]');
        await page.waitForSelector(`[data-testid=${testid}]`);
        const [file] = await Promise.all([page.waitForEvent('download'), page.click(`[data-testid=${testid}]`)]);
        const path = join(out, `${which}_${file.suggestedFilename()}`);
        await file.saveAs(path);
        await page.keyboard.press('Escape');
        return new Uint8Array(readFileSync(path));
    };
    const buildZip = await download('hosted-export-build');
    await shot(page, which, '4_files_menu');
    const modZip = await download('hosted-export-mod');
    entry.slice_mod_files = Object.keys(unzipSync(modZip)).filter((path) => !path.endsWith('/')).sort();
    const projectZip = await zipOf(page, key, 'project');
    const lock = unzipSync(projectZip)['ids.lock.yml'];
    const native = nativeBuild('gatehouse_cellars_install20', copy, installTree);
    entry.slice_vs_native_install = native.rc === 0 ? compareBuild(join(native.work, 'out'), buildZip, lock) : { identical: false, problems: ['native build failed'] };
    const nativeDev = nativeBuild('gatehouse_cellars', copy, assetsDev);
    entry.slice_vs_native_assets_dev = nativeDev.rc === 0 ? compareBuild(join(nativeDev.work, 'out'), buildZip, lock) : { identical: false };
    entry.slice_stats = await workerStats(page);
    entry.page_js_heap_mb = await page.evaluate(() => (performance.memory ? +(performance.memory.usedJSHeapSize / 1048576).toFixed(1) : null));
    await context.close();
}

async function partCalib(browser, which, url, entry)
{
    const context = await browser.newContext({ viewport: { width: 1600, height: 900 } });
    const page = await context.newPage();
    page.on('pageerror', (error) => (entry.page_errors ??= []).push(error.message));
    await openStart(page, url);
    entry.calib = { projects: {} };
    let current = null;
    for (const project of projectsOf())
    {
        if (current !== project.root)
        {
            entry.calib[`assets_${basename(project.root)}`] = await openAssets(page, project.root);
            current = project.root;
        }
        const native = nativeBuild(project.name, project.folder, project.root);
        const record = { root: basename(project.root) };
        try
        {
            const opened = await openProjectFiles(page, project.folder, project.name);
            record.open_ms = Math.round(opened.ms);
            const key = opened.opened.key;
            const built = await page.evaluate(async (projectKey) =>
            {
                const client = window.__studio.hosted.client;
                const started = performance.now();
                const answer = await client.call('build.run', { project: projectKey, dry_run: false });
                return { ms: performance.now() - started, files: answer.files.length, map: answer.map };
            }, key);
            record.build_ms = Math.round(built.ms);
            record.map = built.map;
            const buildZip = await zipOf(page, key, 'build');
            const lock = unzipSync(await zipOf(page, key, 'project'))['ids.lock.yml'];
            record.compare = native.rc === 0 ? compareBuild(join(native.work, 'out'), buildZip, lock) : { identical: false, problems: [`native rc ${native.rc}`] };
            record.heap = (await workerStats(page)).heap_mb;
            await page.evaluate((projectKey) => window.__studio.hosted.client.request({ type: 'close', key: projectKey }), key);
        }
        catch (error)
        {
            record.error = String(error.message ?? error).slice(0, 400);
        }
        record.load = load()[0];
        entry.calib.projects[project.name] = record;
        console.log(`${which} ${project.name}: ${record.compare?.identical ? 'identical' : `DIFFERS ${JSON.stringify(record.compare?.problems ?? record.error)}`} (build ${record.build_ms} ms, heap ${record.heap?.memory} MB)`);
        save();
    }
    const list = Object.values(entry.calib.projects);
    entry.calib.identical = list.filter((record) => record.compare?.identical).length;
    entry.calib.total = list.length;
    entry.calib.stats = await workerStats(page);
    entry.page_js_heap_mb_calib = await page.evaluate(() => (performance.memory ? +(performance.memory.usedJSHeapSize / 1048576).toFixed(1) : null));
    await context.close();
}

// Opens a project through the UI's folder input and waits for its views (the opening budget).
async function openInUi(page, folder)
{
    const started = Date.now();
    await page.evaluate(() => window.__studio.app.controller.closeProject());
    await page.waitForSelector('[data-testid=project-input]', { state: 'attached' });
    await page.setInputFiles('[data-testid=project-input]', folder);
    await page.waitForSelector('[data-testid=hosted-menu]', { timeout: 120000 });
    await page.waitForFunction(() => 'textured_full' in (window.__studio.marks ?? {}), null, { timeout: 180000 }).catch(() => undefined);
    const marks = await page.evaluate(() => window.__studio.marks);
    return { page_ms: Date.now() - started, marks, load: load() };
}

// The person's own gestures (S8f): each through the app's edit session (controller.edit, as a tool commits on pointer
// up), timed to the core's answer (commit) and to the 3D view drawing the mesh of the new revision (the app's own
// refresh after the queue runs dry: history, layout, view.mesh, the bytes, the viewport's "grey" mark). `make(index)`
// is evaluated in the page and returns the gesture's ops.
async function gestureLoop(page, n, makeOps, label)
{
    const runs = { commits: [], meshes: [], workers: [] };
    for (let index = 0; index < n; index += 1)
    {
        // --trace-gesture: a Chrome trace of the fifth gesture of each loop (all threads).
        const tracing = args.includes('--trace-gesture') && index === 4 && page.context().browser()?.browserType().name() === 'chromium';
        if (tracing)
        {
            await page.context().browser().startTracing(page, { path: join(out, `gesture_${label.replace(/\W+/g, '_')}_trace.json`),
                categories: ['devtools.timeline', 'disabled-by-default-devtools.timeline', 'v8', 'v8.execute', 'blink', 'toplevel'] });
        }
        const timing = await page.evaluate(async ([source, at, name]) =>
        {
            const studio = window.__studio;
            const ops = new Function('index', 'studio', source)(at, studio);
            const start = performance.now();
            const result = await studio.app.controller.edit({ ops, label: name });
            const committed = performance.now();
            const worker = studio.hosted?.client?.lastTiming?.get('call:edit.apply')?.ms ?? null;
            if (!result)
            {
                return { error: studio.app.store.getState().edits.error?.message ?? 'refused' };
            }
            // The 3D view's mesh of this revision drawn (marks are whole milliseconds since the page started).
            const deadline = performance.now() + 30000;
            while (!(studio.app.store.getState().edits.pending === 0 && (studio.marks.grey ?? 0) >= Math.floor(committed)
                && studio.viewsRevision === result.revision_after) && performance.now() < deadline)
            {
                await new Promise((done) => setTimeout(done, 2));
            }
            const shown = performance.now();
            // The app's later work (the history, its full check 0.7 s after the views) runs before the next gesture:
            // the next one starts once the worker has had nothing to answer for 0.3 s.
            await new Promise((done) => setTimeout(done, 750));
            const waiting = () => studio.hosted.client.waiting?.size ?? 0;
            for (let quiet = 0; quiet < 3 && performance.now() < deadline + 30000;)
            {
                await new Promise((done) => setTimeout(done, 100));
                quiet = waiting() === 0 ? quiet + 1 : 0;
            }
            return { commit: committed - start, mesh: shown - start, worker, timedOut: shown >= deadline };
        }, [makeOps, index, label]);
        if (tracing)
        {
            await page.context().browser().stopTracing();
        }
        if (timing.error)
        {
            throw new Error(`gesture ${label} ${index}: ${timing.error}`);
        }
        runs.commits.push(timing.commit);
        runs.meshes.push(timing.mesh);
        if (typeof timing.worker === 'number')
        {
            runs.workers.push(timing.worker);
        }
    }
    return { commit: stats(runs.commits), commit_and_mesh: stats(runs.meshes), in_worker: stats(runs.workers), load: load() };
}

async function partBudgets(browser, which, url, entry)
{
    const context = await browser.newContext({ viewport: { width: 1600, height: 900 } });
    const page = await context.newPage();
    page.on('pageerror', (error) => (entry.page_errors ??= []).push(error.message));
    await openStart(page, url);
    entry.budgets = {};
    entry.budgets.assets = await openAssets(page, assetsDev);
    // Each project from a copy (the page writes nothing back: memory), so the briefs are never touched.
    const copyOf = (name) =>
    {
        const target = join(out, 'budget_copies', name);
        if (!existsSync(target))
        {
            cpSync(join(repo, 'devdocs', 'map_studio', 'briefs', name, 'L4'), target, { recursive: true, filter: (path) => !['build', '.oymap'].includes(basename(path)) || path.endsWith('/L4') });
        }
        return target;
    };
    // --- Darkmoor: open, indoor commit, 3D after it, walk, the checks job (its solve).
    entry.budgets.darkmoor_open = await openInUi(page, copyOf('mm6_cd2'));
    entry.budgets.darkmoor_open_heap = (await workerStats(page)).heap_mb;
    // Opened again in the same page: the core's code compiled (the first opening compiles it as it goes).
    entry.budgets.darkmoor_reopen = await openInUi(page, copyOf('mm6_cd2'));
    await shot(page, which, '5_darkmoor');
    entry.budgets.indoor_commit = await page.evaluate(async (n) =>
    {
        const client = window.__studio.hosted.client;
        const key = window.__studio.app.store.getState().projectKey;
        const opened = await client.call('project.open', { project: key });
        let revision = opened.revision;
        const rooms = opened.files['rooms.yml'].tree.rooms;
        let room = null;
        for (const candidate of rooms.filter((r) => Array.isArray(r.outline) && r.outline.length >= 4 && !r.floor_points))
        {
            const point = candidate.outline[1];
            const ops = [{ op: 'patch', id: candidate.id, file: 'rooms.yml', patch: [{ op: 'replace', path: '/outline/1', value: [point[0], point[1] + 16] }] }];
            const answer = await client.call('edit.apply', { project: key, ops, dry_run: true, allow_errors: true }).catch(() => null);
            if (answer && answer.new_issues.length === 0)
            {
                room = candidate;
                break;
            }
        }
        const commits = [];
        const meshes = [];
        const core = [];
        for (let index = 0; index < n; index += 1)
        {
            const point = room.outline[1];
            const moved = index % 2 === 0 ? [point[0], point[1] + 16] : [point[0], point[1] - 16];
            const ops = [{ op: 'patch', id: room.id, file: 'rooms.yml', patch: [{ op: 'test', path: '/outline/1', value: point }, { op: 'replace', path: '/outline/1', value: moved }] }];
            const start = performance.now();
            const answer = await client.call('edit.apply', { project: key, ops, expect_revision: revision, rebase: true, allow_errors: true, author: 'user', label: 'move corner' });
            const committed = performance.now();
            core.push(client.lastTiming.get('call:edit.apply').ms);
            const mesh = await client.call('view.mesh', { project: key });
            await client.fetchBytes(`/mesh/${encodeURIComponent(key)}/${encodeURIComponent(mesh.file.split('/').pop())}`);
            meshes.push(performance.now() - start);
            commits.push(committed - start);
            revision = answer.revision_after;
            room.outline[1] = moved;
        }
        return { room: room.id, commits, meshes, core };
    }, count);
    entry.budgets.indoor_commit = { room: entry.budgets.indoor_commit.room, commit: stats(entry.budgets.indoor_commit.commits),
        commit_and_mesh: stats(entry.budgets.indoor_commit.meshes), in_worker: stats(entry.budgets.indoor_commit.core), load: load() };
    entry.budgets.indoor_heap = (await workerStats(page)).heap_mb;
    // The core calls of the last commits (the app's own refresh after each answer runs in the same worker).
    entry.budgets.indoor_trace = await page.evaluate(async () => (await window.__studio.hosted.client.stats(true)).timings.slice(-24)
        .map((call) => `${call.method} ${Math.round(call.ms)}`));
    // The same corner moved by the person's own gestures (S8f).
    if (gestures)
    {
        await page.evaluate((roomId) => { window.__s8fRoom = roomId; }, entry.budgets.indoor_commit.room);
        entry.budgets.indoor_gesture = await gestureLoop(page, count, `
            const project = studio.app.store.getState().project.value;
            const room = project.files['rooms.yml'].tree.rooms.find((r) => r.id === window.__s8fRoom);
            const point = room.outline[1];
            const moved = index % 2 === 0 ? [point[0], point[1] + 16] : [point[0], point[1] - 16];
            return [{ op: 'patch', id: room.id, file: 'rooms.yml', patch: [{ op: 'test', path: '/outline/1', value: point }, { op: 'replace', path: '/outline/1', value: moved }] }];`, 'move corner');
    }
    // Walk mode on Darkmoor (G), from the start, W for 3 s.
    await page.evaluate(() =>
    {
        const start = window.__studio.app.store.getState().layout.value?.start;
        if (start)
        {
            window.__studio.viewport.setCamera({ eye: [start.at[0], start.at[1], start.at[2] + 160], yaw: ((start.facing ?? 0) * Math.PI) / 180, pitch: 0 });
        }
    });
    await page.locator('canvas.oy-viewport-canvas').hover();
    const walkStarted = Date.now();
    await page.keyboard.press('KeyG');
    await page.waitForFunction(() => ['on', 'error'].includes(window.__studio.app.store.getState().walk.state), null, { timeout: 120000 });
    entry.budgets.walk = { state: await page.evaluate(() => window.__studio.app.store.getState().walk), enter_ms: Date.now() - walkStarted,
        marks: await page.evaluate(() => ({ prepare: window.__studio.marks.walk_prepare_ms, ready: window.__studio.marks.walk_ready_ms })) };
    if (entry.budgets.walk.state.state === 'on')
    {
        const from = entry.budgets.walk.state.pose?.position;
        await page.keyboard.down('KeyW');
        await sleep(3000);
        await page.keyboard.up('KeyW');
        await sleep(200);
        const walked = await page.evaluate(() => ({ pose: window.__studio.app.store.getState().walk.pose, steps: window.__studio.walk.timings.steps, calls: window.__studio.walk.timings.calls }));
        entry.budgets.walk.steps = stats(walked.steps);
        entry.budgets.walk.calls = stats(walked.calls.filter((value) => typeof value === 'number'));
        entry.budgets.walk.moved = from && walked.pose ? Math.round(Math.hypot(walked.pose.position[0] - from[0], walked.pose.position[1] - from[1])) : null;
        entry.budgets.walk.load = load();
        await shot(page, which, '6_darkmoor_walk');
        await page.evaluate(() => window.__studio.app.controller.toggleWalk());
    }
    // The checks job on request (check.audit with reach and solve): Darkmoor's solve is the heap's risk.
    entry.budgets.darkmoor_checks = await page.evaluate(async () =>
    {
        const client = window.__studio.hosted.client;
        const key = window.__studio.app.store.getState().projectKey;
        const started = performance.now();
        const done = new Promise((resolve) => client.onNotice('job_done', (notice) => resolve(notice.job)));
        await client.call('jobs.start', { project: key, kind: 'checks' });
        const job = await done;
        return { ms: performance.now() - started, state: job.state, line: job.line, seconds: job.seconds, error: job.error };
    });
    entry.budgets.darkmoor_checks.heap = (await workerStats(page)).heap_mb;
    entry.budgets.darkmoor_checks.load = load();

    // --- Erathia: open, the structure commit, a stroke.
    entry.budgets.erathia_open = await openInUi(page, copyOf('mm7_7out03'));
    entry.budgets.erathia_open_heap = (await workerStats(page)).heap_mb;
    await shot(page, which, '7_erathia');
    const outdoor = await page.evaluate(async (n) =>
    {
        const client = window.__studio.hosted.client;
        const key = window.__studio.app.store.getState().projectKey;
        const opened = await client.call('project.open', { project: key });
        let revision = opened.revision;
        const sketch = opened.files['sketch.yml'].tree;
        const building = sketch.structures.find((s) => s.kind === 'building' && Array.isArray(s.parts) && s.parts[0].roof_height === 128);
        const runs = { structure: { commits: [], meshes: [], core: [] }, stroke: { commits: [], meshes: [], core: [] } };
        const row = structuredClone(sketch.heights.nodes[0].rows[3]);
        const block = sketch.heights.nodes[0].key ?? 'block1';
        for (const mode of ['structure', 'stroke'])
        {
            for (let index = 0; index < n; index += 1)
            {
                let ops;
                if (mode === 'structure')
                {
                    const from = index % 2 === 0 ? 128 : 136;
                    const to = index % 2 === 0 ? 136 : 128;
                    ops = [{ op: 'patch', id: building.id, file: 'sketch.yml', patch: [{ op: 'test', path: `/parts/${building.parts[0].id}/roof_height`, value: from }, { op: 'replace', path: `/parts/${building.parts[0].id}/roof_height`, value: to }] }];
                }
                else
                {
                    const before = structuredClone(row);
                    const last = row.length - 1;
                    row[last] = (row[last] ?? 0) + (index % 2 === 0 ? 1 : -1);
                    ops = [{ op: 'patch', file: 'sketch.yml', patch: [{ op: 'test', path: `/heights/nodes/${block}/rows/3`, value: before }, { op: 'replace', path: `/heights/nodes/${block}/rows/3`, value: structuredClone(row) }] }];
                }
                const start = performance.now();
                const answer = await client.call('edit.apply', { project: key, ops, expect_revision: revision, rebase: true, allow_errors: true, author: 'user', label: mode });
                const committed = performance.now();
                runs[mode].core.push(client.lastTiming.get('call:edit.apply').ms);
                const mesh = await client.call('view.mesh', { project: key });
                await client.fetchBytes(`/mesh/${encodeURIComponent(key)}/${encodeURIComponent(mesh.file.split('/').pop())}`);
                runs[mode].meshes.push(performance.now() - start);
                runs[mode].commits.push(committed - start);
                revision = answer.revision_after;
            }
        }
        return { building: building.id, runs };
    }, count);
    for (const mode of ['structure', 'stroke'])
    {
        const run = outdoor.runs[mode];
        entry.budgets[`outdoor_${mode}`] = { commit: stats(run.commits), commit_and_mesh: stats(run.meshes), in_worker: stats(run.core), load: load() };
    }
    entry.budgets.outdoor_heap = (await workerStats(page)).heap_mb;
    entry.budgets.outdoor_trace = await page.evaluate(async () => (await window.__studio.hosted.client.stats(true)).timings.slice(-24)
        .map((call) => `${call.method} ${Math.round(call.ms)}`));
    if (gestures)
    {
        await page.evaluate((id) => { window.__s8fBuilding = id; }, outdoor.building);
        entry.budgets.outdoor_structure_gesture = await gestureLoop(page, count, `
            const sketch = studio.app.store.getState().project.value.files['sketch.yml'].tree;
            const building = sketch.structures.find((s) => s.id === window.__s8fBuilding);
            const part = building.parts[0];
            const to = part.roof_height === 128 ? 136 : 128;
            return [{ op: 'patch', id: building.id, file: 'sketch.yml', patch: [{ op: 'test', path: \`/parts/\${part.id}/roof_height\`, value: part.roof_height }, { op: 'replace', path: \`/parts/\${part.id}/roof_height\`, value: to }] }];`, 'structure');
        entry.budgets.outdoor_stroke_gesture = await gestureLoop(page, count, `
            const sketch = studio.app.store.getState().project.value.files['sketch.yml'].tree;
            const block = sketch.heights.nodes[0].key ?? 'block1';
            const before = structuredClone(sketch.heights.nodes[0].rows[3]);
            const row = structuredClone(before);
            const last = row.length - 1;
            row[last] = (row[last] ?? 0) + (index % 2 === 0 ? 1 : -1);
            return [{ op: 'patch', file: 'sketch.yml', patch: [{ op: 'test', path: \`/heights/nodes/\${block}/rows/3\`, value: before }, { op: 'replace', path: \`/heights/nodes/\${block}/rows/3\`, value: row }] }];`, 'stroke');
    }
    entry.budgets.final_stats = await workerStats(page);
    entry.page_js_heap_mb_budgets = await page.evaluate(() => (performance.memory ? +(performance.memory.usedJSHeapSize / 1048576).toFixed(1) : null));
    await context.close();
}

// Only the opening of Darkmoor, first and again in one page (S8f: the budgets part's start, for quick comparisons).
async function partFirstOpen(browser, which, url, entry)
{
    const context = await browser.newContext({ viewport: { width: 1600, height: 900 } });
    // What the core's download took on the wire (its encoding and body bytes).
    const downloads = [];
    context.on('response', (response) =>
    {
        if (/\/core\/oymap_worker\.(wasm|mjs)$/.test(response.url()))
        {
            downloads.push(response.request().sizes().then((sizes) => ({ url: response.url().split('/').pop(),
                encoding: response.headers()['content-encoding'] ?? 'identity', body_bytes: sizes.responseBodySize })).catch(() => null));
        }
    });
    const page = await context.newPage();
    page.on('pageerror', (error) => (entry.page_errors ??= []).push(error.message));
    const coreStarted = Date.now();
    await openStart(page, url);
    const coreMs = Date.now() - coreStarted;
    const copy = join(out, 'budget_copies', 'mm6_cd2');
    if (!existsSync(copy))
    {
        cpSync(join(repo, 'devdocs', 'map_studio', 'briefs', 'mm6_cd2', 'L4'), copy, { recursive: true, filter: (path) => !['build', '.oymap'].includes(basename(path)) || path.endsWith('/L4') });
    }
    entry.firstopen = { core_ms: coreMs, core_download: (await Promise.all(downloads)).filter(Boolean) };
    entry.firstopen.assets = await openAssets(page, firstOpenAssets === 'install' ? install : assetsDev);
    // --trace-open: a Chrome trace of the first opening (all threads, the worker's GC and tasks included).
    if (args.includes('--trace-open') && which === 'chrome')
    {
        await browser.startTracing(page, { path: join(out, 'firstopen_trace.json'), screenshots: false,
            categories: ['devtools.timeline', 'disabled-by-default-devtools.timeline', 'v8', 'v8.execute', 'blink', 'disabled-by-default-v8.gc', 'toplevel'] });
    }
    entry.firstopen.open = await openInUi(page, copy);
    if (args.includes('--trace-open') && which === 'chrome')
    {
        await browser.stopTracing();
    }
    const trace = async () => page.evaluate(async () =>
    {
        const stats = await window.__studio.hosted.client.stats(true);
        return { calls: stats.timings.map((call) => `${call.method} ${Math.round(call.ms)}`), reads: stats.reads };
    });
    entry.firstopen.open_trace = await trace();
    entry.firstopen.reopen = await openInUi(page, copy);
    entry.firstopen.reopen_trace = await trace();
    await context.close();
}

// The first opening of Darkmoor on a second visit (S8f): the same browser profile (its HTTP cache, the service
// worker's copy and the browser's compiled-code cache of the core) opening the page again after a first visit that
// opened Darkmoor once.
async function partRevisit(browser, which, url, entry)
{
    const context = await browser.newContext({ viewport: { width: 1600, height: 900 } });
    const copy = join(out, 'budget_copies', 'mm6_cd2');
    if (!existsSync(copy))
    {
        cpSync(join(repo, 'devdocs', 'map_studio', 'briefs', 'mm6_cd2', 'L4'), copy, { recursive: true, filter: (path) => !['build', '.oymap'].includes(basename(path)) || path.endsWith('/L4') });
    }
    entry.revisit = {};
    for (const visit of ['first_visit', 'second_visit', 'third_visit'])
    {
        const page = await context.newPage();
        page.on('pageerror', (error) => (entry.page_errors ??= []).push(error.message));
        const started = Date.now();
        await openStart(page, url);
        const coreMs = Date.now() - started;
        await openAssets(page, assetsDev);
        const opened = await openInUi(page, copy);
        entry.revisit[visit] = { core_ms: coreMs, darkmoor_open: opened };
        // Time for the browser to write its code cache after the first opening.
        await sleep(3000);
        await page.close();
    }
    await context.close();
}

async function partMm9(browser, which, url, entry)
{
    const context = await browser.newContext({ viewport: { width: 1600, height: 900 } });
    const page = await context.newPage();
    page.on('pageerror', (error) => (entry.page_errors ??= []).push(error.message));
    await openStart(page, url);
    entry.mm9 = { install: await openAssets(page, install) };
    entry.mm9.after_install = (await workerStats(page)).heap_mb;
    entry.mm9.steps = await page.evaluate(async () =>
    {
        const client = window.__studio.hosted.client;
        const steps = {};
        let started = performance.now();
        const made = await client.importMap({ kind: 'memory' }, 'thjorgardcity.blv', 'mm9');
        steps.import_ms = performance.now() - started;
        const stat = async () => (await client.stats()).heap.memory / 1048576;
        steps.import_heap = await stat();
        started = performance.now();
        await client.call('project.open', { project: made.key });
        steps.open_ms = performance.now() - started;
        started = performance.now();
        const original = await client.call('view.original_mesh', { project: made.key });
        const bytes = await client.fetchBytes(`/mesh/${encodeURIComponent(made.key)}/${encodeURIComponent(original.file.split('/').pop())}`);
        steps.original_mesh_ms = performance.now() - started;
        steps.original_mesh_bytes = bytes.bytes.byteLength;
        steps.original_heap = await stat();
        started = performance.now();
        const validated = await client.call('check.validate', { project: made.key });
        steps.validate_ms = performance.now() - started;
        steps.validate_issues = validated.issues?.length ?? null;
        started = performance.now();
        const built = await client.call('build.run', { project: made.key, dry_run: false }).catch((error) => ({ error: error.message }));
        steps.build_ms = performance.now() - started;
        steps.build = built.error ?? `${built.kind} ${built.map} ${built.files?.length} files`;
        steps.build_heap = await stat();
        started = performance.now();
        const done = new Promise((resolve) => client.onNotice('job_done', (notice) => resolve(notice.job)));
        await client.call('jobs.start', { project: made.key, kind: 'checks' });
        const job = await done;
        steps.checks_ms = performance.now() - started;
        steps.checks = `${job.state}: ${job.line || job.error}`;
        steps.checks_heap = await stat();
        return steps;
    });
    entry.mm9.stats = await workerStats(page);
    entry.mm9.load = load();

    await context.close();
}

async function partFolder(browser, which, url, entry)
{
    // The File System Access route: showDirectoryPicker answered with a folder of the origin's private storage (the
    // same FileSystemDirectoryHandle the person's folder is), holding a copy of the slice.
    const context = await browser.newContext({ viewport: { width: 1600, height: 900 } });
    await context.addInitScript(() =>
    {
        window.showDirectoryPicker = async () =>
        {
            const root = await navigator.storage.getDirectory();
            return root.getDirectoryHandle('s5c_folder_test', { create: true });
        };
    });
    const page = await context.newPage();
    page.on('pageerror', (error) => (entry.page_errors ??= []).push(error.message));
    await openStart(page, url);
    await openAssets(page, install);
    // The copy, written into the private folder from a test input.
    await page.evaluate(() =>
    {
        const input = document.createElement('input');
        input.type = 'file';
        input.id = 's5c-copy';
        input.webkitdirectory = true;
        document.body.appendChild(input);
    });
    await page.setInputFiles('#s5c-copy', sliceCopy());
    await page.evaluate(async () =>
    {
        const root = await navigator.storage.getDirectory();
        await root.removeEntry('s5c_folder_test', { recursive: true }).catch(() => undefined);
        const folder = await root.getDirectoryHandle('s5c_folder_test', { create: true });
        for (const file of document.getElementById('s5c-copy').files)
        {
            const parts = file.webkitRelativePath.split('/').slice(1);
            let dir = folder;
            for (const part of parts.slice(0, -1))
            {
                dir = await dir.getDirectoryHandle(part, { create: true });
            }
            const handle = await dir.getFileHandle(parts.at(-1), { create: true });
            const writable = await handle.createWritable();
            await writable.write(await file.arrayBuffer());
            await writable.close();
        }
    });
    await page.click('[data-testid=pick-project]');
    await page.waitForSelector('[data-testid=hosted-menu]', { timeout: 60000 });
    entry.folder = await page.evaluate(async () =>
    {
        const client = window.__studio.hosted.client;
        const key = window.__studio.app.store.getState().projectKey;
        const project = (await client.call('host.projects', {})).projects.find((p) => p.key === key);
        const opened = await client.call('project.open', { project: key });
        const root = await navigator.storage.getDirectory();
        const folder = await root.getDirectoryHandle('s5c_folder_test');
        const read = async () => (await (await folder.getFileHandle('rooms.yml')).getFile()).text();
        const before = await read();
        const room = opened.files['rooms.yml'].tree.rooms[0];
        const point = room.outline[1];
        const ops = [{ op: 'patch', id: room.id, file: 'rooms.yml', patch: [{ op: 'test', path: '/outline/1', value: point },
            { op: 'replace', path: '/outline/1', value: [point[0], point[1] + 16] }] }];
        const answer = await client.call('edit.apply', { project: key, ops, expect_revision: opened.revision, author: 'user', label: 'move corner', allow_errors: true });
        // The folder's own rooms.yml and history, read through its handle.
        const text = await read();
        const history = await folder.getDirectoryHandle('.oymap').then(() => true, () => false);
        return { backing: project.backing, label: project.label, applied: answer.applied, revision: answer.revision_after,
            written_back: text !== before && text.includes(`${point[1] + 16}`), history_folder: history };
    });
    await shot(page, which, '8_folder');
    // The views after the edit's own refresh (the mesh and its textures again).
    await page.waitForFunction(() => window.__studio.app.store.getState().edits.pending === 0, null, { timeout: 30000 }).catch(() => undefined);
    await sleep(3000);
    await shot(page, which, '8_folder_after');
    await context.close();
}

async function partOffline(browser, which, entry)
{
    const server = await startServer();
    const url = server.urls[0];
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    await openStart(page, url);
    await page.waitForFunction(() => navigator.serviceWorker?.controller !== null || navigator.serviceWorker.ready.then(() => true), null, { timeout: 30000 });
    await page.evaluate(() => navigator.serviceWorker.ready);
    await page.reload();
    await page.waitForFunction(() => navigator.serviceWorker.controller !== null, null, { timeout: 30000 });
    server.stop();
    await sleep(500);
    const started = Date.now();
    let ok = false;
    try
    {
        await page.reload();
        await page.waitForSelector('[data-testid=hosted-start]', { timeout: 30000 });
        await waitCore(page);
        ok = true;
    }
    catch (error)
    {
        entry.offline_error = String(error.message).slice(0, 300);
    }
    entry.offline = { opened_without_server: ok, ms: Date.now() - started };
    await shot(page, which, '9_offline');
    await context.close();
}

async function partPair(which, entry)
{
    const certs = join(out, 'certs');
    if (!existsSync(join(certs, 'key.pem')))
    {
        mkdirSync(certs, { recursive: true });
        spawnSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '30', '-subj', '/CN=127.0.0.1', '-addext', 'subjectAltName=IP:127.0.0.1',
            '-keyout', join(certs, 'key.pem'), '-out', join(certs, 'cert.pem')]);
    }
    const httpsPort = await freePort();
    const server = await startServer(['--https', String(httpsPort), '--cert', join(certs, 'cert.pem'), '--key', join(certs, 'key.pem')]);
    const origin = `https://127.0.0.1:${httpsPort}`;
    // The local studio, as a person would start it, allowing the hosted origin.
    const hostPort = await freePort();
    const token = randomBytes(12).toString('hex');
    const host = spawn(process.execPath, [join(studio, 'host', 'src', 'host.mjs'), 'studio', '--port', String(hostPort), '--token', token,
        '--allow-origin', origin, '--discovery', join(out, 'pair_host.json'), '--inbox', join(out, 'pair_inbox'), '--background', 'off'],
    { cwd: repo, stdio: ['ignore', 'pipe', 'pipe'] });
    let hostLog = '';
    host.stdout.on('data', (data) => { hostLog += data; });
    host.stderr.on('data', (data) => { hostLog += data; });
    for (let i = 0; i < 100 && !hostLog.includes('oymap studio:'); ++i)
    {
        await sleep(100);
    }
    const link = `http://127.0.0.1:${hostPort}/#token=${token}`;
    entry.pair = {};
    const cases = [['without_permission', null], ['with_permission', ['local-network-access']]];
    try
    {
        for (const [name, grant] of cases)
        {
            const browser = which === 'firefox'
                ? await firefox.launch({ headless: true, firefoxUserPrefs: { 'network.lna.address_space.public.override': `127.0.0.1:${httpsPort}`,
                    'network.lna.enabled': true, 'network.lna.blocking': true, 'network.lna.websocket.enabled': true } })
                : await chromium.launch({ executablePath: existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : undefined, headless: true,
                    args: [`--ip-address-space-overrides=127.0.0.1:${httpsPort}=public`] });
            const record = { browser: browser.version() };
            try
            {
                const context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1400, height: 900 } });
                if (grant)
                {
                    await context.grantPermissions(grant, { origin }).catch((error) => { record.grant_error = String(error.message).slice(0, 200); });
                }
                const page = await context.newPage();
                await openStart(page, `${origin}/`);
                await page.fill('[data-testid=pair-text]', link);
                const started = Date.now();
                await page.click('[data-testid=pair-button]');
                const states = [];
                const deadline = Date.now() + 20000;
                while (Date.now() < deadline)
                {
                    // Paired, the page reloads into paired mode: a check during the reload is tried again.
                    try
                    {
                        const text = await page.textContent('[data-testid=pair-state]', { timeout: 1000 }).catch(() => null);
                        if (text && states.at(-1)?.text !== text)
                        {
                            states.push({ ms: Date.now() - started, text });
                        }
                        if (await page.$('[data-testid=paired-banner]') || (text && /refused|no answer|closed/.test(text)))
                        {
                            break;
                        }
                    }
                    catch
                    {
                        await page.waitForLoadState('load').catch(() => undefined);
                    }
                    await sleep(100);
                }
                record.states = states;
                record.paired = Boolean(await page.$('[data-testid=paired-banner]'));
                if (record.paired)
                {
                    await page.waitForFunction(() => window.__studio.app.store.getState().projects.state === 'ready', null, { timeout: 30000 });
                    record.host_projects = await page.evaluate(() => window.__studio.app.store.getState().projects.value.length);
                    record.mode = await page.evaluate(() => window.__studio.hosted.client.mode);
                    record.no_token_in_url = !page.url().includes(token);
                    await shot(page, which, '10_paired');
                    // A host project opened from the hosted page: its mesh through the host's byte route (CORS).
                    const first = await page.evaluate(() => window.__studio.app.store.getState().projects.value.find((p) => /gatehouse/.test(p.key))?.key);
                    if (first)
                    {
                        await page.evaluate((key) => window.__studio.app.controller.openProject(key), first);
                        await page.waitForFunction(() => 'textured_full' in (window.__studio.marks ?? {}), null, { timeout: 60000 }).catch(() => undefined);
                        record.paired_open = await page.evaluate(() => ({ marks: window.__studio.marks, play_here: !document.querySelector('[data-testid=play-here]')?.disabled }));
                        await shot(page, which, '11_paired_project');
                        // Walk mode, paired: the host builds, the page's own walk worker (its core from the hosted
                        // site) fetches the walk's files from the host's byte routes with the token.
                        await page.locator('canvas.oy-viewport-canvas').hover();
                        await page.keyboard.press('KeyG');
                        await page.waitForFunction(() => ['on', 'error'].includes(window.__studio.app.store.getState().walk.state), null, { timeout: 60000 }).catch(() => undefined);
                        record.paired_walk = await page.evaluate(() => { const walk = window.__studio.app.store.getState().walk; return { state: walk.state, message: walk.message ?? null }; });
                    }
                }
                else
                {
                    await shot(page, which, `10_pair_${name}`);
                }
                await context.close();
            }
            catch (error)
            {
                record.error = String(error.message).slice(0, 400);
            }
            finally
            {
                await browser.close();
            }
            entry.pair[name] = record;
        }
    }
    finally
    {
        host.kill('SIGTERM');
        server.stop();
    }
}

// --- run -------------------------------------------------------------------------------------------------------------

const server = await startServer();
const url = server.urls[0];
results.origin = url;
try
{
    for (const which of browsers)
    {
        const entry = (results.browsers[which] ??= {});
        const browser = await launch(which);
        entry.version = browser.version();
        try
        {
            for (const [part, run] of [['slice', partSlice], ['calib', partCalib], ['budgets', partBudgets], ['firstopen', partFirstOpen], ['revisit', partRevisit], ['mm9', partMm9], ['folder', partFolder]])
            {
                if (!parts.has(part) || (part === 'folder' && which !== 'chrome'))
                {
                    continue;
                }
                const started = Date.now();
                try
                {
                    await run(browser, which, url, entry);
                }
                catch (error)
                {
                    (entry.failures ??= {})[part] = String(error.stack ?? error).slice(0, 800);
                }
                console.log(`${which} ${part}: ${Math.round((Date.now() - started) / 1000)} s${entry.failures?.[part] ? ` FAILED ${entry.failures[part].split('\n')[0]}` : ''}`);
                save();
            }
            if (parts.has('offline'))
            {
                await partOffline(browser, which, entry).catch((error) => { (entry.failures ??= {}).offline = String(error.message); });
                save();
            }
        }
        finally
        {
            await browser.close();
        }
        if (parts.has('pair'))
        {
            await partPair(which, entry).catch((error) => { (entry.failures ??= {}).pair = String(error.stack ?? error).slice(0, 800); });
            save();
        }
    }
}
finally
{
    server.stop();
    results.load_end = load();
    save();
}
console.log(`results: ${join(out, 'results.json')}`);
