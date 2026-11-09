import {spawn} from 'node:child_process';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));const profile=await mkdtemp('/tmp/gst-playback-');
const browser=spawn('google-chrome',['--headless=new','--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{stdio:'ignore'});let ws;
try {
 let port;for(let i=0;i<100&&!port;i++){try{port=Number((await readFile(profile+'/DevToolsActivePort','utf8')).split('\n')[0]);}catch{}await sleep(100);}
 const page=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p=>p.type==='page');ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);let seq=0;const pending=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){pending.get(m.id)(m.result);pending.delete(m.id);}};
 const send=(method,params={})=>new Promise(r=>{const id=++seq;pending.set(id,r);ws.send(JSON.stringify({id,method,params}));});const ev=async expression=>(await send('Runtime.evaluate',{expression,returnByValue:true})).result.value;
 await send('Emulation.setDeviceMetricsOverride',{width:1080,height:900,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:process.argv[2]});let ready=false;for(let i=0;i<150&&!ready;i++){ready=await ev("document.body?.dataset.ready==='true' && document.getElementById('error').hidden");await sleep(100);}if(!ready)throw Error('viewer not ready');const manifest=await(await fetch(new URL('manifest.json',process.argv[2]))).json();const rows=[];const clips=process.argv[3]?{}:Object.fromEntries(Object.entries(manifest.clips).map(([k,v])=>[k,v.duration]));
 for(const speed of [1,.25])for(const [clip,duration] of Object.entries(clips)){
  await ev(`(()=>{for(const [id,value] of [['clip','${clip}'],['speed','${speed}'],['time','0']]){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('change'));}document.querySelector('[data-view="quarter"]').click();document.getElementById('loop').checked=false;document.getElementById('loop').dispatchEvent(new Event('change'));document.getElementById('play').click();})()`);
  const captured=[];
  for(let i=0;i<10;i++){
   await sleep(duration*1000/10/speed);
   const time=await ev("Number(document.getElementById('time').value)");
   const shot=await send('Page.captureScreenshot',{format:'png',clip:{x:16,y:105,width:692,height:650,scale:1}});
   await writeFile(`/tmp/gst-final-play-${clip}-${speed}-${String(i).padStart(2,'0')}.png`,Buffer.from(shot.data,'base64'));
   captured.push(time);
  }
  if(captured[0]<=0 || Math.abs(captured.at(-1)-duration)>.03)throw Error(`Incomplete playback ${clip}: ${captured}`);
  rows.push({clip,speed,captured});console.log('PLAYED',clip,speed);
 }
 if(process.argv[3]==='loops'){
  const loops=[];
  for(const [clip,duration] of Object.entries({Standing:3,Walking:1.4,Running:1,Fidget:3})){
   await ev(`(()=>{for(const [id,value] of [['clip','${clip}'],['speed','1'],['time','${duration-.1}']]){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('change'));}document.getElementById('loop').checked=true;document.getElementById('loop').dispatchEvent(new Event('change'));document.getElementById('play').click();})()`);
   await sleep(350);const state=await ev('window.reviewState');if(!state.playing||state.time_seconds>=duration-.1)throw Error('Loop did not wrap '+clip);
   loops.push({clip,time:state.time_seconds,wrapped:true});await ev("document.getElementById('play').click()");
  }
  await writeFile('/tmp/gst-loop-check.json',JSON.stringify({pass:true,loops},null,2));console.log(loops);
 }
 if(process.argv[3]!=='loops') for(const tier of manifest.models.map(m=>m.id)){
  await ev(`(()=>{let e=document.getElementById('modelRevision');e.value='${tier}';e.dispatchEvent(new Event('change'));})()`);await sleep(1000);
  for(const focus of ['body','head']){
   await ev(`(()=>{for(const [id,value] of [['clip','Standing'],['time','0'],['focus','${focus}']]){let e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('change'));}document.querySelector('[data-view="front"]').click();})()`);await sleep(300);
   const shot=await send('Page.captureScreenshot',{format:'png'});await writeFile(`/tmp/gst-final-${tier}-${focus}.png`,Buffer.from(shot.data,'base64'));
  }
 }
 if(process.argv[3]==='feedback'){
  await ev(`(()=>{const e=document.getElementById('modelRevision');e.value='gst_a';e.dispatchEvent(new Event('change'));})()`);await sleep(800);
  const poses=[];
  for(const view of ['front','left','quarter'])for(const frame of [0,12,24,36,44,56,70,84]){
   await ev(`(()=>{for(const [id,value] of [['clip','Attack'],['time','${frame/60}'],['focus','body']]){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('change'));}document.querySelector('[data-view="${view}"]').click();})()`);await sleep(150);
   const shot=await send('Page.captureScreenshot',{format:'png',clip:{x:16,y:105,width:692,height:650,scale:1}});await writeFile(`/tmp/gst-v2-${view}-${frame}.png`,Buffer.from(shot.data,'base64'));poses.push(await ev('window.reviewState'));
  }
  await writeFile('/tmp/gst-feedback-check.json',JSON.stringify({revision:manifest.revision,models:manifest.models,poses},null,2));
 }
 if(process.argv[3]==='details'){
  await ev(`(()=>{const e=document.getElementById('modelRevision');e.value='gst_a';e.dispatchEvent(new Event('change'));})()`);await sleep(800);
  const poses=[['Standing',0,'body','back'],['Standing',0,'body','left'],['Standing',0,'head','left'],['Standing',0,'arms','front'],['Attack',.35,'arms','front'],['Attack',.55,'arms','left'],['Attack',.8,'arms','right'],['Fidget',1.2,'arms','front'],['Dead',0,'body','quarter'],['Walking',.35,'body','left']];
  for(let i=0;i<poses.length;i++){
   const [clip,t,focus,view]=poses[i];await ev(`(()=>{for(const [id,value] of [['clip','${clip}'],['time','${t}'],['focus','${focus}']]){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('change'));}document.querySelector('[data-view="${view}"]').click();})()`);await sleep(200);const shot=await send('Page.captureScreenshot',{format:'png'});await writeFile(`/tmp/gst-detail-${i}.png`,Buffer.from(shot.data,'base64'));
  }
  const skin=await ev('window.reviewSkinning');if(skin.meshes!==2 || skin.maximum_weight_sum_error>=1e-4)throw Error('Eight-weight viewer check failed');await writeFile('/tmp/gst-detail-check.json',JSON.stringify({poses,skin,models:manifest.models},null,2));
 }
 await ev(`(()=>{for(const [id,value] of [['clip','Dead'],['time','0'],['focus','body']]){let e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('change'));}document.querySelector('[data-view="left"]').click();})()`);await sleep(300);
 const corpse=await send('Page.captureScreenshot',{format:'png'});await writeFile('/tmp/gst-final-corpse-left.png',Buffer.from(corpse.data,'base64'));

 if(rows.length)await writeFile('/tmp/gst-playback-check.json',JSON.stringify({pass:true,revision:manifest.revision,models:manifest.models.map(m=>({id:m.id,sha256:m.sha256})),rows},null,2));console.log(rows);
}finally{ws?.close();browser.kill();await sleep(300);await rm(profile,{recursive:true,force:true});}
