// Load a three.js creature review viewer in headless Chrome (software WebGL) and wait until it is ready or fails.
// Usage: node check_viewer.mjs <url> [timeout_seconds]
// Prints the viewer's ready flag, the #error text, the readout, the clip list and console errors, then switches to
// every tier and clip; exit 0 only when everything loads without an error. --dump-dom with a virtual time budget
// does not wait for the GLB fetch, so it cannot tell a working viewer from a broken one; this polls the live page over
// the DevTools protocol instead.
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const blade=JSON.parse(readFileSync(new URL('../review/final_blade_gate.json',import.meta.url)));
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
await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
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
const switches=[];
if(state.ready==='true'){
  for(const tier of ['a','b','c']){
    await send('Runtime.evaluate',{expression:`(()=>{let s=document.getElementById('modelRevision');s.value='min1_${tier}';s.dispatchEvent(new Event('change'));})()`});
    await sleep(1000);
    for(let i=0;i<20;i++){let r=await send('Runtime.evaluate',{expression:probe,returnByValue:true});let x=JSON.parse(r.result.value);if(x.ready==='true'&&x.errorHidden)break;await sleep(250);}
    await send('Runtime.evaluate',{expression:"(()=>{let s=document.getElementById('clip');s.value='Standing';s.dispatchEvent(new Event('change'));document.querySelector('[data-view=quarter]').click();})()"});await sleep(400);
    const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(new URL(`../review/viewer_${tier}.png`,import.meta.url),Buffer.from(shot.data,'base64'));
  }
}
await send('Runtime.evaluate',{expression:"(()=>{let s=document.getElementById('modelRevision');s.value='min1_c';s.dispatchEvent(new Event('change'));})()"});await sleep(1200);
for (const [name,clip,t,focus,view] of [["hips_standing_front", "Standing", 0, "skirt", "front"], ["hips_standing_back", "Standing", 0, "skirt", "back"], ["hips_standing_rear", "Standing", 0, "skirt", "rear"], ["hips_walking_front", "Walking", 0.2, "skirt", "front"], ["hips_walking_back", "Walking", 0.2, "skirt", "back"], ["hips_walking_rear", "Walking", 0.2, "skirt", "rear"], ["hips_running_front", "Running", 0.15, "skirt", "front"], ["hips_running_back", "Running", 0.15, "skirt", "back"], ["hips_running_rear", "Running", 0.15, "skirt", "rear"], ["hips_attack_front", "Attack", 0.95, "skirt", "front"], ["hips_attack_back", "Attack", 0.95, "skirt", "back"], ["hips_attack_rear", "Attack", 0.95, "skirt", "rear"], ["hips_cast_front", "Cast", 1.52, "skirt", "front"], ["hips_cast_back", "Cast", 1.52, "skirt", "back"], ["hips_cast_rear", "Cast", 1.52, "skirt", "rear"], ["hips_fidget_front", "Fidget", 1, "skirt", "front"], ["hips_fidget_back", "Fidget", 1, "skirt", "back"], ["hips_fidget_rear", "Fidget", 1, "skirt", "rear"], ["hips_death_front", "Death", 1.4, "skirt", "front"], ["hips_death_back", "Death", 1.4, "skirt", "back"], ["hips_death_rear", "Death", 1.4, "skirt", "rear"]]) {
 await send('Runtime.evaluate',{expression:`(()=>{let c=document.getElementById('clip');c.value='${clip}';c.dispatchEvent(new Event('change'));let t=document.getElementById('time');t.value='${t}';t.dispatchEvent(new Event('change'));let f=document.getElementById('focus');f.value='${focus}';f.dispatchEvent(new Event('change'));document.querySelector('[data-view=${view}]').click();})()`});await sleep(500);
 const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(new URL(`../review/round3/viewer_${name}.png`,import.meta.url),Buffer.from(shot.data,'base64'));
}
const failed = switches.filter(s => s.error || s.ok === false);
console.log(JSON.stringify({ url, seconds: Math.round((Date.now() - start) / 1000), ...state, consoleErrors,
  switched: switches.length, failed }, null, 1));
finish(state.ready === 'true' && failed.length === 0 && consoleErrors.length === 0 ? 0 : 1);
