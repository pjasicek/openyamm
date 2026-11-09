import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir,mkdtemp,rm} from 'node:fs/promises';
const [base,output]=process.argv.slice(2);
await mkdir(output,{recursive:true});
const profile=await mkdtemp('/tmp/openyamm-lizard-review-');
const browser=spawn('google-chrome',['--headless=new','--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=0','--remote-allow-origins=*','--no-first-run','--disable-background-networking','--user-data-dir='+profile,'about:blank'],{stdio:['ignore','ignore','pipe']});
let log='';browser.stderr.on('data',d=>log+=d.toString());
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let ws,serial=0;const pending=new Map(),errors=[],records=[];
try{
  let port;
  for(let i=0;i<100;i++){try{port=Number((await readFile(profile+'/DevToolsActivePort','utf8')).split('\n')[0]);}catch{}if(port)break;await sleep(100);}
  assert.ok(port,log.slice(-1500));
  const page=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p=>p.type==='page');
  ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
  ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
  const ev=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
  const input=(id,value)=>ev(`(()=>{const e=document.getElementById(${JSON.stringify(id)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change'));})()`);
  const click=id=>ev(`document.getElementById(${JSON.stringify(id)}).click()`);
  await send('Page.enable');await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1160,height:960,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:base});
  let ready=false;
  for(let i=0;i<200;i++){ready=await ev("document.body.dataset.ready==='true'&&document.getElementById('error').hidden");if(ready)break;await sleep(100);}
  assert.ok(ready,await ev("document.getElementById('error').textContent"));
  await ev("document.querySelector('h1').textContent='MM8 Lizardman villager A · animation review';document.querySelector('header p').textContent='Shared viewer, isolated lizardman model. Live normal and quarter-speed playback capture.';");
  const clips=await ev("Array.from(document.getElementById('clip').options,o=>o.value)");
  for(const name of clips)for(const view of ['front','right'])for(const speed of [1,0.25]){
    await input('clip',name);await ev(`document.querySelector('[data-view=${view}]').click()`);await input('speed',speed);await click('restart');
    const duration=await ev('window.reviewState.duration');
    const looping=await ev("document.getElementById('loop').checked");
    await click('play');let ended=false;const start=Date.now(),samples=[];
    for(let i=0;i<12;i++){
      await sleep(Math.max(15,duration/speed*1000/11));
      const state=await ev('window.reviewState');
      const data=await ev("document.getElementById('model').toDataURL('image/png').split(',')[1]");
      const file=`${name}_${view}_${speed}x_${String(i).padStart(2,'0')}.png`;
      await writeFile(output+'/'+file,Buffer.from(data,'base64'));
      samples.push({...state,wall_ms:Date.now()-start,file});
      if(!state.playing){ended=true;break;}
    }
    if(await ev('window.reviewState.playing'))await click('play');
    assert.ok(samples.some(s=>s.time_seconds>0),name+' advances');
    if(!looping)assert.ok(ended&&Math.abs(samples.at(-1).time_seconds-duration)<1e-5,name+' reaches endpoint');
    await click('end');assert.ok(Math.abs((await ev('window.reviewState.time_seconds'))-duration)<1e-6);
    records.push({clip:name,view,speed,duration,looping,samples});
  }
  assert.equal(errors.length,0,JSON.stringify(errors));
  await writeFile(output+'/playback.json',JSON.stringify({status:'pass',viewer:'mm6_goblin/review_20261006 (reused without modifying files)',records,console_exceptions:errors},null,2));
  console.log('Live playback captures verified:',records.length);
}finally{if(ws)ws.close();browser.kill('SIGTERM');if(browser.exitCode===null&&browser.signalCode===null)await new Promise(r=>browser.once('exit',r));await rm(profile,{recursive:true,force:true,maxRetries:10,retryDelay:100});}
