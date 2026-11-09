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
    await send('Runtime.evaluate',{expression:`(()=>{let s=document.getElementById('modelRevision');s.value='natf_${tier}';s.dispatchEvent(new Event('change'));})()`});
    await sleep(1000);
    for(let i=0;i<20;i++){let r=await send('Runtime.evaluate',{expression:probe,returnByValue:true});let x=JSON.parse(r.result.value);if(x.ready==='true'&&x.errorHidden)break;await sleep(250);}
    await send('Runtime.evaluate',{expression:"(()=>{let s=document.getElementById('clip');s.value='Standing';s.dispatchEvent(new Event('change'));document.querySelector('[data-view=quarter]').click();})()"});await sleep(400);
    const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(new URL(`../review/viewer_${tier}.png`,import.meta.url),Buffer.from(shot.data,'base64'));
  }
}
const playback=[];
const meta=await (await fetch(new URL('manifest.json',url))).json();
const prior=[]; // A new export requires a fresh complete playback check.
if(state.ready==='true'){
 await send('Runtime.evaluate',{expression:"(()=>{let s=document.getElementById('modelRevision');s.value='natf_a';s.dispatchEvent(new Event('change'));})()"});await sleep(1200);
 await send('Runtime.evaluate',{expression:"(()=>{let s=document.getElementById('focus');s.value='head';s.dispatchEvent(new Event('change'));document.querySelector('[data-view=quarter]').click();})()"});await sleep(250);
 let shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(new URL('../review/viewer_head.png',import.meta.url),Buffer.from(shot.data,'base64'));
 await send('Runtime.evaluate',{expression:"(()=>{let s=document.getElementById('focus');s.value='body';s.dispatchEvent(new Event('change'));})()"});
 for(const [clip,time,view,file] of [['Standing',0,'front','slim_front'],['Standing',0,'left','slim_left'],['Running',7/48,'left','running_7'],['Running',8/48,'left','running_8'],['Attack',.4326923077,'front','attack_windup'],['Attack',.5729166667,'front','attack_impact'],['Attack',1.0368589744,'front','attack_followthrough'],['Attack',1.0368589744,'right','attack_arm_56']]){
  await send('Runtime.evaluate',{expression:`(()=>{let c=document.getElementById('clip');c.value=${JSON.stringify(clip)};c.dispatchEvent(new Event('change'));let t=document.getElementById('time');t.value=${time};t.dispatchEvent(new Event('change'));document.querySelector('[data-view=${view}]').click();})()`});await sleep(250);
  const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(new URL(`../review/viewer_${file}.png`,import.meta.url),Buffer.from(shot.data,'base64'));
 }
 for(const clip of state.clips)for(const speed of ['1','0.25']){
  const duration=meta.clips[clip].duration;
  const old=prior.find(r=>r.clip===clip && r.speed===Number(speed) && r.observed_advance_seconds>=duration*.999);
  if(old){playback.push({...old,ok:true,reused_completed_check:true});continue;}
  await send('Runtime.evaluate',{expression:`(()=>{let s=document.getElementById('clip');s.value=${JSON.stringify(clip)};s.dispatchEvent(new Event('change'));document.getElementById('speed').value=${JSON.stringify(speed)};document.getElementById('play').click();})()`});
  const started=Date.now();let previous=0,advanced=0,maximum=0,seconds=0;
  while(advanced<duration*.999 && Date.now()-started<(3*duration/Number(speed)+2)*1000){
   await sleep(150);
   const result=await send('Runtime.evaluate',{expression:"Number(document.getElementById('time').value)",returnByValue:true});
   seconds=result.result.value;advanced+=seconds>=previous?seconds-previous:duration-previous+seconds;
   maximum=Math.max(maximum,seconds);previous=seconds;
  }
  playback.push({clip,speed:Number(speed),duration,wall_seconds:(Date.now()-started)/1000,observed_advance_seconds:advanced,maximum_time:maximum,seconds,ok:advanced>=duration*.999});
  await send('Runtime.evaluate',{expression:"(()=>{let b=document.getElementById('play');if(b.textContent==='Pause')b.click();})()"});
 }
 writeFileSync(new URL('../review/playback_check.json',import.meta.url),JSON.stringify({playback,errors:consoleErrors},null,2));
 if(playback.some(p=>!p.ok))consoleErrors.push('Playback did not advance');
}
const failed = switches.filter(s => s.error || s.ok === false);
console.log(JSON.stringify({ url, seconds: Math.round((Date.now() - start) / 1000), ...state, consoleErrors,
  switched: switches.length, failed }, null, 1));
finish(state.ready === 'true' && failed.length === 0 && consoleErrors.length === 0 ? 0 : 1);
