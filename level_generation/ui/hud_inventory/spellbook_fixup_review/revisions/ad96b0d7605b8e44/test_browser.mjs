import assert from "node:assert/strict";
import {spawn} from "node:child_process";
import {mkdir, mkdtemp, writeFile} from "node:fs/promises";
import {tmpdir} from "node:os";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";

const directory = dirname(fileURLToPath(import.meta.url));
const evidence = join(directory, "evidence");
await mkdir(evidence, {recursive: true});
const profile = await mkdtemp(join(tmpdir(), "openyamm-spellbook-review-"));
const url = process.argv[2] || "http://127.0.0.1:8899/level_generation/ui/hud_inventory/spellbook_fixup_review/";
const browser = spawn("google-chrome", [
  "--headless", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--no-first-run",
  "--disable-background-networking", "--remote-debugging-pipe", "--user-data-dir=" + profile,
], {stdio: ["ignore", "ignore", "pipe", "pipe", "pipe"]});

let sequence = 0, session, buffer = "", errors = "";
const pending = new Map(), exceptions = [], failedRequests = [];
browser.stderr.on("data", chunk => {errors += chunk.toString();});
for (const pipe of [browser.stdio[3], browser.stdio[4]]) pipe.on("error", () => {});
browser.on("exit", code => {
  for (const entry of pending.values()) {clearTimeout(entry.timer); entry.reject(new Error(`Chrome exited ${code}: ${errors.slice(-1800)}`));}
  pending.clear();
});
browser.stdio[4].on("data", chunk => {
  buffer += chunk.toString();
  let end;
  while ((end = buffer.indexOf("\0")) >= 0) {
    const message = JSON.parse(buffer.slice(0, end)); buffer = buffer.slice(end + 1);
    if (message.id && pending.has(message.id)) {
      const entry = pending.get(message.id); pending.delete(message.id); clearTimeout(entry.timer);
      message.error ? entry.reject(new Error(message.error.message)) : entry.resolve(message.result);
    }
    if (message.method === "Runtime.exceptionThrown") exceptions.push(message.params.exceptionDetails);
    if (message.method === "Network.responseReceived" && message.params.response.status >= 400
      && !message.params.response.url.endsWith("favicon.ico")) failedRequests.push(message.params.response);
  }
});
function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => {pending.delete(id); reject(new Error("Timed out: " + method));}, 20000);
    pending.set(id, {resolve, reject, timer});
    browser.stdio[3].write(JSON.stringify({id, method, params, ...(session ? {sessionId: session} : {})}) + "\0");
  });
}
async function evaluate(expression) {
  const response = await call("Runtime.evaluate", {expression, awaitPromise: true, returnByValue: true});
  if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails));
  return response.result.value;
}
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function ready() {
  for (let i = 0; i < 120; ++i) {
    if (await evaluate("Boolean(window.spellbookReview?.state.ready)")) return;
    await delay(250);
  }
  throw new Error("Preview did not finish loading: " + await evaluate("document.body.innerText"));
}
async function point(id) {
  return evaluate(`(() => {
    const data = spellbookReview.data;
    const item = [...data.schools.map(s=>s.button), ...data.controls, ...data.schools.flatMap(s=>s.spells)].find(s=>s.id===${JSON.stringify(id)});
    const b=document.querySelector('#book').getBoundingClientRect();
    return {x:b.x+(item.rect.x+item.rect.width/2)*b.width/640, y:b.y+(item.rect.y+item.rect.height/2)*b.height/480};
  })()`);
}
async function move(position) {await call("Input.dispatchMouseEvent", {type: "mouseMoved", ...position});}
async function click(id) {
  const position = await point(id); await move(position);
  await call("Input.dispatchMouseEvent", {type: "mousePressed", button: "left", clickCount: 1, ...position});
  await call("Input.dispatchMouseEvent", {type: "mouseReleased", button: "left", clickCount: 1, ...position});
}
async function capture(name, full = false) {
  if (full) {
    const shot = await call("Page.captureScreenshot", {format: "png", captureBeyondViewport: true});
    await writeFile(join(evidence, name), Buffer.from(shot.data, "base64"));
  } else {
    const shot = await evaluate("document.querySelector('#book').toDataURL('image/png').split(',')[1]");
    await writeFile(join(evidence, name), Buffer.from(shot, "base64"));
  }
}

