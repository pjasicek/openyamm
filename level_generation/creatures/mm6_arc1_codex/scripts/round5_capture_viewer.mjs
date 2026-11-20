// Load a three.js creature review viewer in headless Chrome (software WebGL) and wait until it is ready or fails.
// Usage: node check_viewer.mjs <url> [timeout_seconds]
// Prints the viewer's ready flag, the #error text, the readout, the clip list and console errors, then switches to
// every tier and clip; exit 0 only when everything loads without an error. --dump-dom with a virtual time budget
// does not wait for the GLB fetch, so it cannot tell a working viewer from a broken one; this polls the live page over
// the DevTools protocol instead.
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const url = process.argv[2];
const timeout = Number(process.argv[3] || 60) * 1000;
if (!url) { console.error('usage: node check_viewer.mjs <url> [timeout_seconds]'); process.exit(2); }
const profile = mkdtempSync(join(tmpdir(), 'viewer-check-arc1-'));
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
await send('Emulation.setDeviceMetricsOverride', {width:1280,height:960,deviceScaleFactor:1,mobile:false});
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

if(state.ready !== 'true')finish(1);
async function evaluate(expression){return send('Runtime.evaluate',{expression,returnByValue:true});}
for(const tier of ['a','b','c']){
 await evaluate(`document.getElementById('modelRevision').value='arc1_${tier}';document.getElementById('modelRevision').dispatchEvent(new Event('change'))`);
 await sleep(800);
 let ready=false;
 for(let i=0;i<30 && !ready;i++){
  const r=await evaluate(probe);ready=JSON.parse(r.result.value).ready==='true';if(!ready)await sleep(200);
 }
 if(!ready)finish(1);
 await evaluate(`document.getElementById('clip').value='Standing';document.getElementById('clip').dispatchEvent(new Event('change'))`);
 for(const focus of (tier==='a'?['body','head','arms','skirt','feet']:['body'])){
  await evaluate(`document.getElementById('focus').value='${focus}';document.getElementById('focus').dispatchEvent(new Event('change'));document.querySelector('[data-view="${focus==='skirt'?'left':'quarter'}"]').click()`);
  await sleep(250);
  const r=await evaluate(`JSON.stringify((()=>{const r=document.getElementById('model').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1}})())`);
  const shot=await send('Page.captureScreenshot',{format:'png',clip:JSON.parse(r.result.value)});
  writeFileSync(new URL(`../review/browser_${tier}_${focus}.png`,import.meta.url),Buffer.from(shot.data,'base64'));
 }
}
await evaluate(`document.getElementById('modelRevision').value='arc1_a';document.getElementById('modelRevision').dispatchEvent(new Event('change'))`);
await sleep(1200);
await evaluate(`document.getElementById('clip').value='Attack';document.getElementById('clip').dispatchEvent(new Event('change'));document.getElementById('time').value='1.2';document.getElementById('time').dispatchEvent(new Event('change'));document.getElementById('focus').value='feet';document.getElementById('focus').dispatchEvent(new Event('change'));document.querySelector('[data-view="quarter"]').click()`);
await sleep(300);
const bounds=await evaluate(`JSON.stringify((()=>{const r=document.getElementById('model').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1}})())`);
const shot=await send('Page.captureScreenshot',{format:'png',clip:JSON.parse(bounds.result.value)});
writeFileSync(new URL('../review/round5/browser_attack_feet.png',import.meta.url),Buffer.from(shot.data,'base64'));
console.log(JSON.stringify({ready:state.ready,consoleErrors,captures:8}));
finish(consoleErrors.length===0?0:1);
