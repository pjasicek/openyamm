// Headless check of the party creation study: loads every approach in every view, exercises the interactions,
// fails on console errors, measures phone touch targets and writes the screenshots and validation.json.
// Serve the repository root first:  python3 -m http.server 8917 --bind 127.0.0.1   (from the repo root)
// then:  node level_generation/ui/party_creation_study_20261101/test_browser.mjs
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

const base = process.env.STUDY_BASE || 'http://127.0.0.1:8917/level_generation/ui/party_creation_study_20261101/';
const directory = fileURLToPath(new URL('.', import.meta.url));
const port = 9391 + Math.floor(Math.random() * 300);
const browser = spawn('google-chrome', ['--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  `--remote-debugging-port=${port}`, '--remote-allow-origins=*', `--user-data-dir=/tmp/openyamm-party-study-${Date.now()}`,
  'about:blank'], {stdio: 'ignore'});
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const checks = [], errors = [], failed = [], metrics = {};
let ws, serial = 0;
try {
  let page;
  for (let attempt = 0; attempt < 100 && !page; attempt++) {
    try { page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(item => item.type === 'page'); } catch {}
    await delay(100);
  }
  assert.ok(page, 'Chrome starts');
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
  const pending = new Map();
  ws.onmessage = event => {
    const message = JSON.parse(event.data), p = pending.get(message.id);
    if (p) { pending.delete(message.id); message.error ? p.reject(message.error) : p.resolve(message.result); }
    if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails.exception?.description || message.params.exceptionDetails.text);
    if (message.method === 'Runtime.consoleAPICalled' && message.params.type === 'error') errors.push(JSON.stringify(message.params.args));
    if (message.method === 'Network.responseReceived' && message.params.response.status >= 400 && !message.params.response.url.endsWith('favicon.ico')) failed.push(message.params.response.url);
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => { const id = ++serial; pending.set(id, {resolve, reject}); ws.send(JSON.stringify({id, method, params})); });
  const evaluate = async expression => {
    const result = await send('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true});
    assert.ok(!result.exceptionDetails, JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const check = async (name, expression) => { assert.ok(await evaluate(expression), name); checks.push(name); };
  const size = (width, height) => send('Emulation.setDeviceMetricsOverride', {width, height, deviceScaleFactor: 1, mobile: false});
  const open = async (page, query = '') => {
    await send('Page.navigate', {url: `${base}${page}?export=1${query}`});
    for (let attempt = 0; attempt < 100; attempt++) { if (await evaluate("document.body?.dataset.ready === 'true'")) break; await delay(60); }
    await delay(250);
  };
  const capture = async name => {
    const shot = await send('Page.captureScreenshot', {format: 'png'});
    await writeFile(`${directory}shots/${name}.png`, Buffer.from(shot.data, 'base64'));
  };
  await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
  await mkdir(`${directory}shots`, {recursive: true});

  for (const approach of ['a', 'b', 'c']) {
    await size(1600, 900);
    await open(`${approach}.html`);
    await check(`${approach}: stage fills 1600x900`, "Math.round(document.querySelector('#stage').getBoundingClientRect().width) === 1600");
    await check(`${approach}: images load`, "[...document.querySelectorAll('#screen img')].every(i => i.complete && i.naturalWidth > 0)");
    await check(`${approach}: nothing spills out of the canvas`, "[...document.querySelectorAll('#screen *')].every(n => { const r = n.getBoundingClientRect(); return r.right <= 1601 && r.bottom <= 901; })");
    await check(`${approach}: panels do not overflow`, "[...document.querySelectorAll('.col, .editor, .slist, .rail')].every(c => c.scrollHeight <= c.clientHeight + 1 && (c.classList.contains('rail') || c.scrollWidth <= c.clientWidth + 1))");
    await capture(`${approach}-desktop`);
    // interactions
    await check(`${approach}: stat + spends a point`, "(() => { App.sel = 4; App.render(); const m = App.members[4], before = pool(m); document.querySelector('[data-inc=\"4:0\"]').click(); return pool(App.members[4]) < before; })()");
    await check(`${approach}: choosing an optional skill`, "(() => { App.sel = 4; App.render(); const m = App.members[4]; const s = optionalSkills(m)[0]; document.querySelector(`[data-skill=\"${s}\"][data-m=\"4\"]`).click(); return App.members[4].chosen.includes(s); })()");
    await check(`${approach}: plan mode marks a later skill`, "(() => { App.planMode = true; App.sel = 4; App.render(); const m = App.members[4]; const s = skillList().find(x => skillState(m, x) === 'later' || skillState(m, x) === 'promo'); document.querySelector(`[data-skill=\"${s}\"][data-m=\"4\"]`).click(); App.planMode = false; App.render(); return App.members[4].plan.includes(s); })()");
    await check(`${approach}: portrait grid lists every portrait`, "(() => { document.querySelector('[data-portrait]').click(); return document.querySelectorAll('.pg-tile').length === R().portraits.length; })()");
    await check(`${approach}: picking a portrait changes race`, "(() => { document.querySelector('.pg-tile[data-p=\"62\"]').click(); return portraitById(App.members[App.sel].portrait).race === 9; })()");
    await check(`${approach}: class picker shows a mastery table`, "(() => { document.querySelector('[data-class]').click(); const ok = document.querySelectorAll('.cp-card').length > 3 && !!document.querySelector('.mt'); document.querySelectorAll('.cp-card')[0].click(); document.querySelector('[data-pick]').click(); return ok; })()");
    await check(`${approach}: voice picker offers playable lines`, "(() => { const b = document.querySelector('[data-voice]'); b.click(); const ok = document.querySelectorAll('.vp-card').length > 3 && document.querySelectorAll('.vp-card .line').length > 10; closeModal(); return ok; })()");
    await check(`${approach}: MAW ruleset renders 44 skills`, "(() => { App.ruleset = 'maw'; buildParty(); App.render(); const n = new Set([...document.querySelectorAll('[data-skill]')].map(x => x.dataset.skill)).size; App.ruleset = 'standard'; buildParty(); App.render(); return n === 44; })()");
    await open(`${approach}.html`, '&ruleset=maw&continent=jadame');
    await check(`${approach}: MAW view fits`, "[...document.querySelectorAll('#screen *')].every(n => { const r = n.getBoundingClientRect(); return r.right <= 1601 && r.bottom <= 901; })");
    await check(`${approach}: MAW columns do not overflow`, "[...document.querySelectorAll('.col, .editor, .slist, .rail')].every(c => c.scrollHeight <= c.clientHeight + 1 && (c.classList.contains('rail') || c.scrollWidth <= c.clientWidth + 1))");
    await capture(`${approach}-maw`);
    await size(1200, 900);
    await open(`${approach}.html`, '&device=window43');
    await capture(`${approach}-4x3`);
    await size(1600, 720);
    await open(`${approach}.html`, '&device=phone');
    metrics[approach] = await evaluate('smallTargetAudit(false)');
    await evaluate("(() => { const n = document.querySelector('[data-skill][data-m=\"0\"].option, [data-skill][data-m=\"0\"].later'); n.click(); return true; })()");
    await delay(150);
    await check(`${approach}: touch tap opens an action card`, "document.querySelector('#card.on .acts') !== null");
    await evaluate('smallTargetAudit(true)');
    await capture(`${approach}-phone`);
  }
  // shared popups at desktop size
  await size(1600, 900);
  await open('c.html');
  await evaluate('openPortraitPicker(0)'); await delay(300); await capture('popup-portraits');
  await open('c.html');
  await evaluate("App.sel = 2; App.render(); openClassPicker(2)"); await delay(300); await capture('popup-class');
  await open('c.html');
  await evaluate('openVoicePicker(1)'); await delay(200); await capture('popup-voice');
  await open('c.html');
  await check('c: party board overlay is editable', "(() => { document.querySelector('[data-board]').click(); const before = App.members[4].chosen.length; const s = optionalSkills(App.members[4]).find(x => !App.members[4].chosen.includes(x)); document.querySelector(`#modal [data-skill=\"${s}\"][data-m=\"4\"]`).click(); return !!document.querySelector('#modal .board') && App.members[4].chosen.length === before + 1; })()");
  await delay(150); await capture('c-board-overlay');
  await open('a.html');
  await evaluate("(() => { const n = document.querySelector('.chip[data-skill=\"Spear\"]'); n.dispatchEvent(new MouseEvent('mouseenter')); })()"); await delay(150); await capture('popup-skill-card');
  await send('Page.navigate', {url: `${base}index.html`});
  await delay(1200);
  await check('index: every screenshot loads', "[...document.images].length >= 9 && [...document.images].every(i => i.complete && i.naturalWidth > 0)");
  await open('a.html');
  await check('voice WAV (IMA ADPCM) decodes', "fetch(AUDIO + D.voices[0].lines.find(l => l[0] === 'ChooseMe1')[1]).then(r => r.arrayBuffer()).then(b => decodeWav(b).samples.length > 1000)");
  assert.deepEqual(errors, [], 'no console errors');
  assert.deepEqual(failed, [], 'no failed requests');
  await writeFile(`${directory}validation.json`, JSON.stringify({date: new Date().toISOString(), checks, phoneTargets: metrics, errors, failed}, null, 2) + '\n');
  console.log(`${checks.length} checks passed`);
  console.log('phone targets', JSON.stringify(metrics));
} finally {
  ws?.close();
  browser.kill();
}
