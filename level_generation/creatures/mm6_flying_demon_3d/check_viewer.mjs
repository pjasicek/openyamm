import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir,mkdtemp,rm} from 'node:fs/promises';
const project='/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_flying_demon_3d';
if(process.argv.includes('--links-only')) {
 const html=await readFile(project+'/index.html','utf8');
 const links=[...html.matchAll(/<a[^>]*href="([^"]+)"/g)].map(m=>m[1]).filter(h=>h&&!h.startsWith('#'));
 for(const href of links) {
  const result=await fetch('http://127.0.0.1:8901/level_generation/creatures/mm6_flying_demon_3d/'+href,{method:'HEAD'});
  assert.equal(result.status,200,href);
 }
 console.log(links.length+' review links return HTTP 200.');process.exit(0);
}
const output='/tmp/openyamm-flying-demon-browser';await mkdir(output,{recursive:true});
const profile=await mkdtemp('/tmp/openyamm-flying-demon-chrome-');
const browser=spawn('google-chrome',['--headless=new','--no-sandbox','--disable-dev-shm-usage','--allow-file-access-from-files','--remote-debugging-port=0','--remote-allow-origins=*','--no-first-run','--disable-background-networking','--user-data-dir='+profile,'about:blank'],{stdio:['ignore','ignore','pipe']});
let log='';browser.stderr.on('data',d=>log+=d);const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const errors=[],failures=[],checks=[],playback=[];let ws,serial=0;
try {
 let port;for(let i=0;i<100;i++){try{port=Number((await readFile(profile+'/DevToolsActivePort','utf8')).split('\n')[0]);}catch{}if(port||browser.exitCode!==null)break;await sleep(100);}
 assert(port,'Chrome starts: '+log.slice(-1500));const page=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p=>p.type==='page');
 ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});const pending=new Map();
 ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);if(m.method==='Network.loadingFailed')failures.push(m.params.errorText);};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});assert(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
 const input=(id,value,event='change')=>evaluate(`(()=>{const e=document.getElementById(${JSON.stringify(id)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event(${JSON.stringify(event)}));})()`);
 const click=id=>evaluate(`document.getElementById(${JSON.stringify(id)}).click()`);
 const until=async expression=>{for(let i=0;i<100;i++){if(await evaluate(expression))return;await sleep(50);}throw Error('Timed out: '+expression);};
 const check=async(name,expression)=>{assert(await evaluate(expression),name);checks.push(name);};
 await send('Page.enable');await send('Runtime.enable');await send('Network.enable');await send('Emulation.setDeviceMetricsOverride',{width:1400,height:1100,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:'http://127.0.0.1:8901/level_generation/creatures/mm6_flying_demon_3d/'});await until('window.renderedReviewState?.clip==="Flight"');
 await check('Five clips, five views, three playback speeds','document.getElementById("clip").options.length===5&&document.getElementById("view").options.length===5&&document.getElementById("speed").options.length===3');
 await evaluate(`Promise.all(Object.entries(DATA).flatMap(([clip,c])=>['front','diagonal','profile','rear_diagonal','back'].flatMap(view=>Array.from({length:clip==='Ash_Remains'?1:c.end+1},(_,i)=>bitmap('review/preview_frames/'+clip+'_'+view+'_'+String(i).padStart(2,'0')+'.jpg')))))`);
 for(const [clip,end] of Object.entries({Flight:36,Attack:36,Hit:36,Death:42,Ash_Remains:6})){
  await input('clip',clip);await until(`window.renderedReviewState?.clip===${JSON.stringify(clip)}`);
  for(const view of ['front','diagonal','profile','rear_diagonal','back']){
   await input('view',view);await input('frame',clip==='Ash_Remains'?0:Math.min(12,end),'input');await until(`window.renderedReviewState?.view===${JSON.stringify(view)}&&window.renderedReviewState?.frame===${clip==='Ash_Remains'?0:Math.min(12,end)}`);
  }
  await input('view','front');
  for(const speed of [1,.25]){
   await input('speed',String(speed));await click('restart');await click('play');const sequence=[];const interval=clip==='Ash_Remains'?80:Math.round(end/48/speed*1000/7);
   for(let i=0;i<8;i++){
    if(i)await sleep(interval);const state=await evaluate('window.renderedReviewState');sequence.push(state);
    const data=await evaluate('document.getElementById("model").toDataURL("image/png").split(",")[1]');await writeFile(`${output}/${clip}_${speed}_${i}.png`,Buffer.from(data,'base64'));
   }
   const live=await evaluate('window.reviewState');assert(sequence.some(s=>s.frame>0)||clip==='Ash_Remains',clip+' playback advances');
   if(clip==='Flight'){assert(live.playing,'flight loops');await click('play');}else {await until('window.reviewState.playing===false');await check(clip+' endpoint at '+speed+'x',`window.reviewState.frame===${end}`);}
   playback.push({clip,speed,method:'Live requestAnimationFrame playback; displayed canvas captures sampled in wall-clock time',sequence});
  }
 }
 await input('clip','Death');await click('ash');await check('Death button selects held ash','window.reviewState.clip==="Ash_Remains"');
 await input('clip','Flight');await until('window.renderedReviewState?.clip==="Flight"');await check('Flight restarts after ash','window.reviewState.frame===0&&window.reviewState.native==="wdmflya0"');
 await send('Page.captureScreenshot',{format:'png'}).then(r=>writeFile(output+'/desktop.png',Buffer.from(r.data,'base64')));
 await send('Emulation.setDeviceMetricsOverride',{width:390,height:1000,deviceScaleFactor:1,mobile:false});await sleep(100);await check('Mobile layout fits','document.documentElement.scrollWidth<=document.documentElement.clientWidth');
 assert.equal(errors.length,0,JSON.stringify(errors));assert.equal(failures.length,0,JSON.stringify(failures));
 await writeFile(output+'/browser_validation.json',JSON.stringify({status:'pass',checks,playback,console_exceptions:errors,failed_requests:failures},null,2)+'\n');console.log('Browser passes normal/quarter-speed playback, every clip/view, endpoints and resets.');
} catch(error){await writeFile(output+'/browser_validation.json',JSON.stringify({status:'fail',checks,playback,error:String(error),console_exceptions:errors,failed_requests:failures,browser_log:log.slice(-1500)},null,2)+'\n');throw error;}
finally{if(ws)ws.close();browser.kill('SIGTERM');if(browser.exitCode===null&&browser.signalCode===null)await new Promise(r=>browser.once('exit',r));await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:100});}
