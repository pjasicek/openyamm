// Interactive review and content-free exports using Chrome CDP; no packages required.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=dirname(fileURLToPath(import.meta.url)),port=9398;
const delay=ms=>new Promise(ok=>setTimeout(ok,ms));
const browser=spawn('google-chrome',['--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
  '--allow-file-access-from-files',`--remote-debugging-port=${port}`,'--remote-allow-origins=*',
  '--window-size=1600,900',`--user-data-dir=/tmp/obsidian-journal-check-${Date.now()}`,'about:blank'],{stdio:'ignore'});
let ws;const checks=[],errors=[],exports=[];
try{
  let page;
  for(let i=0;i<100;i++){try{page=(await(await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p=>p.type==='page');}catch{}if(page)break;await delay(100);}
  assert.ok(page,'Chrome started');ws=new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((ok,no)=>{ws.onopen=ok;ws.onerror=no;});
  let serial=0;const pending=new Map();
  ws.onmessage=event=>{const m=JSON.parse(event.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.no(m.error):p.ok(m.result);}
    if(m.method==='Runtime.exceptionThrown')errors.push(m.params);
    if(m.method==='Network.loadingFailed'&&m.params.errorText!=='net::ERR_ABORTED')errors.push(m.params);};
  const send=(method,params={})=>new Promise((ok,no)=>{const id=++serial;pending.set(id,{ok,no});ws.send(JSON.stringify({id,method,params}));});
  const ev=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert.ok(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1600,height:900,deviceScaleFactor:1,mobile:false});
  const nav=async(view,extra='')=>{
    await send('Page.navigate',{url:pathToFileURL(resolve(here,'index.html')).href+`?export=1&view=${view}&${extra}`});
    let ready=false;
    for(let i=0;i<100;i++){
      try{ready=await ev(`window.reviewReady===true && document.fonts.status==='loaded' && [...document.images].every(x=>x.complete&&x.naturalWidth>0) && mapImage.complete && mapImage.naturalWidth>0`);}catch{}
      if(ready)break;await delay(100);
    }
    assert.ok(ready,'Viewer ready');await delay(120);
  };
  const shot=async name=>{const r=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});await writeFile(resolve(here,'previews',name+'.png'),Buffer.from(r.data,'base64'));};
  const check=async(name,expression)=>{assert.equal(await ev(expression),true,name);checks.push(name);};
  await mkdir(resolve(here,'assets/exported'),{recursive:true});
  await nav('map');await shot('map');
  await check('Exact 300×300 logical map viewport',`canvas.clientWidth===561 && (()=>{const r=canvas.getBoundingClientRect();return r.x===445.625 && r.y===189.375 && r.width===562.5 && r.height===562.5})()`);
  await check('Three native zoom levels, no invented extra actions',`document.querySelectorAll('[data-zoom]').length===2 && state.zoom===0 && document.querySelector('[data-zoom="-1"]').disabled`);
  await ev(`document.querySelector('[data-zoom="1"]').click();document.querySelector('[data-zoom="1"]').click()`);
  await check('Zoom-in stops at 4× and button recentres on party',`state.zoom===2 && document.querySelector('[data-zoom="1"]').disabled && Math.abs(state.center[0]-party[0])<.001`);
  const oldCenter=await ev('state.center[0]');
  await send('Input.dispatchMouseEvent',{type:'mousePressed',x:690,y:430,button:'left',buttons:1,clickCount:1});
  await send('Input.dispatchMouseEvent',{type:'mouseMoved',x:760,y:430,button:'left',buttons:1});
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:760,y:430,button:'left',buttons:0,clickCount:1});
  await check('Dragging pans and releases pointer capture',`Math.abs(state.center[0]-${oldCenter})>.01 && drag===null`);
  await send('Input.dispatchMouseEvent',{type:'mouseWheel',x:710,y:460,deltaX:0,deltaY:90});
  await check('Mouse wheel zoom works',`state.zoom===1`);
  await nav('map','fog=all');await shot('map-full');
  await ev(`hoveredPin=0;drawMap()`);await check('Hovered discovered pin uses the existing note strip',`document.querySelector('#map-note').textContent.includes('fountain')`);await shot('map-note');
  await nav('map','fog=start&content=reference');await shot('map-sparse');
  for(const view of ['quests','story','notes']){
    await nav(view);await shot(view);
    await check(view+' body fits without clipping',`textViewport.scrollHeight<=textViewport.clientHeight+1`);
    await check(view+' retains native fonts',`getComputedStyle(textViewport).fontFamily.includes('NativeAutonote') && getComputedStyle(document.querySelector('#page-title')).fontFamily.includes('NativeBook2')`);
    await check(view+' uses justified bodies with natural paragraph endings',`getComputedStyle(textViewport).textAlign==='justify' && [...textViewport.querySelectorAll('.entry:not(.continues)')].every(p=>getComputedStyle(p).textAlignLast==='left')`);
    const justifiedText=await ev('textViewport.textContent');
    await ev(`document.querySelector('#body-alignment').value='left';document.querySelector('#body-alignment').dispatchEvent(new Event('change'))`);
    await check(view+' left-alignment comparison preserves text',`getComputedStyle(textViewport).textAlign==='left' && textViewport.textContent===${JSON.stringify(justifiedText)}`);
    await shot(view+'-left');
    await nav(view,'content=long');await shot(view+'-long');
    await check(view+' long content paginates and enables Next',`pages.length>1 && !document.querySelector('[data-page="1"]').disabled`);
    if(view==='story')await check('Continued story paragraph stays justified across page break',`(()=>{const original=JOURNAL_CONTENT.story[0].text;try{JOURNAL_CONTENT.story[0].text=original.replaceAll(String.fromCharCode(10),' ');state.page=0;render();const p=textViewport.querySelector('.continues');return p!==null&&getComputedStyle(p).textAlignLast==='justify'&&textViewport.scrollHeight<=textViewport.clientHeight+1}finally{JOURNAL_CONTENT.story[0].text=original;state.page=0;render()}})()`);
    await ev(`document.querySelector('[data-page="1"]').click()`);
    await check(view+' page turn changes page and enables Previous',`state.page===1 && !document.querySelector('[data-page="-1"]').disabled && textViewport.scrollHeight<=textViewport.clientHeight+1`);
    await shot(view+'-page-two');
    await ev(`state.page=pages.length-1;render()`);
    await check(view+' last page is bounded',`document.querySelector('[data-page="1"]').disabled && textViewport.scrollHeight<=textViewport.clientHeight+1`);
    await nav(view,'content=reference');await shot(view+'-reference');
    await check(view+' reference state stays sparse/empty',view==='quests'?`textViewport.querySelectorAll('.entry').length===1`:`textViewport.textContent===''`);
  }
  await nav('notes');
  for(const category of ['potion','fountain','obelisk','seer','misc','trainer']){
    await ev(`document.querySelector('[data-category="${category}"]').click()`);
    await check(category+' category selection retains content and resets page',`state.category==='${category}' && state.page===0 && document.querySelector('[data-category="${category}"]').getAttribute('aria-pressed')==='true' && textViewport.textContent.length>0 && textViewport.scrollHeight<=textViewport.clientHeight+1`);
    await shot('notes-'+category);
  }
  await check('Navigation controls fit the 4:3 frame without overlap',`(()=>{
    const buttons=[...document.querySelectorAll('#journal button')].filter(b=>b.offsetParent!==null).map(b=>b.getBoundingClientRect());
    const root=journal.getBoundingClientRect();return buttons.every(b=>b.left>=root.left&&b.right<=root.right&&b.top>=root.top&&b.bottom<=root.bottom)&&buttons.every((a,i)=>buttons.slice(i+1).every(b=>a.right<=b.left||a.left>=b.right||a.bottom<=b.top||a.top>=b.bottom));})()`);
  await ev(`document.querySelector('#close').click()`);
  await check('Close reveals approved HUD; reopen restores journal',`journal.hidden && document.querySelector('#journal-backdrop').hidden && !document.querySelector('#reopen').hidden`);
  await ev(`document.querySelector('#reopen').click()`);await check('Reopened with content intact',`!journal.hidden && textViewport.textContent.length>0`);
  await ev(`state.legacy=true;render()`);await check('Original screenshot comparison works',`!document.querySelector('#legacy-image').hidden && document.querySelector('#legacy-image').src.includes('2094.png')`);
  await nav('status');await shot('status');
  await check('2090 is a separate strip specimen',`document.querySelectorAll('.status-sample').length===3 && journal.hidden`);

  // Record live geometry for a concrete journal YAML draft and export only decoration/plates.
  await nav('notes');
  const geometry=await ev(`(()=>{const out={};for(const s of ['#journal','#page-title','#text-viewport','#close','#page-number','#view-emblem','#page-controls button','#note-categories button','#main-navigation button'])out[s]=[...document.querySelectorAll(s)].map(e=>{const r=e.getBoundingClientRect();return {rect:[(r.x-200)/1.875,r.y/1.875,r.width/1.875,r.height/1.875],dataset:{...e.dataset},text:e.textContent,children:[...e.querySelectorAll('img,svg,.obs-label')].map(c=>{const b=c.getBoundingClientRect();return {kind:c.classList.contains('obs-label')?'label':'icon',rect:[(b.x-r.x)/1.875,(b.y-r.y)/1.875,b.width/1.875,b.height/1.875],font_size:parseFloat(getComputedStyle(c).fontSize)/1.875}})}});return out;})()`);
  await nav('map');
  Object.assign(geometry,await ev(`(()=>{const out={};for(const s of ['#map','#map-note','#coordinates','#page-controls button'])out[s==='#page-controls button'?'map_controls':s]=[...document.querySelectorAll(s)].map(e=>{const r=e.getBoundingClientRect();return {rect:[(r.x-200)/1.875,r.y/1.875,r.width/1.875,r.height/1.875],dataset:{...e.dataset},children:[...e.querySelectorAll('svg,.obs-label')].map(c=>{const b=c.getBoundingClientRect();return {kind:c.classList.contains('obs-label')?'label':'icon',rect:[(b.x-r.x)/1.875,(b.y-r.y)/1.875,b.width/1.875,b.height/1.875],font_size:parseFloat(getComputedStyle(c).fontSize)/1.875}})}});return out;})()`));
  await writeFile(resolve(here,'review_geometry.json'),JSON.stringify(geometry,null,2)+'\n');
  const css=async text=>ev(`(()=>{const s=document.createElement('style');s.textContent=${JSON.stringify(text)};document.head.append(s)})()`);
  const capture=async(name,r)=>{const scale=16/15,result=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:r.x,y:r.y,width:Math.ceil(r.width),height:Math.ceil(r.height),scale}});
    await writeFile(resolve(here,'assets/exported',name+'.png'),Buffer.from(result.data,'base64'));
    exports.push({name,logical_size:[r.width/1.875,r.height/1.875],pixel_size:[Math.round(r.width*scale),Math.round(r.height*scale)]});};
  const box=selector=>ev(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height}})()`);
  await css(`#journal>*:not(.control-rail):not(.spine):not(.frame){visibility:hidden!important}`);
  await capture('obsidian_journal_background',await box('#journal'));
  // Separate transparent map frame, repeated wing material, divider and readiness strip.
  // All are captured from the approved CSS with dynamic content removed.
  await nav('map');
  const mapBox=await box('#map');
  await ev(`canvas.getContext('2d').clearRect(0,0,canvas.width,canvas.height);stage.replaceChildren(canvas)`);
  await send('Emulation.setDefaultBackgroundColorOverride',{color:{r:0,g:0,b:0,a:0}});
  await css(`html,body,main,.stage-host,.stage{background:transparent!important;border:0;box-shadow:none}
    #map{left:40px;top:40px;background:transparent!important}`);
  await capture('obsidian_journal_map_frame',{x:16,y:16,width:mapBox.width+48,height:mapBox.height+48});
  await nav('map');
  await ev(`stage.replaceChildren(document.querySelector('#journal-backdrop'))`);
  await css(`#journal-backdrop{inset:auto;left:20px;top:20px;width:550px;height:${550*690/362}px;background-position:0 0}`);
  await capture('obsidian_journal_backdrop_tile',await box('#journal-backdrop'));
  await nav('notes');
  const dividerWidth=(await box('#text-viewport')).width*.8;
  await ev(`stage.innerHTML='<div class="entry" id="divider-export"></div><div class="entry" id="divider-source"></div>'`);
  await css(`html,body,main,.stage-host,.stage{background:transparent!important;border:0;box-shadow:none}
    #divider-source{position:absolute;left:20px;top:20px;width:${dividerWidth}px;height:7px;padding:0}
    #divider-source:before{inset:0;height:7px}`);
  await capture('obsidian_journal_entry_divider',await box('#divider-source'));
  await nav('status');
  const strip=await ev(`document.querySelector('.status-sample:not(.original)').outerHTML`);
  await ev(`stage.innerHTML=${JSON.stringify(strip)};stage.firstElementChild.replaceChildren()`);
  await css(`html,body,main,.stage-host,.stage{background:transparent!important;border:0;box-shadow:none}
    .status-sample{position:absolute;left:20px;top:20px;width:1200px;height:82px;margin:0}`);
  await capture('obsidian_journal_status_strip',await box('.status-sample'));
  await nav('notes');
  await send('Emulation.setDefaultBackgroundColorOverride',{color:{r:0,g:0,b:0,a:0}});
  await css(`html,body,main,.stage-host,.stage{background:transparent!important;border:0;box-shadow:none}`);
  for(const family of ['main','category','page','close']){
    const selector={main:'.main-button',category:'.category',page:'.page-button',close:'#close'}[family];
    await nav('notes');
    const original=await ev(`document.querySelector(${JSON.stringify(selector)}).outerHTML`);
    const size=await box(selector);
    await ev(`stage.innerHTML=${JSON.stringify(original)}`);
    await css(`html,body,main,.stage-host,.stage{background:transparent!important;border:0;box-shadow:none}.stage>.obs-button{position:absolute!important;left:20px!important;top:20px!important;width:${size.width}px!important;height:${size.height}px!important;transition:none!important}.stage>.obs-button>*{visibility:hidden!important}`);
    for(const state of ['normal','hover','pressed','selected','disabled']){
      await ev(`(()=>{const b=stage.firstElementChild;b.disabled=${state==='disabled'};b.setAttribute('aria-pressed','${state==='selected'}');b.dataset.demoState='${state}'})()`);
      await capture(`obsidian_journal_${family}_${state}`,await box('.stage>.obs-button'));
    }
  }
  await nav('map');
  await ev(`stage.innerHTML=document.querySelector('#map-note').outerHTML`);
  await css(`html,body,main,.stage-host,.stage{background:transparent!important;border:0;box-shadow:none}
    #map-note{position:absolute;left:20px;top:20px;color:transparent;text-shadow:none}`);
  await capture('obsidian_journal_note_bar',await box('#map-note'));
  for(const [name,expression] of [['previous',`arrow('previous')`],['next',`arrow('next')`],
                                ['zoom_in',`zoomGlyph(1)`],['zoom_out',`zoomGlyph(-1)`]]){
    await ev(`stage.innerHTML=${expression}`);
    await css(`.stage>svg{position:absolute;left:20px;top:20px;width:38px;height:30px;fill:none;stroke:#e8d1a4;stroke-width:1.7}`);
    await capture('obsidian_journal_'+name,await box('.stage>svg'));
  }
  await writeFile(resolve(here,'exported_assets.json'),JSON.stringify(exports,null,2)+'\n');
  assert.equal(errors.length,0,JSON.stringify(errors));
  await nav('notes');await send('Page.navigate',{url:pathToFileURL(resolve(here,'index.html')).href+'?view=notes'});await delay(650);await shot('browser-review');
  const report={result:'PASS',date:'2026-09-28',checks,browserErrors:errors,scope:'Approved browser design and exported art only; no game installation.'};
  await writeFile(resolve(here,'browser_review.json'),JSON.stringify(report,null,2)+'\n');
  console.log(`PASS: ${checks.length} browser checks and ${exports.length} content-free exports.`);
}finally{ws?.close();browser.kill('SIGTERM');}
