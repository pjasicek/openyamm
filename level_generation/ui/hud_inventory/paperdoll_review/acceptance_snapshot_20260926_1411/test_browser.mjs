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
  const output = 'level_generation/ui/hud_inventory/paperdoll_review/acceptance_snapshot_20260926_1411';
  const info = await evaluate(`(()=>{
    const d=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    const p=JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'));
    return {summary:document.querySelector('#repairPassSummary').textContent,
      pass:PAPERDOLL_REPAIR_PASS.id, decisions:Object.keys(d).length, placements:Object.keys(p).length,
      exactDecisions:JSON.stringify(d)===JSON.stringify(PAPERDOLL_REPAIR_PASS.decisions),
      exactPlacements:JSON.stringify(p)===JSON.stringify(PAPERDOLL_REPAIR_PASS.placements)};
  })()`);
  check(info.pass==='20260926_acceptance_1411','new snapshot loaded');
  check(info.decisions===1225 && info.placements===726 && info.exactDecisions && info.exactPlacements,
    'all approvals and exact saved offsets imported');
  for(const filter of ['held','main','latest']) {
    await change('#decisionFilter',filter);
    check(await evaluate(`document.querySelector('#queueCount').textContent==='0 matching targets'`),
      'accepted queue empty: '+filter);
  }
  await change('#hideAccepted',false);
  await change('#decisionFilter','all');
  await change('#targetScope','all');
  await change('#showBackground',false);
  const updates = await evaluate(`(async()=> (await (await fetch('acceptance_snapshot_20260926_1411/offset_sync.json')).json()).updates)()`);
  const poses=[];
  for(const update of updates) {
    const heldName=update.held_target.replace('engine--icons--','').replace('.bmp','');
    await change('#targetSearch',heldName);
    await evaluate(`(()=>{
      const b=[...document.querySelectorAll('#targetList button')].find(b=>b.firstElementChild.textContent===${JSON.stringify(heldName)});
      if(!b)throw Error('Target missing');b.click();
    })()`);
    await delay(300);
    const held=(await rows()).Armor;
    check(held.asset===heldName && held.status.startsWith('Staged accepted'),'held image approval active: '+heldName);
    check(await evaluate(`document.querySelector('#selectedInspector').textContent.includes('Staged accepted') &&
      !document.querySelector('#selectedInspector').textContent.includes('visual review pending')`),
      'inspector acknowledges staged approval: '+heldName);
    check(await evaluate(`document.querySelector('#poseGrid [data-view="restored"] .pose-summary').textContent.includes('0 pending 2×')`),
      'stage does not mislabel approved artwork as pending');
    check(Number(held.x)===update.proposed[0] && Number(held.y)===update.proposed[1],
      'requested coordinates applied: '+heldName);
    await change('#poseSelect','empty');
    const empty=(await rows()).Armor;
    check(empty.asset===heldName+'a' && empty.status.startsWith('Staged accepted'),
      'empty-hand approval remains active: '+heldName);
    check(held.x===empty.x && held.y===empty.y,'same adjusted position in both poses: '+heldName);
    await change('#poseSelect','two');
    const two=(await rows()).Armor;
    check(two.asset===heldName && two.x===held.x && two.y===held.y && two.status.startsWith('Staged accepted'),
      'two-hand pose also retains offset and approval: '+heldName);
    check(!await evaluate(`[...document.querySelectorAll('.equipment-row .warning')].some(e=>e.textContent.includes('stale'))`),
      'offset source remains valid: '+heldName);
    poses.push({held:held.asset,empty:empty.asset,type:update.doll_type,xy:[Number(held.x),Number(held.y)]});
  }
  await change('#targetSearch','');
  await change('#hideAccepted',true);
  await change('#decisionFilter','held');
  await screenshot(output+'/browser.png');
  // Recreate an existing profile from the raw capture. A newer unrelated note and
  // offset must survive the one-time import; the 12 requested pairs must update.
  await evaluate(`(async()=>{
    const raw=await (await fetch('acceptance_snapshot_20260926_1411/browser_state.original.json')).json();
    const d=JSON.parse(raw.storage['openyamm-paperdoll-context-review-v1']);
    const p=JSON.parse(raw.storage['openyamm-paperdoll-placement-v1']);
    const key=Object.keys(p).find(k=>k.startsWith('fit:'));
    p[key]={...p[key],delta:[13,17],proposed:p[key].base.map((n,i)=>n+[13,17][i]),updated_at:'2099-01-01T00:00:00.000Z'};
    d['engine--icons--item001.bmp']={...d['engine--icons--item001.bmp'],note:'Newer isolated note',updated_at:'2099-01-01T00:00:00.000Z'};
    localStorage.setItem('openyamm-paperdoll-context-review-v1',JSON.stringify(d));
    localStorage.setItem('openyamm-paperdoll-placement-v1',JSON.stringify(p));
    localStorage.setItem('openyamm-paperdoll-context-review-attempt-v1',raw.storage['openyamm-paperdoll-context-review-attempt-v1']);
    localStorage.setItem('openyamm-paperdoll-repair-selection-20260926',raw.storage['openyamm-paperdoll-repair-selection-20260926']);
    localStorage.setItem('test-newer-placement-key',key);
    localStorage.removeItem('openyamm-paperdoll-stage-import-20260926_acceptance_1411-v1');
  })()`);
  await send('Page.reload',{ignoreCache:true});await delay(900);
  const upgrade=await evaluate(`(()=>{
    const d=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    const p=JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'));
    const key=localStorage.getItem('test-newer-placement-key');
    return {decisions:Object.entries(PAPERDOLL_REPAIR_PASS.decisions).every(([k,v])=>k==='engine--icons--item001.bmp'||JSON.stringify(d[k])===JSON.stringify(v)),
      placements:Object.entries(PAPERDOLL_REPAIR_PASS.placements).every(([k,v])=>k===key||JSON.stringify(p[k])===JSON.stringify(v)),
      newerNote:d['engine--icons--item001.bmp'].note==='Newer isolated note',
      newerOffset:JSON.stringify(p[key].delta)==='[13,17]'};
  })()`);
  check(Object.values(upgrade).every(Boolean),'upgrade preserves later edits and applies only authorized changes');
  const report={result:'PASS',info,pose_checks:poses,upgrade,isolated_profile:true,user_browser_modified:false};
  await writeFile(output+'/browser_validation.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({result:report.result,info,offsetPairs:poses.length,upgrade}));
  ws.close();
} finally {
  browser.kill('SIGTERM');
}
