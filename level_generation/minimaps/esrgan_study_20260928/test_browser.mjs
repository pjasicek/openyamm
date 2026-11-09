import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {writeFile} from 'node:fs/promises';

const directory = 'level_generation/minimaps/esrgan_study_20260928/';
const url = 'http://127.0.0.1:8899/' + directory;
const browser = spawn('google-chrome', [
  '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--remote-debugging-port=9288', '--remote-allow-origins=*', '--window-size=1500,1100',
  '--user-data-dir=/tmp/openyamm-minimap-esrgan-browser-' + Date.now(), url,
], {stdio:'ignore'});
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket;
try {
  let page;
  for (let attempt = 0; attempt < 100; attempt++) {
    try {
      page = (await (await fetch('http://127.0.0.1:9288/json/list')).json())
        .find(item => item.type === 'page' && item.url === url);
      if (page) break;
    } catch {}
    await delay(100);
  }
  assert.ok(page, 'Browser page available');
  socket = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {socket.onopen = resolve;socket.onerror = reject;});
  let serial = 0;
  const pending = new Map(), errors = [];
  socket.onmessage = event => {
    const result = JSON.parse(event.data);
    if (result.method === 'Runtime.exceptionThrown') errors.push(result.params);
    const request = pending.get(result.id);
    if (request) {
      pending.delete(result.id);
      if (result.error) request.reject(result.error);else request.resolve(result.result);
    }
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++serial;pending.set(id, {resolve, reject});socket.send(JSON.stringify({id, method, params}));
  });
  await send('Runtime.enable');
  const evaluate = async expression => {
    const result = await send('Runtime.evaluate', {expression, returnByValue:true, awaitPromise:true});
    assert.ok(!result.exceptionDetails, JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  const ready = async () => {
    for (let attempt = 0; attempt < 200; attempt++) {
      if (await evaluate("document.body?.dataset.ready === 'true'")) return;
      await delay(100);
    }
    throw new Error('Image loading timeout');
  };
  await ready();
  assert.equal(await evaluate("document.querySelector('#map').options.length"), 27);
  assert.equal(await evaluate("document.querySelector('#rightMode').value"), 'video2');
  const loaded = await evaluate(`(async () => {
    const data = await (await fetch('exports.json')).json();
    let count = 0;
    for (const row of data.records) {
      for (const key of ['nearest', 'lanczos', ...Object.keys(row.variants)]) {
        const image = new Image();image.src = 'maps/' + row.key + '/' + key + '.png';
        await image.decode();
        if (image.naturalWidth !== row.x2_size[0] || image.naturalHeight !== row.x2_size[1]) {
          throw new Error('Wrong canvas: ' + image.src);
        }
        count++;
      }
    }
    return count;
  })()`);
  assert.equal(loaded, 167);
  await evaluate(`const select = document.querySelector('#map');
    select.selectedIndex = [...select.options].findIndex(option => option.text.includes('Ravenshore'));
    select.dispatchEvent(new Event('change'));`);
  await ready();
  assert.equal(await evaluate("document.querySelector('#right').height"), 1020);
  assert.equal(await evaluate("document.querySelector('#rightMode').options.length"), 9);
  const canvas = id => evaluate(`document.querySelector('#${id}').toDataURL()`);
  const setControl = (id, value) => evaluate(`document.querySelector('#${id}').value='${value}';
    document.querySelector('#${id}').dispatchEvent(new Event('change'));`);
  const full = await canvas('right');
  await setControl('zoom', '2');
  const zoom = await canvas('right');
  assert.notEqual(zoom, full);
  await send('Input.dispatchKeyEvent', {type:'keyDown', key:' ', code:'Space', windowsVirtualKeyCode:32});
  assert.equal(await canvas('right'), await canvas('left'));
  await send('Input.dispatchKeyEvent', {type:'keyUp', key:' ', code:'Space', windowsVirtualKeyCode:32});
  assert.equal(await canvas('right'), zoom);
  await setControl('rightMode', 'general4');
  await ready();assert.notEqual(await canvas('right'), zoom);
  await setControl('rightMode', 'video2');
  await ready();
  await setControl('zoom', '1');
  const selected = await evaluate("document.querySelector('#map').selectedIndex");
  await send('Input.dispatchKeyEvent', {type:'keyDown', key:'ArrowRight', code:'ArrowRight', windowsVirtualKeyCode:39});
  await ready();assert.equal(await evaluate("document.querySelector('#map').selectedIndex"), selected + 1);
  const screenshot = await send('Page.captureScreenshot', {format:'png'});
  await writeFile(directory + 'browser_review.png', Buffer.from(screenshot.data, 'base64'));
  assert.equal(errors.length, 0, JSON.stringify(errors));
  const result = {
    result:'PASS', maps:27, images:loaded, url,
    checks:['All candidates and baselines decode at exact canvas sizes', 'Recommended default',
      'Nine-method trial dropdown', '1020-pixel MM8 height', 'Shared zoom', 'Blink and restore',
      'Model selection', 'Keyboard map navigation', 'No browser exceptions'],
  };
  await writeFile(directory + 'browser_check.json', JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result));
} finally {
  socket?.close();browser.kill('SIGTERM');
}
