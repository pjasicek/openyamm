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
  const output = 'level_generation/ui/hud_inventory/paperdoll_review/jewelry_repairs_20260926';
  const saved = () => evaluate(`({decisions:JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1')),
    placements:JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'))})`);
  const row = slot => evaluate(`(()=>{const e=document.querySelector('.equipment-row[data-slot="${slot}"]');
    return {...e.dataset,status:e.querySelector('.decision-status')?.textContent};})()`);
  const captured = await evaluate(`(async()=>{
    const raw=await(await fetch('jewelry_repairs_20260926/browser_state.original.json')).json();
    return {raw,decisions:JSON.parse(raw.storage['openyamm-paperdoll-context-review-v1']),
      placements:JSON.parse(raw.storage['openyamm-paperdoll-placement-v1'])};})()`);
  const baseline=await saved();
  check(JSON.stringify(baseline.decisions)===JSON.stringify(captured.decisions),'all 1260 latest decisions preserved');
  check(JSON.stringify(baseline.placements)===JSON.stringify(captured.placements),'all 728 latest offsets preserved');
  const progress=await evaluate(`document.querySelector('#jewelryProgress').textContent`);
  check(progress.includes('61 accepted') && progress.includes('0 flagged') && progress.includes('2 unreviewed'),progress);
  await change('#targetScope','all');
  await change('#hideAccepted',true);
  for(const scope of ['latest','jewelry','main','held']) {
    await change('#decisionFilter',scope);
    const count=scope==='latest'||scope==='jewelry'?2:0;
    check(await evaluate(`document.querySelector('#queueCount').textContent===${JSON.stringify(count+' matching targets')}`),
      scope+' remaining count');
  }
  await change('#decisionFilter','jewelry');
  const pendingNames=await evaluate(`Array.from(document.querySelectorAll('#targetList button'),e=>e.firstElementChild.textContent).sort()`);
  check(JSON.stringify(pendingNames)===JSON.stringify(['item150','ring1']),'only the two replacements await review');
  await change('#hideAccepted',false);
  const entries=[
    {id:150,slot:'Amulet',name:'item150',scale:32/34,repaired:true},
    {id:1722,slot:'Ring1',name:'ring1',scale:.8,repaired:true},
    {id:1714,slot:'Gauntlets',name:'gontlet3',scale:60/81,repaired:false},
    {id:1729,slot:'Ring1',name:'ring6',scale:.8,repaired:false},
    {id:1731,slot:'Ring1',name:'ring10',scale:32/42,repaired:false},
  ];
  const checked=[];
  for(const entry of entries) {
    await change(`select[data-slot="${entry.slot}"]`,entry.id);
    const current=await row(entry.slot);
    check(current.asset===entry.name,'correct item selected '+entry.name);
    check(Math.abs(Number(current.drawScale)-entry.scale)<1e-9,'uniform fit '+entry.name);
    check(Number(current.width)<=32 && Number(current.height)<=(entry.slot==='Ring1'?32:64),
      'jewelry fits slot '+entry.name);
    check(current.status.includes(entry.repaired?'needs re-review':'Staged accepted'),'review state '+entry.name+': '+current.status);
    check(current.artUrl.includes('jewelry_repairs_20260926/repaired')===entry.repaired,'expected artwork '+entry.name);
    const inventory=await evaluate(`(()=>{
      const c=document.querySelector('#inventoryPreview canvas');
      const ctx=c.getContext('2d');const pixels=ctx.getImageData(0,0,c.width,c.height).data;let outside=0;
      for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++) {
        if(x<12||y<12||x>=c.width-12||y>=c.height-12)outside+=pixels[(y*c.width+x)*4+3]>0;
      }
      return {...c.dataset,outside};})()`);
    check(Number(inventory.itemId)===entry.id && inventory.outside===0,'inventory fit '+entry.name);
    const original=await evaluate(`document.querySelector('[data-view="original"] canvas').toDataURL()`);
    await change('#keyboardMode',entry.slot);
    await evaluate(`document.activeElement?.blur()`);
    await key('ArrowRight');
    await key('ArrowUp');
    const moved=await row(entry.slot);
    check(Math.abs(Number(moved.x)-Number(current.x)-1)<1e-9 && Math.abs(Number(moved.y)-Number(current.y)+1)<1e-9,
      'one-pixel keyboard movement after resizing '+entry.name);
    check(await evaluate(`document.querySelector('[data-view="original"] canvas').toDataURL()` )===original,
      'original comparison remains unchanged '+entry.name);
    // Restore the captured review before testing the next item; never touches the user's browser profile.
    await evaluate(`localStorage.setItem('openyamm-paperdoll-context-review-v1',${JSON.stringify(JSON.stringify(baseline.decisions))});
      localStorage.setItem('openyamm-paperdoll-placement-v1',${JSON.stringify(JSON.stringify(baseline.placements))});`);
    await send('Page.reload',{ignoreCache:true});await delay(600);
    await change('#hideAccepted',false);
    await change(`select[data-slot="${entry.slot}"]`,entry.id);
    const canvases=await evaluate(`Array.from(document.querySelectorAll('#poseGrid canvas'),c=>c.toDataURL())`);
    for(let i=0;i<canvases.length;i++)await writeFile(output+'/'+entry.name+'-'+(i===0?'original':'current')+'.png',
      Buffer.from(canvases[i].split(',')[1],'base64'));
    checked.push({...entry,...current,inventory});
  }
  check(JSON.stringify(await saved())===JSON.stringify(baseline),'all feedback restored after isolated shortcut checks');
  for(const id of [2033,2048]) {
    await send('Page.navigate',{url:'http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?item='+id+'&hide_accepted=0'});
    await delay(700);
    const current=await row('Ring1');
    check(current.asset==='ring10' && Math.abs(Number(current.drawScale)-32/42)<1e-9,
      'artifact alias uses corrected shared Scarab Ring '+id);
    check(current.status.includes('Staged accepted'),'old alias flag cannot override latest shared approval');
  }
  await evaluate(`window.reviewBlob=null;URL.createObjectURL=blob=>{window.reviewBlob=blob;return 'blob:review-test';};
    HTMLAnchorElement.prototype.click=function(){};`);
  await click('#exportDecisions');
  const exported=await evaluate(`(async()=>JSON.parse(await window.reviewBlob.text()))()`);
  check(JSON.stringify(exported.placements)===JSON.stringify(baseline.placements),'export preserves all offsets');
  check(exported.inventory_fit_proposals.groups.length===63 && exported.inventory_fit_proposals.records.length===79,
    'export covers all distinct images and aliases');
  for(const entry of entries)check(exported.inventory_fit_proposals.records.find(r=>r.item_id===entry.id).overlay_scale===entry.scale,
    'export includes corrected overlay scale '+entry.name);
  // Simulate an existing browser receiving this pass: preserve newer notes and placement edits on import.
  const newer=structuredClone(captured.raw.storage);
  const newerDecisions=structuredClone(baseline.decisions),newerPlacements=structuredClone(baseline.placements);
  newerDecisions['engine--icons--item150.bmp'].note='newer review note must survive';
  newerDecisions['engine--icons--item150.bmp'].updated_at='2099-01-01T00:00:00.000Z';
  const offsetKey=Object.keys(newerPlacements).find(k=>newerPlacements[k].item_id===1714);
  check(!!offsetKey,'gauntlet manual offset saved');
  newerPlacements[offsetKey].delta=[-1,-7];newerPlacements[offsetKey].updated_at='2099-01-01T00:00:00.000Z';
  newer['openyamm-paperdoll-context-review-v1']=JSON.stringify(newerDecisions);
  newer['openyamm-paperdoll-placement-v1']=JSON.stringify(newerPlacements);
  await evaluate(`localStorage.clear();for(const [key,value] of Object.entries(${JSON.stringify(newer)}))localStorage.setItem(key,value);`);
  await send('Page.reload',{ignoreCache:true});await delay(700);
  const preserved=await saved();
  check(JSON.stringify(preserved.decisions)===JSON.stringify(newerDecisions),'newer decisions and notes survive pass import');
  check(JSON.stringify(preserved.placements)===JSON.stringify(newerPlacements),'newer manual offsets survive pass import');
  await evaluate(`localStorage.clear();for(const [key,value] of Object.entries(${JSON.stringify(captured.raw.storage)}))localStorage.setItem(key,value);`);
  await send('Page.navigate',{url:'http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?review=latest&hide_accepted=1&item=150'});
  await delay(800);
  const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
  await writeFile(output+'/browser.png',Buffer.from(shot.data,'base64'));
  const report={result:'PASS',preservedDecisions:1260,preservedPlacements:728,
    groups:{total:63,accepted:61,flagged:0,unreviewed:2},pendingNames,mainPending:0,heldPending:0,
    onePixelNudges:true,originalComparisonUnchanged:true,newerLocalEditsPreserved:true,
    sharedAliasesVerified:[2033,2048],inventoryOverflowPixels:0,checked};
  await writeFile(output+'/browser_checks.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({...report,checked:undefined}));
  ws.close();
} finally {browser.kill('SIGTERM');}
