import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtempSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const profile = mkdtempSync(join(tmpdir(), 'remaining-art-chrome-'));
const browser = spawn('google-chrome', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--allow-file-access-from-files',
  '--remote-debugging-pipe', '--no-first-run', '--disable-background-networking',
  '--user-data-dir=' + profile,
], {stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe']});

let nextId = 0;
let buffer = '';
let sessionId;
const pending = new Map();
const exceptions = [];
let stderr = '';
browser.stderr.on('data', chunk => { stderr += chunk.toString(); });
for (const pipe of [browser.stdio[3], browser.stdio[4]]) pipe.on('error', () => {});
browser.on('exit', code => {
  if (pending.size) {
    for (const {reject} of pending.values()) reject(new Error(`Chrome exited ${code}: ${stderr.slice(-1200)}`));
    pending.clear();
  }
});
browser.stdio[4].on('data', chunk => {
  buffer += chunk.toString();
  for (let end; (end = buffer.indexOf('\0')) >= 0;) {
    const message = JSON.parse(buffer.slice(0, end));
    buffer = buffer.slice(end + 1);
    if (message.id && pending.has(message.id)) {
      const {resolve: done, reject} = pending.get(message.id);
      pending.delete(message.id);
      message.error ? reject(message.error) : done(message.result);
    }
    if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails);
  }
});

function call(method, params = {}) {
  return new Promise((done, reject) => {
    const id = ++nextId;
    pending.set(id, {resolve: done, reject});
    browser.stdio[3].write(JSON.stringify({id, method, params, ...(sessionId ? {sessionId} : {})}) + '\0');
  });
}

