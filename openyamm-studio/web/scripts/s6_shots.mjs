// S6 screenshots (devdocs/map_studio/S6_PLAN.md): the MCP App viewer (host/src/viewer.html) inside a stand-in host
// page that answers its bridge with map_view's structured result, for a new map and for an overlay of an MM9 region;
// light and dark.
//   node web/scripts/s6_shots.mjs [--out <folder>] [--oymap <oymap>] [--overlay <overlay project>]
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join, resolve } from 'node:path';

const web = resolve(import.meta.dirname, '..');
const studio = resolve(web, '..');
const repo = resolve(studio, '..');
const args = process.argv.slice(2);
const option = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);
const out = resolve(option('--out', join(repo, 'output', 'studio_s6', 'shots_viewer')));
const oymap = resolve(option('--oymap', join(studio, 'build-s4', 'oymap')));
const overlayProject = resolve(option('--overlay', join(repo, 'output', 'studio_s6', 'isle')));
const assets = join(repo, 'assets_dev');
mkdirSync(out, { recursive: true });
const spike = join(repo, 'output', 's5_spikes', '1_viewer');
process.env.PLAYWRIGHT_BROWSERS_PATH ??= join(spike, 'browsers');
const { chromium } = createRequire(join(spike, 'package.json'))('playwright');

const call = (method, params) => JSON.parse(execFileSync(oymap, ['call', method, JSON.stringify(params), '--assets',
  assets], { encoding: 'utf8', maxBuffer: 1 << 28 })).result;

const breakwater = join(studio, 'examples', 's6_breakwater');
const cases = [
  { name: 'viewer_new_map', data: { title: 'The Breakwater Store', subtitle: 'indoor map, mm6',
    layout: call('view.layout', { project: breakwater }) } },
];

if (existsSync(join(overlayProject, 'project.yml'))) {
  const overlay = call('view.overlay', { project: overlayProject });
  cases.push({ name: 'viewer_overlay', data: { title: 'Isle of Ashes: the beacon overlay',
    subtitle: `overlay of ${overlay.base} (${overlay.world}, ${overlay.profile})`, overlay } });
}

const viewer = readFileSync(join(studio, 'host', 'src', 'viewer.html'), 'utf8');
const browser = await chromium.launch({ executablePath: existsSync('/usr/bin/google-chrome') ? '/usr/bin/google-chrome'
  : undefined, headless: true });

for (const scheme of ['light', 'dark']) {
  const page = await browser.newPage({ viewport: { width: 1100, height: 760 }, colorScheme: scheme });

  for (const entry of cases) {
    const host = `<!doctype html><html><body style="margin:0;background:#888">
      <iframe id="app" style="border:0;width:100vw;height:100vh" sandbox="allow-scripts"></iframe></body></html>`;
    await page.setContent(host);
    // The stand-in host: it records the app's ui/initialize and answers it, then sends the tool's result.
    const initialized = await page.evaluate(async ({ html, data }) => {
      const frame = document.getElementById('app');
      const asked = new Promise((done) => window.addEventListener('message', (event) => {
        if (event.data?.method === 'ui/initialize') {
          frame.contentWindow.postMessage({ jsonrpc: '2.0', id: event.data.id, result: { protocolVersion: '2026-01-26',
            hostInfo: { name: 'stand-in', version: '0' }, hostCapabilities: {} } }, '*');
          done(true);
        }
      }));
      frame.srcdoc = html;
      const ok = await asked;
      frame.contentWindow.postMessage({ jsonrpc: '2.0', method: 'ui/notifications/tool-result',
        params: { content: [{ type: 'text', text: '{}' }], structuredContent: data } }, '*');
      return ok;
    }, { html: viewer, data: entry.data });
    await page.waitForTimeout(400);
    const file = join(out, `${entry.name}_${scheme}.png`);
    await page.screenshot({ path: file });
    console.log(`${file} (initialize ${initialized ? 'asked' : 'not asked'})`);
  }

  await page.close();
}

await browser.close();
