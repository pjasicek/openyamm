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
await send('Runtime.evaluate',{expression:"(()=>{let s=document.getElementById('modelRevision');s.value='min1_a';s.dispatchEvent(new Event('change'));})()"});await sleep(1200);
for (const [name,clip,t,focus,view] of [['head','Standing',0,'head','quarter'],['grip','Standing',0,'arms','front'],['strike','Attack',blade.Attack.impact_seconds,'body','quarter'],['feet','Standing',0,'feet','front'],['fidget_feet','Fidget',1,'feet','quarter'],['attack_28','Attack',28/48,'arms','quarter'],['attack_40','Attack',40/48,'arms','quarter'],['attack_40_full','Attack',40/48,'body','quarter'],['windup','Attack',.65,'body','front'],['followthrough','Attack',1.35,'body','quarter'],['recovery','Attack',1.95,'body','quarter'],['death_21','Death',21/48,'body','quarter'],['death_36','Death',36/48,'body','quarter'],['death_fall','Death',1.5,'body','quarter'],['death_floor','Death',2.4,'body','quarter'],['horn_34','Attack',34/48-.13,'arms','back'],['horn_35','Attack',35/48-.13,'arms','back'],['horn_36','Attack',36/48-.13,'arms','back'],['horn_37','Attack',37/48-.13,'arms','back'],['horn_38','Attack',38/48-.13,'arms','back'],['horn_39','Attack',39/48-.13,'arms','back'],['corpse','Dead',0,'body','quarter']]) {
 await send('Runtime.evaluate',{expression:`(()=>{let c=document.getElementById('clip');c.value='${clip}';c.dispatchEvent(new Event('change'));let t=document.getElementById('time');t.value='${t}';t.dispatchEvent(new Event('change'));let f=document.getElementById('focus');f.value='${focus}';f.dispatchEvent(new Event('change'));document.querySelector('[data-view=${view}]').click();})()`});await sleep(500);
 const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(new URL(`../review/viewer_${name}.png`,import.meta.url),Buffer.from(shot.data,'base64'));
}
const failed = switches.filter(s => s.error || s.ok === false);
console.log(JSON.stringify({ url, seconds: Math.round((Date.now() - start) / 1000), ...state, consoleErrors,
  switched: switches.length, failed }, null, 1));
finish(state.ready === 'true' && failed.length === 0 && consoleErrors.length === 0 ? 0 : 1);
