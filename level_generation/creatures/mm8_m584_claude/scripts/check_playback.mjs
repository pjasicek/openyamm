import {spawn} from 'node:child_process';
import {mkdirSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
const [url,out,onlyClip]=process.argv.slice(2);
if(!url||!out)throw new Error('Expected viewer URL and output directory');
mkdirSync(out,{recursive:true});
const profile=mkdtempSync(join(tmpdir(),'gog-chrome-')),port=9700+Math.floor(Math.random()*200);
const chrome=spawn('google-chrome',['--headless=new','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',
 '--window-size=1280,1000',`--user-data-dir=${profile}`,`--remote-debugging-port=${port}`,'about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let ws;
try {
 let target;
 for(let i=0;i<30&&!target;i++){await sleep(100);try{target=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t=>t.type==='page');}catch{}}
 if(!target)throw new Error('Chrome debug connection unavailable');
 ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
 let id=0;const pending=new Map(),errors=[];
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){pending.get(m.id)?.(m);pending.delete(m.id);}
  if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text);
  if(m.method==='Runtime.consoleAPICalled'&&m.params.type==='error')errors.push(m.params.args.map(a=>a.value||a.description).join(' '));};
 const send=(method,params={})=>new Promise(r=>{const n=++id;pending.set(n,r);ws.send(JSON.stringify({id:n,method,params}));});
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.error||r.result.exceptionDetails)throw new Error(JSON.stringify(r));return r.result.result.value;};
 await send('Runtime.enable');await send('Page.navigate',{url});
 for(let i=0;i<100;i++){if(await evaluate("document.body?.dataset.ready==='true'"))break;await sleep(100);}
 if(!await evaluate("document.body?.dataset.ready==='true'"))throw new Error('Viewer not ready');
 const clips=await evaluate("[...document.querySelectorAll('#clip option')].map(x=>x.value)");
 const report=[];
 for(const rate of [1,.25])for(const clip of clips.filter(c=>!onlyClip||c===onlyClip)){
  await evaluate(`(()=>{let s=document.getElementById('clip');s.value=${JSON.stringify(clip)};s.dispatchEvent(new Event('change'));document.querySelector('[data-view="quarter"]').click();document.getElementById('speed').value=${JSON.stringify(String(rate))};document.getElementById('loop').checked=false;})()`);
  await evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');
  const row={clip,rate,frames:[]};const started=Date.now();
  for(const phase of [0,.25,.5,.75,.98]){
   let state;
   do {state=await evaluate('window.reviewState');if(Date.now()-started>30000)throw new Error('Playback stalled');if(state.time_seconds<state.duration*phase)await sleep(15);}while(state.time_seconds<state.duration*phase);
   const png=await evaluate("document.getElementById('model').toDataURL('image/png')");
   const filename=`${clip}_${rate}_${row.frames.length}.png`;writeFileSync(join(out,filename),Buffer.from(png.split(',')[1],'base64'));
   row.frames.push({...state,file:filename});
   if(phase===0)await evaluate("document.getElementById('play').click()");
  }
  if(row.frames.at(-1).time_seconds<=row.frames[0].time_seconds)throw new Error('No playback progress');
  report.push(row);writeFileSync(join(out,'playback.json'),JSON.stringify({url,errors,clips:report},null,2));
  console.log('PLAYED',clip,rate);
 }
 if(errors.length)throw new Error(errors.join('\n'));
} finally {ws?.close();chrome.kill('SIGKILL');await sleep(100);rmSync(profile,{recursive:true,force:true});}
