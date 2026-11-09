import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";

const browser = spawn("google-chrome", [
  "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--remote-debugging-port=9243", "--remote-allow-origins=*",
  "--user-data-dir=/tmp/openyamm-repair-review-cdp-" + Date.now(), "--window-size=1900,1400",
  "http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?doll=1&art=candidate&pose=one",
], { stdio: "ignore" });

function delay(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

try {
  let page;
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const pages = await (await fetch("http://127.0.0.1:9243/json/list")).json();
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
  const info = await evaluate(`({ summary:document.querySelector('#repairPassSummary').textContent,
    decisions:Object.keys(JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'))).length,
    placements:Object.keys(JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'))).length,
    repairs:Object.keys(PAPERDOLL_REPAIR_PASS.repairs).length, canvases:document.querySelectorAll('#poseGrid canvas').length })`);
  check(info.decisions===849,'all exported decisions imported');
  check(info.placements===683,'original and inherited placements imported');
  check(info.canvases===2,'two comparison canvases');
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"] .placement-readout').textContent.includes('Shift -1, +3')`),'original nonzero item001 offset applies to new repaired art');
  await screenshot('/tmp/paperdoll-chipped-equipped.png');
  await change('select[data-slot="oneHand"]','152');
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"] .placement-readout').textContent.includes('Shift +1, +0')`),'inherited shared-sprite wand offset applies');
  await change('#artMode','native');
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"]').dataset.artUrl.startsWith('native/')`),'native comparison remains available');
  await change('#artMode','candidate');

  await change('#targetScope','all'); await change('#decisionFilter','repairs');
  check(await evaluate(`document.querySelectorAll('#targetList button').length>0`),'repair queue populated');
  await change('#targetSearch','7item235v2a');
  await click('#targetList button'); await delay(600);
  check(await evaluate(`document.querySelector('#selectedInspector').textContent.includes('Repaired candidate')`),'repair selected');
  check(await evaluate(`document.querySelector('#candidateAttempt').value.startsWith('repair:')`),'repair attempt default');
  await screenshot('/tmp/paperdoll-gold-equipped.png');
  const preservation = await evaluate(`(() => {
    const d=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    const p=JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'));
    return { decisions:Object.entries(PAPERDOLL_REPAIR_PASS.decisions).every(([k,v])=>JSON.stringify(d[k])===JSON.stringify(v)),
      placements:Object.entries(PAPERDOLL_REPAIR_PASS.placements).every(([k,v])=>JSON.stringify(p[k])===JSON.stringify(v)),
      offset:document.querySelector('.equipment-row[data-slot="Armor"] .placement-readout').textContent,
      note:document.querySelector('.equipment-row[data-slot="Armor"] textarea')?.value };
  })()`);
  check(preservation.decisions && preservation.placements,'baseline decisions, notes, and placements preserved exactly');
  console.log(JSON.stringify({preservation}));

  const before=await rows();
  const armor=before.Armor;check(armor.artUrl.includes('review_pass_20260926/repaired'),'repaired artwork on doll');
  await click('.equipment-row[data-slot="Armor"] [data-move="1,0"]');
  check(Number((await rows()).Armor.x)===Number(armor.x)+1,'retained offset nudges by one');
  await click('.equipment-row[data-slot="Armor"] [data-decision="approve"]');
  await send('Page.reload',{ignoreCache:true});await delay(1000);
  const kept=await evaluate(`JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'))['engine--icons--7item235v2a.bmp']`);
  check(kept.decision==='approve' && kept.attempt.startsWith('repair:'),'repair approval survives reload');
  await change('#targetScope','all'); await change('#targetSearch','7item235v2a');await click('#targetList button');await delay(400);
  check(await evaluate(`document.querySelector('#candidateAttempt').value.startsWith('repair:')`),'repair remains selected on reload');
  await click('#clearSelected');await send('Page.reload',{ignoreCache:true});await delay(800);
  check(await evaluate(`!JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'))['engine--icons--7item235v2a.bmp']`),'clear is not undone by handoff import');
  await evaluate(`(() => {
    const k='openyamm-paperdoll-context-review-v1';const d=JSON.parse(localStorage.getItem(k));
    d['engine--icons--item001.bmp'].note='Isolated newer local note';
    localStorage.setItem(k,JSON.stringify(d));
    const pk='openyamm-paperdoll-placement-v1';const p=JSON.parse(localStorage.getItem(pk));
    p['fit:1:0:MainHand'].delta=[7,9];localStorage.setItem(pk,JSON.stringify(p));
    localStorage.removeItem('openyamm-paperdoll-stage-import-20260926');
  })()`);
  await send('Page.reload',{ignoreCache:true});await delay(1000);
  check(await evaluate(`JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'))['engine--icons--item001.bmp'].note==='Isolated newer local note'`),'existing local note wins during one-time merge');
  check(await evaluate(`JSON.stringify(JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'))['fit:1:0:MainHand'].delta)==='[7,9]'`),'existing local placement wins during one-time merge');
  console.log(JSON.stringify({ ...info, result:'PASS' , screenshot:'/tmp/paperdoll-gold-equipped.png' }));
  ws.close();

} finally { browser.kill('SIGTERM'); }
