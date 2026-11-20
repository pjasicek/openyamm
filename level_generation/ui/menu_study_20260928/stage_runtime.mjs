// Export the approved browser geometry and blank UI surfaces. Does not install assets into the game.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdir, writeFile, readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {parseArgs} from 'node:util';

const root = fileURLToPath(new URL('.', import.meta.url));
const {values} = parseArgs({options:{output:{type:'string'}}});
const stage = `${resolve(values.output ?? `${root}runtime_stage`)}/`;
const art = `${stage}engine/icons_x2/`;
const port = 9393;
await mkdir(art, {recursive:true});
await mkdir(`${stage}source`, {recursive:true});
const browser = spawn('google-chrome', ['--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--disable-background-networking', `--remote-debugging-port=${port}`, '--remote-allow-origins=*',
  `--user-data-dir=/tmp/openyamm-menu-staging-${Date.now()}`, 'about:blank'], {stdio:'ignore'});
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
let ws, serial = 0;
const errors = [];
try {
  let page;
  for (let attempt=0;attempt<100;attempt++) {
    try {page=(await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(item=>item.type==='page');} catch {}
    if(page)break;await delay(100);
  }
  assert.ok(page, 'Chrome starts');
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  const pending = new Map();
  ws.onmessage = event => {
    const message = JSON.parse(event.data), call = pending.get(message.id);
    if(call){pending.delete(message.id);message.error?call.reject(message.error):call.resolve(message.result);}
    if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails);
  };
  const send = (method,params={}) => new Promise((resolve,reject)=>{
    const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));
  });
  const evaluate = async expression => {
    const result=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    assert.ok(!result.exceptionDetails,JSON.stringify(result.exceptionDetails));return result.result.value;
  };
  await send('Page.enable');await send('Runtime.enable');await send('DOM.enable');await send('CSS.enable');
  const viewport={width:1600,height:900};
  await send('Emulation.setDeviceMetricsOverride',{...viewport,deviceScaleFactor:1,mobile:false});
  await send('Emulation.setDefaultBackgroundColorOverride',{color:{r:0,g:0,b:0,a:0}});
  const navigate = async screen => {
    const loaded = new URL(`index.html?export=1&screen=${screen}`, import.meta.url).href;
    await send('Page.navigate',{url:loaded});
    for(let attempt=0;attempt<100;attempt++){
      if(await evaluate(`document.body?.dataset.ready==='true' && document.querySelector('#review-screen')?.value===${JSON.stringify(screen)}`))break;
      await delay(60);
    }
    await evaluate('document.fonts.ready');
    await evaluate(`Promise.all([...document.images].filter(img=>img.closest('#screen')).map(img=>img.decode()))`);
    await delay(100);
  };
  const selectors = {
    frame:'.frame', head:'.frame-head', body:'.frame-body', footer:'.frame-footer',
    brand:'.brand', seal:'.seal', wordmark:'.brand-name', subtitle:'.brand-subtitle',
    h1:'#screen h1', h2:'#screen h2', h3:'#screen h3', eyebrow:'.eyebrow', fineprint:'.fineprint',
    actions:'.button', titlePanel:'.title-actions', titleFooter:'.title-footer', continueInfo:'.continue-info',
    pausePanel:'.pause-panel', ornament:'.ornament', saveList:'.save-list', saveRows:'.save-row',
    saveNames:'.save-row strong', saveLocations:'.save-row small', saveTags:'.save-row .tag',
    saveDetail:'.save-detail', savePreview:'.save-preview', saveMetaLabels:'.save-meta dt',
    saveMetaValues:'.save-meta dd', saveName:'.save-name input', saveNameLabel:'.save-name',
    nav:'.settings-nav', tabs:'.nav-tab', settingScroll:'.setting-scroll', contentTitle:'.content-title',
    groups:'.group-title', settings:'.setting', settingNames:'.setting-name', settingDescriptions:'.setting-desc',
    controls:'.setting-control', toggles:'.toggle', selects:'#screen select', ranges:'input[type=range]', outputs:'output',
    fields:'input[type=text],input[type=search]', bindingsFilter:'.bindings-filter', bindingHead:'.binding-head',
    bindingRows:'.binding-row', bindingNames:'.binding-name', bindingKeys:'.key',
    worlds:'.world-card', worldImages:'.world-card > img', worldTags:'.world-card .tag',
    identity:'.identity-column', portrait:'.identity-portrait', identityFields:'.identity-column .field',
    voice:'.voice-row span', stats:'.stats-column', statsHead:'.attribute-head', pool:'.pool', statRows:'.stat-row',
    statNames:'.stat-row > span', statValues:'.stat-row > b', skills:'.skills-column',
    assigned:'.assigned-skill', skillsTitles:'.skills-title', skillGrid:'.skills-grid', skillChoices:'.skill-choice',
    appearance:'.appearance', doll:'.doll', roster:'.party-roster', partySlots:'.party-slot', partySummary:'.party-summary',
    creationNote:'#creation-note', footerNote:'.footer-note', credits:'.credits', creditSections:'.credits section',
    creditHeadings:'.credits h2', creditParagraphs:'.credits p', creditLinks:'.credits a',
    stepNote:'.step-note', settingSubtitle:'.content-title p', skillCounts:'.skills-title > span',
    modal:'.modal', modalTitle:'.modal h2', modalBody:'.modal p', modalActions:'.modal .button',
  };
  const geometry = {};
  for(const screen of ['main','pause','load','save','worlds','creation','gameplay','video','audio','controls','keyboard','credits','confirmation']) {
    await navigate(screen==='confirmation'?'main':screen);
    if(screen==='confirmation') await evaluate(`document.querySelector('[data-action="quit"]').click()`);
    geometry[screen] = await evaluate(`(()=>{
      const selectors=${JSON.stringify(selectors)}; const result={};
      for(const [key,selector] of Object.entries(selectors)) result[key]=[...document.querySelectorAll(selector)].map(element=>{
        const r=element.getBoundingClientRect(), c=getComputedStyle(element);
        return {rect:[r.x,r.y,r.width,r.height].map(value=>Math.round(value*1000)/1000),
          text:element.textContent.trim(),font:c.fontFamily,fontSize:parseFloat(c.fontSize),color:c.color,
          align:c.textAlign,lineHeight:c.lineHeight,padding:[c.paddingTop,c.paddingRight,c.paddingBottom,c.paddingLeft],
          id:element.id,tag:element.tagName,classes:element.className.baseVal??element.className,
          data:{...element.dataset},src:element.getAttribute('src'),value:element.value,
          scroll:[element.scrollWidth,element.scrollHeight,element.clientWidth,element.clientHeight]};
      });return result;
    })()`);
  }
  const catalog = await evaluate('({sections:MENU_DATA.sections,settings:MENU_DATA.settings,bindings:MENU_DATA.bindings,fixedBindings:MENU_DATA.fixedBindings,worlds:MENU_DATA.worlds.map(({text,...world})=>world),stats:MENU_DATA.stats})');
  await writeFile(`${stage}source/seal.svg`,await evaluate(`document.querySelector('.title-brand .seal').outerHTML.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" style="fill:none;stroke:#cbb47f;stroke-width:1.2" ')`)+'\n');
  await writeFile(`${stage}source/geometry.json`,JSON.stringify(geometry,null,2)+'\n');
  await writeFile(`${stage}source/catalog.json`,JSON.stringify(catalog,null,2)+'\n');

  // Each export keeps the original CSS material/state. Only text and unrelated elements are hidden.
  const surfaces = [];
  async function surface(name,screen,selector,{width,height,pad=0,states=['default'],descendants=false,kind='surface',insets=null,setup=''}={}) {
    await navigate(screen);
    if(setup)await evaluate(setup);
    const original = await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e)throw Error('Missing export target: '+${JSON.stringify(selector)});return {style:e.getAttribute('style'),disabled:e.disabled};})()`);
    const documentNode = await send('DOM.getDocument');
    const {nodeId} = await send('DOM.querySelector',{nodeId:documentNode.root.nodeId,selector});
    for(const state of states) {
      await evaluate(`(()=>{
        document.activeElement?.blur();const e=document.querySelector(${JSON.stringify(selector)});
        e.dataset.exportTarget='true';${width?`e.style.width='${width}px';e.style.minWidth='${width}px';e.style.maxWidth='${width}px';`:''}
        ${height?`e.style.height='${height}px';e.style.minHeight='${height}px';e.style.maxHeight='${height}px';`:''}
        e.style.flexShrink='0'; if('disabled' in e)e.disabled=${state==='disabled'};
        const style=document.createElement('style');style.id='export-mask';style.textContent=
          'html,body {background:transparent!important} body * {visibility:hidden!important} '+
          '[data-export-target], [data-export-target]::before, [data-export-target]::after {visibility:visible!important;transition:none!important;outline:none!important} '+
          ${JSON.stringify(descendants?'[data-export-target] * {visibility:visible!important}':'[data-export-target] {color:transparent!important;text-shadow:none!important} [data-export-target]::placeholder {color:transparent!important}')};
        document.head.append(style);
      })()`);
      await send('CSS.forcePseudoState',{nodeId,forcedPseudoClasses:state==='hover'?['hover']:state==='pressed'?['hover','active']:[]});
      // Keep percentage-width surfaces at their measured dimensions during capture.
      const r = await evaluate(`(()=>{
        const e=document.querySelector(${JSON.stringify(selector)}),r=e.getBoundingClientRect();
        e.style.width=r.width+'px';e.style.height=r.height+'px';
        return [r.x,r.y,r.width,r.height];
      })()`);
      // Round the outer endpoints so a fractional origin cannot clip the bottom/right border.
      const x=Math.max(0,Math.floor(r[0]-pad)),y=Math.max(0,Math.floor(r[1]-pad));
      const clip={x,y,width:Math.ceil(r[0]+r[2]+pad)-x,height:Math.ceil(r[1]+r[3]+pad)-y,scale:1};
      assert.ok(clip.x+clip.width<=viewport.width && clip.y+clip.height<=viewport.height,
        `${name}: export rectangle fits the viewport`);
      // Beyond-viewport capture hides scrollbars and shifts right-aligned controls out of this rectangle.
      const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,clip});
      const file=`omenu_${name}${states.length>1?'_'+state:''}.png`;
      await writeFile(art+file,Buffer.from(shot.data,'base64'));
      surfaces.push({file:`engine/icons_x2/${file}`,key:file.slice(0,-4),kind,state,
        imageSize:[clip.width,clip.height],contentSize:[r[2],r[3]],padding:pad,nineSliceInsets:insets,
        source:{screen,selector,rect:r,clip,
          operation:'Browser rasterization of approved UI styling; all labels excluded.'}});
      await evaluate(`document.querySelector('#export-mask').remove();delete document.querySelector(${JSON.stringify(selector)}).dataset.exportTarget;`);
    }
    await send('CSS.forcePseudoState',{nodeId,forcedPseudoClasses:[]});
    await evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});const old=${JSON.stringify(original)};old.style===null?e.removeAttribute('style'):e.setAttribute('style',old.style);e.disabled=old.disabled;})()`);
  }
  await surface('title_backdrop','main','#backdrop',{kind:'background'});
  await surface('seal','main','.title-brand .seal',{descendants:true,kind:'emblem'});
  for(const [name,screen,selector] of [
    ['frame','load','.frame'],['party_frame','creation','.frame'],['title_panel','main','.title-actions'],['pause_panel','pause','.pause-panel']
  ]) await surface(name,screen,selector,{pad:16,kind:'panel'});
  for(const [name,screen,selector,width,height] of [
    ['button','main','[data-action="new-game"]',240,54],
    ['button_primary','main','[data-action="continue"]',240,54],
    ['button_quiet','load','[data-action="back"]',240,54],
    ['button_danger','pause','[data-action="quit"]',240,54],
    ['button_small','gameplay','[data-action="defaults"]',160,38],
    ['button_square','creation','[data-action="portrait-next"]',33,31],
  ]) await surface(name,screen,selector,{width,height,pad:6,states:['default','hover','pressed','disabled'],insets:[14,18,14,18],kind:'button'});
  for(const [name,screen,selector] of [
    ['assigned_skill','creation','.assigned-skill'],['skill','creation','.skill-choice'],
    ['save_row','load','.save-row:not([aria-pressed="true"])'],['save_row_selected','load','.save-row[aria-pressed="true"]'],
    ['tab','gameplay','.nav-tab:not([aria-current])'],['tab_selected','gameplay','.nav-tab[aria-current]'],
    ['toggle_off','gameplay','[data-setting="bolster_monsters"]'],['toggle_on','gameplay','[data-setting="quest_markers"]'],
    ['keycap','keyboard','button.key'],['text_field','creation','#hero-name'],
    ['world_card','worlds','.world-card[aria-pressed="false"]'],['world_card_selected','worlds','.world-card[aria-pressed="true"]'],
  ]) await surface(name,screen,selector,{insets:[8,8,8,8],kind:'widget'});
  await surface('skill_selected','creation','.skill-choice[aria-pressed="true"]',{
    setup:`document.querySelector('.skill-choice').click()`,insets:[8,8,8,8],kind:'widget'});
  await surface('party_slot','creation','.party-slot.add',{insets:[8,8,8,8],kind:'widget'});
  await surface('party_slot_selected','creation','.party-slot[aria-pressed="true"]',{insets:[8,8,8,8],kind:'widget'});
  await surface('modal','main','.modal',{setup:`document.querySelector('[data-action="quit"]').click()`,pad:16,kind:'panel'});
  await surface('modal_veil','main','.modal-veil',{setup:`document.querySelector('[data-action="quit"]').click()`,kind:'veil'});
  assert.deepEqual(errors,[], 'No browser export errors');
  const sourceFiles=['app.js','style.css','index.html','data.js'];
  const sourceHashes={};
  for(const file of sourceFiles) sourceHashes[file]=createHash('sha256').update(await readFile(root+file)).digest('hex');
  await writeFile(`${stage}source/surfaces.json`,JSON.stringify({design:'Carved Obsidian menus r03',sourceHashes,surfaces},null,2)+'\n');
  console.log(`Exported ${Object.keys(geometry).length} screen measurements and ` +
    `${surfaces.length} blank graphics to ${stage}.`);
} finally {ws?.close();browser.kill('SIGTERM');}
