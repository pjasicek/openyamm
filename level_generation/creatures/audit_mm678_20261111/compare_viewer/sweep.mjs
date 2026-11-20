// Capture the compare viewer's stage for every model (two shots: standing front at t=0, default role three-quarter at
// t=0.45) into sweep/<stem>_{rest,clip}.png, in one headless Chrome. Usage: node sweep.mjs [stem ...]
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const here = dirname(fileURLToPath(import.meta.url));
const manifest = JSON.parse(readFileSync(join(here, 'manifest.json'), 'utf8'));
const only = process.argv.slice(2);
const base = 'http://127.0.0.1:8912/level_generation/creatures/audit_mm678_20261111/compare_viewer/';
const port = 9600 + Math.floor(Math.random() * 100);
const chrome = spawn('google-chrome', ['--headless=new', '--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'sweep-'))}`, `--remote-debugging-port=${port}`, '--window-size=1700,1000', 'about:blank'],
  { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let target; for (let i = 0; i < 60 && !target; i++) { await sleep(250); try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page'); } catch {} }
const ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise(r => ws.onopen = r);
let id = 0; const pending = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
const send = (method, params = {}) => new Promise(r => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
await send('Emulation.setDeviceMetricsOverride', { width: 1700, height: 1000, deviceScaleFactor: 1, mobile: false });
const evalv = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true })).result.result.value;
for (const m of manifest.models) {
  if (only.length && !only.includes(m.stem)) continue;
  for (const [tag, q] of [['rest', '?role=standing&t=0&view=front'], ['clip', '?t=0.45&view=three-quarter']]) {
    await send('Page.navigate', { url: `${base}${q}&s=${Date.now()}#${m.stem}` });
    let ok = false;
    for (let i = 0; i < 240 && !ok; i++) { await sleep(500); ok = (await evalv('document.body && document.body.dataset.ready')) === 'true'; }
    await sleep(1200);
    const r = JSON.parse(await evalv("JSON.stringify(document.getElementById('stage').getBoundingClientRect())"));
    const shot = await send('Page.captureScreenshot', { format: 'png', clip: { x: r.x, y: r.y, width: r.width, height: r.height, scale: 1 } });
    writeFileSync(join(here, 'sweep', `${m.stem}_${tag}.png`), Buffer.from(shot.result.data, 'base64'));
    console.log(m.stem, tag, ok ? 'ok' : 'TIMEOUT');
  }
}
chrome.kill('SIGKILL'); process.exit(0);
