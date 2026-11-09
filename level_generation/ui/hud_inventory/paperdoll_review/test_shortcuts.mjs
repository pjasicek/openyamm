import { spawn } from "node:child_process";
import { writeFile } from "node:fs/promises";

const browser = spawn("google-chrome", [
  "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--remote-debugging-port=9238", "--remote-allow-origins=*",
  "--user-data-dir=/tmp/openyamm-shortcuts-check-cdp", "--window-size=1900,1400",
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



  const check=(value,message)=>{if(!value)throw new Error(message);};
  const click=async(selector)=>{await evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);await delay(250);};
  const key=async(k,shift=false)=>{
    const codes={ArrowUp:38,ArrowDown:40,ArrowLeft:37,ArrowRight:39,Tab:9,Escape:27,' ':32};
    const vk=k.startsWith('F') ? 111+Number(k.slice(1)) : codes[k];
    await send('Input.dispatchKeyEvent',{type:'keyDown',key:k,code:k===' '?'Space':k,windowsVirtualKeyCode:vk,modifiers:shift?8:0});
    await send('Input.dispatchKeyEvent',{type:'keyUp',key:k,code:k===' '?'Space':k,windowsVirtualKeyCode:vk,modifiers:shift?8:0});
    await delay(180);
  };
  const saved=()=>evaluate(`Object.fromEntries(['openyamm-paperdoll-context-review-v1','openyamm-paperdoll-context-review-attempt-v1','openyamm-paperdoll-placement-v1'].map(k=>[k,localStorage.getItem(k)]))`);
  await evaluate('localStorage.clear()');await send('Page.reload',{ignoreCache:true});await delay(1000);
  await click('.equipment-row[data-slot="MainHand"] [data-decision="flag"]');
  await evaluate(`{const t=document.querySelector('.equipment-row[data-slot="MainHand"] textarea');t.value='Keep this existing note';t.dispatchEvent(new Event('input',{bubbles:true}));t.blur();}`);
  await click('.equipment-row[data-slot="MainHand"] [data-move="1,0"]');
  const prior=await saved();
  await send('Page.reload',{ignoreCache:true});await delay(1000);
  check(JSON.stringify(await saved())===JSON.stringify(prior),'reload preserves all existing storage byte-for-byte');
  check(await evaluate(`JSON.stringify(JSON.parse(localStorage.getItem('openyamm-paperdoll-before-shortcuts-v1')).storage)` )===JSON.stringify(prior),'backup preserves original records');
  for(const [f,slot] of [['F1','oneHand'],['F2','twoHand'],['F3','OffHand'],['F4','Bow'],['F5','Cloak'],['F6','Armor'],['F7','Helm'],['F8','Boots'],['F9','Belt']]) {
    await key(f);
    check(await evaluate(`document.querySelector('#keyboardMode').value`)===f,`${f} selects mode`);
    const before=await evaluate(`document.querySelector('select[data-slot="${slot}"]').value`);
    await key(' ');
    const after=await evaluate(`document.querySelector('select[data-slot="${slot}"]').value`);
    check(before!==after && after!=='0',`${f} advances its own item`);
    if(f==='F3') check(await evaluate(`window.PAPERDOLL_REVIEW_DATA.items.find(i=>i.id===Number(document.querySelector('select[data-slot="OffHand"]').value)).stat`)==='Shield','F3 shield only');
  }
  await key('F1');
  const x=await evaluate(`Number(document.querySelector('.equipment-row[data-slot="MainHand"]').dataset.x)`);
  for(let i=0;i<3;i++)await key('ArrowRight');
  check(await evaluate(`Number(document.querySelector('.equipment-row[data-slot="MainHand"]').dataset.x)` )===x+3,'arrows move one game pixel');
  const selection=await evaluate(`document.querySelector('select[data-slot="oneHand"]').value`);
  await key(' ',true);
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"] .decision-status').textContent.includes('Accepted here')`),'shift-space accepts active mode');
  check(await evaluate(`document.querySelector('select[data-slot="oneHand"]').value`)===selection,'accept does not advance');
  const types=[];
  for(let i=0;i<5;i++){await key('Tab');types.push(await evaluate(`Number(document.querySelector('#typeShortcuts button.active').dataset.type)`));}
  check(types.join(',')==='1,2,3,4,0','Tab cycles exactly five types');
  await key('F6');await key(' ',true);
  await key('Tab');
  check(await evaluate(`!document.querySelector('.equipment-row[data-slot="Armor"] .decision-status').textContent.includes('Accepted here')`),'accept only current armor variant');
  await key('Tab',true);
  await key('F1');
  await click('.equipment-row[data-slot="MainHand"] [data-decision="flag"]');
  const oldX=await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"]').dataset.x`);
  await key('ArrowRight');
  check(await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"]').dataset.x`)===oldX,'notes retain arrow editing');
  await key('Escape');await key('ArrowRight');
  check(Number(await evaluate(`document.querySelector('.equipment-row[data-slot="MainHand"]').dataset.x`))===Number(oldX)+1,'Escape resumes shortcuts');
  // Both offsets and the note created before the update still exist after unrelated mode navigation.
  check(await evaluate(`JSON.parse(localStorage.getItem('openyamm-paperdoll-context-review-v1'))['engine--icons--item001.bmp'].note`)==='Keep this existing note','existing note survives mode workflow');
  console.log(JSON.stringify({passed:true,storageRetained:true,backup:true,nineModes:true,shieldOnly:true,offsets:true,acceptCurrent:true,fiveTypes:true,notesEditing:true}));
  ws.close();
} finally {browser.kill('SIGTERM');}
