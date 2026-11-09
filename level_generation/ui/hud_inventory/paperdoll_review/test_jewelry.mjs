import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";

const browser = spawn("google-chrome", [
  "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--remote-debugging-port=9247", "--remote-allow-origins=*",
  "--user-data-dir=/tmp/openyamm-jewelry-check-cdp-" + Date.now(), "--window-size=1900,1400",
  "http://127.0.0.1:8899/level_generation/ui/hud_inventory/paperdoll_review/index.html?doll=1&art=candidate&item=517&hide_accepted=0",
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
  const output = 'level_generation/ui/hud_inventory/paperdoll_review/jewelry_inventory_20260926';
  const saved = () => evaluate(`({decisions:JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1')),
    placements:JSON.parse(localStorage.getItem('openyamm-paperdoll-placement-v1'))})`);
  const row = (slot) => evaluate(`(()=>{const e=document.querySelector('.equipment-row[data-slot="${slot}"]');
    return {...e.dataset,status:e.querySelector('.decision-status')?.textContent};})()`);
  const baseline = await saved();
  check(Object.keys(baseline.decisions).length === 1225 && Object.keys(baseline.placements).length === 726,
    'all staged approvals and saved offsets loaded');
  check(await evaluate(`document.querySelector('#repairPassSummary').textContent.includes('0 equipment images still')`),
    'accepted main equipment remains complete');
  const modes = ['Gauntlets','Amulet','Ring1','Ring2','Ring3','Ring4','Ring5','Ring6'];
  check(await evaluate(`document.querySelector('#showJewelry').checked && document.querySelector('#keyboardMode').value==='Gauntlets'`),
    'direct item link opens the jewelry overlay and Gloves selection mode');
  check((await row('Gauntlets')).asset==='item261' && (await row('Gauntlets')).artUrl.includes('jewelry_prepared'),
    'reported Fleetfingers glove uses retained 2x artwork');
  await click('button[title="Next Gauntlets"]');
  check(await evaluate(`document.querySelector('#showJewelry').checked`),'next glove button keeps overlay');
  await click('button[title="Previous Gauntlets"]');
  check(await evaluate(`document.querySelector('#showJewelry').checked`),'previous glove button keeps overlay');
  const icons = await evaluate(`Array.from(new Map(PAPERDOLL_REVIEW_DATA.items.filter(i=>
    ['Gauntlets','Amulet','Ring'].includes(i.stat) && PAPERDOLL_INVENTORY_FIT.records.some(r=>
      r.item_id===i.id && r.representative_item_id===i.id)).map(i=>[i.icon,i])).values())`);
  const drawn = [];
  for (const definition of icons) {
    const slot = definition.stat==='Ring' ? 'Ring1' : definition.stat;
    await change(`select[data-slot="${slot}"]`,definition.id);
    const r = await row(slot);
    check(r.asset===definition.icon && !r.artUrl.startsWith('native/'), 'restored item displayed: '+definition.icon);
    const dimensions = await evaluate(`(async()=>{
      const entry=PAPERDOLL_REVIEW_DATA.assets[${JSON.stringify(r.asset)}];
      const image=new Image();image.src=${JSON.stringify(r.artUrl)};await image.decode();
      return {actual:[image.naturalWidth,image.naturalHeight],expected:entry.size.map(v=>v*2)};
    })()`);
    check(JSON.stringify(dimensions.actual)===JSON.stringify(dimensions.expected),'actual image is 2x: '+definition.icon);
    const fit = await evaluate(`(()=>{
      const canvas=document.querySelector('#inventoryPreview canvas');
      const context=canvas.getContext('2d');const pixels=context.getImageData(0,0,canvas.width,canvas.height).data;
      let outside=0;
      for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++) {
        if(x<12 || y<12 || x>=canvas.width-12 || y>=canvas.height-12)outside+=pixels[(y*canvas.width+x)*4+3]>0;
      }
      return {...canvas.dataset,outside,size:[canvas.width-24,canvas.height-24]};
    })()`);
    check(Number(fit.itemId)===definition.id,'inventory preview follows selected item');
    check(fit.cells===(slot==='Gauntlets'?'1x2':slot==='Ring1'?'1x1':fit.cells) &&
      ['1x1','1x2'].includes(fit.cells),'requested inventory footprint: '+definition.icon);
    const drawSize=JSON.parse(fit.drawSize);
    check(drawSize.every((v,i)=>v<=fit.size[i]+1e-9) && fit.outside===0,
      'full image fits actual inventory grid without overflow: '+definition.icon);
    drawn.push({name:r.asset,slot,path:r.artUrl,size:dimensions.actual,cells:fit.cells,drawSize});
  }
  check(JSON.stringify(await saved())===JSON.stringify(baseline),'navigation preserves every prior approval and offset');
  await change('#hideAccepted',true);
  for(const slot of modes) {
    await change('#keyboardMode',slot);
    await key(' ');
    const before=await row(slot);
    check(before.asset && !before.status.includes('native shown'),'Space selects restored item in '+slot);
    check(await evaluate(`document.querySelector('#showJewelry').checked`),'Space keeps overlay in '+slot);
    const selection=await evaluate(`document.querySelector('select[data-slot="${slot}"]').value`);
    const original=await evaluate(`document.querySelector('[data-view="original"] canvas').toDataURL()`);
    await key('ArrowRight');
    await key('ArrowUp');
    const moved=await row(slot);
    check(Number(moved.x)===Number(before.x)+1 && Number(moved.y)===Number(before.y)-1,
      'arrows adjust active jewelry slot by one native pixel: '+slot);
    check(await evaluate(`document.querySelector('[data-view="original"] canvas').toDataURL()` )===original,
      'native comparison unchanged');
    await key(' ',true);
    check((await row(slot)).status.includes('Accepted here'),'Shift+Space accepts current '+slot);
    check(await evaluate(`document.querySelector('select[data-slot="${slot}"]').value`)===selection,
      'accept does not advance '+slot);
    await key(' ');
    check((await row(slot)).asset!==before.asset,'Space skips the just-accepted image in '+slot);
    check(await evaluate(`document.querySelector('#showJewelry').checked`),'accept/next keeps overlay '+slot);
  }
  // Two slots can display the same ring. Clicking Ring2 must keep controls bound to Ring2.
  await change('#hideAccepted',false);
  const ring=icons.find(i=>i.stat==='Ring');
  await change('select[data-slot="Ring1"]',ring.id);
  await change('select[data-slot="Ring2"]',ring.id);
  await click('.equipment-row[data-slot="Ring2"] .asset-name');
  check(await evaluate(`document.querySelector('#keyboardMode').value==='Ring2'`),'duplicate ring selects intended slot');
  const ringOne=await row('Ring1');
  const ringTwo=await row('Ring2');
  await key('ArrowRight');
  check((await row('Ring1')).x===ringOne.x && Number((await row('Ring2')).x)===Number(ringTwo.x)+1,
    'duplicate ring nudge remains slot-specific');
  // Notes keep normal editing behavior; Escape resumes shortcuts.
  await change('#keyboardMode','Gauntlets');
  await click('.equipment-row[data-slot="Gauntlets"] [data-decision="flag"]');
  const gloveBefore=await row('Gauntlets');
  await key('ArrowRight');
  check((await row('Gauntlets')).x===gloveBefore.x,'notes retain arrow editing');
  await key('Escape');
  await key('ArrowRight');
  check(Number((await row('Gauntlets')).x)===Number(gloveBefore.x)+1,'Escape resumes jewelry shortcuts');
  await key('Tab');
  check(await evaluate(`document.querySelector('#showJewelry').checked && document.querySelector('#keyboardMode').value==='Gauntlets'`),
    'body type switch preserves overlay and current slot');
  for (const [mode,slot] of [['F1','oneHand'],['F2','twoHand'],['F3','OffHand'],['F4','Bow'],
    ['F5','Cloak'],['F6','Armor'],['F7','Helm'],['F8','Boots'],['F9','Belt']]) {
    await key(mode);
    check(await evaluate(`!document.querySelector('#showJewelry').checked && document.querySelector('#keyboardMode').value===${JSON.stringify(mode)}`),
      'existing function key returns to doll: '+mode);
    const before=await evaluate(`document.querySelector('select[data-slot="${slot}"]').value`);
    await key(' ');
    check(await evaluate(`document.querySelector('select[data-slot="${slot}"]').value`)!==before,'existing next mode: '+mode);
  }
  await change('#showJewelry',true);
  check(await evaluate(`document.querySelector('#keyboardMode').value==='Gauntlets'`),'overlay toggle selects jewelry mode');
  await change('#targetScope','all');
  await evaluate(`{const e=document.querySelector('#targetSearch');e.value='item261';e.dispatchEvent(new Event('input'));}`);
  await evaluate(`{const b=[...document.querySelectorAll('#targetList button')].find(b=>b.firstElementChild.textContent==='item261');
    if(!b)throw Error('jewelry target absent');b.click();}`);
  await delay(300);
  check((await row('Gauntlets')).asset==='item261' && (await row('Gauntlets')).artUrl.includes('jewelry_prepared'),
    'queue selection equips actual jewelry target');
  const modified=await saved();
  for(const field of ['decisions','placements']) {
    for(const [id,value] of Object.entries(baseline[field])) {
      check(JSON.stringify(modified[field][id])===JSON.stringify(value),'existing '+field+' unchanged: '+id);
    }
  }
  await send('Page.reload',{ignoreCache:true});await delay(1000);
  check(JSON.stringify(await saved())===JSON.stringify(modified),'reload retains original and new review records');
  // Recreate the user's latest captured feedback in this isolated profile only.
  await evaluate(`(async()=>{
    const captured=await (await fetch('jewelry_inventory_20260926/browser_state.original.json')).json();
    for(const [key,value] of Object.entries(captured.storage)) {
      if(value===null)localStorage.removeItem(key);else localStorage.setItem(key,value);
    }
    localStorage.removeItem('openyamm-paperdoll-'+PAPERDOLL_APPROVAL_SNAPSHOT_SYNC.id);
  })()`);
  await send('Page.reload',{ignoreCache:true});await delay(1000);
  const feedback=await saved();
  check(Object.keys(feedback.decisions).length===1260 && Object.keys(feedback.placements).length===728,
    'latest feedback preserved');
  check(await evaluate(`document.querySelector('#repairPassSummary').textContent.includes('0 equipment images still')`),
    'twelve already-authorized offset approvals imported after the old marker');
  check(await evaluate(`(async()=>{
    const captured=await (await fetch('jewelry_inventory_20260926/browser_state.original.json')).json();
    const original=JSON.parse(captured.storage['openyamm-paperdoll-context-review-v1']);
    const current=JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'));
    const patch=PAPERDOLL_APPROVAL_SNAPSHOT_SYNC;
    return Object.keys(original).every(id=>JSON.stringify(current[id])===JSON.stringify(patch.records[id]?.after||original[id])) &&
      localStorage.getItem('openyamm-paperdoll-placement-v1')===captured.storage['openyamm-paperdoll-placement-v1'];
  })()`),'exact twelve approved snapshots updated; every other decision and all offsets unchanged');
  const progress=await evaluate(`document.querySelector('#jewelryProgress').textContent`);
  check(progress.includes('79 items / 63 distinct images') && progress.includes('58 accepted') && progress.includes('5 flagged') &&
    progress.includes('0 unreviewed'),'live counts cover every underlying image including canonical approvals');
  await change('#targetScope','all');
  await change('#decisionFilter','jewelry');
  await change('#hideAccepted',true);
  check(await evaluate(`document.querySelector('#queueCount').textContent==='5 matching targets'`),
    'only five flagged image groups remain');
  await evaluate(`{const e=document.querySelector('#targetSearch');e.value='Igraine';e.dispatchEvent(new Event('input'));}`);
  check(await evaluate(`document.querySelector('#queueCount').textContent==='1 matching targets'`),
    'artifact name finds the shared image');
  await evaluate(`{const b=[...document.querySelectorAll('#targetList button')].find(b=>b.firstElementChild.textContent==='ring10');
    if(!b)throw Error('Shared Scarab Ring missing from remaining queue');b.click();}`);
  await delay(300);
  check((await row('Ring1')).asset==='ring10','Igraine routes to the shared normal-item image');
  check(await evaluate(`document.querySelector('#inventoryPreview').textContent.includes('Athena') &&
    document.querySelector('#inventoryPreview').textContent.includes('Igraine')`),'shared item names visible');
  await evaluate(`{const e=document.querySelector('#targetSearch');e.value='';e.dispatchEvent(new Event('input'));}`);
  await change('#hideAccepted',false);
  check(await evaluate(`document.querySelector('#queueCount').textContent==='63 matching targets'`),
    'all 63 unique images visible when accepted items shown');
  const optionCounts=await evaluate(`Object.fromEntries(['Gauntlets','Amulet','Ring1'].map(slot=>
    [slot,document.querySelector('select[data-slot="'+slot+'"]').options.length-1]))`);
  check(optionCounts.Gauntlets===17 && optionCounts.Amulet===15 && optionCounts.Ring1===31,
    'selectors do not repeat exact-image artifacts');
  await change('#hideAccepted',true);
  await evaluate(`window.reviewBlob=null;URL.createObjectURL=blob=>{window.reviewBlob=blob;return 'blob:review-test';};
    HTMLAnchorElement.prototype.click=function(){};`);
  await click('#exportDecisions');
  const exported=await evaluate(`(async()=>JSON.parse(await window.reviewBlob.text()))()`);
  check(exported.inventory_fit_proposals.records.length===79 && exported.inventory_fit_proposals.changed_footprints===6 &&
    exported.inventory_fit_proposals.groups.length===63,
    'export carries all sizing proposals and six item-table changes');
  check(JSON.stringify(await saved())===JSON.stringify(feedback),'coverage and fitting do not modify user feedback');
  const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
  await writeFile(output+'/browser.png',Buffer.from(shot.data,'base64'));
  const report={result:'PASS',icons:drawn.length,gloves:drawn.filter(r=>r.slot==='Gauntlets').length,
    jewelry:drawn.filter(r=>r.slot!=='Gauntlets').length,modes,overlayPreserved:true,shortcuts:true,
    previousDecisionsPreserved:1225,previousPlacementsPreserved:726,
    latestDecisionsPreserved:1260,latestPlacementsPreserved:728,
    authorizedOffsetApprovalsSynchronized:12,
    reviewCounts:{accepted:58,flagged:5,unreviewed:0},inventoryOverflowPixels:0,
    itemDefinitionsCovered:79,duplicateImagesRemoved:16,drawn};
  await writeFile(output+'/browser_checks.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({...report,drawn:undefined}));
  ws.close();
} finally {browser.kill('SIGTERM');}
