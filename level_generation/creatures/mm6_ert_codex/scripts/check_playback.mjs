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
 for(const speed of [1,.25])for(const [clip,duration] of Object.entries(clips)){
  await ev(`(()=>{for(const [id,value] of [['clip','${clip}'],['speed','${speed}'],['time','0']]){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('change'));}document.querySelector('[data-view="quarter"]').click();document.getElementById('loop').checked=false;document.getElementById('loop').dispatchEvent(new Event('change'));document.getElementById('play').click();})()`);
  const captured=[];
  for(let i=0;i<10;i++){
   await sleep(duration*1000/10/speed);
   const time=await ev("Number(document.getElementById('time').value)");
   const shot=await send('Page.captureScreenshot',{format:'png',clip:{x:16,y:105,width:692,height:650,scale:1}});
   await writeFile(`/tmp/ert-final-play-${clip}-${speed}-${String(i).padStart(2,'0')}.png`,Buffer.from(shot.data,'base64'));
   captured.push(time);
  }
  if(captured[0]<=0 || Math.abs(captured.at(-1)-duration)>.03)throw Error(`Incomplete playback ${clip}: ${captured}`);
  rows.push({clip,speed,captured});console.log('PLAYED',clip,speed);
 }
 await writeFile('/tmp/ert-playback-check.json',JSON.stringify({pass:true,rows},null,2));console.log(rows);
}finally{ws?.close();browser.kill();await sleep(300);await rm(profile,{recursive:true,force:true});}
