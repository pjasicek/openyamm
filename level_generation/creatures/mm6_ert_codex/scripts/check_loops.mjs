import {spawn} from 'node:child_process';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));const profile=await mkdtemp('/tmp/ert-playback-');
const browser=spawn('google-chrome',['--headless=new','--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{stdio:'ignore'});let ws;
try {
 let port;for(let i=0;i<100&&!port;i++){try{port=Number((await readFile(profile+'/DevToolsActivePort','utf8')).split('\n')[0]);}catch{}await sleep(100);}
 const page=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p=>p.type==='page');ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);let seq=0;const pending=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){pending.get(m.id)(m.result);pending.delete(m.id);}};
 const send=(method,params={})=>new Promise(r=>{const id=++seq;pending.set(id,r);ws.send(JSON.stringify({id,method,params}));});const ev=async expression=>(await send('Runtime.evaluate',{expression,returnByValue:true})).result.value;
 await send('Emulation.setDeviceMetricsOverride',{width:1080,height:900,deviceScaleFactor:1,mobile:false});
 await send('Page.navigate',{url:process.argv[2]});let ready=false;for(let i=0;i<150&&!ready;i++){ready=await ev("document.body?.dataset.ready==='true' && document.getElementById('error').hidden");await sleep(100);}if(!ready)throw Error('viewer not ready');const rows=[];const clips={Standing:2.4,Walking:43/30,Attack:1.5,Hit:.75,Fidget:2.4,Death:1.8,Dead:1};
 for(const clip of ['Standing','Walking','Fidget']){
  const duration=clips[clip];await ev(`(()=>{for(const [id,value] of [['clip','${clip}'],['speed','1'],['time','${duration-.1}']]){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('change'));}document.getElementById('loop').checked=true;document.getElementById('loop').dispatchEvent(new Event('change'));document.getElementById('play').click();})()`);
  await sleep(400);const state=await ev('window.reviewState');if(!state.playing || state.time_seconds>=duration-.1)throw Error('Loop did not wrap '+clip);rows.push({clip,wrapped:true,time:state.time_seconds});await ev("document.getElementById('play').click()");
 }
 await writeFile('/tmp/ert-loop-check.json',JSON.stringify({pass:true,rows},null,2));console.log(rows);
}finally{ws?.close();browser.kill();await sleep(300);await rm(profile,{recursive:true,force:true});}
