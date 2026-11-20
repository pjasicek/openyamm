// Browser check in a fresh Chrome profile; never touches the user's saved review.
import assert from "node:assert/strict";
import {spawn} from "node:child_process";
import {writeFile} from "node:fs/promises";

const url = "http://127.0.0.1:8899/level_generation/ui/hud_inventory/spill_audit_20260926/index.html";
const browser = spawn("google-chrome", ["--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
  "--remote-debugging-port=9256", "--remote-allow-origins=*", "--window-size=1500,1050",
  "--user-data-dir=/tmp/openyamm-spill-keyboard-" + Date.now(), url], {stdio: "ignore"});
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const flagKey = "openyamm-icon-spill-flags-v1";
let socket;
try {
  let page;
  for (let i = 0; i < 100; ++i) {
    try {
      const pages = await (await fetch("http://127.0.0.1:9256/json/list")).json();
      page = pages.find(page => page.type === "page" && page.url.includes("spill_audit"));
      if (page) break;
    } catch { /* Wait for the isolated browser. */ }
    await delay(100);
  }
  assert.ok(page, "Browser started");
  socket = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, {once: true});
    socket.addEventListener("error", reject, {once: true});
  });
  let serial = 0;
  const pending = new Map();
  socket.addEventListener("message", event => {
    const result = JSON.parse(event.data), request = pending.get(result.id);
    if (!request) return;
    pending.delete(result.id);
    if (result.error) request.reject(new Error(result.error.message));
    else request.resolve(result.result);
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++serial;
    pending.set(id, {resolve, reject});
    socket.send(JSON.stringify({id, method, params}));
  });
  const evaluate = async expression => {
    const result = await send("Runtime.evaluate", {expression, returnByValue: true, awaitPromise: true});
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const ready = async () => {
    for (let i = 0; i < 100; ++i) {
      if (await evaluate("Boolean(document.querySelector('article.selected'))")) return;
      await delay(100);
    }
    throw new Error("Review UI did not load");
  };
  await ready();
  await evaluate("localStorage.setItem('openyamm-paperdoll-placement-v1','sentinel-do-not-touch')");
  const state = () => evaluate(`({position:document.querySelector('#position').textContent,
    key:document.querySelector('article.selected')?.dataset.reviewKey,
    reason:document.querySelector('[data-reason][aria-pressed=true]')?.dataset.reason,
    flags:JSON.parse(localStorage.getItem('${flagKey}')||'{"flags":{}}').flags,
    note:document.querySelector('#notes').value})`);
  const key = async (key, repeat = false) => {
    const code = key === " " ? "Space" : key;
    const virtual = {ArrowUp:38, ArrowDown:40, ArrowLeft:37, ArrowRight:39, " ":32}[key];
    await send("Input.dispatchKeyEvent", {type:"keyDown", key, code, windowsVirtualKeyCode:virtual, autoRepeat:repeat});
    await send("Input.dispatchKeyEvent", {type:"keyUp", key, code, windowsVirtualKeyCode:virtual});
  };
  const filter = async (id, value) => evaluate(`(() => {const el=document.getElementById(${JSON.stringify(id)});
    el.value=${JSON.stringify(value)};el.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  const first = await state();
  assert.match(first.position, /^1 \/ /);
  await key("ArrowUp");
  assert.equal((await state()).key, first.key, "Up clamps at first item");
  await key("ArrowDown");
  const second = await state();
  assert.notEqual(second.key, first.key, "Down selects next item");
  await key("ArrowRight");
  assert.equal((await state()).reason, "outline_spill");
  await key(" ");
  const flagged = await state();
  assert.equal(flagged.key, second.key, "Space does not advance");
  assert.equal(flagged.flags[second.key].reason, "outline_spill");
  await key(" ", true);
  assert.deepEqual((await state()).flags, flagged.flags, "Held Space does not rewrite flags");
  await key("ArrowRight");
  assert.equal((await state()).reason, "interior_spill");
  await key("ArrowRight");
  assert.equal((await state()).reason, "other");
  await key("ArrowRight");
  assert.equal((await state()).reason, "border_magenta", "Reasons wrap");
  await key("ArrowLeft");
  assert.equal((await state()).reason, "other");
  await evaluate("document.querySelector('#notes').focus()");
  const beforeTyping = await state();
  await key("ArrowDown");
  await key("ArrowRight");
  await key(" ");
  assert.equal((await state()).key, beforeTyping.key, "Typing does not navigate");
  assert.equal((await state()).reason, beforeTyping.reason, "Typing does not change reason");
  assert.deepEqual((await state()).flags, beforeTyping.flags, "Typing does not flag");
  await evaluate("document.querySelector('#notes').value='Review seam';document.querySelector('#notes').dispatchEvent(new Event('input'));document.querySelector('article.selected').focus()");
  await key(" ");
  assert.equal((await state()).flags[second.key].note, "Review seam");
  for (let i = 0; i < 40; ++i) await key("ArrowDown");
  assert.match((await state()).position, /^42 \/ /, "Navigation crosses the 40-card boundary");
  const beforeReload = await state();
  await send("Page.reload", {ignoreCache:true});
  await delay(250);
  await ready();
  assert.equal((await state()).key, beforeReload.key, "Selection survives reload");
  assert.deepEqual((await state()).flags, beforeReload.flags, "Flags and notes survive reload");
  await filter("reviewFilter", "flagged");
  assert.equal((await state()).position, "1 / 1");
  assert.equal((await state()).reason, "other", "Selected flagged item restores saved reason");
  await evaluate("document.querySelector('#scope').focus()");
  const beforeFilterKey = await state();
  await key("ArrowRight");
  assert.equal((await state()).reason, beforeFilterKey.reason, "Filter controls keep their native keys");
  // The native select may itself move to another scope when given an arrow.
  await filter("scope", "accepted_x2");
  await evaluate("document.querySelector('#search').value='no-such-spill-item';document.querySelector('#search').dispatchEvent(new Event('input'));document.activeElement.blur()");
  await key("ArrowDown"); await key(" ");
  assert.equal((await state()).key, undefined, "Empty filtered queue is safe");
  await filter("search", "");
  assert.equal((await state()).key, second.key, "Clearing search restores the flagged item");
  await evaluate("window.exportedBlob=null;URL.createObjectURL=b=>{window.exportedBlob=b;return 'blob:test'};HTMLAnchorElement.prototype.click=function(){};document.querySelector('#export').click()");
  const exported = await evaluate("(async()=>JSON.parse(await window.exportedBlob.text()))()");
  assert.deepEqual(exported.flags, (await state()).flags, "Export includes reasons, notes and image hashes");
  assert.equal(await evaluate("localStorage.getItem('openyamm-paperdoll-placement-v1')"), "sentinel-do-not-touch");
  await evaluate("document.querySelector('#unflag').click()");
  assert.equal(Object.keys((await state()).flags).length, 0, "Flag can be removed explicitly");
  await filter("reviewFilter", "");
  await filter("search", "item019.bmp");
  await evaluate("document.querySelector('article.selected').focus()");
  await key("ArrowLeft");
  await key(" ");
  const screenshot = await send("Page.captureScreenshot", {format:"png"});
  await writeFile("/tmp/openyamm-spill-keyboard.png", Buffer.from(screenshot.data,"base64"));
  console.log(JSON.stringify({result:"PASS", checks:["navigation and boundaries", "four reasons", "flag/update",
    "held-key guard", "typing/filter controls", "cross-page navigation", "reload persistence", "saved notes",
    "empty queue", "export", "unflag", "other review storage untouched"], screenshot:"/tmp/openyamm-spill-keyboard.png"}));
  const originalFlags = await evaluate(`localStorage.getItem('${flagKey}')`);
  await send("Page.navigate", {url:url.replace("spill_audit_20260926/index.html", "spill_repairs_20260927/review/index.html")});
  for (let i = 0; i < 100; ++i) {
    if (await evaluate("Boolean(window.SPILL_REPAIRS && document.querySelector('#title')?.textContent)")) break;
    await delay(100);
  }
  assert.equal(await evaluate("window.SPILL_REPAIRS.records.length"),1722);
  assert.ok(await evaluate("Boolean(window.SPILL_PUBLICATION)"),"Accepted publication is loaded");
  await filter("filter","pending");
  assert.equal(await evaluate("document.querySelector('#position').textContent"),"0 / 0","Blanket acceptance covers all entries");
  await filter("filter","resolved");
  assert.match(await evaluate("document.querySelector('#position').textContent"),/\/ 12$/,"Only recent comments were resolved");
  assert.match(await evaluate("document.querySelector('#heading').textContent"),/accepted and installed/);
  await filter("filter","all");
  await filter("search","item019.bmp");
  await filter("filter","oldflag");
  assert.equal(await evaluate("document.querySelector('#position').textContent"),"1 / 1");
  assert.match(await evaluate("document.querySelector('#originalFeedback').textContent"),/Original flag/);
  await filter("filter","all");
  await filter("search","");
  const repairState = () => evaluate(`({title:document.querySelector('#title').textContent,
    position:document.querySelector('#position').textContent,
    decisions:JSON.parse(localStorage.getItem('openyamm-icon-spill-repairs-v1')||'{"decisions":{}}').decisions})`);
  const initialRepair = await repairState();
  await key("ArrowDown");
  assert.notEqual((await repairState()).title,initialRepair.title);
  await key("ArrowRight");await key(" ");
  const flaggedRepair = await repairState();
  assert.equal(Object.values(flaggedRepair.decisions)[0].reason,"outline_spill");
  await evaluate("document.querySelector('#notes').value='Keep the contour';document.querySelector('#notes').dispatchEvent(new Event('input'));document.querySelector('#notes').focus()");
  await key("ArrowDown");
  assert.equal((await repairState()).title,flaggedRepair.title,"Repair note typing does not navigate");
  await evaluate("document.activeElement.blur();document.querySelector('#accept').click()");
  const acceptedRepair = Object.values((await repairState()).decisions)[0];
  assert.equal(acceptedRepair.status,"accept");assert.equal(acceptedRepair.note,"Keep the contour");
  await send("Page.reload",{ignoreCache:true});await delay(500);
  assert.equal((await repairState()).title,flaggedRepair.title,"Repair selection survives reload");
  assert.equal(await evaluate("document.querySelector('#notes').value"),"Keep the contour");
  await filter("search","item019.bmp");
  for (let i = 0; i < 100; ++i) {
    if (await evaluate("['native','before','after'].every(id=>{const im=document.getElementById(id);return im.complete&&im.naturalWidth>0})")) break;
    await delay(100);
  }
  assert.ok(await evaluate("['native','before','after'].every(id=>document.getElementById(id).naturalWidth>0)"),"Original and repair images load");
  await evaluate("window.exportedBlob=null;URL.createObjectURL=b=>{window.exportedBlob=b;return 'blob:test'};HTMLAnchorElement.prototype.click=function(){};document.querySelector('#export').click()");
  const repairExport = await evaluate("(async()=>JSON.parse(await window.exportedBlob.text()))()");
  assert.deepEqual(repairExport.decisions,(await repairState()).decisions);
  assert.equal(await evaluate(`localStorage.getItem('${flagKey}')`),originalFlags,"Original flags remain unchanged");
  assert.equal(await evaluate("localStorage.getItem('openyamm-paperdoll-placement-v1')"),"sentinel-do-not-touch");
  const repairScreenshot = await send("Page.captureScreenshot", {format:"png"});
  await writeFile("/tmp/openyamm-spill-repairs.png",Buffer.from(repairScreenshot.data,"base64"));
  console.log(JSON.stringify({result:"PASS",checks:["repair queue", "original feedback retained", "repair keyboard",
    "separate acceptance", "notes", "reload", "images", "export", "placement storage intact"],
    screenshot:"/tmp/openyamm-spill-repairs.png"}));
} finally {
  socket?.close();
  browser.kill("SIGTERM");
}
