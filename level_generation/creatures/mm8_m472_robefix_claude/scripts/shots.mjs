// Stage-only shots of the audit compare viewer (left HEAD, right installed) in a 1500x1100 headless Chrome.
//   node shots.mjs <out_prefix> <stem> <role> <views,comma> <ts,comma>   -> <out_prefix>_<view>_t<t>.png
// The compare viewer must be served on 8912 (claude_shared/serve_review.py 8912). VIEWER=<repo-relative dir> picks a private
// copy (mm6_sor1_followup2_claude/scripts/build_cmp.py) instead of the audit's.
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const [out, stem, role, views, ts] = process.argv.slice(2);
const profile = mkdtempSync(join(tmpdir(), 'shots-'));
const port = 9800 + Math.floor(Math.random() * 150);
const chrome = spawn('google-chrome', ['--headless=new', '--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
  `--user-data-dir=${profile}`, `--remote-debugging-port=${port}`, '--window-size=1500,1100', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const finish = c => { chrome.kill('SIGKILL'); try { rmSync(profile, { recursive: true, force: true }); } catch {} process.exit(c); };
let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page'); } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let id = 0; const pending = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); } };
const send = (method, params = {}) => new Promise(r => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
await send('Emulation.setDeviceMetricsOverride', { width: 1500, height: 1100, deviceScaleFactor: 1, mobile: false });
for (const view of views.split(',')) for (const t of ts.split(',')) {
  const viewer = process.env.VIEWER || 'level_generation/creatures/audit_mm678_20261111/compare_viewer';
  const url = `http://127.0.0.1:8912/${viewer}/?role=${role}&view=${view}&t=${t}#${stem}`;
  await send('Page.navigate', { url });
  let ready = false;
  for (let i = 0; i < 120 && !ready; i++) {
    await sleep(1000);
    const r = await send('Runtime.evaluate', { expression: 'document.body && document.body.dataset.ready', returnByValue: true });
    ready = r.result.value === 'true';
  }
  await sleep(2500);
  const box = JSON.parse((await send('Runtime.evaluate', {
    expression: 'JSON.stringify(document.getElementById("stage").getBoundingClientRect())', returnByValue: true })).result.value);
  const shot = await send('Page.captureScreenshot', { format: 'png',
    clip: { x: box.x, y: box.y, width: box.width, height: box.height, scale: 1 } });
  writeFileSync(`${out}_${view}_t${t}.png`, Buffer.from(shot.data, 'base64'));
  console.log('shot', view, t, ready);
}
finish(0);
