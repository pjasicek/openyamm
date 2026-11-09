// Headless check of the timing review viewer: open every model and role, report load and console errors.
// Usage: node check_review.mjs <url> [SHOT_DIR=dir for one screenshot per model]
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const url = process.argv[2];
const profile = mkdtempSync(join(tmpdir(), 'timing-review-'));
const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn('google-chrome', ['--headless=new', '--no-sandbox', '--use-angle=swiftshader',
  '--enable-unsafe-swiftshader', '--window-size=1700,1000', '--autoplay-policy=no-user-gesture-required',
  `--user-data-dir=${profile}`, `--remote-debugging-port=${port}`, 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const finish = code => { chrome.kill('SIGKILL'); try { rmSync(profile, { recursive: true, force: true }); } catch {} process.exit(code); };
let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page'); } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let id = 0; const pending = new Map(); const errors = [];
ws.onmessage = event => {
  const msg = JSON.parse(event.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg.result); pending.delete(msg.id); }
  if (msg.method === 'Runtime.exceptionThrown') errors.push(msg.params.exceptionDetails.exception?.description || msg.params.exceptionDetails.text);
  if (msg.method === 'Runtime.consoleAPICalled' && ['error', 'warning'].includes(msg.params.type))
    errors.push(msg.params.args.map(a => a.value ?? a.description).join(' '));
  if (msg.method === 'Log.entryAdded' && msg.params.entry.level === 'error') errors.push(msg.params.entry.text + ' ' + (msg.params.entry.url || ''));
};
const send = (method, params = {}) => new Promise(r => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
const evaluate = async expression => (await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })).result?.value;
await send('Runtime.enable'); await send('Log.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1700, height: 1000, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url });
for (let i = 0; i < 120 && await evaluate("document.body?.dataset.ready") !== 'true'; i++) await sleep(500);
const models = JSON.parse(await evaluate("JSON.stringify([...document.querySelectorAll('#list .item b')].map(b => b.textContent))") || '[]');
const results = [];
for (const [index, name] of models.entries()) {
  await evaluate(`document.querySelectorAll('#list .item')[${index}].click()`);
  let loaded = false;
  for (let i = 0; i < 120 && !loaded; i++) {
    await sleep(250);
    loaded = await evaluate(`document.body.dataset.loaded === ${JSON.stringify(name + '.glb')} && document.getElementById('error').hidden`);
  }
  const error = loaded ? null : await evaluate("document.getElementById('error').textContent");
  const roles = JSON.parse(await evaluate("JSON.stringify([...document.querySelectorAll('#roles button')].map(b => b.textContent))") || '[]');
  for (let r = 0; r < roles.length; r++) {
    await evaluate(`document.querySelectorAll('#roles button')[${r}].click()`);
    await sleep(120);
    const state = JSON.parse(await evaluate(`JSON.stringify({error: document.getElementById('error').hidden ? null : document.getElementById('error').textContent,
      suggestions: document.querySelectorAll('#suggestions li').length, track: document.getElementById('track').value})`));
    results.push({ model: name, role: roles[r], loadError: error, ...state });
  }
  if (process.env.SHOT_DIR && loaded) {
    await evaluate("document.getElementById('play').click()");
    await sleep(700);
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(join(process.env.SHOT_DIR, `${name}.png`), Buffer.from(shot.data, 'base64'));
    await evaluate("document.getElementById('play').click()");
  }
}
const failed = results.filter(r => r.loadError || r.error || !r.suggestions);
console.log(JSON.stringify({ models: models.length, roles: results.length, failed, errors: [...new Set(errors)] }, null, 1));
finish(failed.length || errors.length ? 1 : 0);
