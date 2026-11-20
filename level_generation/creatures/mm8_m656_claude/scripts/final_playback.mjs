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
  const report=[];
  for (const speed of [1,0.5]) for (const clip of ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']) {
    await input('clip',clip);await input('speed',String(speed));await input('focus','body');
    await evaluate(`document.querySelector('[data-view="${speed===1?'quarter':'left'}"]').click()`);
    await evaluate("document.getElementById('loop').checked=false;document.getElementById('restart').click();document.getElementById('play').click()");
    await until("Number(document.getElementById('time').value)>0");
    const duration=Number(await evaluate("document.getElementById('time').max"));
    const times=[];
    for(let i=0;i<4;i++) {
      await sleep(Math.max(100,duration*1000/speed/4));
      times.push(Number(await evaluate("document.getElementById('time').value")));
      if(true) {
        const r=await send('Page.captureScreenshot',{format:'png',clip:{x:16,y:104,width:1036,height:763,scale:.5}});
        await writeFile(`${output}/${clip}_${speed}_${i}.png`,Buffer.from(r.data,'base64'));
      }
    }
    if(!(times[0]>0 && times.every((t,i)=>i===0 || t>=times[i-1])))throw Error('playback stalled '+clip+' '+times);
    await until(`Number(document.getElementById('time').value)>=${duration-.01}`);
    report.push({clip,speed,duration,times,completed:true});
  }
  for (const tier of ['mercenary_a','mercenary_b','mercenary_c']) {
    await input('modelRevision',tier);await until("document.body.dataset.ready==='true'");await input('clip','Standing');
    await evaluate("document.getElementById('restart').click()");
    for (const focus of ['body','head','arms']) {
      await input('focus',focus);await evaluate("document.querySelector('[data-view=\"quarter\"]').click()");await sleep(300);
      const shot=await send('Page.captureScreenshot',{format:'png'});await writeFile(`${output}/${tier}_${focus}.png`,Buffer.from(shot.data,'base64'));
    }
  }
  await writeFile(`${output}/playback.json`,JSON.stringify(report,null,2));
  console.log('PLAYBACK',report.length,'clip/speed combinations passed');
} finally { ws?.close(); browser.kill(); await sleep(300); await rm(profile, {recursive: true, force: true}).catch(() => {}); }
