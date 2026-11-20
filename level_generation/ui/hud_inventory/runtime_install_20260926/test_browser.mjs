import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";

const browser = spawn("google-chrome", [
  "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--remote-debugging-port=9247", "--remote-allow-origins=*",
  "--user-data-dir=/tmp/openyamm-jewelry-check-cdp-" + Date.now(), "--window-size=1900,1400",
  "http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?doll=1&art=candidate&item=150&hide_accepted=0",
], { stdio: "ignore" });

function delay(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

try {
  let page;
  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const pages = await (await fetch("http://127.0.0.1:9247/json/list")).json();
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



  const check=(value,message)=>{if(!value)throw new Error(message);};
  const click=async(selector)=>{await evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);await delay(250);};
  const key=async(k,shift=false)=>{
    const codes={ArrowUp:38,ArrowDown:40,ArrowLeft:37,ArrowRight:39,Tab:9,Escape:27,' ':32};
    const vk=k.startsWith('F') ? 111+Number(k.slice(1)) : codes[k];
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:k,code:k===' '?'Space':k,windowsVirtualKeyCode:vk,modifiers:shift?8:0});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:k,code:k===' '?'Space':k,windowsVirtualKeyCode:vk,modifiers:shift?8:0});
    await delay(180);
  };
  const output = 'level_generation/ui/hud_inventory/runtime_install_20260926';
  const captured=await evaluate(`(async()=>await(await fetch('../finalization_20260926/browser_state.original.json')).json())()`);
  await evaluate(`localStorage.clear();for(const [key,value] of Object.entries(${JSON.stringify(captured.storage)}))localStorage.setItem(key,value);`);
  await send('Page.reload',{ignoreCache:true});await delay(800);
  const saved=()=>evaluate(`({decisions:JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1')),
    placements:JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'))})`);
  const row=slot=>evaluate(`(()=>{const e=document.querySelector('.equipment-row[data-slot="${slot}"]');
    return {...e.dataset,status:e.querySelector('.decision-status')?.textContent};})()`);
  const baseline=await saved();
  const expected=await evaluate(`(async()=>await(await fetch('../finalization_20260926/decisions.json')).json())()`);
  check(JSON.stringify(baseline.decisions)===JSON.stringify(expected),'all recorded browser/chat approvals imported exactly');
  check(JSON.stringify(baseline.placements)===captured.storage['openyamm-paperdoll-placement-v1'],'all 728 offsets preserved exactly');
  const progress=await evaluate(`document.querySelector('#jewelryProgress').textContent`);
  check(progress.includes('63 accepted') && progress.includes('0 flagged') && progress.includes('0 unreviewed'),progress);
  check(await evaluate(`document.querySelector('#repairPassSummary').textContent.includes('9920 images accepted in icon ledger')`),'canonical acceptance shown');
  await change('#targetScope','all');await change('#hideAccepted',true);
  for(const scope of ['latest','jewelry','main','held']) {
    await change('#decisionFilter',scope);
    check(await evaluate(`document.querySelector('#queueCount').textContent==='0 matching targets'`),scope+' complete');
  }
  await change('#hideAccepted',false);
  await change('#artMode','accepted');
  const entries=[{id:150,slot:'Amulet',name:'item150'}, {id:1722,slot:'Ring1',name:'ring1'},
    {id:1714,slot:'Gauntlets',name:'gontlet3'}, {id:1729,slot:'Ring1',name:'ring6'},
    {id:1731,slot:'Ring1',name:'ring10'}];
  const displayed=[];
  for(const e of entries) {
    await change(`select[data-slot="${e.slot}"]`,e.id);
    const r=await row(e.slot);
    check(r.asset===e.name && r.artUrl.includes('runtime_install_20260926/stage/'),'accepted-only mode uses canonical export '+e.name);
    check(r.status.includes('Accepted in icon ledger'),r.status);
    check(Number(r.width)<=32 && Number(r.height)<=(e.slot==='Ring1'?32:64),'slot fitting preserved '+e.name);
    displayed.push(r);
  }
  check(JSON.stringify(await saved())===JSON.stringify(baseline),'navigation does not rewrite reviews or offsets');
  await evaluate(`window.reviewBlob=null;URL.createObjectURL=b=>{window.reviewBlob=b;return 'blob:check';};HTMLAnchorElement.prototype.click=function(){};`);
  await click('#exportDecisions');
  const exported=await evaluate(`(async()=>JSON.parse(await reviewBlob.text()))()`);
  check(JSON.stringify(exported.placements)===JSON.stringify(baseline.placements),'all placements in export');
  check(exported.inventory_fit_proposals.groups.every(g=>g.review_status==='canonical'),'63 groups canonical in export');
  const newer=structuredClone(baseline);
  const tid='engine--icons--ring1.bmp';newer.decisions[tid].note='newer note preserved';newer.decisions[tid].updated_at='2099-01-01T00:00:00.000Z';
  await evaluate(`localStorage.setItem('openyamm-paperdoll-context-review-v1',${JSON.stringify(JSON.stringify(newer.decisions))});
    localStorage.removeItem('openyamm-paperdoll-stage-import-20260926_runtime_icons-v1');`);
  await send('Page.reload',{ignoreCache:true});await delay(700);
  check(JSON.stringify((await saved()).decisions)===JSON.stringify(newer.decisions),'newer local note survives canonical import');
  await evaluate(`localStorage.setItem('openyamm-paperdoll-context-review-v1',${JSON.stringify(JSON.stringify(baseline.decisions))});`);
  await send('Page.reload',{ignoreCache:true});await delay(600);
  await change('#decisionFilter','jewelry');await change('#hideAccepted',true);
  const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
  await writeFile(output+'/browser.png',Buffer.from(shot.data,'base64'));
  const report={result:'PASS',canonicalImages:9920,decisions:1260,placements:728,jewelryGroupsAccepted:63,
    remainingMain:0,remainingHeld:0,remainingJewelry:0,remainingRepairs:0,acceptedOnlyUsesCanonical:true,
    exactSavedPlacementsPreserved:true,newerBrowserEditsPreserved:true,displayed};
  await writeFile(output+'/browser_checks.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({...report,displayed:undefined}));ws.close();
} finally {browser.kill('SIGTERM');}
