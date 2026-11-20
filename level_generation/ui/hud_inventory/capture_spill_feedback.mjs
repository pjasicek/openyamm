// Read only spill-review keys from a stable COPY of Chrome Local Storage.
// The live browser profile is never opened for writing or launched by this tool.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {mkdtemp, mkdir, readdir, readFile, writeFile, copyFile} from 'node:fs/promises';
import {homedir} from 'node:os';
import path from 'node:path';

const output = process.argv[2];
assert.ok(output, 'Supply an output JSON path');
const source = path.join(homedir(), '.config/google-chrome/Default/Local Storage/leveldb');
const profile = await mkdtemp('/tmp/openyamm-spill-feedback-');
const destination = path.join(profile, 'Default/Local Storage/leveldb');
await mkdir(destination, {recursive:true});
const signature = async directory => {
  const result = {};
  for (const name of (await readdir(directory)).sort()) {
    if (name === 'LOCK' || name.startsWith('LOG')) continue;
    result[name] = createHash('sha256').update(await readFile(path.join(directory,name))).digest('hex');
  }
  return result;
};
const before = await signature(source);
for (const name of Object.keys(before)) await copyFile(path.join(source,name),path.join(destination,name));
assert.deepEqual(await signature(source),before,'Local Storage changed while copying; retry capture');
assert.deepEqual(await signature(destination),before,'Local Storage snapshot mismatch');
const browser = spawn('google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
  '--disable-background-networking','--no-first-run','--remote-debugging-port=9287',
  '--remote-allow-origins=*','--user-data-dir='+profile,'http://127.0.0.1:8899/'],{stdio:'ignore'});
const delay = ms => new Promise(resolve=>setTimeout(resolve,ms));
let socket;
try {
  let page;
  for (let i=0;i<100;++i) {
    try {
      const pages = await (await fetch('http://127.0.0.1:9287/json/list')).json();
      page = pages.find(p=>p.type==='page' && p.url==='http://127.0.0.1:8899/');
      if(page) break;
    } catch { /* Wait for this isolated browser. */ }
    await delay(100);
  }
  assert.ok(page,'Isolated browser did not start');
  socket = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
  let serial=0;const requests=new Map();
  socket.addEventListener('message',event=>{
    const message=JSON.parse(event.data),request=requests.get(message.id);
    if(!request)return;requests.delete(message.id);
    if(message.error)request.reject(new Error(JSON.stringify(message.error)));else request.resolve(message.result);
  });
  const send=(method,params)=>new Promise((resolve,reject)=>{
    const id=++serial;requests.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));
  });
  const keys=['openyamm-icon-spill-repairs-v1','openyamm-icon-spill-repairs-v1-view',
    'openyamm-icon-spill-flags-v1','openyamm-icon-spill-view-v1'];
  let result;
  for (let i=0;i<100;++i) {
    result=await send('Runtime.evaluate',{returnByValue:true,
      expression:`Object.fromEntries(${JSON.stringify(keys)}.map(key=>[key,localStorage.getItem(key)]))`});
    if(!result.exceptionDetails)break;
    await delay(100);
  }
  assert.ok(!result.exceptionDetails,JSON.stringify(result.exceptionDetails));
  const storage=result.result.value;
  assert.ok(Object.values(storage).some(Boolean),'No saved spill feedback in this profile');
  await mkdir(path.dirname(output),{recursive:true});
  await writeFile(output,JSON.stringify({schema:'openyamm-spill-browser-capture-v1',captured_at:new Date().toISOString(),
    origin:'http://127.0.0.1:8899',method:'stable_local_storage_copy_isolated_browser',source_snapshot:before,storage},null,2)+'\n');
  console.log(JSON.stringify({output,keys:Object.fromEntries(Object.entries(storage).map(([key,value])=>[key,value?.length||0]))}));
} finally {socket?.close();browser.kill('SIGTERM');}
