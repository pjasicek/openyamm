import {spawn} from 'node:child_process';
import {mkdtempSync,writeFileSync,mkdirSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
const out=process.argv[2],url=process.argv[3];mkdirSync(out,{recursive:true});
const profile=mkdtempSync(tmpdir()+'/wolf-review-'),port=9673;
const chrome=spawn('google-chrome',['--headless=new','--no-sandbox','--use-angle=swiftshader',
 '--enable-unsafe-swiftshader','--window-size=1400,1000',`--user-data-dir=${profile}`,
 `--remote-debugging-port=${port}`,'about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let ws;
try {
 let target;
 for(let i=0;i<50&&!target;i++){await sleep(100);try{target=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t=>t.type==='page');}catch{}}
 if(!target)throw Error('Chrome did not start');
 ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
 let id=0;const pending=new Map(),errors=[];
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){pending.get(m.id)?.(m);pending.delete(m.id);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params);};
 const send=(method,params={})=>new Promise((r,j)=>{const n=++id;pending.set(n,m=>m.error?j(m.error):r(m.result));ws.send(JSON.stringify({id:n,method,params}));});
 const evaluate=async expression=>(await send('Runtime.evaluate',{expression,returnByValue:true})).result.value;
 await send('Runtime.enable');await send('Page.navigate',{url});
 for(let i=0;i<100;i++){if(await evaluate("document.body?.dataset.ready==='true'"))break;await sleep(100);}
 if(!await evaluate("document.body?.dataset.ready==='true'"))throw Error('Viewer did not load');
 const clips=JSON.parse(await evaluate("JSON.stringify([...document.querySelectorAll('#clip option')].map(o=>o.value))"));
 const rect=JSON.parse(await evaluate("JSON.stringify((()=>{const r=document.getElementById('stage').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1};})())"));
 const rows=[];
 for(const clip of clips.filter(c=>['Death','Dead'].includes(c)))for(const speed of [1,.25]){
  await evaluate(`(()=>{const c=document.getElementById('clip');c.value=${JSON.stringify(clip)};c.dispatchEvent(new Event('change'));document.getElementById('speed').value=${JSON.stringify(String(speed))};document.querySelector('[data-view="right"]').click();document.getElementById('restart').click();if(!window.reviewState.playing)document.getElementById('play').click();})()`);
  const initial=JSON.parse(await evaluate('JSON.stringify(window.reviewState)'));
  const samples=7,wait=Math.max(45,initial.duration*1000/speed/(samples-1));
  for(let i=0;i<samples;i++){
   if(i)await sleep(wait);
   const state=JSON.parse(await evaluate('JSON.stringify(window.reviewState)'));
   const shot=await send('Page.captureScreenshot',{format:'png',clip:rect});
   const file=`${clip}_${speed}_${i}.png`;writeFileSync(out+'/'+file,Buffer.from(shot.data,'base64'));
   rows.push({clip,speed,index:i,file,state,wall_time:Date.now()});
  }
  await evaluate("if(window.reviewState.playing)document.getElementById('play').click()");
 }
 for(const [clip,time,view,focus] of [['Standing',0,'front','body'],['Standing',0,'quarter','body'],
 ['Standing',0,'back','body'],['Standing',0,'left','head'],['Standing',0,'right','head'],
 ['Attack',.5,'quarter','head'],['Death',.625,'quarter','body']]){
  await evaluate(`(()=>{const c=document.getElementById('clip');c.value=${JSON.stringify(clip)};c.dispatchEvent(new Event('change'));const t=document.getElementById('time');t.value=${time};t.dispatchEvent(new Event('change'));const f=document.getElementById('focus');f.value=${JSON.stringify(focus)};f.dispatchEvent(new Event('change'));document.querySelector('[data-view="${view}"]').click();})()`);
  await sleep(100);const shot=await send('Page.captureScreenshot',{format:'png',clip:rect});
  writeFileSync(out+`/detail_${clip}_${view}_${focus}.png`,Buffer.from(shot.data,'base64'));
 }
 if(errors.length)throw Error(JSON.stringify(errors));
 writeFileSync(out+'/playback.json',JSON.stringify({method:'Live browser AnimationMixer playback sampled from screen at 1x and 0.25x',rows,errors},null,2));
 console.log(JSON.stringify({clips,speeds:[1,.25],screenshots:rows.length,errors}));
}finally{ws?.close();chrome.kill('SIGKILL');await sleep(100);rmSync(profile,{recursive:true,force:true});}
