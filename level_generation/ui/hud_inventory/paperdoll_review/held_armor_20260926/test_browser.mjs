import { spawn } from "node:child_process";
import { writeFile, mkdir } from "node:fs/promises";

const browser = spawn("google-chrome", [
  "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--remote-debugging-port=9246", "--remote-allow-origins=*",
  "--user-data-dir=/tmp/openyamm-acceptance-check-cdp-" + Date.now(), "--window-size=1900,1400",
  "http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=held&hide_accepted=1&art=candidate&pose=one",
], { stdio: "ignore" });

function delay(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

try {
  let page;
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const pages = await (await fetch("http://127.0.0.1:9246/json/list")).json();
      page = pages.find((entry) => entry.type === "page" && entry.url.includes("paperdoll_review"));
      if (page) break;
    } catch { /* Chrome is starting. */ }
    await delay(200);
  }
  if (!page) throw new Error("Chrome did not open the paperdoll page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });
  let nextId = 0;
  const pending = new Map();
  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (!message.id || !pending.has(message.id)) return;
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) reject(new Error(message.error.message));
    else resolve(message.result);
  });
  function send(method, params = {}) {
    const id = ++nextId;
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });
  }
  await send("Runtime.enable");
  await send("Page.enable");
  await send("Network.enable");
  await send("Network.setCacheDisabled", {cacheDisabled:true});
  await send("Page.reload", {ignoreCache:true});
  await delay(1500);
  const evaluate = async (expression) => {
    const value = await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    if(value.exceptionDetails) throw new Error(JSON.stringify(value.exceptionDetails));
    return value.result.value;
  };
  const change = async (selector,value) => {
    await evaluate(`(() => {const e=document.querySelector(${JSON.stringify(selector)});
      if(e.type==='checkbox')e.checked=${JSON.stringify(value)};else e.value=${JSON.stringify(String(value))};
      e.dispatchEvent(new Event(e.matches('input[type="search"], input[type="text"]') ? 'input' : 'change',{bubbles:true}));})()`);
    await delay(250);
  };


  const check = (value, message) => { if (!value) throw new Error(message); };
  const click = async (selector) => {
    await evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);
    await delay(350);
  };
  const rows = () => evaluate(`Object.fromEntries([...document.querySelectorAll('.equipment-row[data-asset]')].map(e=>[e.dataset.slot,{...e.dataset,status:e.querySelector('.decision-status').textContent}]))`);
  const screenshot = async (path) => { const result=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true}); await writeFile(path,Buffer.from(result.data,'base64')); };
  const output = 'level_generation/ui/hud_inventory/paperdoll_review/held_armor_20260926';
  const quick = process.argv.includes('--quick');
  await mkdir(output+'/equipped', {recursive:true});
  const info = await evaluate(`(()=>{
    const d=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    const p=JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'));
    return {summary:document.querySelector('#repairPassSummary').textContent,
      pass:PAPERDOLL_REPAIR_PASS.id, decisions:Object.keys(d).length, placements:Object.keys(p).length,
      exactDecisions:JSON.stringify(d)===JSON.stringify(PAPERDOLL_REPAIR_PASS.decisions),
      exactPlacements:JSON.stringify(p)===JSON.stringify(PAPERDOLL_REPAIR_PASS.placements)};
  })()`);
  check(info.pass==='20260926_held_armor','held armor pass loaded');
  check(info.decisions===964 && info.placements===724 && info.exactDecisions && info.exactPlacements,
    'all approvals and offsets preserved');
  check(await evaluate(`PAPERDOLL_REPAIR_PASS.held_armor_scope.every(id=>
    PAPERDOLL_REPAIR_PASS.magenta_scan.records.some(r=>r.target===id &&
      r.candidate_hash===PAPERDOLL_REPAIR_PASS.repairs[id].sha256))`), 'all current candidate hashes have spill screening');
  check(await evaluate(`document.querySelector('#queueCount').textContent.startsWith('266 matching targets')`),
    '266 held candidates require separate image approval');
  await change('#decisionFilter','main');
  check(await evaluate(`document.querySelector('#queueCount').textContent==='0 matching targets'`),
    'main equipment remains fully accepted');
  await change('#decisionFilter','held');
  await change('#showBackground',false);
  const pairs = await evaluate(`(async()=> (await (await fetch('held_armor_20260926/manifest.json')).json()).pairs)()`);
  const select = async name => {
    await change('#targetSearch',name);
    await evaluate(`(()=>{const b=[...document.querySelectorAll('#targetList button')].find(b=>b.firstElementChild.textContent===${JSON.stringify(name)});
      if(!b)throw Error('Missing target '+${JSON.stringify(name)});b.click();})()`);
    for(let n=0;n<40;n++) {
      if(await evaluate(`document.querySelector('.equipment-row[data-slot="Armor"]')?.dataset.asset===${JSON.stringify(name)}`))return;
      await delay(100);
    }
    throw new Error('Armor did not render: '+name);
  };
  const capture = async name => {
    const uri = await evaluate(`document.querySelector('#poseGrid [data-view="restored"] canvas').toDataURL('image/png')`);
    await writeFile(output+'/equipped/'+name+'.png',Buffer.from(uri.split(',')[1],'base64'));
  };
  const checks=[];
  for(const pair of pairs.filter(p=>!p.native_pair_identical && (!quick || /^7item078v[1-5]$/.test(p.held)))) {
    await select(pair.held);
    const row=(await rows()).Armor;
    check(row.artUrl.split('?')[0]===pair.path, 'derived image selected: '+pair.held);
    check(!await evaluate(`document.querySelector('#missingAssets').textContent`), 'no missing layers: '+pair.held);
    check(!await evaluate(`[...document.querySelectorAll('.equipment-row .warning')].some(e=>e.textContent.includes('stale'))`),
      'manual offsets remain active: '+pair.held);
    await capture(pair.held);
    checks.push({name:pair.held,type:pair.doll_type,x:Number(row.x),y:Number(row.y),art:row.artUrl});
    if(checks.length%20===0)console.log('Equipped arm checks: '+checks.length+'/82');
  }
  const poses=[];
  for(const pair of pairs.filter(p=>/^7item078v[1-5]$/.test(p.held))) {
    await select(pair.held);
    const held=(await rows()).Armor;
    await change('#poseSelect','empty');
    const empty=(await rows()).Armor;
    check(empty.asset===pair.empty && empty.status.startsWith('Staged accepted'), 'accepted empty base still selected');
    check(held.x===empty.x && held.y===empty.y,'both poses retain identical placement');
    await capture(pair.empty);
    await change('#poseSelect','two');
    const two=(await rows()).Armor;
    check(two.asset===pair.held && two.x===held.x && two.y===held.y,'two-hand pose uses same armor and offsets');
    await capture(pair.held+'-two');
    poses.push({type:pair.doll_type,empty:empty.asset,held:held.asset,two:two.asset,xy:[held.x,held.y]});
  }
  await select('7item078v1');
  await change('#targetSearch','');
  await screenshot(output+'/browser.png');
  // Only this throwaway profile receives these writes; verify that newer user edits
  // would survive the pass import, including a held-target alternative selection.
  const preserved = await evaluate(`(()=>{
    const d=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    const p=JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'));
    return JSON.stringify(d)===JSON.stringify(PAPERDOLL_REPAIR_PASS.decisions) &&
      JSON.stringify(p)===JSON.stringify(PAPERDOLL_REPAIR_PASS.placements);
  })()`);
  check(preserved,'browsing and pose changes do not edit decisions or placements');
  await evaluate(`(()=>{
    const d=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    d['engine--icons--item001.bmp']={...d['engine--icons--item001.bmp'],note:'Newer local note',updated_at:'2099-01-01T00:00:00.000Z'};
    localStorage.setItem('openyamm-paperdoll-context-review-v1',JSON.stringify(d));
    localStorage.removeItem('openyamm-paperdoll-stage-import-20260926_held_armor-v1');
  })()`);
  await send('Page.reload',{ignoreCache:true});await delay(900);
  check(await evaluate(`JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'))['engine--icons--item001.bmp'].note==='Newer local note'`),
    'newer local note retained across import');
  const report={result:'PASS',info,queue:266,checked_held:checks,pose_checks:poses,
    newer_note_preserved:true,isolated_profile:true,user_browser_modified:false};
  await writeFile(output+(quick?'/browser_refresh_validation.json':'/browser_validation.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({result:report.result,info,held:checks.length,poseTypes:poses.length}));
  ws.close();
} finally {
  browser.kill('SIGTERM');
}
