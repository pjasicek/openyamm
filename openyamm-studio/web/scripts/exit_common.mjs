// What the two S5b1 exit tests share (s5b1_hand_author.mjs, s5b1_mixed.mjs): the host and the native core over a
// run folder, a headless Chrome on the machine's GPU (Playwright from S5-0 spike 1's folder), screenshots, waiting
// for the views of the latest revision, and the plan's screen points. Build the web app first (npm run build).
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, unlinkSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createServer } from 'node:net';
import { join, resolve } from 'node:path';
import { randomBytes } from 'node:crypto';

export const web = resolve(import.meta.dirname, '..');
export const studio = resolve(web, '..');
export const repo = resolve(studio, '..');
export const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

const freePort = () => new Promise((done) =>
{
    const server = createServer();
    server.listen(0, '127.0.0.1', () =>
    {
        const { port } = server.address();
        server.close(() => done(port));
    });
});

// A run: the host over `roots`, a browser page, and the helpers. `prefix` names this test's screenshots in `out`;
// `hostArgs` are more options of the host (S6: --mods).
export async function startRun({ out, prefix, roots, hostArgs = [] })
{
    mkdirSync(out, { recursive: true });
    for (const name of readdirSync(out).filter((entry) => entry.startsWith(`${prefix}_`) && entry.endsWith('.png')))
    {
        unlinkSync(join(out, name));
    }
    const spike = join(repo, 'output', 's5_spikes', '1_viewer');
    process.env.PLAYWRIGHT_BROWSERS_PATH ??= join(spike, 'browsers');
    const { chromium } = createRequire(join(spike, 'package.json'))('playwright');
    const port = await freePort();
    const token = randomBytes(12).toString('hex');
    const host = spawn(process.execPath, [join(studio, 'host', 'src', 'host.mjs'), 'studio', '--port', String(port), '--token', token,
        '--roots', ...roots, '--discovery', join(out, `${prefix}_host.json`), '--inbox', join(out, `${prefix}_inbox`), '--background', 'off', ...hostArgs],
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
    const context = await browser.newContext({ viewport: { width: 1680, height: 1000 }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (error) => errors.push(String(error)));
    // A failed request is named by its response (the console's line has no address); a texture the world lacks (a
    // project's own generated textures, not installed) is a note, not an error.
    const missingTextures = new Set();
    page.on('console', (message) => { if (message.type() === 'error' && !message.text().startsWith('Failed to load resource')) errors.push(message.text()); });
    page.on('response', (response) =>
    {
        if (response.status() < 400)
        {
            return;
        }
        const url = response.url().replace(/#.*$/, '');
        if (response.status() === 404 && /\/tex\//.test(url))
        {
            missingTextures.add(url.replace(/^.*\/tex\//, '').replace(/\?.*$/, ''));
        }
        else
        {
            errors.push(`${response.status()} ${url}`);
        }
    });
    const results = { started: new Date().toISOString(), steps: {}, checks: {} };
    let shotNumber = 0;
    const run = {
        page, base, token, results, errors, out,
        hostLog: () => hostLog,
        async shot(name, note = '')
        {
            shotNumber += 1;
            const file = `${prefix}_${String(shotNumber).padStart(2, '0')}_${name}.png`;
            await page.screenshot({ path: join(out, file) });
            results.steps[file] = note;
            console.log(`shot ${file}: ${note}`);
        },
        // A picture of one part of the page (a panel close up).
        async shotOf(selector, name, note = '')
        {
            shotNumber += 1;
            const file = `${prefix}_${String(shotNumber).padStart(2, '0')}_${name}.png`;
            await page.locator(selector).first().screenshot({ path: join(out, file) });
            results.steps[file] = note;
            console.log(`shot ${file}: ${note}`);
        },
        check(name, ok, detail = '')
        {
            results.checks[name] = { ok: Boolean(ok), detail: String(detail).slice(0, 600) };
            console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${detail ? `: ${String(detail).slice(0, 300)}` : ''}`);
        },
        async waitFor(test, timeout = 20000, arg = undefined)
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
        },
        state: () => page.evaluate(() => window.__studio.app.store.getState()),
        files: () => page.evaluate(() => window.__studio.app.store.getState().project.value.files),
        // Every gesture written and the views of the new revision read.
        settled: (timeout = 30000) => run.waitFor(() =>
        {
            const s = window.__studio.app.store.getState();
            if (s.edits.pending > 0 || s.project.state !== 'ready' || window.__studio.app.controller.session.busy)
            {
                return false;
            }
            return window.__studio.viewsRevision === s.project.value.revision && s.history.state === 'ready'
                && s.history.value.revision === s.project.value.revision;
        }, timeout),
        at: (x, y) => page.evaluate(([px, py]) => window.__studio.plan.screenOf(px, py), [x, y]),
        async click(x, y, options = {})
        {
            const [sx, sy] = await run.at(x, y);
            await page.mouse.click(sx, sy, options);
            await sleep(80);
        },
        async drag(from, to, steps = 12)
        {
            const [ax, ay] = await run.at(from[0], from[1]);
            const [bx, by] = await run.at(to[0], to[1]);
            await page.mouse.move(ax, ay);
            await page.mouse.down();
            await page.mouse.move(ax + (bx - ax) * 0.1, ay + (by - ay) * 0.1, { steps: 3 });
            await page.mouse.move(bx, by, { steps });
            await page.mouse.up();
            await sleep(100);
        },
        async key(name)
        {
            await page.keyboard.press(name);
            await sleep(80);
        },
        // The plan showing a box of the map (the person's wheel and pan, in one step).
        async frame(minX, minY, maxX, maxY)
        {
            await page.evaluate((b) => window.__studio.plan.frameBounds(...b), [minX, minY, maxX, maxY]);
            await sleep(250);
        },
        // A field typed into and committed with Enter.
        async type(testId, text)
        {
            const field = page.locator(`[data-testid="${testId}"]`).first();
            await field.click();
            await field.fill(String(text));
            // An input commits on Enter, a text area on Ctrl Enter.
            const tag = await field.evaluate((element) => element.tagName);
            await field.press(tag === 'TEXTAREA' ? 'Control+Enter' : 'Enter');
            await sleep(120);
        },
        // A Library row dragged onto the plan at a map point (HTML drag and drop).
        async dropOnPlan(assetTestId, x, y, modifiers = {})
        {
            const [sx, sy] = await run.at(x, y);
            const surface = await page.locator('[data-testid="plan-surface"]').boundingBox();
            await page.dragAndDrop(`[data-testid="${assetTestId}"]`, '[data-testid="plan-surface"]',
                { targetPosition: { x: sx - surface.x, y: sy - surface.y }, ...modifiers });
            await sleep(200);
        },
        async finish(name)
        {
            results.errors = errors;
            results.missing_textures = [...missingTextures].sort();
            results.failed = Object.entries(results.checks).filter(([, value]) => !value.ok).map(([check]) => check);
            writeFileSync(join(out, `${name}.json`), JSON.stringify(results, null, 1));
            writeFileSync(join(out, `${prefix}_host.log`), hostLog);
            await browser.close();
            host.kill();
            console.log(`${Object.keys(results.checks).length - results.failed.length} of ${Object.keys(results.checks).length} checks passed; ${errors.length} page errors`
                + `${missingTextures.size ? `; ${missingTextures.size} textures the world lacks (drawn grey): ${[...missingTextures].slice(0, 8).join(', ')}` : ''}`);
            if (errors.length)
            {
                console.log(errors.slice(0, 10).join('\n'));
            }
            return results.failed.length;
        },
    };
    return run;
}

export function stampFolder(kind, base = 's5b1')
{
    const stamp = new Date().toISOString().replace(/[:.]/g, '-');
    const folder = join(repo, 'output', base, 'web', 'runs', `${stamp}-${kind}`);
    mkdirSync(folder, { recursive: true });
    return folder;
}

export const randomToken = () => randomBytes(6).toString('hex');
