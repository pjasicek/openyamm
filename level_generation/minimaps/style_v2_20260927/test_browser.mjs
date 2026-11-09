import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
const dir='level_generation/minimaps/style_v2_20260927/';
const base='http://127.0.0.1:8899/'+dir;
const browser=spawn('google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
 '--remote-debugging-port=9288','--remote-allow-origins=*','--window-size=1500,1100',
 '--user-data-dir=/tmp/openyamm-minimap-style-browser-'+Date.now(),base],{stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));let ws;
try{
 let page;
 for(let n=0;n<100;n++){try{page=(await(await fetch('http://127.0.0.1:9288/json/list')).json()).find(p=>p.type==='page'&&p.url===base);if(page)break;}catch{}await delay(100);}
 assert.ok(page);ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
 let serial=0;const pending=new Map(),errors=[];
 ws.onmessage=e=>{const r=JSON.parse(e.data);if(r.method==='Runtime.exceptionThrown')errors.push(r.params);const p=pending.get(r.id);if(p){pending.delete(r.id);r.error?p.reject(r.error):p.resolve(r.result);}};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 await send('Runtime.enable');
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
 const ready=async()=>{for(let n=0;n<150;n++){if(await evaluate("document.body?.dataset.ready==='true'"))return;await delay(100);}throw new Error('Image load timeout');};
 await ready();assert.equal(await evaluate("document.querySelector('#map').options.length"),4);
 const images=new Set();
 for(let i=0;i<4;i++){
  await evaluate(`document.querySelector('#map').value='${i}';document.querySelector('#map').dispatchEvent(new Event('change'))`);await ready();
  images.add(await evaluate("document.querySelector('#right').toDataURL()"));
  assert.equal(await evaluate("document.querySelector('#right').height"),i%2?1020:1024);
 }
 assert.equal(images.size,4);
 await evaluate("document.querySelector('#map').value='1';document.querySelector('#map').dispatchEvent(new Event('change'))");await ready();
 const snapshot=()=>evaluate("document.querySelector('#right').toDataURL()");const full=await snapshot();
 await evaluate("document.querySelector('#outline').click()");assert.notEqual(await snapshot(),full);
 await evaluate("document.querySelector('#zoom').click()");const zoom=await snapshot();assert.notEqual(zoom,full);
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:' ',code:'Space',windowsVirtualKeyCode:32});assert.notEqual(await snapshot(),zoom);
 await send('Input.dispatchKeyEvent',{type:'keyUp',key:' ',code:'Space',windowsVirtualKeyCode:32});assert.equal(await snapshot(),zoom);
 await evaluate("document.querySelector('#zoom').click();document.querySelector('#outline').click()");
 const before=await evaluate("document.querySelector('#left').toDataURL()");
 await evaluate("document.querySelector('#baseline').value='previous';document.querySelector('#baseline').dispatchEvent(new Event('change'))");
 assert.notEqual(await evaluate("document.querySelector('#left').toDataURL()"),before);
 await evaluate("document.querySelector('#baseline').value='original';document.querySelector('#baseline').dispatchEvent(new Event('change'))");
 const screenshot=await send('Page.captureScreenshot',{format:'png'});
 await writeFile(dir+'browser_review.png',Buffer.from(screenshot.data,'base64'));
 assert.equal(errors.length,0,JSON.stringify(errors));
 const result={result:'PASS',count:4,url:base,checks:['Four distinct Blender candidates loaded','Native 1024/1020 canvas heights','Original/deployed comparisons','Geometry overlay','Zoom','Blink and restore','No browser exceptions']};
 await writeFile(dir+'browser_check.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{ws?.close();browser.kill('SIGTERM');}
