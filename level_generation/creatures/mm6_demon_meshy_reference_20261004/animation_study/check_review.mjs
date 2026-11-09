// Check the study viewer in a real browser; this does not validate a 3D animation or effect.
import {spawn} from 'node:child_process';
import {mkdtempSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, join} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const browser = spawn('google-chrome', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run',
  '--disable-background-networking', '--remote-debugging-pipe',
  '--user-data-dir=' + mkdtempSync(join(tmpdir(), 'demon-animation-study-')),
], {stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe']});
let counter = 0, incoming = '', session;
const pending = new Map(), exceptions = [];
let diagnostics = '';
browser.stderr.on('data', chunk => diagnostics += chunk);
browser.stdio[4].on('data', chunk => {
  incoming += chunk;
  let end;
  while ((end = incoming.indexOf('\0')) >= 0) {
    const message = JSON.parse(incoming.slice(0, end));
    incoming = incoming.slice(end + 1);
    if (message.id) {
      const request = pending.get(message.id);
      pending.delete(message.id);
      if (request) message.error ? request.reject(message.error) : request.resolve(message.result);
    }
    if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails);
  }
});
for (const stream of [browser.stdio[3], browser.stdio[4]]) stream.on('error', () => {});
browser.on('exit', code => {
  for (const request of pending.values()) request.reject(new Error('Browser exited ' + code + ': ' + diagnostics.slice(-1000)));
  pending.clear();
});
function cdp(method, params = {}, attached = true) {
  const id = ++counter;
  return new Promise((resolve, reject) => {
    pending.set(id, {resolve, reject});
    browser.stdio[3].write(JSON.stringify({id, method, params, ...(attached && session ? {sessionId: session} : {})}) + '\0');
  });
}
async function evaluate(expression) {
  const r = await cdp('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true});
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
async function screenshot(name) {
  const r = await cdp('Page.captureScreenshot', {format: 'png'});
  writeFileSync(join(directory, name + '.png'), Buffer.from(r.data, 'base64'));
}
const watchdog = setTimeout(() => browser.kill(), 45000);
try {
  const target = await cdp('Target.createTarget', {url: 'about:blank'}, false);
  session = (await cdp('Target.attachToTarget', {targetId: target.targetId, flatten: true}, false)).sessionId;
  await cdp('Runtime.enable');
  await cdp('Page.enable');
  await cdp('Emulation.setDeviceMetricsOverride', {width: 1400, height: 1600, deviceScaleFactor: 1, mobile: false});
  await cdp('Page.navigate', {url: pathToFileURL(join(directory, 'index.html')).href});
  await evaluate(`new Promise((resolve,reject)=>{
    let attempts=0;const timer=setInterval(()=>{
      if(typeof loaded!=='undefined'&&loaded===61){clearInterval(timer);resolve(true)}
      else if(++attempts>300){clearInterval(timer);reject('61 native images did not load')}
    },20)
  })`);
  const report = await evaluate(`(()=>{
    const expected={standing:{start:[0],duration:6},walk:{start:[0,6,15,27,33,42],duration:54},
      hit:{start:[0,6,12,18,24,30],duration:36},fidget:{start:[0,6,12,18,24],duration:30},
      death:{start:[0,6,12,18,24,30,36,42,51],duration:60},corpse:{start:[0],duration:6}};
    function assert(value,message){if(!value)throw Error(message)}
    const pixel=document.createElement('canvas');pixel.width=354;pixel.height=330;
    const pc=pixel.getContext('2d',{willReadFrequently:true});const sourcePixel=new Map();
    function firstPixel(name){
      if(sourcePixel.has(name))return sourcePixel.get(name);
      pc.clearRect(0,0,354,330);pc.drawImage(sprites[name],0,0);
      const data=pc.getImageData(0,0,354,330).data;
      for(let y=0;y<329;y++)for(let x=0;x<354;x++){
        const i=(y*354+x)*4;
        if(data[i+3]===255){const result={x,y,rgb:Array.from(data.slice(i,i+3))};sourcePixel.set(name,result);return result}
      }throw Error('Empty native image '+name)
    }
    let states=0,pixelChecks=0,anchorClicks=0;
    const checkedActions=[];
    for(const [key,config] of Object.entries(expected)){
      action.value=key;action.dispatchEvent(new Event('change'));
      const c=spec.clips[key];assert(+slider.max===config.duration,'Duration '+key);
      assert(c.anchors.map(a=>a.sample).join(',')===config.start.join(','),'Anchor timing '+key);
      assert(view.options.length===(c.single_view?1:8),'Directional availability '+key);
      const views=Array.from(view.options,o=>o.value);
      for(const v of views){
        view.value=v;view.dispatchEvent(new Event('change'));
        for(let sample=0;sample<=config.duration;sample++){
          slider.value=sample;slider.dispatchEvent(new Event('input'));
          const expectedAnchor=sample===config.duration&&c.loop?0:
            config.start.reduce((result,start,index)=>start<=sample?index:result,0);
          const binding=c.native_binding.frames[expectedAnchor].texture_name;
          const suffix=c.single_view?'':String([0,1,2,3,4,3,2,1][+v]);
          const expectedName=binding+suffix;
          assert(window.studyState.native===expectedName,'Source hold '+key+'/'+v+'/'+sample);
          assert(window.studyState.mirror===(+v>=5),'Mirror '+key+'/'+v+'/'+sample);
          assert($('time').textContent.startsWith(sample+'/'+config.duration),'Displayed time');
          assert($('movement').textContent.length>20&&$('support').textContent.length>20,'Sample instructions');
          assert($('anchors').children.length===config.start.length,'Anchor table');
          assert($('checks').children.length===(['death','corpse'].includes(key)?8:7),'Review checks');
          const p=firstPixel(expectedName),x=(+v>=5?353-p.x:p.x)*2+1;
          const actual=$('native').getContext('2d').getImageData(x,p.y*2+1,1,1).data;
          assert(p.rgb.every((value,i)=>value===actual[i]),'Native canvas pixels '+key+'/'+v+'/'+sample);
          states++;pixelChecks++;
        }
      }
      for(const [i,button] of Array.from($('anchors').querySelectorAll('button')).entries()){
        button.click();assert(+slider.value===config.start[i],'Anchor jump '+key+'/'+i);anchorClicks++;
      }
      checkedActions.push({action:key,anchors:config.start,samples:config.duration+1,views:views.length});
    }
    action.value='walk';action.dispatchEvent(new Event('change'));view.value='2';view.dispatchEvent(new Event('change'));
    slider.value=15;slider.dispatchEvent(new Event('input'));
    assert(window.studyState.guideCount>0,'Profile guide missing');
    assert(document.documentElement.scrollWidth<=innerWidth,'Desktop horizontal overflow');
    return {nativeImages:loaded,states,pixelChecks,anchorClicks,checkedActions,
      exactNativeHolds:true,mirrorPixels:true,endpoints:true,profileGuides:true};
  })()`);
  await screenshot('reviewer_walk_profile');
  await evaluate(`action.value='hit';action.dispatchEvent(new Event('change'));
    slider.value=18;slider.dispatchEvent(new Event('input'));`);
  await screenshot('reviewer_hit');
  await evaluate(`action.value='death';action.dispatchEvent(new Event('change'));
    slider.value=42;slider.dispatchEvent(new Event('input'));`);
  await screenshot('reviewer_death');
  report.playback = await evaluate(`(()=>{
    // Control browser animation timestamps to exercise loop and one-shot behavior without timing races.
    const original=requestAnimationFrame;let callback;window.requestAnimationFrame=fn=>{callback=fn;return 1};
    function assert(value,message){if(!value)throw Error(message)}
    try{
      action.value='walk';action.dispatchEvent(new Event('change'));play.click();
      callback(start+1125+125);assert(window.studyState.sample===6&&playing,'Walk loop timing');
      play.click();assert(!playing,'Pause');
      action.value='hit';action.dispatchEvent(new Event('change'));play.click();
      callback(start+751);assert(window.studyState.sample===36&&!playing,'One-shot endpoint');
      play.click();assert(+slider.value===0&&playing,'Restart');
      action.value='fidget';action.dispatchEvent(new Event('change'));assert(!playing,'Action stops playback');
      return {loopWrap:true,oneShotStop:true,pause:true,restart:true,actionChangeStops:true};
    }finally{stop();window.requestAnimationFrame=original}
  })()`);
  await cdp('Emulation.setDeviceMetricsOverride', {width: 390, height: 1000, deviceScaleFactor: 1, mobile: false});
  report.mobile = await evaluate(`(()=>{
    const actions=[];
    for(const key of Object.keys(spec.clips)){
      action.value=key;action.dispatchEvent(new Event('change'));
      if(document.documentElement.scrollWidth>innerWidth)throw Error('Mobile overflow '+key);
      actions.push(key)
    }
    action.value='walk';action.dispatchEvent(new Event('change'));
    return {width:innerWidth,allActionsNoHorizontalOverflow:actions};
  })()`);
  await screenshot('reviewer_mobile');
  await cdp('Page.navigate', {url: pathToFileURL(join(directory, 'index.html')).href + '?action=hit&view=7&sample=18'});
  report.query = await evaluate(`new Promise((resolve,reject)=>{
    let attempts=0;const timer=setInterval(()=>{
      if(typeof loaded!=='undefined'&&loaded===61){
        clearInterval(timer);
        if(window.studyState.action!=='hit'||window.studyState.view!==0||window.studyState.sample!==18)
          reject('Query state incorrect');else resolve({action:'hit',invalidViewIgnored:true,sample:18})
      }else if(++attempts>300){clearInterval(timer);reject('Query page failed to load')}
    },20)
  })`);
  if (exceptions.length) throw new Error(JSON.stringify(exceptions));
  report.browserExceptions=exceptions;
  report.scope='Study page only; native source/timing/controls/layout checked, no new 3D animation or effect acceptance';
  writeFileSync(join(directory, 'reviewer_check.json'), JSON.stringify(report,null,2)+'\n');
  console.log(`PASS: ${report.states} action/view/sample states, ${report.pixelChecks} native pixel checks, `+
    `${report.anchorClicks} anchor jumps, playback and mobile layout; zero browser exceptions.`);
} finally {
  clearTimeout(watchdog);
  browser.kill();
}
