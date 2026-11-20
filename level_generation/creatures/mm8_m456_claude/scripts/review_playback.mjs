import {spawn} from 'node:child_process';
import {mkdtempSync,writeFileSync,mkdirSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
const out=process.argv[3]||process.env.PIRATE_REVIEW_OUT||'/tmp/dragon_hunter-playback';mkdirSync(out,{recursive:true});const profile=mkdtempSync(join(tmpdir(),'dragon_hunter-browser-'));const port=9541;
const chrome=spawn('google-chrome',['--headless=new','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',`--user-data-dir=${profile}`,`--remote-debugging-port=${port}`,'about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let target;
for(let i=0;i<50&&!target;i++){await sleep(200);try{target=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t=>t.type==='page');}catch{}}
if(!target)throw Error('Chrome failed');const ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);let id=0;const pending=new Map(),errors=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){pending.get(m.id)(m.result);pending.delete(m.id);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);};
const send=(method,params={})=>new Promise(r=>{const n=++id;pending.set(n,r);ws.send(JSON.stringify({id:n,method,params}));});
const ev=async expression=>(await send('Runtime.evaluate',{expression,returnByValue:true})).result?.value;
await send('Runtime.enable');await send('Emulation.setDeviceMetricsOverride',{width:1300,height:1000,deviceScaleFactor:1,mobile:false});await send('Page.navigate',{url:'http://127.0.0.1:8912/level_generation/creatures/mm8_m456_claude/review/viewer/'});
for(let i=0;i<80;i++){await sleep(300);if(await ev("document.body.dataset.ready==='true'"))break;}
if(!await ev("document.body.dataset.ready==='true'"))throw Error(await ev("document.getElementById('error').textContent"));
let clips=JSON.parse(await ev("JSON.stringify([...document.querySelectorAll('#clip option')].map(o=>o.value))"));if(process.argv[2]||process.env.PIRATE_REVIEW_CLIP)clips=clips.filter(c=>c===(process.argv[2]||process.env.PIRATE_REVIEW_CLIP));const report={clips:[],errors};
for(const speed of [1,.5])for(const clip of clips){
 await ev(`(()=>{if(document.getElementById('play').textContent==='Pause')document.getElementById('play').click();const c=document.getElementById('clip');c.value=${JSON.stringify(clip)};c.dispatchEvent(new Event('change'));const s=document.getElementById('speed');s.value='${speed}';s.dispatchEvent(new Event('change'));document.querySelector('[data-view="${speed===1?'quarter':'left'}"]').click();document.getElementById('loop').checked=false;document.getElementById('restart').click();if(document.getElementById('play').textContent!=='Pause')document.getElementById('play').click();})()`);
 const duration=await ev("Number(document.getElementById('time').max)") || (await (await fetch('http://127.0.0.1:8912/level_generation/creatures/mm8_m456_claude/review/viewer/manifest.json')).json()).clips[clip].duration;
 const box=JSON.parse(await ev("JSON.stringify((()=>{const r=document.getElementById('stage').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1};})())"));const frames=[];
 for(let i=0;i<8;i++){if(i)await sleep(duration/7/speed*1000);const time=await ev("Number(document.getElementById('time').value)");const shot=await send('Page.captureScreenshot',{format:'png',clip:box});const file=`${clip}_${speed}_${i}.png`;writeFileSync(join(out,file),Buffer.from(shot.data,'base64'));frames.push({time,file});}
 report.clips.push({clip,speed,duration,frames});console.log(clip,speed,frames.map(x=>x.time));
}
if(process.argv[2]==='arm-pads')for(const [clip,frames] of [['Attack',[0,6,12,18,22,28,34,38]],['Running',[0,9,18,27]]])for(const frame of frames)for(const view of ['front','rear','right']){
 await ev(`(()=>{if(document.getElementById('play').textContent==='Pause')document.getElementById('play').click();const c=document.getElementById('clip');c.value='${clip}';c.dispatchEvent(new Event('change'));const f=document.getElementById('frame');f.value='${frame}';f.dispatchEvent(new Event('change'));const s=document.getElementById('focus');s.value='arms';s.dispatchEvent(new Event('change'));document.querySelector('[data-view="${view}"]').click();})()`);await sleep(100);const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(join(out,`${clip}_${frame}_${view}.png`),Buffer.from(shot.data,'base64'));
}
// Stable material comparison in the same pose and camera.
for(const tier of ['a','b','c']){
 await ev(`(()=>{if(document.getElementById('play').textContent==='Pause')document.getElementById('play').click();const s=document.getElementById('modelRevision');s.value='dragon_hunter_${tier}';s.dispatchEvent(new Event('change'));})()`);await sleep(600);
 await ev("(()=>{const c=document.getElementById('clip');c.value='Standing';c.dispatchEvent(new Event('change'));document.querySelector('[data-view=front]').click();})()");await sleep(100);const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(join(out,`tier_${tier}.png`),Buffer.from(shot.data,'base64'));
}
if(process.argv[2]==='closeups')for(const focus of ['head','skirt','feet','arms'])for(const view of ['front','quarter','back']){
 await ev(`(()=>{const s=document.getElementById('focus');s.value='${focus}';s.dispatchEvent(new Event('change'));document.querySelector('[data-view="${view}"]').click();})()`);await sleep(100);const shot=await send('Page.captureScreenshot',{format:'png'});writeFileSync(join(out,`closeup_${focus}_${view}.png`),Buffer.from(shot.data,'base64'));
}
writeFileSync(join(out,'playback.json'),JSON.stringify(report,null,2));chrome.kill();try{rmSync(profile,{recursive:true,force:true,maxRetries:5,retryDelay:200});}catch{}if(errors.length)process.exitCode=1;
