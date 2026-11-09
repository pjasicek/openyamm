import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const here=dirname(fileURLToPath(import.meta.url));
const profile=`/tmp/obsidian-curved-${Date.now()}`;
const delay=ms=>new Promise(ok=>setTimeout(ok,ms));
const browser=spawn('google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
  '--allow-file-access-from-files','--remote-debugging-port=0','--remote-allow-origins=*',
  `--user-data-dir=${profile}`,'about:blank'],{stdio:'ignore'});
let ws;
const checks=[],errors=[];
try{
  let port;
  for(let i=0;i<100;i++){
    try{port=Number((await readFile(resolve(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]);}catch{}
    if(port)break;
    await delay(100);
  }
  assert.ok(port,'Chrome started');
  const pages=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
  await new Promise((ok,no)=>{ws.onopen=ok;ws.onerror=no;});
  let serial=0;const pending=new Map();
  ws.onmessage=event=>{const m=JSON.parse(event.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.no(m.error):p.ok(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params);if(m.method==='Network.loadingFailed')errors.push(m.params);};
  const send=(method,params={})=>new Promise((ok,no)=>{const id=++serial;pending.set(id,{ok,no});ws.send(JSON.stringify({id,method,params}));});
  const ev=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
  const check=async(name,expression)=>{assert.equal(await ev(expression),true,name);checks.push(name);};
  const shot=async name=>{await delay(150);const r=await send('Page.captureScreenshot',{format:'png'});await writeFile(resolve(here,'images',`${name}.png`),Buffer.from(r.data,'base64'));};
  const navigate=async mode=>{await send('Page.navigate',{url:pathToFileURL(resolve(here,'index.html')).href+`?mode=${mode}`});await delay(700);await ev('document.fonts.ready');};
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1600,height:1200,deviceScaleFactor:1,mobile:false});
  await mkdir(resolve(here,'images'),{recursive:true});
  await navigate('split');
  await check('Five portraits, four mana gauges, one selected diamond',`document.querySelectorAll('#bar .pc').length===5 && document.querySelectorAll('#bar .sp-meter').length===4 && document.querySelectorAll('#bar .selection-diamond').length===1`);
  await check('Native image assets and reference exist',`Promise.all([...document.querySelectorAll('image')].map(i=>new Promise(ok=>{const image=new Image();image.onload=()=>ok(true);image.onerror=()=>ok(false);image.src=i.getAttribute('href');}))).then(r=>r.every(Boolean))`);
  await shot('split');
  await ev(`document.querySelector('#bar [data-pc="2"]').dispatchEvent(new MouseEvent('click',{bubbles:true}))`);
  await check('Portrait selection updates the resource controls',`document.getElementById('active-name').textContent==='Corin' && document.getElementById('no-mana').checked && document.getElementById('mana').disabled`);
  await ev(`document.querySelector('#bar [data-buff="0"]').dispatchEvent(new MouseEvent('click',{bubbles:true}))`);
  await check('Buff button opens its own member without selecting that member',`!document.getElementById('buff-popup').hidden && document.querySelector('#buff-popup h3').textContent==='Ariel' && document.getElementById('active-name').textContent==='Corin'`);
  await ev(`document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}));document.getElementById('recovering').click();document.getElementById('aggro').value='combat';document.getElementById('aggro').dispatchEvent(new Event('change'))`);
  await check('All recovering hides selection and draws five recovery arcs',`document.querySelectorAll('#bar .selection-diamond').length===0 && document.querySelectorAll('#bar .recovery-arc').length===5 && [...document.querySelectorAll('#bar .aggro-indicator')].every(i=>i.getAttribute('href').includes('combat'))`);
  await shot('recovering');
  await ev(`document.getElementById('recovering').click();document.querySelector('#bar [data-pc="0"]').dispatchEvent(new MouseEvent('click',{bubbles:true}));document.getElementById('no-mana').click()`);
  await check('No mana hides the entire mana gauge and track',`document.querySelectorAll('#bar [data-pc="0"] .sp-meter').length===0`);
  await ev(`document.getElementById('hp').value=30;document.getElementById('hp').dispatchEvent(new Event('input'));document.getElementById('damage').click()`);
  await delay(1000);
  await check('Damage updates HP and leaves valid arc paths',`document.getElementById('hp').value==='8' && [...document.querySelectorAll('#bar path')].every(p=>!p.getAttribute('d')?.includes('NaN'))`);
  await shot('low-hp-no-mana');
  await navigate('nested');await shot('nested');
  await check('Nested gauges preserve selection and buff controls',`document.querySelectorAll('#bar .hp-meter').length===5 && document.querySelectorAll('#bar .sp-meter').length===4 && document.querySelectorAll('#bar .buff-button').length===3 && document.querySelectorAll('#bar .selection-diamond').length===1`);
  await navigate('vertical');await shot('vertical');
  await check('Vertical baseline remains available',`document.querySelectorAll('#bar .hp-meter rect').length===10`);
  await navigate('split');
  for(const count of [1,3,5]){
    await ev(`document.getElementById('party').value='${count}';document.getElementById('party').dispatchEvent(new Event('change'))`);
    await check(`${count}-member basebar remains centered and inside review stage`,`(()=>{const a=document.querySelector('#bar svg').getBoundingClientRect(),b=document.getElementById('stage').getBoundingClientRect();return document.querySelectorAll('#bar .pc').length===${count} && a.left>=b.left && a.right<=b.right && Math.abs((a.left+a.right)-(b.left+b.right))<2;})()`);
  }
  await send('Emulation.setDeviceMetricsOverride',{width:1280,height:1100,deviceScaleFactor:1,mobile:false});
  await ev(`document.getElementById('view').value='classic';document.getElementById('view').dispatchEvent(new Event('change'))`);
  await check('4:3 logical scale fits all five members',`(()=>{const r=document.querySelector('#bar svg').getBoundingClientRect();return Math.abs(r.width-980)<1 && document.documentElement.scrollWidth<=innerWidth;})()`);
  await shot('split-4by3');
  await send('Emulation.setDeviceMetricsOverride',{width:600,height:1000,deviceScaleFactor:1,mobile:false});
  await check('Narrow browser page has no horizontal overflow',`document.documentElement.scrollWidth<=innerWidth`);
  assert.equal(errors.length,0,JSON.stringify(errors));
  await writeFile(resolve(here,'checks.json'),JSON.stringify({date:'2026-09-29',checks,errors},null,2)+'\n');
  console.log(`${checks.length} browser checks passed`);
}finally{ws?.close();browser.kill('SIGTERM');}
