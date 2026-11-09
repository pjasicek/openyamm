import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
const base='http://127.0.0.1:8899/level_generation/minimaps/';
const output=process.argv[2]||'level_generation/minimaps';
const browser=spawn('google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
 '--remote-debugging-port=9288','--remote-allow-origins=*','--window-size=1500,1100',
 '--user-data-dir=/tmp/openyamm-minimap-batch-browser-'+Date.now(),base],{stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));let ws;
try{
 let page;
 for(let n=0;n<100;n++){try{page=(await(await fetch('http://127.0.0.1:9288/json/list')).json()).find(p=>p.type==='page'&&p.url===base);if(page)break;}catch{}await delay(100);}
 assert.ok(page);ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
 let serial=0;const pending=new Map();const errors=[];
 ws.onmessage=e=>{const r=JSON.parse(e.data);if(r.method==='Runtime.exceptionThrown')errors.push(r.params);const p=pending.get(r.id);if(p){pending.delete(r.id);r.error?p.reject(r.error):p.resolve(r.result);}};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 await send('Runtime.enable');
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
 const ready=async()=>{for(let n=0;n<150;n++){if(await evaluate("document.body?.dataset.ready==='true'"))return;await delay(100);}throw new Error('Image load timeout');};
 await ready();assert.equal(await evaluate("document.querySelector('#map').options.length"),42);
 const manifest=await(await fetch(base+'exports.json')).json();
 const accepted=await(await fetch(new URL('../ui/hud_inventory/accepted_icons.json',base))).json();
 const snapshots=new Set();
 for(let i=0;i<42;i++){
  await evaluate(`document.querySelector('#map').value='${i}';document.querySelector('#map').dispatchEvent(new Event('change'))`);await ready();
  const row=manifest.records[i],record=accepted.records[row.target];
  const path=new URL('../../'+record.runtime_output_path+'?v='+record.sha256.slice(0,12),base).href;
  const expected=await evaluate(`(async()=>{const image=new Image();image.src=${JSON.stringify(path)};await image.decode();
   const canvas=document.createElement('canvas');canvas.width=${row.x2_size[0]};canvas.height=${row.x2_size[1]};
   canvas.getContext('2d').drawImage(image,0,0);return canvas.toDataURL();})()`);
  const actual=await evaluate("document.querySelector('#current').toDataURL()");
  assert.equal(actual,expected,'Displayed accepted art: '+row.target);snapshots.add(actual);
 }
 for(const [world,count] of [['mm6',15],['mm7',13],['mm8',14]]){
  await evaluate(`document.querySelector('#world').value='${world}';document.querySelector('#world').dispatchEvent(new Event('change'))`);await ready();
  assert.equal(await evaluate("document.querySelector('#map').options.length"),count);
 }
 await evaluate("document.querySelector('#world').value='mm6';document.querySelector('#world').dispatchEvent(new Event('change'))");await ready();
 await evaluate("document.querySelector('#map').value='14';document.querySelector('#map').dispatchEvent(new Event('change'))");await ready();
 if(process.argv[2]){
  assert.equal(await evaluate("document.querySelector('#validation').href"),new URL('../../'+output+'/validation.json',base).href);
  assert.equal(await evaluate("(async()=>{const r=await fetch(document.querySelector('#validation').href);return r.status})()"),200);
 }
 const snapshot=()=>evaluate("document.querySelector('#current').toDataURL()");const full=await snapshot();
 await evaluate("document.querySelector('#outline').click()");assert.notEqual(await snapshot(),full);
 await evaluate("document.querySelector('#town').click()");const zoom=await snapshot();assert.notEqual(zoom,full);
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:' ',code:'Space',windowsVirtualKeyCode:32});assert.notEqual(await snapshot(),zoom);
 await send('Input.dispatchKeyEvent',{type:'keyUp',key:' ',code:'Space',windowsVirtualKeyCode:32});assert.equal(await snapshot(),zoom);
 await evaluate("document.querySelector('#town').click();document.querySelector('#outline').click()");
 const screenshot=await send('Page.captureScreenshot',{format:'png'});
 await writeFile(output+'/browser_review.png',Buffer.from(screenshot.data,'base64'));
 assert.equal(errors.length,0,JSON.stringify(errors));
 const result={result:'PASS',count:42,unique_images:snapshots.size,url:base,checks:['42 replacements match installed accepted art','15/13/14 world filters','geometry overlay','zoom','native blink and restore','no browser exceptions']};
 await writeFile(output+'/browser_check.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{ws?.close();browser.kill('SIGTERM');}
