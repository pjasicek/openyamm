// Load a three.js creature review viewer in headless Chrome (software WebGL) and wait until it is ready or fails.
// Usage: node check_viewer.mjs <url> [timeout_seconds]
// Prints the viewer's ready flag, the #error text, the readout, the clip list and console errors, then switches to
// every tier and clip; exit 0 only when everything loads without an error. --dump-dom with a virtual time budget
// does not wait for the GLB fetch, so it cannot tell a working viewer from a broken one; this polls the live page over
// the DevTools protocol instead.
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const url = process.argv[2];
const timeout = Number(process.argv[3] || 60) * 1000;
if (!url) { console.error('usage: node check_viewer.mjs <url> [timeout_seconds]'); process.exit(2); }
const profile = mkdtempSync(join(tmpdir(), 'viewer-check-'));
const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn('google-chrome', ['--headless=new', '--no-sandbox', '--use-angle=swiftshader',
  '--enable-unsafe-swiftshader', `--user-data-dir=${profile}`, `--remote-debugging-port=${port}`, 'about:blank'],
  { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const finish = code => { chrome.kill('SIGKILL'); try { rmSync(profile, { recursive: true, force: true }); } catch {} process.exit(code); };

let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try {
    const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    target = list.find(t => t.type === 'page');
  } catch {}
}
if (!target) { console.error('Chrome did not start'); finish(2); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let id = 0; const pending = new Map(); const consoleErrors = [];
ws.onmessage = event => {
  const msg = JSON.parse(event.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg.result); pending.delete(msg.id); }
  if (msg.method === 'Runtime.exceptionThrown') consoleErrors.push(msg.params.exceptionDetails.exception?.description
    || msg.params.exceptionDetails.text);
  if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error')
    consoleErrors.push(msg.params.args.map(a => a.value ?? a.description).join(' '));
  if (msg.method === 'Log.entryAdded' && msg.params.entry.level === 'error') consoleErrors.push(msg.params.entry.text + ' ' + (msg.params.entry.url || ''));
};
const send = (method, params = {}) => new Promise(r => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
await send('Runtime.enable'); await send('Log.enable');
await send('Page.navigate', { url });
const probe = `JSON.stringify({ready: document.body && document.body.dataset.ready,
  error: (document.getElementById('error') || {}).textContent,
  errorHidden: (document.getElementById('error') || {}).hidden,
  readout: (document.getElementById('readout') || {}).textContent,
  clips: [...document.querySelectorAll('#clip option')].map(o => o.value)})`;
const start = Date.now(); let state = {};
while (Date.now() - start < timeout) {
  await sleep(1000);
  const r = await send('Runtime.evaluate', { expression: probe, returnByValue: true });
  try { state = JSON.parse(r.result.value); } catch { continue; }
  if (state.ready === 'true' || (state.error && /could not load/i.test(state.error))) break;
}
// Then every model (tier) and every clip: each switch must come back ready without an error.
const switches = [];
if (state.ready === 'true') {
  const models = (await send('Runtime.evaluate', { expression:
    "JSON.stringify([...document.querySelectorAll('#modelRevision option')].map(o => o.value))", returnByValue: true }));
  for (const model of JSON.parse(models.result.value || '[]')) {
    await send('Runtime.evaluate', { expression: `(() => { const s = document.getElementById('modelRevision');
      s.value = ${JSON.stringify(model)}; s.dispatchEvent(new Event('change')); })()` });
    let ok = false;
    for (let i = 0; i < 60 && !ok; i++) {
      await sleep(500);
      const r = await send('Runtime.evaluate', { expression: probe, returnByValue: true });
      const s = JSON.parse(r.result.value);
      ok = s.ready === 'true' && s.errorHidden; if (!ok && s.error && /could not load/i.test(s.error)) { switches.push({ model, error: s.error }); break; }
    }
    for (const clip of state.clips) {
      await send('Runtime.evaluate', { expression: `(() => { const s = document.getElementById('clip');
        s.value = ${JSON.stringify(clip)}; s.dispatchEvent(new Event('change')); })()` });
      await sleep(150);
      const r = await send('Runtime.evaluate', { expression: probe, returnByValue: true });
      const s = JSON.parse(r.result.value);
      switches.push({ model, clip, ok: s.ready === 'true' && s.errorHidden !== false, readout: s.readout });
    }
  }
}
const failed = switches.filter(s => s.error || s.ok === false);

const playback = [];
if (state.ready === 'true') {
 for (const speed of [1, .5]) for (const clip of state.clips) {
  await send('Runtime.evaluate', {expression: `(() => {const s=document.getElementById('clip');s.value=${JSON.stringify(clip)};s.dispatchEvent(new Event('change'));document.getElementById('speed').value='${speed}';document.getElementById('loop').checked=false;document.getElementById('play').click();})()`});
  const begun=Date.now();let last={};
  while(Date.now()-begun<30000){
   await sleep(300);const r=await send('Runtime.evaluate',{expression:'JSON.stringify(window.reviewState)',returnByValue:true});last=JSON.parse(r.result.value);
   if(!last.playing)break;
  }
  const ok=!last.playing&&Math.abs(last.time_seconds-last.duration)<.0001;
  playback.push({clip,speed,ok,time:last.time_seconds,duration:last.duration,wall_seconds:(Date.now()-begun)/1000});
  if(!ok)failed.push({clip,speed,error:'Playback did not reach clip endpoint'});
 }
}
console.log(JSON.stringify({ playback, url, seconds: Math.round((Date.now() - start) / 1000), ...state, consoleErrors,
  switched: switches.length, failed }, null, 1));
finish(state.ready === 'true' && failed.length === 0 && consoleErrors.length === 0 ? 0 : 1);
