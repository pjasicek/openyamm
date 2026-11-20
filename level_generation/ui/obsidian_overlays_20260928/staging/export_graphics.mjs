// Export the approved HTML/CSS/SVG treatments, with all fixture content excluded.
// Run from any directory with Node 22+ and a local Chrome installation.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const study = resolve(here, '..');
const out = resolve(here, 'engine/icons_x2');
const port = 9397;
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const browser = spawn(process.env.CHROME || 'google-chrome', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--allow-file-access-from-files', `--remote-debugging-port=${port}`, '--remote-allow-origins=*',
  '--window-size=1600,900', `--user-data-dir=/tmp/openyamm-obsidian-export-${Date.now()}`, 'about:blank',
], {stdio: 'ignore'});
let ws;
const exports = [], geometry = {}, errors = [];
try {
  await mkdir(out, {recursive: true});
  let page;
  for (let i = 0; i < 100; ++i) {
    try { page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p => p.type === 'page'); }
    catch {}
    if (page) break;
    await delay(100);
  }
  assert.ok(page, 'Chrome must start');
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((ok, fail) => { ws.onopen = ok; ws.onerror = fail; });
  let serial = 0;
  const pending = new Map();
  ws.onmessage = event => {
    const message = JSON.parse(event.data), request = pending.get(message.id);
    if (request) {
      pending.delete(message.id);
      message.error ? request.reject(message.error) : request.resolve(message.result);
    }
    if (message.method === 'Runtime.exceptionThrown') errors.push(message.params);
    if (message.method === 'Network.loadingFailed' && message.params.errorText !== 'net::ERR_ABORTED')
      errors.push(message.params);
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++serial; pending.set(id, {resolve, reject}); ws.send(JSON.stringify({id, method, params}));
  });
  const evaluate = async expression => {
    const result = await send('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
    assert.ok(!result.exceptionDetails, JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride', {width:1600, height:900, deviceScaleFactor:1, mobile:false});
  await send('Emulation.setDefaultBackgroundColorOverride', {color:{r:0,g:0,b:0,a:0}});
  const navigate = async (file, query = '') => {
    await send('Page.navigate', {url: pathToFileURL(file).href + query});
    let ready = false;
    for (let i = 0; i < 100; ++i) {
      try {
        ready = await evaluate(`(async () => {
          if (document.readyState !== 'complete' || !document.querySelector('#stage')) return false;
          await document.fonts.ready;
          const child = document.querySelector('#base-frame');
          if (child && !child.hidden && child.contentDocument?.readyState !== 'complete') return false;
          return [...document.images].every(i => i.complete && i.naturalWidth > 0);
        })()`);
      } catch {}
      if (ready) break;
      await delay(80);
    }
    assert.ok(ready, `Page ready: ${file}`);
    await evaluate(`document.querySelector('#stage').style.transform = 'none'`);
    await delay(200);
  };
  const inject = css => evaluate(`(() => { const s=document.createElement('style'); s.textContent=${JSON.stringify(css)};document.head.append(s); })()`);
  const rect = (selector, index = 0) => evaluate(`(() => {
    const r=document.querySelectorAll(${JSON.stringify(selector)})[${index}].getBoundingClientRect();
    return {x:r.x,y:r.y,width:r.width,height:r.height}; })()`);
  const capture = async (name, r, source, scale = 16/15) => {
    const result = await send('Page.captureScreenshot', {format:'png', captureBeyondViewport:true,
      clip:{...r, width:Math.ceil(r.width), height:Math.ceil(r.height), scale}, fromSurface:true});
    await writeFile(resolve(out, name + '.png'), Buffer.from(result.data, 'base64'));
    exports.push({file:`engine/icons_x2/${name}.png`, method:'approved-browser-rasterization', source,
      review_rect:r, logical_size:[r.width/1.875,r.height/1.875], pixels_per_logical_unit:scale*1.875,
      pixel_size:[Math.round(r.width*scale),Math.round(r.height*scale)]});
  };
  const saveGeometry = async (screen, selector) => {
    geometry[screen] = await evaluate(`(() => {
      return [...document.querySelectorAll(${JSON.stringify(selector)})].map(e => {
        const r=e.getBoundingClientRect(), s=getComputedStyle(e);
        return {id:e.id,tag:e.tagName,classes:e.className,dataset:{...e.dataset},
          text:e.textContent.trim(),review_rect:[r.x,r.y,r.width,r.height],
          logical_rect:[(r.x-200)/1.875,r.y/1.875,r.width/1.875,r.height/1.875],
          font:s.fontFamily,font_size:parseFloat(s.fontSize)/1.875,line_height:s.lineHeight};
      }); })()`);
  };
  // Fixed backgrounds retain section lines; names, values, items and controls remain live content.
  for (const screen of ['inventory','stats','skills','awards','rest','quickref']) {
    await navigate(resolve(study,'index.html'), `?export=1&screen=${screen}&party=5`);
    await saveGeometry(screen, '#screen-layer section, #screen-layer h2, #screen-layer h3, .stat-group, .stat-row, .stat-row > span, .skill-points, .skill-row, .skill-level, .character-nav button, .inventory-grid, .rest-page *, .quick-table tr, .quick-table tr > *, .quick-footer');
    await inject(`.page-surface{width:877.5px;height:648.75px;top:45px}
      .inventory-grid{top:15px}
      .skill-group h3{border-bottom-color:transparent!important}
      #screen-layer,#screen-layer *{color:transparent!important;text-shadow:none!important}
      #screen-layer img,#screen-layer svg,#screen-layer .obs-button{visibility:hidden!important}`);
    await capture(`obsidian_${screen}_surface`, await rect(screen === 'rest' || screen === 'quickref' ? '.full-page' : '.page-surface'),
      [`../style.css`, `../app.js`, '../../hud_overlay_study_20260927/assets/material-evt.png']);
  }
  // A large material master is sampled at a fixed world/UI scale; never stretch it to window bounds.
  await navigate(resolve(study,'index.html'), '?export=1&screen=materials');
  await evaluate(`document.querySelector('#stage').innerHTML='<div id="texture-export"></div>'`);
  await inject(`html,body,main,.stage-host,.stage{background:transparent!important;border:0;box-shadow:none}
    #texture-export{position:absolute;left:0;top:0;width:1200px;height:900px;
      background:linear-gradient(#111b12d9,#111b12e8),var(--stone) 0 0/550px auto}`);
  await capture('obsidian_reading_surface', await rect('#texture-export'), ['../style.css', '../../hud_overlay_study_20260927/assets/material-evt.png']);
  await evaluate(`document.querySelector('#stage').innerHTML='<div id="value-rule"></div>'`);
  await inject(`#value-rule{position:absolute;left:0;top:0;width:450px;height:1px;background:#bda27265}`);
  await capture('obsidian_value_divider', await rect('#value-rule'), ['../style.css']);

  // Plates are label-free; font and state text colours are in design/theme.yml.
  for (const [variant,w,h] of [['tab',75,26],['rest',272,42],['wait',188,30],['rest_exit',185,43],['quick_exit',155/1.875,53/1.875],['close',194/1.875,48/1.875]]) {
    for (const state of ['normal','hover','pressed','selected','disabled']) {
      await evaluate(`document.querySelector('#stage').innerHTML='<button id="plate" class="obs-button" ${state==='disabled'?'disabled':''} data-demo-state="${state}"></button>'`);
      await inject(`#plate{position:absolute;left:20px;top:20px;width:${w*1.875}px;height:${h*1.875}px;min-height:0;transition:none}`);
      await capture(`obsidian_button_${variant}_${state}`, await rect('#plate'), ['../../hud_overlay_study_20260927/button-theme.css']);
    }
  }
  // Keep the approved illustration masks; do not regenerate the spellbook or include its lettering.
  const buffData = JSON.parse(await readFile(resolve(study,'buff_art.json'),'utf8'));
  for (const name of Object.keys(buffData)) {
    await evaluate(`document.querySelector('#stage').innerHTML=glyphFreeBuff(${JSON.stringify(name)})`);
    await inject(`.buff-art{position:absolute;left:0;top:0;width:128px;height:128px}`);
    await delay(30);
    await capture(`obsidian_buff_${name}`, {x:0,y:0,width:128,height:128},
      ['../buff_art.json',`../assets/spells/${name}.png`], 1);
    Object.assign(exports.at(-1), {logical_size:[19.2,19.2], pixels_per_logical_unit:128/19.2,
      note:'Uniform 128px transparent master. HUD box 19.2 logical; catalogue box 23.466667 logical. Preserve aspect.'});
  }

  // Shared full-screen frame: export approved artwork after its deliberate three-part fitting and colour treatment.
  await navigate(resolve(study,'../hud_overlay_study_20260927/index.html'), '?export=1&screen=2060&treatment=carved&party=1');
  await saveGeometry('fullscreen_baseline', '.bottom-dock,.topbar,.person,.portrait-ring,.meter,.personal-buff,.empty-slot,.status-text');
  await inject(`.topbar>*{visibility:hidden!important}.bottom-dock>*:not(.basebar-art){visibility:hidden!important}
    .topbar{height:54.375px!important}.bottom-dock{height:213.75px!important;top:686.25px!important}`);
  await capture('obsidian_topbar', await rect('.topbar'), ['../../hud_overlay_study_20260927/style.css','../../hud_overlay_study_20260927/assets/generated/carved-obsidian-basebar-v2.png']);
  await capture('obsidian_basebar', await rect('.bottom-dock'), ['../../hud_overlay_study_20260927/style.css','../../hud_overlay_study_20260927/app.js','../../hud_overlay_study_20260927/assets/generated/carved-obsidian-basebar-v2.png']);
  await navigate(resolve(study,'../hud_overlay_study_20260927/index.html'), '?export=1&screen=2061&treatment=carved');
  await inject(`.dialogue-panel>*{visibility:hidden!important}.dialogue-panel{width:322.5px!important;height:690px!important}
    .video-left-frame{width:15px!important;height:650.625px!important}`);
  await capture('obsidian_house_sidebar', await rect('.dialogue-panel'), ['../../hud_overlay_study_20260927/style.css','../../hud_overlay_study_20260927/assets/generated/carved-obsidian-sidebar-v1.png']);
  await capture('obsidian_left_edge', await rect('.video-left-frame'), ['../../hud_overlay_study_20260927/style.css','../../hud_overlay_study_20260927/assets/generated/carved-obsidian-sidebar-v1.png']);
  // The selected gameplay HUD's plain shaded diamond: no checkmark or exclamation mark.
  await navigate(resolve(study,'../hud_concepts_20260927/index.html'), '?export=1');
  await inject(`html,body,main,.stage-host,.stage{background:transparent!important;border:0;box-shadow:none;overflow:visible}
    .alert-sigil{position:absolute;left:8px;top:8px;width:22px;height:25px}`);
  for (const kind of ['explore','nearby','combat','unlit']) {
    await evaluate(`document.querySelector('#stage').innerHTML=alertSigil(${JSON.stringify(kind)})`);
    await capture(`obsidian_aggro_${kind}`, {x:0,y:0,width:38,height:41},
      ['../../hud_concepts_20260927/app.js','../../hud_concepts_20260927/style.css'], 2);
    Object.assign(exports.at(-1), {logical_size:[38/1.875,41/1.875], pixels_per_logical_unit:3.75,
      content_rect_review:[8,8,22,25],note:'Includes eight review-pixel shadow padding. Visible diamond 22×25 review pixels.'});
  }
  assert.equal(errors.length,0,JSON.stringify(errors));
  await writeFile(resolve(here,'browser_exports.json'),JSON.stringify({revision:'03',exports,errors},null,2)+'\n');
  await writeFile(resolve(here,'review_geometry.json'),JSON.stringify(geometry,null,2)+'\n');
  console.log(`Exported ${exports.length} content-free PNGs; no browser errors.`);
} finally { ws?.close(); browser.kill('SIGTERM'); }
