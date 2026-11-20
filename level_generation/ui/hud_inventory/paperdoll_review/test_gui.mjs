import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";

const browser = spawn("google-chrome", [
  "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--remote-debugging-port=9238", "--remote-allow-origins=*",
  "--user-data-dir=/tmp/openyamm-equipment-review-cdp", "--window-size=1900,1400",
  "http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?doll=1&art=candidate&pose=one",
], { stdio: "ignore" });

function delay(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

try {
  let page;
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const pages = await (await fetch("http://127.0.0.1:9238/json/list")).json();
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
      e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    await delay(250);
  };


  const check = (value, message) => { if (!value) throw new Error(message); };
  const click = async (selector) => {
    await evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);
    await delay(350);
  };
  const rows = () => evaluate(`Object.fromEntries([...document.querySelectorAll('.equipment-row[data-asset]')].map(e=>[e.dataset.slot,{...e.dataset,status:e.querySelector('.decision-status').textContent}]))`);
  const screenshot = async (path) => { const result=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true}); await writeFile(path,Buffer.from(result.data,'base64')); };
  await evaluate(`localStorage.clear()`);
  await send('Page.reload',{ignoreCache:true}); await delay(1200);
  check(await evaluate(`document.querySelectorAll('#poseGrid canvas').length===2`),'two comparison canvases');
  check(await evaluate(`document.querySelectorAll('#typeShortcuts button').length===6`),'six body type shortcuts');
  const original = () => evaluate(`document.querySelector('[data-view="original"] canvas').toDataURL()`);
  await change('select[data-slot="Armor"]',84);
  let before=await rows();
  check(before.Armor.asset==='item084v1','male held armor');
  const nativeBefore=await original();
  await click('.equipment-row[data-slot="Armor"] [data-decision="approve"]');
  await click('.equipment-row[data-slot="Armor"] [data-move="1,0"]');
  let after=await rows();
  check(Number(after.Armor.x)===Number(before.Armor.x)+1,'armor moves one game pixel');
  check(after.Armor.status.includes('Changed since'),'changed placement invalidates decision');
  check(await original()===nativeBefore,'original canvas unaffected by movement');
  await click('.equipment-row[data-slot="Armor"] [data-decision="approve"]');
  await click('#typeShortcuts [data-type="1"]');
  after=await rows();
  check(after.Armor.asset==='item084v2' && after.Armor.status.includes('Awaiting'),'female approval independent');
  check(Number(after.Armor.x)===50,'female position unaffected');
  await click('#typeShortcuts [data-type="0"]');
  check((await rows()).Armor.status.includes('Accepted here'),'male decision preserved');
  await change('#poseSelect','empty');
  after=await rows();
  check(after.Armor.asset==='item084v1a' && after.Armor.status.includes('Awaiting'),'open armor variant approval independent');
  check(Number(after.Armor.x)===48,'both armor poses share per-type table coordinates');
  await change('#poseSelect','one');
  before=await rows();
  await click('.equipment-row[data-slot="MainHand"] [data-move="1,0"]');
  after=await rows();
  check(Number(after.MainHand.x)===Number(before.MainHand.x)+1,'weapon right nudge sign');
  await change('select[data-slot="OffHand"]',1);
  before=await rows();
  await click('.equipment-row[data-slot="OffHand"] [data-move="1,0"]');
  after=await rows();
  check(Number(after.OffHand.x)===Number(before.OffHand.x)+1,'rotated offhand right nudge');
  check(Number(after.MainHand.y)===Number(before.MainHand.y),'offhand adjustment does not move main hand');
  await click('.equipment-row[data-slot="MainHand"] [data-decision="approve"]');
  const maleMain = (await rows()).MainHand;
  await click('#typeShortcuts [data-type="1"]');
  check((await rows()).MainHand.status.includes('Accepted here'),'weapon approval shared across types');
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"] .placement-details summary').textContent.startsWith('Placement +0, +0')`),'female starts without male shift');
  await click('.equipment-row[data-slot="MainHand"] [data-move="0,1"]');
  await click('#typeShortcuts [data-type="0"]');
  check((await rows()).MainHand.x===maleMain.x && (await rows()).MainHand.y===maleMain.y,'female shift leaves male unchanged');
  await change('#dollSelect',3);
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"] .placement-details summary').textContent.startsWith('Placement +1, +0')`),'same body type shares adjustment');
  await click('#typeShortcuts [data-type="0"]');
  await change('select[data-slot="Bow"]',56);
  await click('.equipment-row[data-slot="Bow"] [data-move="0,-1"]');
  const saved=await evaluate(`({decisions:JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1')),placements:JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'))})`);
  check(saved.placements['fit:1:0:MainHand'].delta.join(',')==='1,0','male main hand fitting proposal');
  check(saved.placements['fit:1:0:OffHand'].delta.join(',')==='1,0','male off hand fitting proposal');
  check(saved.placements['fit:1:1:MainHand'].delta.join(',')==='0,1','female fitting proposal');
  check(saved.placements['fit:56:0:Bow'].table===null,'bow explicitly preview-only');
  await send('Page.reload',{ignoreCache:true}); await delay(1200);
  await change('select[data-slot="Armor"]',84);
  check((await rows()).Armor.status.includes('Accepted here'),'decisions persisted');
  check(Number((await rows()).Armor.x)===48,'movement persisted');
  // Capture the download content without touching the operator's filesystem.
  await evaluate(`window.reviewBlob=null;URL.createObjectURL=(blob)=>{window.reviewBlob=blob;return 'blob:review-test';};HTMLAnchorElement.prototype.click=function(){};`);
  await click('#exportDecisions');
  const exported=await evaluate(`(async () => JSON.parse(await window.reviewBlob.text()))()`);
  check(exported.placement_schema==='openyamm-paperdoll-placement-v1' && exported.placements['fit:1:0:MainHand'],'export includes table proposals');
  // Exercise the real file-input import and verify image/placement decisions survive it.
  await evaluate(`localStorage.clear()`); await send('Page.reload',{ignoreCache:true}); await delay(1000);
  await evaluate(`{const input=document.querySelector('#importDecisions');const transfer=new DataTransfer();transfer.items.add(new File([${JSON.stringify(JSON.stringify(exported))}], 'review.json',{type:'application/json'}));input.files=transfer.files;input.dispatchEvent(new Event('change'));}`);
  await delay(450);
  await change('select[data-slot="Armor"]',84);
  check(Number((await rows()).Armor.x)===48 && (await rows()).Armor.status.includes('Accepted here'),'export/import roundtrip');
  await change('select[data-slot="Bow"]',56);
  await change('select[data-slot="OffHand"]',99);
  await click('#typeShortcuts [data-type="0"]');
  await screenshot('/tmp/openyamm-equipment-review.png');
  await change('#artMode','native');
  check(await evaluate(`[...document.querySelectorAll('.equipment-row [data-decision="approve"]')].every(e=>e.disabled)`),'cannot accept unseen candidate in native mode');
  await change('#artMode','candidate');
  await click('#typeShortcuts [data-type="2"]');
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="Helm"]').textContent.includes('Unavailable')`),'minotaur restrictions');
  await click('#typeShortcuts [data-type="4"]');
  check(await evaluate(`document.querySelector('#dollMeta').textContent.includes('Type 4')`),'dwarf shortcut');
  await click('#typeShortcuts [data-type="5"]');
  check(Object.keys(await rows()).length===0,'dragon has no equipment');
  // Older global corrections are preserved but must not leak into the new fitting model.
  await evaluate(`{const key='openyamm-paperdoll-placement-v1';const records=JSON.parse(localStorage.getItem(key));records['grip:1']={key:'grip:1',table:'items.txt',item_id:1,base:[14,131],delta:[-20,0]};localStorage.setItem(key,JSON.stringify(records));}`);
  await send('Page.reload',{ignoreCache:true}); await delay(1200);
  check(await evaluate(`document.querySelector('#placementSummary').textContent.includes('old global proposals retained')`),'old global proposals explicitly inactive');
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"] .placement-details summary').textContent.startsWith('Placement +1, +0')`),'legacy global shift not applied');
  const priorDecisions = await evaluate(`localStorage.getItem('openyamm-paperdoll-context-review-v1')`);
  await change('#decisionFilter','magenta');
  check(await evaluate(`document.querySelector('#queueCount').textContent.startsWith('70 matching')`),'automatic spill queue');
  check(await evaluate(`[...document.querySelectorAll('.target-row')].every(row=>row.textContent.includes('MAGENTA'))`),'automatic flags visible');
  await change('#decisionFilter','clean');
  check(await evaluate(`document.querySelector('#queueCount').textContent.startsWith('1178 matching')`),'no-spill queue');
  await change('#decisionFilter','purple');
  check(await evaluate(`document.querySelector('#queueCount').textContent.startsWith('14 matching')`),'purple material separate');
  const spillBow = await evaluate(`window.PAPERDOLL_REVIEW_DATA.items.find(item=>item.icon==='item245').id`);
  await change('select[data-slot="Bow"]',spillBow);
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="Bow"] .magenta-warning').textContent.includes('AUTO FLAG')`),'visible equipment spill flag');
  check(await evaluate(`localStorage.getItem('openyamm-paperdoll-context-review-v1')`)===priorDecisions,'screening preserves manual decisions');
  const result={passed:true,automaticSpillScreen:true,typeSpecificPlacement:true,handSpecificPlacement:true,legacyGlobalInactive:true,comparison:true,variantIsolation:true,sharedWeaponAcceptance:true,placementSigns:true,
    originalUnchanged:true,persistence:true,exportImport:true,bodyTypes:6};
  console.log(JSON.stringify(result));
  await writeFile('/tmp/openyamm-equipment-review-checks.json',JSON.stringify(result,null,2));
  ws.close();
} finally { browser.kill('SIGTERM'); }
