import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";

const browser = spawn("google-chrome", [
  "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--remote-debugging-port=9245", "--remote-allow-origins=*",
  "--user-data-dir=/tmp/openyamm-round2-review-cdp-" + Date.now(), "--window-size=1900,1400",
  "http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?doll=1&art=candidate&pose=one",
], { stdio: "ignore" });

function delay(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

try {
  let page;
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const pages = await (await fetch("http://127.0.0.1:9245/json/list")).json();
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
  const info = await evaluate(`(() => {
    const d=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    const p=JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'));
    const choices=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-attempt-v1'));
    const changedApprovals=Object.values(PAPERDOLL_REVIEW_DATA.assets).filter(a=>{
      const decision=d[a.id];if(decision?.decision!=='approve')return false;
      const selected=a.preparedAlternatives.find(c=>c.attempt===choices[a.id]);
      return decision.candidate_hash!==(selected?.sha256 || a.candidateHash);
    }).map(a=>a.name);
    return { summary:document.querySelector('#repairPassSummary').textContent,
      decisions:Object.keys(d).length,placements:Object.keys(p).length,changedApprovals,
      exactDecisions:JSON.stringify(d)===JSON.stringify(PAPERDOLL_REPAIR_PASS.decisions),
      exactPlacements:JSON.stringify(p)===JSON.stringify(PAPERDOLL_REPAIR_PASS.placements),
      pass:PAPERDOLL_REPAIR_PASS.id,
      originalRendering:getComputedStyle(document.querySelector('[data-view="original"] canvas')).imageRendering,
      restoredRendering:getComputedStyle(document.querySelector('[data-view="restored"] canvas')).imageRendering };
  })()`);
  console.log(JSON.stringify({info}));
  check(info.pass==='20260926_round2','round 2 loaded');
  check(info.decisions===916 && info.placements===714,'all decisions and placements imported');
  check(info.exactDecisions && info.exactPlacements,'immutable feedback imported exactly');
  check(info.originalRendering==='pixelated' && info.restoredRendering==='auto','restored CSS resampling');
  check(await evaluate(`PAPERDOLL_REPAIR_PASS.magenta_scan.records.length===51 &&
    PAPERDOLL_REPAIR_PASS.magenta_scan.records.every(r=>r.status==='no_spill_detected')`),'new replacements have hash-bound magenta scan');
  check(await evaluate(`Object.values(PAPERDOLL_REVIEW_DATA.assets).every(a=>{
    const d=PAPERDOLL_REPAIR_PASS.decisions[a.id];
    if(d?.decision!=='approve'||!a.repair||d.updated_at<=a.repair.review_baseline_at)return true;
    const choices=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-attempt-v1'));
    return d.candidate_hash===(a.preparedAlternatives.find(c=>c.attempt===choices[a.id])?.sha256||a.candidateHash);
  })`),'approvals made after their repair pass keep their exact selected art');
  check(info.changedApprovals.length===38,'25 older approvals, 3 revised aliases and 10 crop repairs remain pending');
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"] .placement-readout').textContent.includes('Shift -1, +3')`),'two-round inherited item001 offset applies');
  await screenshot('/tmp/round2-sword-equipped.png');
  await change('#targetScope','all');
  await change('#decisionFilter','latest');
  check(await evaluate(`document.querySelector('#queueCount').textContent.startsWith('51 matching')`),'51 latest repairs');
  await change('#hideAccepted',true);
  check(await evaluate(`document.querySelector('#queueCount').textContent.startsWith('51 matching')`),'revised shared sprites remain reviewable');
  check(await evaluate(`JSON.stringify(PAPERDOLL_REPAIR_PASS.placements['fit:1753:0:MainHand'].delta)==='[1,-1]'`),
    'newer first-wand adjustment propagated to matching sprite');
  const selectTarget=async(name)=>{
    await change('#targetSearch',name);await click('#targetList button');await delay(300);
  };
  await selectTarget('7item074v1a');
  check(await evaluate(`document.querySelector('#candidateAttempt').value.startsWith('repair:')`),'new neckline selected');
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="Armor"] .placement-readout').textContent.includes('Shift -1, +0')`),'neckline offset retained');
  await screenshot('/tmp/round2-neckline-equipped.png');
  await selectTarget('item110v1');await screenshot('/tmp/round2-helmet-equipped.png');
  await selectTarget('sshield1');await screenshot('/tmp/round2-shield-equipped.png');
  await selectTarget('bow3');await screenshot('/tmp/round2-bowstring-equipped.png');
  await selectTarget('item001');
  const before=(await rows()).MainHand;
  await click('.equipment-row[data-slot="MainHand"] [data-move="1,0"]');
  check(Number((await rows()).MainHand.x)===Number(before.x)+1,'nudge continues from preserved offset');
  await click('.equipment-row[data-slot="MainHand"] [data-decision="approve"]');
  await send('Page.reload',{ignoreCache:true});await delay(1000);
  check(await evaluate(`JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'))['engine--icons--item001.bmp'].decision==='approve'`),'new approval persists');
  await change('#targetScope','all');await change('#decisionFilter','latest');await change('#targetSearch','item001');
  check(await evaluate(`document.querySelector('#queueCount').textContent.startsWith('0 matching')`),'accepted repair hidden');
  // Recreate an old browser profile: earlier import marker, old choices, and one newer local edit.
  await evaluate(`(async()=>{
    const previous=await (await fetch('review_pass_20260926_round2/previous_review.js')).text();
    const old=JSON.parse(previous.slice(previous.indexOf('=')+1).trim().replace(/;$/,''));
    const d=old.decisions,p=old.placements;
    d['engine--icons--item001.bmp']={...PAPERDOLL_REPAIR_PASS.decisions['engine--icons--item001.bmp'],
      note:'Isolated newer local note',updated_at:'2099-01-01T00:00:00.000Z'};
    p['fit:1:0:MainHand']={...PAPERDOLL_REPAIR_PASS.placements['fit:1:0:MainHand'],
      delta:[7,9],updated_at:'2099-01-01T00:00:00.000Z'};
    localStorage.setItem('openyamm-paperdoll-context-review-v1',JSON.stringify(d));
    localStorage.setItem('openyamm-paperdoll-placement-v1',JSON.stringify(p));
    localStorage.setItem('openyamm-paperdoll-context-review-attempt-v1',JSON.stringify(Object.fromEntries(
      Object.entries(old.repairs).map(([id,r])=>[id,'repair:'+r.sha256.slice(0,12)]))));
    localStorage.setItem('openyamm-paperdoll-repair-selection-20260926',JSON.stringify(Object.fromEntries(
      Object.entries(old.repairs).map(([id,r])=>[id,r.sha256]))));
    localStorage.setItem('openyamm-paperdoll-stage-import-20260926','complete');
    localStorage.removeItem('openyamm-paperdoll-stage-import-20260926_round2-v2');
  })()`);
  await send('Page.reload',{ignoreCache:true});await delay(1200);
  const upgrade=await evaluate(`(()=>{
    const d=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    const p=JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'));
    return {decisions:Object.entries(PAPERDOLL_REPAIR_PASS.decisions).every(([k,v])=>k==='engine--icons--item001.bmp'||JSON.stringify(d[k])===JSON.stringify(v)),
      placements:Object.entries(PAPERDOLL_REPAIR_PASS.placements).every(([k,v])=>k==='fit:1:0:MainHand'||JSON.stringify(p[k])===JSON.stringify(v)),
      note:d['engine--icons--item001.bmp'].note,delta:p['fit:1:0:MainHand'].delta,
      backup:!!localStorage.getItem('openyamm-paperdoll-stage-import-20260926_round2-v2-backup')};
  })()`);
  console.log(JSON.stringify({upgrade}));
  check(upgrade.decisions && upgrade.placements,'new export upgrades old browser records');
  check(upgrade.note==='Isolated newer local note' && String(upgrade.delta)==='7,9' && upgrade.backup,'newer browser edits and backup retained');
  await change('#hideAccepted',false);await change('#targetScope','all');await change('#decisionFilter','all');
  await selectTarget('sshield1');await click('#clearSelected');
  await send('Page.reload',{ignoreCache:true});await delay(800);
  check(await evaluate(`!JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'))['engine--icons--sshield1.bmp']`),'clear is not undone by round import');
  const report={info,upgrade,checks:'PASS: fresh import, offsets, candidate selection, filtering, new approvals, old-profile upgrade, clear persistence'};
  await writeFile('/tmp/round2-browser-validation.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({checks:report.checks}));
  ws.close();
} finally {
  browser.kill('SIGTERM');
}
