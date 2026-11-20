// The studio's camera against the game's at one pose (S5a4; the open point of S5a3: "go to pin" from a game pose
// showed the wall closer than the game's picture). The game is started minimised on the shapes gallery from the
// host's mount (as Play here installed it) with a start console file putting the party at the pose and the HUD off,
// and takes its own screenshot; the studio's 3D view is put at the same pose (the eye over the feet, the same yaw and
// pitch) at the game's picture size and at the narrower sizes the split view gives it. Writes the pictures and a
// side-by-side of each pair into the output folder.
//
//   node scripts/camera_check.mjs [--out <folder>] [--width 1280 --height 720] [--skip-game]
//       [--project <key> --map <file> --world <w> --pose x,y,z,yaw-radians,pitch-degrees --eye <height>]
// The map must be installed as Play here installs it (output/studio_host/play_mounts/<project key>; --mount).
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { createServer } from 'node:net';
import { join, resolve } from 'node:path';
import { randomBytes } from 'node:crypto';

const web = resolve(import.meta.dirname, '..');
const studio = resolve(web, '..');
const repo = resolve(studio, '..');
const args = process.argv.slice(2);
const option = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);
const out = resolve(option('--out', join(repo, 'output', 's5a4_shots', 'camera')));
const width = Number(option('--width', 1280));
const height = Number(option('--height', 720));
mkdirSync(out, { recursive: true });
const spike = join(repo, 'output', 's5_spikes', '1_viewer');
process.env.PLAYWRIGHT_BROWSERS_PATH ??= join(spike, 'browsers');
const { chromium } = createRequire(join(spike, 'package.json'))('playwright');
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

// The pose, as `loc` gives it: the feet, yaw in radians, pitch in degrees.
const given = option('--pose', '1520,1640,256,0.35,-6').split(',').map(Number);
const pose = { position: given.slice(0, 3), yaw: given[3], pitch: given[4] };
const eyeHeight = Number(option('--eye', 160));
const projectKey = option('--project', 'openyamm-studio/examples/shapes_gallery');
const mapFile = option('--map', 'studio02.blv');
const world = option('--world', 'mm6');
// Where Play here installed the project (host/src/studio.mjs: a mount of its own per project).
const mountFolder = resolve(option('--mount', join(repo, 'output', 'studio_host', 'play_mounts', projectKey.replace(/[^A-Za-z0-9_-]+/g, '_'))));

// --- the game ------------------------------------------------------------------------------------------------------

if (!args.includes('--skip-game'))
{
    const consoleFile = join(out, 'camera.console');
    writeFileSync(consoleFile, `tp ${pose.position.join(' ')} ${pose.yaw} ${pose.pitch}\nrender hud off\nrender actors off\n`
        + 'render effects off\n');
    const game = spawn(join(repo, 'tools', 'run_game.sh'), ['--isolated', 's5a4-camera', '--world', world, '--map', mapFile,
        '--extra-mount', mountFolder, '--set', `debug.startup_console_file=${consoleFile}`,
        '--set', `debug.screenshot_path=${join(out, 'game.png')}`, '--set', 'debug.screenshot_delay_seconds=3',
        '--set', `video.resolution=${width}x${height}`, '--set', 'video.window_mode=windowed', '--warmup', '0', '--seconds', '6'],
    { cwd: repo, stdio: 'inherit', env: { ...process.env, SDL_AUDIODRIVER: 'dummy' } });
    const code = await new Promise((done) => game.on('close', done));
    if (code !== 0 || !existsSync(join(out, 'game.png')))
    {
        throw new Error(`the game run failed (${code})`);
    }
}

// --- the studio ----------------------------------------------------------------------------------------------------

const port = await new Promise((done) =>
{
    const server = createServer();
    server.listen(0, '127.0.0.1', () => { const { port: p } = server.address(); server.close(() => done(p)); });
});
const token = randomBytes(12).toString('hex');
const host = spawn(process.execPath, [join(studio, 'host', 'src', 'host.mjs'), 'studio', '--port', String(port), '--token', token,
    '--discovery', join(out, 'host.json'), '--inbox', join(out, 'inbox')], { cwd: repo, stdio: ['ignore', 'pipe', 'pipe'] });
let hostLog = '';
host.stdout.on('data', (data) => { hostLog += data; });
for (let i = 0; i < 100 && !hostLog.includes('oymap studio:'); ++i)
{
    await sleep(100);
}
const browser = await chromium.launch({ headless: true, executablePath: existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome' : undefined,
    args: ['--use-angle=vulkan', '--enable-features=Vulkan', '--ignore-gpu-blocklist'] });
const results = { pose, eyeHeight, game: { width, height }, studio: [] };

// The canvas at a given size: the page grown or shrunk by what the frame around the maximised 3D view takes.
async function studioShot(name, canvasWidth, canvasHeight)
{
    const context = await browser.newContext({ viewport: { width: canvasWidth + 600, height: canvasHeight + 300 }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    await page.goto(`http://127.0.0.1:${port}/?project=${encodeURIComponent(projectKey)}#token=${token}`);
    for (let i = 0; i < 600 && !(await page.evaluate(() => !!window.__studio?.marks.textured_full)); ++i)
    {
        await sleep(100);
    }
    await page.evaluate(() => window.__studio.app.store.setState({ viewMode: '3d', maximised: '3d' }));
    await sleep(300);
    const box = await page.locator('canvas.oy-viewport-canvas').boundingBox();
    await page.setViewportSize({ width: Math.round(canvasWidth + 600 + (canvasWidth - box.width)), height: Math.round(canvasHeight + 300 + (canvasHeight - box.height)) });
    await sleep(500);
    await page.evaluate(({ p, eye }) => window.__studio.viewport.setCamera({ eye: [p.position[0], p.position[1], p.position[2] + eye],
        yaw: p.yaw, pitch: (p.pitch * Math.PI) / 180 }), { p: pose, eye: eyeHeight });
    await sleep(500);
    const canvas = page.locator('canvas.oy-viewport-canvas');
    const size = await canvas.boundingBox();
    const fov = await page.evaluate(() => window.__studio.viewport.verticalFov?.() ?? null);
    await canvas.screenshot({ path: join(out, `studio_${name}.png`) });
    results.studio.push({ name, width: Math.round(size.width), height: Math.round(size.height), verticalFovDegrees: fov });
    await context.close();
}

await studioShot('same_size', width, height);
await studioShot('split_pane', 590, 575);
await studioShot('tall_pane', 480, 720);
await browser.close();
host.kill();
writeFileSync(join(out, 'camera.json'), `${JSON.stringify(results, null, 1)}\n`);
console.log(JSON.stringify(results, null, 1));
