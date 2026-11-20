// Rasterize the approved gameplay CSS into reusable, content-free RGBA assets.
// No portraits, text, map tiles, counters or spell illustrations are baked here.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdir, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const study = resolve(here, '../hud_concepts_20260927');
const out = resolve(here, 'engine/icons_x2');
const port = 9399;
const delay = ms => new Promise(ok => setTimeout(ok, ms));
const browser = spawn(process.env.CHROME || 'google-chrome', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--allow-file-access-from-files', `--remote-debugging-port=${port}`, '--remote-allow-origins=*',
  '--window-size=1600,1000', `--user-data-dir=/tmp/openyamm-hud-handoff-${Date.now()}`, 'about:blank',
], {stdio: 'ignore'});
const exports = [], checks = [], errors = [];
let ws;
try {
  await mkdir(out, {recursive: true});
  await mkdir(resolve(here, 'previews'), {recursive: true});
  let page;
  for (let i = 0; i < 100 && !page; ++i) {
    try { page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p => p.type === 'page'); }
    catch {}
    if (!page) await delay(100);
  }
  assert.ok(page, 'Chrome startup');
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((ok, fail) => {ws.onopen = ok; ws.onerror = fail;});
  let serial = 0;
  const pending = new Map();
  ws.onmessage = event => {
    const m = JSON.parse(event.data), p = pending.get(m.id);
    if (p) {pending.delete(m.id); m.error ? p.reject(m.error) : p.resolve(m.result);}
    if (m.method === 'Runtime.exceptionThrown') errors.push(m.params);
    if (m.method === 'Network.loadingFailed' && m.params.errorText !== 'net::ERR_ABORTED') errors.push(m.params);
  };
  const send = (method, params = {}) => new Promise((ok, fail) => {
    const id = ++serial; pending.set(id, {resolve:ok, reject:fail}); ws.send(JSON.stringify({id, method, params}));
  });
  const evaluate = async expression => {
    const r = await send('Runtime.evaluate', {expression, returnByValue:true, awaitPromise:true});
    assert.ok(!r.exceptionDetails, JSON.stringify(r.exceptionDetails)); return r.result.value;
  };
  await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride', {width:1600,height:1000,deviceScaleFactor:1,mobile:false});
  await send('Emulation.setDefaultBackgroundColorOverride', {color:{r:0,g:0,b:0,a:0}});
  await send('Page.navigate', {url:pathToFileURL(resolve(study,'index.html')).href +
    '?export=1&concept=obsidian&party=5&buffs=22&buffArt=clean&bars=shaded'});
  let ready = false;
  for (let i=0;i<100&&!ready;++i) {
    try {ready = await evaluate(`(async()=>{
      if(document.readyState!=='complete'||!document.querySelector('.pc'))return false;
      await document.fonts.ready;return [...document.images].every(i=>i.complete&&i.naturalWidth>0);
    })()`);} catch {}
    if (!ready) await delay(100);
  }
  assert.ok(ready, 'Approved HUD and glyph-free art loaded');
  const inject = css => evaluate(`(()=>{const s=document.createElement('style');s.textContent=${JSON.stringify(css)};
    document.head.append(s);})()`);
  await inject(`html,body,main,.stage-host,#stage{margin:0!important;padding:0!important;border:0!important;
    background:transparent!important;box-shadow:none!important;overflow:visible!important}
    #stage{transform:none!important;position:relative!important;left:0!important;top:0!important}
    *,*:before,*:after{animation:none!important;transition:none!important}`);

  // Check bounded buffs and all party counts on the approved 16:9 composition.
  for (const count of [1,2,3,4,5]) {
    for (const effects of [0,4,12,22]) {
      const result = await evaluate(`(()=>{partyCount=${count};buffCount=${effects};render();
        const chips=[...document.querySelectorAll('.buff-chip')],more=document.querySelector('.buff-more');
        return {portraits:document.querySelectorAll('.pc-slot').length,chips:chips.length,
          more:more?.querySelector('strong')?.textContent||'',glyphs:chips.every(c=>!!c.querySelector('.buff-art'))};})()`);
      assert.equal(result.portraits,count); assert.equal(result.chips,Math.min(effects,4));
      assert.equal(result.more,effects>4?`+${effects-4}`:''); assert.ok(result.glyphs);
      checks.push({party:count,buffs:effects,...result});
    }
  }
  for (const state of ['explore','nearby','combat']) {
    await evaluate(`partyCount=5;buffCount=22;sceneState=${JSON.stringify(state)};statusPreview='long';render()`);
    const shot=await send('Page.captureScreenshot',{format:'png',clip:{x:0,y:0,width:1600,height:900,scale:1}});
    await writeFile(resolve(here,`previews/hud-${state}.png`),Buffer.from(shot.data,'base64'));
  }
  // Geometry is measured in review pixels; engine units use 480px reference height.
  const geometry=await evaluate(`(()=>{const selectors=['.resources','.party','.pc','.portrait-frame',
    '.pc-name','.pc-state','.vitals','.readiness','.personal-buff','.commands','.command','.buffs',
    '.buff-chip','.buff-more','.minimap','.map-viewport','.map-label','.map-controls button',
    '.followers-button','.status-message'];return Object.fromEntries(selectors.map(s=>[s,
      [...document.querySelectorAll(s)].map(e=>{const r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height];})]));})()`);
  await writeFile(resolve(here,'hud_geometry.json'),JSON.stringify(geometry,null,2)+'\n');

  const capture = async (name, markup, css, width, height, padding=0, note='') => {
    await evaluate(`document.querySelector('#stage').innerHTML=${JSON.stringify(markup)}`);
    await evaluate(`document.getElementById('component-export-style')?.remove()`);
    const rules = `#stage :has(#asset){position:static!important;transform:none!important;visibility:hidden!important}
      #asset{visibility:visible!important;position:absolute!important;left:${padding}px!important;top:${padding}px!important;
      right:auto!important;bottom:auto!important;transform:none!important;margin:0!important;
      width:${width}px!important;min-width:0!important;height:${height}px!important;min-height:0!important}
      ${css}`;
    await evaluate(`(()=>{const s=document.createElement('style');s.id='component-export-style';
      s.textContent=${JSON.stringify(rules)};document.head.append(s);})()`);
    const r={x:0,y:0,width:width+2*padding,height:height+2*padding,scale:16/15};
    const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,
      clip:{...r,width:Math.ceil(r.width),height:Math.ceil(r.height)}});
    const file=`engine/icons_x2/obsidian_hud_${name}.png`;
    await writeFile(resolve(here,file),Buffer.from(shot.data,'base64'));
    exports.push({file,review_size:[r.width,r.height],logical_size:[r.width/1.875,r.height/1.875],
      content_rect:[padding/1.875,padding/1.875,width/1.875,height/1.875],
      pixels_per_logical_unit:2,source:'hud_concepts_20260927/style.css (approved Obsidian r04)',note});
  };
  for (const state of ['normal','selected'])
    await capture(`portrait_rim_${state}`,`<div class="pc ${state}"><div id="asset" class="portrait-frame"></div></div>`,
      '#asset{background:transparent!important}',81,109,18,'Transparent centre; layer above the live portrait.');
  await capture('portrait_mask','<div id="asset"></div>',
    '#asset{border-radius:47%;background:white}',81,109,0,'Alpha mask only; never render as a white icon.');
  await capture('selection_diamond','<div class="pc selected"><span id="asset" class="selection-mark"></span></div>',
    '#asset{transform:rotate(45deg)!important}',12,12,14);
  await capture('meter_track','<div class="pc"><span id="asset" class="meter"></span></div>','',103,7,1);
  for(const [kind,classes] of [['hp',''],['hp_injured','injured'],['hp_critical','critical'],['sp','']])
    await capture(`meter_${kind}`,`<div class="pc ${classes}"><span class="meter ${kind==='sp'?'sp':'hp'}">
      <i id="asset" class="fill"></i></span></div>`, '#asset{--fill:100%;width:103px!important}',103,7);
  await capture('resource_plate','<div id="asset" class="resources panel"></div>','',267,43,10,
    'Counters and the two original resource illustrations remain live; widen centre only if needed.');
  await capture('command_plate','<div id="asset" class="commands panel"></div>','',284,68,10);
  await capture('command_hover','<button id="asset" class="command"></button>',
    '#asset{background:#ccba8024}',68,59);
  for(const kind of ['normal','expiring','hover'])
    await capture(`buff_${kind}`,`<button id="asset" class="buff-chip ${kind}"></button>`,
      kind==='hover'?'#asset{background:#2a302cf2;border-color:#cab485ad}':'',48,57);
  await capture('buff_overflow','<button id="asset" class="buff-more"></button>','',48,57);
  await capture('popup_plate','<section id="asset" class="preview-popover buff-overflow-popup"></section>',
    '#asset{display:block!important}',360,180,12,
    'Nine-slice cap 14 review px incl. padding; body is flat. Render text separately.');
  for(const state of ['normal','hover']) {
    await capture(`followers_${state}`,'<button id="asset" class="followers-button"></button>',
      state==='hover'?'#asset{background:#272a24}':'',193,33,6);
    await capture(`turn_${state}`,'<button id="asset" class="turn-dock"></button>',
      state==='hover'?'#asset{background:#272a24}':'',130,62,6);
    await capture(`zoom_${state}`,'<div class="map-controls"><button id="asset"></button></div>',
      `#asset{border-radius:100%;background:${state==='hover'?'#272a24':'#0c141a'}}`,24,24,2);
  }
  await capture('minimap_rim','<div id="asset" class="map-viewport"></div>',
    '#asset{background:transparent!important}',204,204,32,'Transparent circular centre; fixed aspect, no stretching.');
  await capture('minimap_mask','<div id="asset"></div>',
    '#asset{border-radius:100%;background:white}',200,200,0,'Alpha clip for the native live minimap.');
  await capture('status_plate','<div id="asset" class="status-message"> </div>',
    '#asset{display:block!important;max-width:none;max-height:none}',620,48,6,
    'Keep horizontal fade caps; grow the middle, do not stretch its border. Height is runtime text dependent.');
  await capture('ambient_shade','<div id="asset" class="ambient-shade"></div>','',8,900,0,
    'Stretch only horizontally; vertical normalized gradient follows viewport height.');

  const fullscreen = resolve(here,'../hud_overlay_study_20260927/index.html');
  for (const status of ['short','long','bank','withdraw','password']) {
    await send('Page.navigate',{url:pathToFileURL(fullscreen).href+
      `?screen=2060&treatment=carved&party=1&buttons=fondamento&export=1&status=${status}`});
    let complete=false;
    for(let i=0;i<100&&!complete;++i) {
      try {complete=await evaluate(`(async()=>{if(document.readyState!=='complete'||
        !document.querySelector('.dock-status'))return false;await document.fonts.ready;
        return [...document.images].every(i=>i.complete&&i.naturalWidth>0);})()`);}catch{}
      if(!complete)await delay(100);
    }
    assert.ok(complete,'Fullscreen status page loaded');
    await inject('#stage{transform:none!important}');
    await delay(120);
    const b=await evaluate(`(()=>{const e=document.querySelector('.dock-status'),r=e.getBoundingClientRect();
      return {status:${JSON.stringify(status)},width:r.width,height:r.height,
        scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,input:!!e.querySelector('input')};})()`);
    assert.ok(b.scrollWidth<=b.clientWidth,`Status text fits: ${status}`);checks.push(b);
    const r=await evaluate(`(()=>{const r=document.querySelector('#stage').getBoundingClientRect();
      return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1};})()`);
    const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:r});
    await writeFile(resolve(here,`previews/fullscreen-${status}.png`),Buffer.from(shot.data,'base64'));
  }
  await inject(`html,body,main,.stage-host,#stage{margin:0!important;padding:0!important;border:0!important;
    background:transparent!important;box-shadow:none!important;overflow:visible!important}
    #stage{transform:none!important;position:relative!important;left:0!important;top:0!important}`);
  const basebarMarkup=await evaluate(`carvedBasebar()`);
  await capture('fullscreen_basebar',`<div id="asset" class="bottom-dock">${basebarMarkup}</div>`,
    '',1200,213.75,0,'640x114 logical. Revised blank status rail 22.4 logical high; original body/right art retained.');
  for(const selected of [false,true])
    await capture(`fullscreen_rim_${selected?'selected':'normal'}`,
      `<button class="person" aria-pressed="${selected}"><span id="asset" class="portrait-ring"></span></button>`,
      '#asset{background:transparent!important}',85,113,18,'Fullscreen live portrait rim; true-alpha centre.');

  // Review the consolidated browser with the final overlay layered over the shared basebar.
  // The nested documents are local and intentionally share an origin for this review.
  const reviewChecks=[];
  await send('Page.navigate',{url:pathToFileURL(resolve(here,'index.html')).href});
  const waitFor = async expression => {
    for(let i=0;i<150;++i){try{if(await evaluate(expression))return;}catch{}await delay(80);}
    assert.fail('Review condition did not settle: '+expression);
  };
  await waitFor(`document.readyState==='complete'&&!!document.querySelector('#viewer')`);
  for(const [view,status] of [['inventory','short'],['inventory','long'],['inventory','bank'],
    ['inventory','withdraw'],['dialogue','password']]) {
    await evaluate(`document.querySelector('#status').value=${JSON.stringify(status)};
      document.querySelector('[data-view="${view}"]').click()`);
    await waitFor(`(()=>{const outer=document.querySelector('#viewer'),d=outer.contentDocument;
      if(!d||d.readyState!=='complete'||!d.querySelector('#base-frame'))return false;
      const inner=d.querySelector('#base-frame'),b=inner.contentDocument;
      return inner.src.includes('status=${status}')&&b?.readyState==='complete'&&
        !!b.querySelector('.dock-status')&&b.fonts.status==='loaded'&&d.fonts.status==='loaded'&&
        [...d.images,...b.images].every(i=>i.complete&&i.naturalWidth>0);})()`);
    await delay(100);
    const result=await evaluate(`(()=>{const d=document.querySelector('#viewer').contentDocument,
      b=d.querySelector('#base-frame').contentDocument,s=b.querySelector('.dock-status'),i=s.querySelector('input');
      if(i){i.focus();i.value=${JSON.stringify(status==='password'?'JBARD':'1234567890')};i.dispatchEvent(new Event('input',{bubbles:true}));}
      return {view:${JSON.stringify(view)},status:${JSON.stringify(status)},text:s.textContent,
        inputValue:i?.value||null,overflow:s.scrollWidth>s.clientWidth};})()`);
    assert.ok(!result.overflow); if(['bank','withdraw','password'].includes(status))assert.ok(result.inputValue);
    reviewChecks.push(result);
    const clip=await evaluate(`(()=>{const r=document.querySelector('#viewer').getBoundingClientRect();
      return {x:r.x,y:r.y,width:r.width,height:r.height,scale:1};})()`);
    const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip});
    await writeFile(resolve(here,`previews/${view}-${status}.png`),Buffer.from(shot.data,'base64'));
  }
  await evaluate(`document.querySelector('[data-view="journal"]').click()`);
  await waitFor(`(()=>{const d=document.querySelector('#viewer').contentDocument;
    return d?.readyState==='complete'&&!!d.querySelector('#text-viewport')&&d.fonts.status==='loaded';})()`);
  reviewChecks.push({view:'journal',loaded:true});
  await evaluate(`document.querySelector('[data-view="assets"]').click()`);
  await waitFor(`document.querySelectorAll('#gallery img').length>=150`);
  await evaluate(`document.querySelectorAll('#gallery img').forEach(i=>i.loading='eager')`);
  await waitFor(`[...document.querySelectorAll('#gallery img')].every(i=>i.complete&&i.naturalWidth>0)`);
  reviewChecks.push({view:'assets',count:await evaluate(`document.querySelectorAll('#gallery img').length`)});
  await writeFile(resolve(here,'browser_review.json'),JSON.stringify({result:'PASS',checks:reviewChecks,errors},null,2)+'\n');
  assert.equal(errors.length,0,JSON.stringify(errors));
  await writeFile(resolve(here,'hud_exports.json'),JSON.stringify({exports,checks,errors},null,2)+'\n');
  console.log(`Exported ${exports.length} HUD pieces, ${checks.length} source cases, ${reviewChecks.length} handoff cases.`);
} finally {ws?.close();browser.kill('SIGTERM');}
