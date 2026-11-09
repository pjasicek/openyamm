import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";

const browser = spawn("google-chrome", [
  "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--remote-debugging-port=9246", "--remote-allow-origins=*",
  "--user-data-dir=/tmp/openyamm-acceptance-check-cdp-" + Date.now(), "--window-size=1900,1400",
  "http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?doll=1&art=candidate&pose=one",
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
  const info = await evaluate(`(()=>{
    const d=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    const p=JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'));
    return {summary:document.querySelector('#repairPassSummary').textContent,
      pass:PAPERDOLL_REPAIR_PASS.id, decisions:Object.keys(d).length, placements:Object.keys(p).length,
      exactDecisions:JSON.stringify(d)===JSON.stringify(PAPERDOLL_REPAIR_PASS.decisions),
      exactPlacements:JSON.stringify(p)===JSON.stringify(PAPERDOLL_REPAIR_PASS.placements)};
  })()`);
  check(info.pass==='20260926_round3','latest acceptance snapshot loaded');
  check(info.decisions===964 && info.placements===724 && info.exactDecisions && info.exactPlacements,'all latest feedback preserved');
  check(info.summary.startsWith('961 approvals staged · 3 equipment images'),'live summary agrees with offline scope audit');
  await change('#targetScope','all');await change('#decisionFilter','main');await change('#hideAccepted',true);
  const remaining=await evaluate(`(async()=>{
    const audit=await (await fetch('review_pass_20260926_round3/completion_audit.json')).json();
    const names=[...document.querySelectorAll('#targetList button')].map(b=>b.firstElementChild.textContent).sort();
    return {count:document.querySelector('#queueCount').textContent,names,
      exact:JSON.stringify(names)===JSON.stringify(audit.remaining_main_equipment.map(r=>r.name).sort())};
  })()`);
  check(remaining.count==='3 matching targets' && remaining.exact,'remaining queue contains exactly the audited 3 targets');
  await screenshot('/tmp/paperdoll-round3.png');
  await change('#decisionFilter','latest');
  check(await evaluate(`document.querySelector('#queueCount').textContent==='3 matching targets'`),'latest batch alone has exactly three pending targets');
  await change('#decisionFilter','main');await change('#targetSearch','7item235v2a');await click('#targetList button');
  check(await evaluate(`document.querySelector('#selectedInspector').textContent.includes('7item235v2a')`),'repaired female armor pending and selectable');
  // Confirm upgrade from the prior snapshot retains a newer local note while importing all latest approvals.
  await evaluate(`(async()=>{
    const raw=await (await fetch('review_pass_20260926_round3/previous_review.js')).text();
    const old=JSON.parse(raw.slice(raw.indexOf('=')+1).trim().replace(/;$/,''));
    old.decisions['engine--icons--item001.bmp']={...PAPERDOLL_REPAIR_PASS.decisions['engine--icons--item001.bmp'],
      note:'Isolated newer local note',updated_at:'2099-01-01T00:00:00.000Z'};
    localStorage.setItem('openyamm-paperdoll-context-review-v1',JSON.stringify(old.decisions));
    localStorage.setItem('openyamm-paperdoll-placement-v1',JSON.stringify(old.placements));
    localStorage.removeItem('openyamm-paperdoll-stage-import-20260926_round3-v1');
  })()`);
  await send('Page.reload',{ignoreCache:true});await delay(900);
  const upgrade=await evaluate(`(()=>{
    const d=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    const p=JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'));
    return {decisions:Object.entries(PAPERDOLL_REPAIR_PASS.decisions).every(([k,v])=>k==='engine--icons--item001.bmp'||JSON.stringify(d[k])===JSON.stringify(v)),
      placements:Object.keys(p).length===Object.keys(PAPERDOLL_REPAIR_PASS.placements).length &&
      Object.entries(PAPERDOLL_REPAIR_PASS.placements).every(([k,v])=>JSON.stringify(p[k])===JSON.stringify(v)),
      newerNote:d['engine--icons--item001.bmp'].note==='Isolated newer local note'};
  })()`);
  check(upgrade.decisions && upgrade.placements && upgrade.newerNote,'upgrade preserves newer browser edits and incorporates exported approvals');
  const report={result:'PASS',info,remaining,upgrade,isolated_profile:true,user_browser_modified:false};
  await writeFile('/tmp/paperdoll-round3-validation.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({result:report.result,info,remaining:remaining.count,upgrade}));
  ws.close();
} finally {
  browser.kill('SIGTERM');
}
