// Check the study viewer in a real browser; this does not validate a 3D animation.
import {spawn} from 'node:child_process';
import {mkdtempSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, join} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const directory = dirname(fileURLToPath(import.meta.url));
const browser = spawn('google-chrome', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run',
  '--disable-background-networking', '--remote-debugging-pipe',
  '--user-data-dir=' + mkdtempSync(join(tmpdir(), 'demon-attack-study-')),
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
const watchdog = setTimeout(() => browser.kill(), 20000);
try {
  const target = await cdp('Target.createTarget', {url: 'about:blank'}, false);
  session = (await cdp('Target.attachToTarget', {targetId: target.targetId, flatten: true}, false)).sessionId;
  await cdp('Runtime.enable');
  await cdp('Page.enable');
  await cdp('Emulation.setDeviceMetricsOverride', {width: 1300, height: 1200, deviceScaleFactor: 1, mobile: false});
  await cdp('Page.navigate', {url: pathToFileURL(join(directory, 'index.html')).href});
  const result = await cdp('Runtime.evaluate', {awaitPromise: true, returnByValue: true, expression: `
    new Promise((resolve,reject)=>{
      let attempts=0;
      const timer=setInterval(()=>{
        if(typeof loaded==='undefined'||loaded!==6){if(++attempts>100){clearInterval(timer);reject('Native art did not load')}return}
        clearInterval(timer);
        const records=[];
        for(let i=0;i<37;i++){
          slider.value=i;slider.dispatchEvent(new Event('input'));
          records.push({sample:i,time:document.querySelector('#time').textContent,
                        title:document.querySelector('#guideTitle').textContent,
                        controls:document.querySelector('#controls').children.length,
                        checks:document.querySelector('#checks').children.length});
        }
        slider.value=24;slider.dispatchEvent(new Event('input'));
        resolve({nativeImages:loaded,records,hasHorizontalOverflow:document.documentElement.scrollWidth>innerWidth});
      },20)
    })`});
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  const report = result.result.value;
  if (report.nativeImages !== 6 || report.records.length !== 37 || exceptions.length || report.hasHorizontalOverflow)
    throw new Error(JSON.stringify({report, exceptions}));
  for (const record of report.records) {
    if (record.checks !== 8 || record.controls !== 15 || !record.time.startsWith(record.sample + '/36'))
      throw new Error('Bad sample UI: ' + JSON.stringify(record));
  }
  const screenshot = await cdp('Page.captureScreenshot', {format: 'png'});
  writeFileSync(join(directory, 'reviewer_sweep.png'), Buffer.from(screenshot.data, 'base64'));
  report.browserExceptions = exceptions;
  report.scope = 'Study viewer only; no authored 3D clip or deformation acceptance';
  writeFileSync(join(directory, 'reviewer_check.json'), JSON.stringify(report, null, 2) + '\n');
  console.log('PASS: six native images, all 37 sample states, 15 control seeds and eight checks; no browser errors.');
} finally {
  clearTimeout(watchdog);
  browser.kill();
}
