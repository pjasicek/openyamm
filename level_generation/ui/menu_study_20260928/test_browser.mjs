import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {writeFile, mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';

const base = 'http://127.0.0.1:8899/level_generation/ui/menu_study_20260928/';
const directory = fileURLToPath(new URL('.', import.meta.url));
const port = 9391;
const browser = spawn('google-chrome', ['--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  `--remote-debugging-port=${port}`, '--remote-allow-origins=*', '--window-size=1600,900',
  `--user-data-dir=/tmp/openyamm-menu-browser-${Date.now()}`, 'about:blank'], {stdio:'ignore'});
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const checks = [], errors = [], failedRequests = [];
let ws, serial = 0;
try {
  let page;
  for (let attempt=0;attempt<80;attempt++) {
    try {page=(await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(item=>item.type==='page');} catch {}
    if(page)break;await delay(100);
  }
  assert.ok(page,'Chrome starts');
  ws=new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  const pending=new Map();
  ws.onmessage=event=>{
    const message=JSON.parse(event.data),p=pending.get(message.id);
    if(p){pending.delete(message.id);message.error?p.reject(message.error):p.resolve(message.result);}
    if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails);
    if(message.method==='Network.responseReceived'&&message.params.response.status>=400)failedRequests.push(message.params.response.url);
  };
  const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
  const evaluate=async expression=>{
    const result=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
    assert.ok(!result.exceptionDetails,JSON.stringify(result.exceptionDetails));return result.result.value;
  };
  const check=async(name,expression)=>{assert.ok(await evaluate(expression),name);checks.push(name);};
  const click=selector=>evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);
  const input=(selector,value,type='input')=>evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(selector)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event(${JSON.stringify(type)},{bubbles:true}));})()`);
  const key=async(key,code=key)=>{await send('Input.dispatchKeyEvent',{type:'keyDown',key,code});await send('Input.dispatchKeyEvent',{type:'keyUp',key,code});};
  const navigate=async(screen,query='')=>{
    await send('Page.navigate',{url:`${base}?export=1&screen=${screen}${query}`});
    for(let attempt=0;attempt<80;attempt++){if(await evaluate(`document.body?.dataset.ready==='true' && document.querySelector('#stage')?.dataset.screen`))break;await delay(50);}
    await evaluate('document.fonts.ready');await delay(180);
  };
  const capture=async(name)=>{
    const shot=await send('Page.captureScreenshot',{format:'png'});
    await writeFile(`${directory}previews/${name}.png`,Buffer.from(shot.data,'base64'));
  };
  await send('Page.enable');await send('Runtime.enable');await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1600,height:900,deviceScaleFactor:1,mobile:false});
  await mkdir(`${directory}previews`,{recursive:true});
  for(const screen of ['main','pause','load','save','worlds','creation','gameplay','video','audio','controls','keyboard','credits']){
    await navigate(screen);
    await check(`${screen}: scene fits`,"document.querySelector('#stage').getBoundingClientRect().width===1600 && document.documentElement.scrollWidth===1600");
    await check(`${screen}: images load`,"[...document.querySelectorAll('#screen img')].every(image=>image.complete&&image.naturalWidth>0)");
    await capture(`r03-${screen}`);
  }
  await navigate('pause');
  await check('Pause has no branding or redundant paused copy', "!document.querySelector('.pause-panel .brand') && !document.querySelector('.pause-panel').textContent.includes('Adventure paused') && !document.querySelector('.pause-panel').textContent.includes('Esc ·')");
  for (const screen of ['load','save']) {
    await navigate(screen);
    await check(`${screen}: simplified list and footer`, "!document.querySelector('#save-search,#save-world') && !document.querySelector('.frame-head .eyebrow') && !document.querySelector('.frame-footer .footer-note')");
  }
  await navigate('worlds');
  await check('Continent choice has a direct heading and no flavour paragraphs', "document.querySelector('h1').textContent==='Choose Starting Continent' && [...document.querySelectorAll('.world-card p')].every(p=>p.classList.contains('eyebrow'))");
  await navigate('creation','&context=pause');
  await check('Party creation uses the full screen', "document.querySelector('.creation-frame').getBoundingClientRect().width===1560");
  await check('Portrait is substantially larger', "document.querySelector('.identity-portrait').getBoundingClientRect().width===152");
  await check('No obsolete party-review route', "!document.querySelector('#review-screen option[value=ready]') && !document.querySelector('[data-action=review-party]')");
  await check('Party creation omits class boilerplate', "!document.querySelector('.learned').textContent.includes('Included with your class')");
  await click('[data-action="back"]');
  await check('Party Cancel returns to main even when started from pause', "document.querySelector('#stage').dataset.screen==='main'");
  await navigate('worlds');await click('[data-world="antagarich"]');await click('[data-action="create-party"]');
  const classes=await evaluate("[...document.querySelector('#hero-class').options].map(option=>option.value)");
  for (const name of classes) {
    await input('#hero-class',name,'change');
    await check(`${name}: skills fit two columns without scrolling`, "(()=>{const grid=document.querySelector('.skills-grid');const roster=document.querySelector('.party-roster');return getComputedStyle(grid).gridTemplateColumns.split(' ').length===2 && grid.scrollHeight<=grid.clientHeight+1 && grid.getBoundingClientRect().bottom<roster.getBoundingClientRect().top && [...grid.children].every(button=>button.scrollWidth<=button.clientWidth+1);})()");
  }
  await check('Paperdoll stays clear of party roster', "document.querySelector('.doll').getBoundingClientRect().bottom<document.querySelector('.party-roster').getBoundingClientRect().top");
  await navigate('credits');
  await check('Credits contain the requested people and projects', "['New World Computing','OpenEnroth','Rodril','MMMerge','pjasicek','testing OpenYAMM'].every(text=>document.querySelector('.credits').textContent.includes(text)) && document.querySelector('.credits a').href==='https://github.com/pjasicek/openyamm'");
  await check('Credits omit the previous universe and type sections', "!document.querySelector('.credits').textContent.includes('Universe of Might and Magic') && !document.querySelector('.credits').textContent.includes('Type & materials')");
  await navigate('main');
  for (const id of ['dusk','fortress','atlas','sketch']) {
    await input('#review-background',id,'change');
    await evaluate(`new Promise((resolve,reject)=>{const image=new Image();image.onload=resolve;image.onerror=reject;image.src=window.MENU_BACKGROUNDS.find(item=>item.id===${JSON.stringify(id)}).file;})`);
    await check(`${id}: background choice applied and linked`, `document.querySelector('#stage').dataset.background===${JSON.stringify(id)} && document.querySelector('#background-credit a').textContent.length>0`);
    await capture(`r03-main-${id}`);
  }
  await navigate('main','&background=fortress');
  await check('Background choice survives a shared URL', "document.querySelector('#stage').dataset.background==='fortress' && document.querySelector('#review-background').value==='fortress'");
  await navigate('main');
  await check('TTF fonts load',"document.fonts.check('26px Fondamento') && document.fonts.check('22px OpenYAMMArrus') && document.fonts.check('18px OpenYAMMLucida')");
  await click('[data-action="settings"]');
  await check('Settings omits redundant copy',"!document.querySelector('.frame-head .eyebrow') && !document.querySelector('.settings-nav .fineprint')");
  await check('Main menu opens Settings',"document.querySelector('h1').textContent==='Settings'");
  await check('No baked text buttons',"[...document.querySelectorAll('.button,.nav-tab')].every(button=>button.textContent.trim().length>0 && !button.querySelector('img'))");
  await click('[data-setting="quest_markers"]');
  await click('[data-section="audio"]');
  await input('#setting-music_volume','3');
  await check('Changes persist across sections',"document.querySelector('.footer-note').textContent==='2 unapplied changes'");
  await click('[data-action="back"]');
  await check('Unsaved settings are protected',"document.querySelector('[role=dialog]') && document.querySelector('#screen').inert");
  await capture('r03-unsaved-settings');
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',modifiers:8});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',modifiers:8});
  await check('Dialog keeps keyboard focus inside',"document.querySelector('[role=dialog]').contains(document.activeElement)");
  await key('Escape');
  await click('[data-action="apply"]');
  await check('Apply clears pending changes',"document.querySelector('[data-action=apply]').disabled");
  await click('[data-section="video"]');
  await input('#setting-window_mode','fullscreen','change');
  await click('[data-action="apply"]');
  await check('Display confirmation counts down',"document.querySelector('#display-countdown')?.textContent==='15'");
  await capture('r03-display-confirm');
  await click('[data-modal="0"]');
  await check('Display rollback restores previous mode',"document.querySelector('#setting-window_mode').value==='windowed'");
  await input('#setting-window_mode','fullscreen','change');await click('[data-action="apply"]');
  await click('[data-modal="1"]');
  await check('Display confirmation keeps changes',"document.querySelector('#setting-window_mode').value==='fullscreen' && document.querySelector('[data-action=apply]').disabled");
  await input('#setting-window_mode','windowed','change');await click('[data-action="apply"]');
  await delay(15500);
  await check('Unconfirmed display changes time out',"!document.querySelector('[role=dialog]') && document.querySelector('#setting-window_mode').value==='fullscreen'");
  await input('#setting-window_mode','windowed_fullscreen','change');
  await check('Borderless uses desktop resolution',"document.querySelector('#setting-resolution').disabled");
  await click('[data-action="revert"]');
  await click('[data-setting="cinematic_grading"]');
  await check('Grading strength follows its toggle',"document.querySelector('#setting-cinematic_strength').disabled");
  await click('[data-action="revert"]');
  await click('[data-section="controls"]');await input('#setting-control_scheme','classic','change');
  await check('Changing presets protects custom bindings',"document.querySelector('#dialog-title').textContent==='Use Classic controls?'");
  await click('[data-modal="1"]');
  await click('[data-section="keyboard"]');
  await check('Classic preset changes movement and attack',"document.querySelector('[data-binding=forward]').textContent==='↑' && document.querySelector('[data-binding=attack]').textContent==='A'");
  await click('[data-action="revert"]');
  await click('[data-section="keyboard"]');
  await click('[data-binding="forward"]');await key('s','KeyS');
  await check('Binding conflict names the existing action',"document.querySelector('[role=dialog]').textContent.includes('Backward')");
  await capture('r03-binding-conflict');await click('[data-modal="1"]');
  await check('Binding conflict swaps both assignments',"document.querySelector('[data-binding=forward]').textContent==='S' && document.querySelector('[data-binding=backward]').textContent==='W'");
  await click('[data-binding="forward"]');await key('F9');
  await check('Fixed shortcut remains reserved',"document.querySelector('#capture-note').textContent.includes('reserved')");await key('Escape');
  await click('[data-binding="jump"]');await key('Escape');
  await check('Cancelled key capture preserves assignment',"document.querySelector('[data-binding=jump]').textContent==='X'");
  await click('[data-binding="jump"]');await click('[data-modal="1"]');
  await check('Binding can be cleared explicitly',"document.querySelector('[data-binding=jump]').textContent==='Unbound'");
  await click('[data-action="defaults"]');await click('[data-modal="1"]');
  await check('Keyboard defaults restore the chosen preset',"document.querySelector('[data-binding=jump]').textContent==='X' && document.querySelector('[data-binding=forward]').textContent==='W'");
  await input('#binding-search','double');
  await check('Previously hidden double speed is discoverable',"document.querySelectorAll('[data-binding]').length===1 && document.querySelector('[data-binding=double_speed]')");
  await input('#binding-search','not-a-real-action');
  await check('No-result search has an empty state',"document.querySelector('#binding-list').textContent.includes('No matching actions')");
  await navigate('save');await input('#save-name','A new chapter');await click('[data-action="commit-save"]');
  await check('New save returns to pause',"document.querySelector('#stage').dataset.screen==='pause'");
  await click('[data-action="save"]');await click('[data-save="manual1"]');await click('[data-action="commit-save"]');
  await check('Overwrite requires confirmation',"document.querySelector('#dialog-title').textContent==='Replace this save?'");await capture('r03-overwrite');await key('Escape');
  await navigate('main','&saves=empty');
  await check('No saves disables Continue and Load',"document.querySelector('[data-action=continue]').disabled && document.querySelector('[data-action=load]').disabled");
  await capture('r03-main-empty');await navigate('load','&saves=empty');
  await check('Empty load action disabled',"document.querySelector('[data-action=commit-load]').disabled");await capture('r03-load-empty');
  await navigate('creation');
  await check('Character controls clear the roster',"document.querySelector('.identity-column .footer-actions').getBoundingClientRect().bottom<=document.querySelector('.party-roster').getBoundingClientRect().top");
  await check('Native appearance is composed from all layers',"document.querySelectorAll('.doll img').length===4");
  await check('Incomplete party cannot begin',"document.querySelector('[data-action=begin]').disabled");
  for(let index=0;index<15;index++)await click('[data-action="stat"][data-stat="0"][data-delta="1"]');
  await click('[data-skill="Axe"]');await click('[data-skill="Spear"]');
  await check('Point and skill completion enables Begin Adventure',"!document.querySelector('[data-action=begin]').disabled");
  await capture('r03-party-complete');
  await click('[data-action="begin"]');
  await check('Completed party starts directly without a review screen',"document.querySelector('#stage').dataset.screen==='game'");
  await navigate('creation');
  for(let index=0;index<4;index++)await click('[data-action="add-hero"]');
  await check('Party capacity is five',"document.querySelectorAll('[data-hero]').length===5 && !document.querySelector('[data-action=add-hero]')");await capture('r03-party-five');
  await navigate('worlds');await click('[data-world="jadame"]');await click('[data-action="create-party"]');
  await input('#hero-class','Necromancer','change');
  await check('Jadame skills also fit without scrolling',"document.querySelector('.skills-grid').scrollHeight<=document.querySelector('.skills-grid').clientHeight+1 && document.querySelector('.skills-grid').getBoundingClientRect().bottom<document.querySelector('.party-roster').getBoundingClientRect().top");
  await check('Jadame class changes update skills',"document.querySelector('.learned').textContent.includes('Dark Magic') || document.querySelector('.learned').textContent.includes('Staff')");
  await input('#hero-class','Priest','change');
  await check('Priest skills fit without scrolling',"document.querySelector('.skills-grid').scrollHeight<=document.querySelector('.skills-grid').clientHeight+1 && document.querySelector('.skills-grid').getBoundingClientRect().bottom<document.querySelector('.party-roster').getBoundingClientRect().top");
  await navigate('pause');await click('[data-action="settings"]');await click('[data-action="back"]');
  await check('Settings remembers pause origin',"document.querySelector('#stage').dataset.screen==='pause'");
  await click('[data-action="resume"]');await key('Escape');
  await check('Escape reopens pause after resume',"document.querySelector('#stage').dataset.screen==='pause'");
  await navigate('main');await click('#compare-original');
  await check('Supplied title reference is available',"document.querySelector('.original-overlay img').getAttribute('src')==='assets/original-2077.png'");
  await check('All active bindings represented',"window.MENU_DATA.bindings.length===26 && window.MENU_DATA.settings.length===30");
  await navigate('keyboard');
  await check('Keyboard fits two columns',"getComputedStyle(document.querySelector('#binding-list')).gridTemplateColumns.split(' ').length===2");
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await check('Reduced motion is respected',"getComputedStyle(document.querySelector('.button')).transitionDuration==='0s'");
  await navigate('load');await click('[data-save="auto"]');await capture('r03-load-autosave');
  await click('[data-save="manual2"]');await capture('r03-load-harmondale');
  await click('[data-save="manual3"]');
  await check('Save list directly selects Jadame save',"document.querySelector('.save-detail').textContent.includes('Ravenshore')");
  await capture('r03-load-missing-preview');
  await send('Emulation.setDeviceMetricsOverride',{width:1280,height:720,deviceScaleFactor:1,mobile:false});
  await navigate('keyboard');await check('1280×720 fits',"document.documentElement.scrollWidth===1280");await capture('r03-keyboard-1280');
  await send('Emulation.setDeviceMetricsOverride',{width:1600,height:1150,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:base});
  for(let attempt=0;attempt<80;attempt++){if(await evaluate("document.body?.dataset.ready==='true' && !document.body.classList.contains('export')"))break;await delay(50);}
  await evaluate('document.fonts.ready');await delay(200);
  await check('Review toolbar and gallery fit the page', "document.documentElement.scrollWidth===document.documentElement.clientWidth && document.querySelectorAll('[data-background-choice]').length===4");
  await input('#review-screen','creation','change');await input('#review-background','fortress','change');
  await check('Background selector opens the main menu from another screen', "document.querySelector('#stage').dataset.screen==='main' && document.querySelector('#stage').dataset.background==='fortress'");
  await click('[data-background-choice="atlas"]');
  await check('Gallery chooses a background with its attribution', "document.querySelector('#review-background').value==='atlas' && document.querySelector('#background-credit a').textContent.includes('MarkonPhoenix')");
  await click('[data-background-choice="dusk"]');
  await evaluate('window.scrollTo(0,0)');
  await capture('r03-review-page');
  assert.deepEqual(errors,[],'No JavaScript exceptions');
  assert.deepEqual(failedRequests.filter(url=>!url.endsWith('favicon.ico')),[],'No missing local assets');
  const report={revision:'r03',result:'PASS',checks:checks.length,details:checks,javascriptErrors:errors,failedRequests:failedRequests.filter(url=>!url.endsWith('favicon.ico')),url:base};
  await writeFile(`${directory}browser_validation_r03.json`,JSON.stringify(report,null,2)+'\n');
  await writeFile(`${directory}browser_validation.json`,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
}finally{ws?.close();browser.kill('SIGTERM');}
