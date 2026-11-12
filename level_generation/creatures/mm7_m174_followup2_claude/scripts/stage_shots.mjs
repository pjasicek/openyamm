// Capture the compare viewer's (or any review viewer's) #stage element for several URLs in one headless Chrome.
// Usage: node stage_shots.mjs <out.png> <url> [<out.png> <url> ...]   (env SCALE=2, SEL=stage)
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const args = process.argv.slice(2);
const scale = Number(process.env.SCALE || 2), sel = process.env.SEL || 'stage';
const port = 9700 + Math.floor(Math.random() * 200);
const chrome = spawn('google-chrome', ['--headless=new', '--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'stshot-'))}`, `--remote-debugging-port=${port}`, '--window-size=1700,1000', 'about:blank'],
  { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let target;
for (let i = 0; i < 80 && !target; i++) {
  await sleep(250);
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page'); } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise(r => ws.onopen = r);
let id = 0; const pending = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
const send = (method, params = {}) => new Promise(r => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
await send('Emulation.setDeviceMetricsOverride', { width: 1700, height: 1000, deviceScaleFactor: scale, mobile: false });
const evalv = async expr => (await send('Runtime.evaluate', { expression: expr, returnByValue: true })).result.result.value;
for (let i = 0; i < args.length; i += 2) {
  const [out, url] = [args[i], args[i + 1]];
  await send('Page.navigate', { url: 'about:blank' }); await sleep(200);
  await send('Page.navigate', { url });
  let ok = false;
  for (let k = 0; k < 240 && !ok; k++) { await sleep(500); ok = (await evalv('document.body && document.body.dataset.ready')) === 'true'; }
  await sleep(1500);
  const r = JSON.parse(await evalv(`JSON.stringify((document.getElementById('${sel}')||document.body).getBoundingClientRect())`));
  const shot = await send('Page.captureScreenshot', { format: 'png', clip: { x: r.x, y: r.y, width: r.width, height: r.height, scale: 1 } });
  writeFileSync(out, Buffer.from(shot.result.data, 'base64'));
  console.log(out, ok ? 'ok' : 'TIMEOUT');
}
chrome.kill('SIGKILL'); process.exit(0);
