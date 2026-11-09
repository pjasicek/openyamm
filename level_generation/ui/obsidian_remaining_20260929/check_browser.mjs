import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {readFile, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const here=dirname(fileURLToPath(import.meta.url));
const profile=`/tmp/obsidian-remaining-browser-${Date.now()}`;
const delay=ms=>new Promise(done=>setTimeout(done,ms));
const chrome=spawn('google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
  '--allow-file-access-from-files','--remote-debugging-port=0','--remote-allow-origins=*',
  `--user-data-dir=${profile}`,'about:blank'],{stdio:'ignore'});
let ws;
try {
  let port;
  for(let attempt=0;attempt<60&&!port;attempt++) {
    try {port=Number((await readFile(resolve(profile,'DevToolsActivePort'),'utf8')).split('\n')[0]);} catch {}
    if(!port)await delay(100);
  }
  assert.ok(port,'Headless Chrome started');
  const pages=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
  await new Promise((ok,no)=>{ws.onopen=ok;ws.onerror=no;});
  let serial=0;const pending=new Map(),errors=[];
  ws.onmessage=e=>{
    const m=JSON.parse(e.data),p=pending.get(m.id);
    if(p){pending.delete(m.id);m.error?p.no(m.error):p.ok(m.result);}
    if(m.method==='Runtime.exceptionThrown')errors.push(m.params);
  };
  const send=(method,params={})=>new Promise((ok,no)=>{const id=++serial;pending.set(id,{ok,no});ws.send(JSON.stringify({id,method,params}));});
  const evaluate=async expression=>{
    const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;
  };
  await send('Page.enable');await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1080,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:pathToFileURL(resolve(here,'index.html')).href});
  await delay(500);
  await evaluate('document.fonts.ready');
  const counts=await evaluate(`(async()=>{
    let views=0;
    for(const name of Object.keys(groups)){
      showGroup(name);
      if(name==='Icons')continue;
      for(const option of [...view.options]){
        view.value=option.value;showView();await screen.decode();
        if(!screen.naturalWidth)throw Error(option.value);views++;
      }
    }
    showGroup('Icons');
    for(const image of document.querySelectorAll('#icons img'))await image.decode();
    for(const s of [...state.options]){state.value=s.value;paint();await document.querySelector('.plate').decode();}
    showGroup('Android');await screen.decode();
    return {nativeViews:views,icons:document.querySelectorAll('#icons img').length,states:state.options.length};
  })()`);
  assert.equal(counts.icons,19);assert.equal(counts.states,4);assert.deepEqual(errors,[]);
  const shot=await send('Page.captureScreenshot',{format:'png'});
  await writeFile(resolve(here,'browser-review.png'),Buffer.from(shot.data,'base64'));
  await writeFile(resolve(here,'browser-check.json'),JSON.stringify({passed:true,...counts,errors},null,2)+'\n');
  console.log(counts);
} finally {
  ws?.close();chrome.kill('SIGTERM');
}