try {
  const {targetId} = await call("Target.createTarget", {url: "about:blank"});
  session = (await call("Target.attachToTarget", {targetId, flatten: true})).sessionId;
  await call("Runtime.enable"); await call("Page.enable"); await call("Network.enable");
  await call("Emulation.setDeviceMetricsOverride", {width: 1700, height: 1150, deviceScaleFactor: 1, mobile: false});
  await call("Page.navigate", {url}); await ready();
  assert.deepEqual(await evaluate("spellbookReview.data.checks"), {
    schools: 12, spellPairs: 111, allProposedIconAlphaIdentical: true, allProposedIconCanvasesIdentical: true,
    pagePixelsIdenticalOutsideSymbolAndName: true,
  });
  assert.equal(await evaluate("document.querySelector('#schoolSelect').options.length"), 12);
  await capture("fire_normal.png");
  await move(await point("SpellbookPageFireSpellFireaura"));
  await capture("fire_hover.png");
  assert.equal(await evaluate("document.querySelector('#hoverStatus').textContent"), "Fire Aura");
  await click("SpellbookPageFireSpellFireaura");
  await move({x: 30, y: 30});
  assert.equal(await evaluate("spellbookReview.state.selected"), "SpellbookPageFireSpellFireaura");
  await click("SpellbookQuickCastButton");
  assert.equal(await evaluate("spellbookReview.state.quick"), "SpellbookPageFireSpellFireaura");
  await click("SpellbookAttackCastButton");
  assert.equal(await evaluate("spellbookReview.state.attack"), "SpellbookPageFireSpellFireaura");
  const pressed = await point("SpellbookAttackCastButton");
  await call("Input.dispatchMouseEvent", {type: "mousePressed", button: "left", clickCount: 1, ...pressed});
  assert.equal(await evaluate("spellbookReview.state.down"), true);
  await capture("controls_pressed.png");
  await call("Input.dispatchMouseEvent", {type: "mouseReleased", button: "left", clickCount: 1, ...pressed});
  assert.equal(await evaluate("spellbookReview.state.attack"), null);
  await click("SpellbookCloseButton");
  assert.equal(await evaluate("spellbookReview.state.closed && !document.querySelector('#closedOverlay').hidden"), true);
  await evaluate("document.querySelector('#reopen').click()");
  const schools = await evaluate("spellbookReview.data.schools.map(s=>({key:s.key,id:s.button.id,count:s.spells.length}))");
  for (const school of schools) {
    await click(school.id);
    assert.equal(await evaluate("spellbookReview.state.school.key"), school.key);
    assert.equal(await evaluate("document.querySelector('#reviewTarget').options.length"), school.count + 5);
    if (["Air", "Body", "DarkElf"].includes(school.key)) {
      await move({x: 30, y: 30}); await capture(school.key.toLowerCase() + ".png");
    }
  }
  await click("SpellbookSchoolButtonFire");
  await evaluate("document.querySelector('#installedMode').click()");
  assert.equal(await evaluate("spellbookReview.state.mode"), "installed");
  await capture("fire_installed.png");
  await call("Input.dispatchKeyEvent", {type: "keyDown", key: "b", code: "KeyB", windowsVirtualKeyCode: 66});
  await call("Input.dispatchKeyEvent", {type: "keyUp", key: "b", code: "KeyB", windowsVirtualKeyCode: 66});
  assert.equal(await evaluate("spellbookReview.state.mode"), "proposed");

  await evaluate(`document.querySelector('#flag').click(); document.querySelector('#note').value='Keep glyphs fixed <review> & colour.';
    document.querySelector('#note').dispatchEvent(new Event('input',{bubbles:true}));`);
  const exported = await evaluate("spellbookReview.reviewExport()");
  assert.equal(exported.decisions.SpellbookPageFire.decision, "flag");
  assert.equal(exported.decisions.SpellbookPageFire.note, "Keep glyphs fixed <review> & colour.");
  assert.equal(exported.decisions.SpellbookPageFire.artwork.proposed.sha256.length, 64);
  await call("Page.reload", {ignoreCache: true}); await ready();
  assert.equal(await evaluate("document.querySelector('#note').value"), "Keep glyphs fixed <review> & colour.");
  await evaluate("document.querySelector('#resetDecision').click()");
  await evaluate(`(() => {
    const input=document.querySelector('#importReview'), transfer=new DataTransfer();
    transfer.items.add(new File([${JSON.stringify(JSON.stringify(exported))}], 'review.json', {type:'application/json'}));
    input.files=transfer.files; input.dispatchEvent(new Event('change',{bubbles:true}));
  })()`);
  await delay(150);
  assert.equal(await evaluate("spellbookReview.state.decisions.SpellbookPageFire.decision"), "flag");
  await evaluate("document.querySelector('#resetDecision').click()");

  await evaluate("document.querySelector('#backgroundOnly').click()");
  assert.equal(await evaluate("spellbookReview.state.backgroundOnly"), true);
  await capture("background.png");
  await evaluate("document.querySelector('#backgroundOnly').click()");
  await call("Emulation.setDeviceMetricsOverride", {width: 740, height: 1050, deviceScaleFactor: 1, mobile: false});
  await delay(150);
  const mobile = await evaluate(`(() => {const r=document.querySelector('#book').getBoundingClientRect();
    return {ratio:r.width/r.height, width:r.width, window:innerWidth};})()`);
  assert.ok(Math.abs(mobile.ratio - 4 / 3) < .01, "mobile canvas must retain its aspect ratio");
  assert.ok(mobile.width <= mobile.window, "fit view must fit on a narrow screen");
  await click("SpellbookSchoolButtonWater");
  assert.equal(await evaluate("spellbookReview.state.school.key"), "Water");
  await call("Emulation.setDeviceMetricsOverride", {width: 1700, height: 1150, deviceScaleFactor: 1, mobile: false});
  await delay(150);
  await click("SpellbookSchoolButtonFire"); await move({x: 30, y: 30});
  await capture("review.png", true);
  assert.deepEqual(exceptions, [], "no browser exceptions");
  assert.deepEqual(failedRequests, [], "all artwork and fonts must load");
  const report = {result: "PASS", revision: await evaluate("spellbookReview.data.revision"),
    schoolsClicked: 12, spellsAvailable: 111, leftButtons: 3, hoverAndSelection: true,
    quickAndAttackAssignments: true, closeAndReopen: true, comparison: true,
    reviewPersistence: true, exportAndImport: true, narrowScreen: true, browserErrors: 0};
  await writeFile(join(evidence, "browser_checks.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify(report, null, 2));
} finally {
  browser.kill("SIGTERM");
  for (const entry of pending.values()) clearTimeout(entry.timer);
}
