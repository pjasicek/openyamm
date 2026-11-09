import {spawn} from 'node:child_process';
import {mkdtempSync,readFileSync,writeFileSync,existsSync,rmSync,mkdirSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
const profile=mkdtempSync(join(tmpdir(),'mfp-review-')),wait=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn('google-chrome',['--headless=new','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',`--user-data-dir=${profile}`,'--remote-debugging-port=0','about:blank'],{stdio:'ignore'});
let ws;
try {
 for(let i=0;i<100&&!existsSync(join(profile,'DevToolsActivePort'));i++)await wait(100);
 const port=readFileSync(join(profile,'DevToolsActivePort'),'utf8').split('\n')[0];
 const page=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(x=>x.type==='page');
 ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((r,e)=>{ws.onopen=r;ws.onerror=e});let id=0;const pending=new Map();
 ws.onmessage=e=>{const m=JSON.parse(e.data);if(pending.has(m.id)){pending.get(m.id)(m.result);pending.delete(m.id)}};
 const send=(method,params={})=>new Promise(r=>{const n=++id;pending.set(n,r);ws.send(JSON.stringify({id:n,method,params}))});
 await send('Emulation.setDeviceMetricsOverride',{width:1200,height:1000,deviceScaleFactor:1,mobile:false});await send('Page.navigate',{url:process.argv[2]});
 let ready=false;for(let i=0;i<100&&!ready;i++){await wait(200);const r=await send('Runtime.evaluate',{expression:"document.body?.dataset.ready==='true'",returnByValue:true});ready=r.result?.value===true;}if(!ready)throw Error('viewer not ready');
 const shots=JSON.parse(readFileSync(process.argv[4],'utf8'));
 for(const [name,clip,time,camera,target,sha]of shots){const pose={clip,time_seconds:time,camera,target,view:'front',focus:'arms',model_sha256:sha};await send('Runtime.evaluate',{expression:`location.hash=encodeURIComponent(${JSON.stringify(JSON.stringify(pose))})`});for(let k=0;k<200;k++){await wait(100);const state=await send('Runtime.evaluate',{expression:'window.reviewState',returnByValue:true});const v=state.result?.value;if(v&&v.clip===clip&&Math.abs(v.time_seconds-time)<1e-5&&(!sha||v.model_sha256===sha))break;if(k===199)throw Error('Pose did not load: '+name);}await wait(100);const r=await send('Runtime.evaluate',{expression:"document.getElementById('model').toDataURL('image/png')",returnByValue:true});const path=join(process.argv[3],`${name}.png`);mkdirSync(dirname(path),{recursive:true});writeFileSync(path,Buffer.from(r.result.value.split(',')[1],'base64'));}
 console.log(`Captured ${shots.length} final viewer poses`);
} finally {if(ws)ws.close();chrome.kill('SIGKILL');await wait(100);rmSync(profile,{recursive:true,force:true});}
