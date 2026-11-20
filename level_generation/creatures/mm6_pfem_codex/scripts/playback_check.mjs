// Screenshots from the three.js review viewer (what the user sees). Usage:
//   node viewer_shots.mjs <viewer_url> <out_dir> name:clip:time:view:focus ...
//   view = front|right|left|back|quarter|rear, focus = body|head|arms|shoulders|skirt|feet
//   optional 6th/7th fields: camera x,y,z and target x,y,z in viewer (glTF, Y-up) metres for close-ups
import {spawn} from 'node:child_process';
import {readFile, writeFile, mkdir, mkdtemp, rm} from 'node:fs/promises';
const [base, output, ...specs] = process.argv.slice(2);
await mkdir(output, {recursive: true});
const profile = await mkdtemp('/tmp/openyamm-viewer-shots-');
const browser = spawn('google-chrome', ['--headless=new', '--no-sandbox', '--disable-dev-shm-usage', '--use-angle=swiftshader',
  '--enable-unsafe-swiftshader', '--remote-debugging-port=0', '--remote-allow-origins=*', '--no-first-run',
  '--user-data-dir=' + profile, 'about:blank'], {stdio: ['ignore', 'ignore', 'ignore']});
const sleep = ms => new Promise(r => setTimeout(r, ms));
let ws, serial = 0;
try {
  let port;
  for (let i = 0; i < 100 && !port; ++i) { try { port = Number((await readFile(profile + '/DevToolsActivePort', 'utf8')).split('\n')[0]); } catch {} await sleep(100); }
  const page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p => p.type === 'page');
  ws = new WebSocket(page.webSocketDebuggerUrl); await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  const pending = new Map();
  ws.onmessage = e => { const m = JSON.parse(e.data), p = pending.get(m.id); if (p) { pending.delete(m.id); m.error ? p.reject(m.error) : p.resolve(m.result); } };
  const send = (method, params = {}) => new Promise((resolve, reject) => { const id = ++serial; pending.set(id, {resolve, reject}); ws.send(JSON.stringify({id, method, params})); });
  const evaluate = async expr => (await send('Runtime.evaluate', {expression: expr, awaitPromise: true, returnByValue: true})).result.value;
  const until = async expr => { for (let i = 0; i < 300; ++i) { if (await evaluate(expr)) return; await sleep(100); } throw Error('timeout ' + expr); };
  const input = (id, value) => evaluate(`(()=>{const e=document.getElementById(${JSON.stringify(id)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change'));})()`);
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1060, deviceScaleFactor: 1, mobile: false});
  await send('Page.navigate', {url: base});
  await until("document.body.dataset.ready==='true'");

  const recordings=[];
  for (const clip of ['Standing','Walking','Hit','Death','Dead','Fidget']) {
    for (const speed of [1,0.25]) {
      await input('clip',clip); await input('time',0); await input('speed',speed);
      await evaluate("document.querySelector('[data-view=\"quarter\"]').click()");
      await input('focus','body');
      if (clip==='Death'||clip==='Dead') {
        const state={clip,time_seconds:0,view:'quarter',focus:'body',camera:[2,2,3],target:[0,.15,.65]};
        await evaluate('location.hash='+JSON.stringify(encodeURIComponent(JSON.stringify(state))));await sleep(200);
      }
      const duration=await evaluate('window.reviewState.duration');
      const looping=['Standing','Walking','Fidget'].includes(clip);
      await evaluate('document.getElementById("loop").checked='+looping);
      await evaluate('document.getElementById("play").click()');
      const frames=[],start=Date.now();let last=0,cycles=0;
      while (Date.now()-start<30000) {
        await sleep(150);
        const state=await evaluate('window.reviewState');
        if (state.time_seconds<last) cycles++;
        last=state.time_seconds;
        const rect=await evaluate('(()=>{const r=document.getElementById("stage").getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1};})()');
        const shot=await send('Page.captureScreenshot',{format:'jpeg',quality:72,clip:rect});
        const file=clip+'_'+speed+'_'+String(frames.length).padStart(3,'0')+'.jpg';
        await writeFile(output+'/'+file,Buffer.from(shot.data,'base64'));
        frames.push({file,wall_ms:Date.now()-start,time:state.time_seconds,playing:state.playing});
        if ((!looping&&!state.playing)||(looping&&cycles>=1))break;
      }
      await evaluate('if(window.reviewState.playing)document.getElementById("play").click()');
      if (looping ? cycles<1 : last<duration-.001) throw Error('Playback incomplete '+clip+' '+speed);
      recordings.push({clip,speed,duration,cycles,frames});console.log('PLAYBACK',clip,speed,frames.length);
      await writeFile(output+'/playback.json',JSON.stringify(recordings,null,2));
    }
  }
} finally { ws?.close(); browser.kill(); await sleep(300); await rm(profile, {recursive: true, force: true}).catch(() => {}); }