async function evaluate(expression) {
  const result = await call('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true});
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

try {
  const {targetId} = await call('Target.createTarget', {url: 'about:blank'});
  sessionId = (await call('Target.attachToTarget', {targetId, flatten: true})).sessionId;
  await call('Runtime.enable');
  await call('Page.enable');
  await call('Page.navigate', {url: pathToFileURL(resolve(directory, 'index.html')).href});
  await new Promise(done => setTimeout(done, 1500));

  assert.equal(await evaluate('window.REMAINING_ART_CATALOG.summary.total'), 1718);
  assert.equal(await evaluate('window.REMAINING_ART_CATALOG.summary.with_candidate'), 1718);
  assert.equal(await evaluate('Object.keys(window.REMAINING_ART_ACCEPTANCE.decisions).length'), 1541);
  assert.equal(await evaluate('Object.keys(window.KEPT_EFFECT_ACCEPTANCE.decisions).length'), 178);
  assert.equal(await evaluate('window.REMAINING_ART_CATALOG.summary.imagegen_slice_candidates'), 590);
  assert.equal(await evaluate(`window.REMAINING_ART_CATALOG.items.filter(item => item.imagegen_slice).length`), 590);
  assert.equal(await evaluate(`window.REMAINING_ART_CATALOG.items.every(item =>
    item.candidates.every(candidate => !candidate.origin.includes('Real-ESRGAN')))`), true);
  assert.equal(await evaluate('window.REMAINING_ART_CATALOG.summary.accepted_reuse_candidates'), 20);
  assert.equal(await evaluate('document.querySelectorAll(".card").length'), 36);
  assert.equal(await evaluate('document.querySelector(".card .badge.ready") !== null'), true);
  assert.equal(await evaluate('document.querySelector("#summary").textContent.includes("0 flagged here")'), true);
  assert.equal(await evaluate('document.querySelector("#summary").textContent.includes("1718 accepted")'), true);
  assert.equal(await evaluate(`window.REMAINING_ART_CATALOG.items.filter(item => item.review_repair).length`), 236);
  assert.equal(await evaluate(`window.REMAINING_ART_CATALOG.items.filter(item => item.sequence_repair).length`), 173);
  assert.equal(await evaluate(`window.REMAINING_ART_CATALOG.items.filter(item =>
    item.world_master?.source_rgb_correlation >= 0.9).length`), 139);
  assert.deepEqual(await evaluate(`['item160', 'item162'].map(name => {
    const item = window.REMAINING_ART_CATALOG.items.find(row => row.name === name);
    return [item.candidates[0].origin, item.candidates[0].kind,
      item.candidates[0].sha256 === item.world_master.candidate_sha256];
  })`), [
    ['Approved world sprite master', 'approved_world_master', true],
    ['Approved world sprite master', 'approved_world_master', true],
  ]);
  assert.deepEqual(await evaluate(`(() => {
    const families = window.REMAINING_ART_CATALOG.items.filter(item =>
      item.name.startsWith('terra') || item.name.startsWith('t_') || item.name.startsWith('bt_'));
    return [families.length, families.every(item => item.candidates.length === 1 &&
      item.candidates[0].path.startsWith('magenta_perimeter/candidates/'))];
  })()`), [269, true]);
  assert.equal(await evaluate('document.querySelector("#duplicates").value'), 'unique');
  assert.deepEqual(await evaluate(`(() => {
    const artwork = document.querySelector('#artwork');
    artwork.value = 'imagegen';
    artwork.dispatchEvent(new Event('input', {bubbles:true}));
    const state = [document.querySelectorAll('.card').length > 0,
      document.querySelector('.card').textContent.includes('Imagegen restoration')];
    artwork.value = '';
    artwork.dispatchEvent(new Event('input', {bubbles:true}));
    return state;
  })()`), [true, true]);
  assert.equal(await evaluate(`(() => {
    document.querySelector('#duplicates').value = '';
    document.querySelector('#duplicates').dispatchEvent(new Event('input', {bubbles:true}));
    document.querySelector('#artwork').value = 'imagegen';
    document.querySelector('#artwork').dispatchEvent(new Event('input', {bubbles:true}));
    const count = Number(document.querySelector('#summary').textContent.match(/^(\\d+) match filters/)[1]);
    document.querySelector('#artwork').value = '';
    document.querySelector('#artwork').dispatchEvent(new Event('input', {bubbles:true}));
    document.querySelector('#duplicates').value = 'unique';
    document.querySelector('#duplicates').dispatchEvent(new Event('input', {bubbles:true}));
    return count;
  })()`), 590);
  assert.deepEqual(await evaluate(`(() => {
    const duplicates = document.querySelector('#duplicates');
    duplicates.value = '';
    duplicates.dispatchEvent(new Event('input', {bubbles:true}));
    const search = document.querySelector('#search');
    search.value = 'engine--icons--item339.bmp';
    search.dispatchEvent(new Event('input', {bubbles:true}));
    const card = document.querySelector('.card');
    const state = [card.dataset.decision,
      card.textContent.includes('Earlier flag on previous candidate'),
      card.textContent.includes('Imagegen restoration')];
    search.value = '';
    search.dispatchEvent(new Event('input', {bubbles:true}));
    duplicates.value = 'unique';
    duplicates.dispatchEvent(new Event('input', {bubbles:true}));
    return state;
  })()`), ['approve', true, true]);
  assert.deepEqual(await evaluate(`(() => {
    const search = document.querySelector('#search');
    search.value = 'engine--icons--tp_regna.bmp';
    search.dispatchEvent(new Event('input', {bubbles:true}));
    const card = document.querySelector('.card');
    const result = [card.dataset.decision,
      card.querySelector('.pane img[alt^="2× candidate"]').getAttribute('src')
        === window.REMAINING_ART_CATALOG.items.find(item => item.name === 'tp_regna').candidates[0].path,
      card.querySelector('textarea.note').value];
    search.value = '';
    search.dispatchEvent(new Event('input', {bubbles:true}));
    return result;
  })()`), ['approve', true, '']);
  assert.deepEqual(await evaluate(`(() => {
    const control = document.querySelector('#duplicates');
    const counts = [];
    for (const value of ['accepted', 'pending', 'unique', '']) {
      control.value = value;
      control.dispatchEvent(new Event('input', {bubbles:true}));
      counts.push(Number(document.querySelector('#summary').textContent.match(/^(\\d+) match filters/)[1]));
    }
    return counts;
  })()`), [20, 118, 1655, 1718]);
  assert.equal(await evaluate(`(() => {
    const duplicates = document.querySelector('#duplicates');
    const artwork = document.querySelector('#artwork');
    duplicates.value = '';
    duplicates.dispatchEvent(new Event('input', {bubbles:true}));
    artwork.value = 'review';
    artwork.dispatchEvent(new Event('input', {bubbles:true}));
    const count = Number(document.querySelector('#summary').textContent.match(/^(\\d+) match filters/)[1]);
    artwork.value = '';
    artwork.dispatchEvent(new Event('input', {bubbles:true}));
    duplicates.value = '';
    duplicates.dispatchEvent(new Event('input', {bubbles:true}));
    return count;
  })()`), 236);
  assert.deepEqual(await evaluate(`(() => {
    const duplicates = document.querySelector('#duplicates');
    const artwork = document.querySelector('#artwork');
    duplicates.value = '';
    duplicates.dispatchEvent(new Event('input', {bubbles:true}));
    const counts = [];
    for (const value of ['sequence', 'world']) {
      artwork.value = value;
      artwork.dispatchEvent(new Event('input', {bubbles:true}));
      counts.push(Number(document.querySelector('#summary').textContent.match(/^(\\d+) match filters/)[1]));
    }
    artwork.value = '';
    artwork.dispatchEvent(new Event('input', {bubbles:true}));
    duplicates.value = '';
    duplicates.dispatchEvent(new Event('input', {bubbles:true}));
    return counts;
  })()`), [173, 139]);
  assert.deepEqual(await evaluate(`(() => {
    const search = document.querySelector('#search');
    search.value = 'engine--icons--item338.bmp';
    search.dispatchEvent(new Event('input', {bubbles:true}));
    document.querySelector('.card [data-action="approve"]').click();
    return [document.querySelectorAll('.card').length, document.querySelector('.card').dataset.decision,
      JSON.parse(localStorage.getItem('openyamm-remaining-ui-art-review-v5'))['engine--icons--item338.bmp'].candidate_sha256
        === window.REMAINING_ART_CATALOG.items.find(item => item.id === 'engine--icons--item338.bmp').candidates[0].sha256];
  })()`), [1, 'approve', true]);

  assert.deepEqual(await evaluate(`(() => {
    document.querySelector('#search').value = '';
    document.querySelector('#search').dispatchEvent(new Event('input', {bubbles:true}));
    const category = document.querySelector('#category');
    category.value = 'UI backgrounds and loading images';
    category.dispatchEvent(new Event('input', {bubbles:true}));
    const first = document.querySelector('.card');
    first.querySelector('[data-action="flag"]').click();
    return [document.querySelector('#summary').textContent.includes('87 match filters'),
      first.querySelector('[data-action="approve"]').disabled,
      document.querySelector('.card').dataset.decision];
  })()`), [true, false, 'flag']);
  assert.deepEqual(await evaluate(`(() => {
    const RealBlob = window.Blob;
    const realClick = HTMLAnchorElement.prototype.click;
    window.Blob = class extends RealBlob {
      constructor(parts, options) { window.__exportText = String(parts[0]); super(parts, options); }
    };
    HTMLAnchorElement.prototype.click = function () {};
    document.querySelector('#download').click();
    window.Blob = RealBlob;
    HTMLAnchorElement.prototype.click = realClick;
    const exported = JSON.parse(window.__exportText);
    const ids = Object.keys(exported.decisions);
    localStorage.removeItem('openyamm-remaining-ui-art-review-v5');
    const input = document.querySelector('#import');
    const transfer = new DataTransfer();
    transfer.items.add(new File([window.__exportText], 'review.json', {type:'application/json'}));
    input.files = transfer.files;
    input.dispatchEvent(new Event('change', {bubbles:true}));
    return [exported.schema, exported.scope, ids.length >= 1541,
      exported.decisions['engine--icons--7item102.bmp']?.decision || 'unreviewed',
      exported.decisions['engine--icons--item338.bmp'].decision];
  })()`), [1, 'remaining_ui_art', true, 'approve', 'approve']);
  await new Promise(done => setTimeout(done, 250));
  assert.equal(await evaluate(`JSON.parse(localStorage.getItem('openyamm-remaining-ui-art-review-v5'))
    ['engine--icons--item338.bmp'].decision`), 'approve');
  await call('Page.navigate', {url: pathToFileURL(resolve(directory, 'index.html')).href + '?repairs=1'});
  await new Promise(done => setTimeout(done, 500));
  assert.deepEqual(await evaluate(`[
    document.querySelector('#artwork').value,
    document.querySelector('#duplicates').value,
    Number(document.querySelector('#summary').textContent.match(/^(\\d+) match filters/)[1])
  ]`), ['review', '', 236]);
  await call('Page.navigate', {url: pathToFileURL(resolve(directory, 'index.html')).href + '?effects=1'});
  await new Promise(done => setTimeout(done, 500));
  assert.deepEqual(await evaluate(`[
    document.querySelector('#duplicates').value,
    Number(document.querySelector('#summary').textContent.match(/^(\\d+) match filters/)[1]),
    [...document.querySelectorAll('.card')].every(card =>
      window.REMAINING_ART_ACCEPTANCE.pending_effect_ids.includes(card.dataset.id)
      && window.KEPT_EFFECT_ACCEPTANCE.decisions[card.dataset.id]?.decision === "approve")
  ]`), ['', 177, true]);
  await call('Page.navigate', {url: pathToFileURL(resolve(directory,
    'review_repairs/full_sequences/index.html')).href});
  await new Promise(done => setTimeout(done, 500));
  assert.deepEqual(await evaluate(`[
    document.querySelectorAll('section').length,
    Object.values(window.SEQUENCE_PREVIEW).every(frames => frames.length === 8),
    [...document.querySelectorAll('figure img.new')].every(img => img.naturalWidth > 0)
  ]`), [4, true, true]);
  assert.deepEqual(await evaluate(`(() => {
    const first = document.querySelector('section');
    first.querySelector('button').click();
    first.querySelector('.guide-toggle').click();
    const slider = first.querySelector('input');
    slider.value = '5';
    slider.dispatchEvent(new Event('input', {bubbles:true}));
    return [first.querySelector('.current').textContent,
      first.classList.contains('guide'),
      first.querySelector('img.new').getAttribute('src').includes('sp05e50')];
  })()`), ['5 / 8 · sp05e50', true, true]);
  await call('Page.navigate', {url: pathToFileURL(resolve(directory,
    'pc_effect_sequences/index.html')).href + '?sequence=sp96h&frame=12&pause=1'});
  await new Promise(done => setTimeout(done, 500));
  assert.deepEqual(await evaluate(`[
    window.PC_EFFECT_SEQUENCES.summary.sequences,
    window.PC_EFFECT_SEQUENCES.summary.frames,
    window.PC_EFFECT_SEQUENCES.summary.kept_approved_sequences,
    window.PC_EFFECT_SEQUENCES.summary.hud_pending_frames,
    document.querySelector('#title').textContent,
    document.querySelector('#current').textContent,
    document.querySelector('#candidate').naturalWidth > 0
  ]`), [22, 174, 4, 0, 'sp96h', '12 / 12 · sp96hl', true]);
  assert.deepEqual(await evaluate(`(() => {
    document.querySelector('[data-sequence="sp21a"]').click();
    const first = [document.querySelector('#current').textContent,
      document.querySelector('#candidate').getAttribute('src').includes(
        'remaining_sequences/locked/engine--icons--sp21a10')];
    document.querySelector('#next-frame').click();
    document.querySelector('#guide').click();
    return [...first, document.querySelector('#current').textContent,
      document.querySelector('#review-link').getAttribute('href').includes('sp21a20'),
      document.querySelector('#compare').classList.contains('guide')];
  })()`), ['1 / 8 · sp21a10', true, '2 / 8 · sp21a20', true, true]);
  assert.deepEqual(await evaluate(`(() => {
    document.querySelector('[data-sequence="sp109"]').click();
    const six = document.querySelectorAll('.thumb').length;
    const pinned = document.querySelector('#candidate').getAttribute('src').includes(
      'remaining_sequences/locked/engine--icons--sp109-01');
    document.querySelector('[data-sequence="sptext01"]').click();
    return [six, pinned, document.querySelectorAll('.thumb').length,
      document.querySelector('#current').textContent];
  })()`), [6, true, 4, '1 / 4 · sptext01a']);
  assert.deepEqual(await evaluate(`(() => {
    document.querySelector('[data-sequence="sp58e"]').click();
    const upperCenter = Number.parseFloat(document.querySelector('#candidate-art')
      .style.getPropertyValue('--guide-y'));
    document.querySelector('[data-sequence="sp96h"]').click();
    const curtainShape = document.querySelector('#candidate-art').dataset.guideShape;
    document.querySelector('[data-sequence="sp27a"]').click();
    const idle = [document.querySelector('#status').textContent,
      document.querySelector('#contact-link').getAttribute('href').endsWith('#sp27a')];
    document.querySelector('[data-sequence="sp05e"]').click();
    return [upperCenter < 30, curtainShape, ...idle, document.querySelector('#status').textContent,
      document.querySelector('#contact-link').hidden];
  })()`), [true, 'rect', 'Accepted · recorded in effect ledger', true,
    'Accepted · recorded in effect ledger', true]);
  await evaluate(`document.querySelector('[data-sequence="sp21a"]').click()`);
  await new Promise(done => setTimeout(done, 200));
  assert.deepEqual(await evaluate(`[
    document.querySelector('#native').naturalWidth,
    document.querySelector('#candidate').naturalWidth,
    document.querySelector('#review-link').getAttribute('href').includes('remaining_sequences/first_frame.html')
  ]`), [64, 128, true]);
  await call('Page.navigate', {url: pathToFileURL(resolve(directory,
    'review_repairs/remaining_sequences/first_frame.html')).href});
  await new Promise(done => setTimeout(done, 350));
  assert.deepEqual(await evaluate(`(() => {
    if (document.querySelector('#approve').getAttribute('aria-pressed') !== 'true')
      throw new Error('Supplemental effect acceptance did not load');
    document.querySelector('#approve').click();
    document.querySelector('#note').value = 'Kept for review';
    document.querySelector('#note').dispatchEvent(new Event('input', {bubbles:true}));
    const saved = JSON.parse(localStorage.getItem('openyamm-sp21a10-imagegen-v2'));
    return [document.querySelector('#native').naturalWidth,
      document.querySelector('#candidate').naturalWidth, saved.decision, saved.note,
      document.querySelector('#approve').getAttribute('aria-pressed')];
  })()`), [64, 128, 'approve', 'Kept for review', 'true']);
  await call('Page.navigate', {url: pathToFileURL(resolve(directory,
    'review_repairs/remaining_sequences/contacts/index.html')).href + '#sp27a'});
  await new Promise(done => setTimeout(done, 400));
  assert.deepEqual(await evaluate(`[
    document.querySelectorAll('section').length,
    document.querySelector('#sp27a img').naturalHeight,
    document.querySelector('#sp109 img').getAttribute('src')
  ]`), [18, 776, 'sp109.png']);
  assert.deepEqual(exceptions, []);
  console.log('Viewer smoke test passed: catalog, review controls, and effect sequence playback.');
} catch (error) {
  console.error(error);
  console.error(stderr.slice(-1200));
  process.exitCode = 1;
} finally {
  browser.kill();
}
