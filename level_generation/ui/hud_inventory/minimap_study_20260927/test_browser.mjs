import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {writeFile} from 'node:fs/promises';
const base='http://127.0.0.1:8899/level_generation/ui/hud_inventory/minimap_study_20260927/';
const browser=spawn('google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
  '--remote-debugging-port=9288','--remote-allow-origins=*','--window-size=1500,1050',
  '--user-data-dir=/tmp/openyamm-minimap-browser-'+Date.now(),base],{stdio:'ignore'});
const delay=ms=>new Promise(r=>setTimeout(r,ms));let ws;
try {
 let page;
 for(let n=0;n<100;n++){
  try{page=(await(await fetch('http://127.0.0.1:9288/json/list')).json()).find(p=>p.type==='page'&&p.url.startsWith(base));if(page)break;}catch{}
  await delay(100);
 }
 assert.ok(page,'Browser started');ws=new WebSocket(page.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
 let serial=0;const pending=new Map();
 ws.onmessage=e=>{const r=JSON.parse(e.data),p=pending.get(r.id);if(p){pending.delete(r.id);r.error?p.reject(r.error):p.resolve(r.result);}};
 const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
 const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
 for(let n=0;n<100;n++){if(await evaluate("document.body?.dataset.ready==='true'"))break;await delay(100);}
 assert.equal(await evaluate("document.body.dataset.ready"),'true');
 assert.equal(await evaluate("document.querySelector('#right').options.length"),16);
 assert.equal(await evaluate("window.MINIMAP_STUDY.blender_projection.max_projection_error_x2_pixels"),0);
 const snapshot=()=>evaluate("document.querySelector('#rightMap').toDataURL()");
 assert.equal(await evaluate("document.querySelector('#right').value"),'vinevi_noise_light_x2');
 assert.equal(await evaluate("window.MINIMAP_STUDY.vinevi_process.processed_object_alpha_exactly_preserved"),true);
 assert.equal(await evaluate("window.MINIMAP_STUDY.vinevi_process.capture.max_projection_error_x2_pixels"),0);
 for(const key of await evaluate("Array.from(document.querySelector('#right').options,o=>o.value)")){
  await evaluate(`document.querySelector('#right').value=${JSON.stringify(key)};document.querySelector('#right').dispatchEvent(new Event('change'))`);
  assert.ok((await snapshot()).length>10000,key+' draws');
 }
 await evaluate("document.querySelector('#process').click()");
 assert.equal(await evaluate("document.querySelector('#right').value"),'vinevi_x2');
 await evaluate("document.querySelector('#processCompare').click()");
 assert.equal(await evaluate("document.querySelector('#left').value"),'vinevi_previous_x2');
 await evaluate("document.querySelector('#process').click()");
 await evaluate("document.querySelector('#noiseMedium').click()");
 assert.equal(await evaluate("document.querySelector('#right').value"),'vinevi_noise_medium_x2');
 await evaluate("document.querySelector('#noiseLight').click()");
 assert.equal(await evaluate("document.querySelector('#right').value"),'vinevi_noise_light_x2');
 assert.equal(await evaluate("document.querySelector('#left').value"),'vinevi_x2');
 const full=await snapshot();
 await evaluate("document.querySelector('[data-view=town]').click()");assert.notEqual(await snapshot(),full);
 const town=await snapshot();
 await evaluate("document.querySelector('#geometry').click()");assert.notEqual(await snapshot(),town);
 await evaluate("document.querySelector('#capture').click()");assert.equal(await evaluate("document.querySelector('#right').value"),'blender_styled_x2');
 const capture=await snapshot();
 await send('Input.dispatchKeyEvent',{type:'keyDown',key:' ',code:'Space',windowsVirtualKeyCode:32});assert.notEqual(await snapshot(),capture);
 await send('Input.dispatchKeyEvent',{type:'keyUp',key:' ',code:'Space',windowsVirtualKeyCode:32});assert.equal(await snapshot(),capture);
 await evaluate("document.querySelector('#noiseLight').click()");
 const screenshot=await send('Page.captureScreenshot',{format:'png'});
 await writeFile('/tmp/openyamm-minimap-town.png',Buffer.from(screenshot.data,'base64'));
 await evaluate("document.querySelector('#noiseMedium').click();document.querySelector('#geometry').click();document.querySelector('[data-view=full]').click()");
 const fullScreenshot=await send('Page.captureScreenshot',{format:'png'});
 await writeFile('/tmp/openyamm-minimap-full.png',Buffer.from(fullScreenshot.data,'base64'));
 const result={result:'PASS',checks:['16 images loaded and drawn','both terrain noise presets','vinevi default and both presets','building alpha preserved','shared town zoom','model overlay','capture selection','blink original and restore','zero camera projection error'],url:base};
 await writeFile('level_generation/ui/hud_inventory/minimap_study_20260927/browser_check.json',JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(result));
} finally{ws?.close();browser.kill('SIGTERM');}
