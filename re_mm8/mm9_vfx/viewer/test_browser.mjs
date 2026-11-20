// Headless Chrome through a private DevTools pipe; no browser automation dependencies.
import {spawn} from 'node:child_process';
import {mkdtempSync, writeFileSync, mkdirSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import assert from 'node:assert/strict';

const url = process.argv[2] ?? 'http://127.0.0.1:8099/';
const output = resolve(process.argv[3] ?? 'work/mm9_vfx/viewer_checks');
mkdirSync(output, {recursive: true});
const profile = mkdtempSync(join(tmpdir(), 'mm9-fx-chrome-'));
const chrome = spawn('google-chrome', ['--headless', '--no-sandbox', '--disable-dev-shm-usage',
    '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--remote-debugging-pipe',
    '--no-first-run', '--no-default-browser-check', '--disable-background-networking',
    '--autoplay-policy=no-user-gesture-required', '--user-data-dir='+profile],
    {stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe']});
let nextId = 0, pending = new Map(), buffer = '', errors = [], stderr = '';
chrome.stderr.on('data', data => { stderr += data; });
for (const pipe of [chrome.stdio[3], chrome.stdio[4]]) pipe.on('error', () => {});
chrome.on('exit', code =>
{
    for (const {reject, timer} of pending.values())
    {
        clearTimeout(timer); reject(new Error(`Chrome exited (${code}): ${stderr.slice(-2000)}`));
    }
    pending.clear();
});
chrome.stdio[4].on('data', data =>
{
    buffer += data.toString();
    for (let at; (at = buffer.indexOf('\0')) >= 0;)
    {
        const message = JSON.parse(buffer.slice(0, at)); buffer = buffer.slice(at+1);
        if (message.id && pending.has(message.id))
        {
            const {resolve, reject, timer} = pending.get(message.id); pending.delete(message.id); clearTimeout(timer);
            if (message.error) reject(new Error(JSON.stringify(message.error))); else resolve(message.result);
        }
        if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails);
    }
});
function command(method, params = {}, sessionId)
{
    return new Promise((resolve, reject) =>
    {
        const id = ++nextId, timer = setTimeout(() => reject(new Error('CDP timed out: '+method+'\n'+stderr.slice(-1500))), 20000);
        pending.set(id, {resolve, reject, timer});
        chrome.stdio[3].write(JSON.stringify({id, method, params, ...(sessionId ? {sessionId} : {})})+'\0');
    });
}
let session;
async function evaluate(expression)
{
    const result = await command('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true}, session);
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
}
try
{
    const {targetId} = await command('Target.createTarget', {url: 'about:blank'});
    session = (await command('Target.attachToTarget', {targetId, flatten: true})).sessionId;
    await command('Runtime.enable', {}, session);
    await command('Page.enable', {}, session);
    await command('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false}, session);
    await command('Page.navigate', {url}, session);
    await evaluate(`new Promise((resolve,reject) => {
        let n=0; const timer=setInterval(() => {
            if(window.fxViewer) { clearInterval(timer); resolve(true); }
            else if(++n>150) { clearInterval(timer); reject(document.getElementById('loading')?.textContent); }
        },100);
    })`);
    assert.equal(await evaluate('fxViewer.catalog().effects.length'), 51);
    await evaluate(`fxViewer.seek(.55)`);
    const initial = await evaluate('fxViewer.state()');
    assert.ok(initial.particles > 0); assert.equal(initial.glError, 0);
    for (const [name, time, file] of [['spell-column of fire', .55, 'column-of-fire'],
        ['spell-column of fire', 2, 'column-of-fire-rise'], ['spell-armor', .65, 'armor'],
        ['spell-death\'s touch', 1, 'deaths-touch'], ['fireblue', .8, 'blue-fire'],
        ['openyamm:fx/healing_bloom', .75, 'healing-bloom'],
        ['openyamm:fx/ember_impact', .35, 'ember-impact'],
        ['openyamm:fx/arcane_pulse', .3, 'arcane-pulse']])
    {
        await evaluate(`document.getElementById('monk').checked = ${!name.startsWith('openyamm:')};
            fxViewer.select(${JSON.stringify(name)})`);
        await evaluate(`fxViewer.seek(${time})`);
        const state = await evaluate('fxViewer.state()');
        assert.equal(state.glError, 0, name);
        const {data} = await command('Page.captureScreenshot', {format: 'png'}, session);
        writeFileSync(join(output, file+'.png'), Buffer.from(data, 'base64'));
        console.log(name, JSON.stringify(state));
    }
    // Select every available effect and force a rendered intermediate frame.
    const names = await evaluate('fxViewer.catalog().effects.map(e=>e.name)');
    for (const name of names)
    {
        await evaluate(`fxViewer.select(${JSON.stringify(name)})`);
        await evaluate('fxViewer.seek(.7)');
        const state = await evaluate('fxViewer.state()');
        assert.equal(state.glError, 0, name);
        assert.ok(state.warnings.length === 0 || ['ghost', 'blobby'].includes(name), JSON.stringify(state));
    }
    await evaluate(`document.getElementById('search').value='fire';
        document.getElementById('search').dispatchEvent(new Event('input'))`);
    assert.equal(await evaluate(`document.querySelectorAll('#effects button').length`), 3);
    await evaluate(`document.getElementById('monk').checked = true; fxViewer.select('spell-column of fire')`);
    await evaluate(`document.getElementById('sound').click()`);
    await evaluate(`new Promise(resolve => setTimeout(resolve, 900))`);
    assert.ok(await evaluate('fxViewer.activeSounds()') > 0, 'Sound component should be playing');
    await evaluate(`document.getElementById('pause').click()`);
    assert.equal(await evaluate('fxViewer.activeSounds()'), 0, 'Pause should stop audio');
    // Monk skin has an all-zero alpha channel, but the model material is opaque.
    await evaluate(`fxViewer.seek(100);
        window.readPreview = () => {
            const canvas=document.getElementById('canvas'), gl=canvas.getContext('webgl2');
            const pixels=new Uint8Array(canvas.width*canvas.height*4);
            gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
            return pixels;
        };
        window.withMonk=readPreview(); document.getElementById('monk').click();
        new Promise(resolve => { const timer=setInterval(() => {
            if(!fxViewer.state().loading) { clearInterval(timer); resolve(); }
        },50); })`);
    const changed = await evaluate(`fxViewer.seek(100);
        readPreview().reduce((count,value,i) => count+(value!==withMonk[i]),0)`);
    assert.ok(changed > 1500, 'Target monk should visibly render');
    assert.equal(errors.length, 0, JSON.stringify(errors));
    console.log('Browser checks passed: all 51 effects, search, screenshots, sound, pause and visible monk; no JS/WebGL errors.');
}
finally
{
    for (const {timer} of pending.values()) clearTimeout(timer);
    if (chrome.exitCode === null && chrome.signalCode === null)
    {
        chrome.kill('SIGTERM');
        await new Promise(resolve => chrome.once('exit', resolve));
    }
    rmSync(profile, {recursive: true, force: true});
}
