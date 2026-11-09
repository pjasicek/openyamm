// Rasterize the approved SVG sand into a padded atlas; keep the painted frame separate
// so its shape and its smooth native rotation never depend on animation frame rate.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../..');
const out = resolve(repo, 'assets_dev/engine/icons_x2');
const spec = {
  drainSeconds: 8, turnSeconds: 1, framesPerOrientation: 129,
  canvasWidth: 144, canvasHeight: 216,
  cropX: 36, cropY: 42, cropWidth: 72, cropHeight: 132,
  padding: 2, columns: 16, rows: 17,
  frameWidth: 256, frameHeight: 384
};
spec.cellWidth = spec.cropWidth + 2*spec.padding;
spec.cellHeight = spec.cropHeight + 2*spec.padding;
spec.atlasWidth = spec.cellWidth*spec.columns;
spec.atlasHeight = spec.cellHeight*spec.rows;
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const port = 9421;
const browser = spawn('google-chrome', ['--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
  '--allow-file-access-from-files', `--remote-debugging-port=${port}`, '--remote-allow-origins=*',
  `--user-data-dir=/tmp/openyamm-rest-hourglass-export-${Date.now()}`, 'about:blank'], {stdio:'ignore'});
let ws;
try {
  let page;
  for (let i=0; i<100 && !page; ++i) {
    try { page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p=>p.type==='page'); }
    catch {}
    if (!page) await delay(100);
  }
  assert(page, 'Chrome did not start');
  ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  let serial=0;
  const pending=new Map();
  ws.onmessage=event=>{
    const message=JSON.parse(event.data), request=pending.get(message.id);
    if(request) {
      pending.delete(message.id);
      message.error ? request.reject(message.error) : request.resolve(message.result);
    }
  };
  const send=(method,params={})=>new Promise((resolve,reject)=>{
    const id=++serial;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));
  });
  const evaluate=async expression=>{
    const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
    assert(!result.exceptionDetails,JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  await send('Page.enable');
  await send('Page.navigate',{url:pathToFileURL(resolve(here,'index.html')).href+'?phase=0'});
  let ready=false;
  for(let i=0;i<100 && !ready;++i) {
    ready=await evaluate('!!window.hourglassStudy');
    if(!ready)await delay(100);
  }
  assert(ready,'Hourglass preview did not initialize');
  const sandData='data:image/png;base64,'+(await readFile(resolve(here,'art/v2/sand-material.png'))).toString('base64');
  const frameData='data:image/png;base64,'+(await readFile(resolve(here,'art/v2/hourglass-master-v1.png'))).toString('base64');
  await evaluate(`window.exportSpec=${JSON.stringify(spec)};window.sandData=${JSON.stringify(sandData)};
    window.frameData=${JSON.stringify(frameData)};`);
  const result=await evaluate(`(async()=>{
    const spec=window.exportSpec, ns='http://www.w3.org/2000/svg';
    const svg=document.createElementNS(ns,'svg');
    svg.setAttribute('width',spec.atlasWidth);svg.setAttribute('height',spec.atlasHeight);
    const defs=document.createElementNS(ns,'defs'), material=document.createElementNS(ns,'image');
    material.setAttribute('id','shared-sand-material');material.setAttribute('href',window.sandData);
    material.setAttribute('width','768');material.setAttribute('height','768');
    defs.append(material);svg.append(defs);
    const serializer=new XMLSerializer();
    for(let turn=0;turn<2;++turn)for(let frame=0;frame<spec.framesPerOrientation;++frame) {
      const index=turn*spec.framesPerOrientation+frame;
      window.hourglassStudy.setPhase(frame/(spec.framesPerOrientation-1)*8/9,turn);
      const node=window.hourglassStudy.targets[0].querySelector('svg').cloneNode(true);
      node.querySelector('.painted-master').remove();
      const image=node.querySelector('pattern image'), use=document.createElementNS(ns,'use');
      use.setAttribute('href','#shared-sand-material');image.replaceWith(use);
      let text=serializer.serializeToString(node);
      for(const el of node.querySelectorAll('[id]')) {
        const id=el.id, replacement='f'+index+'-'+id;
        text=text.replaceAll('id="'+id+'"','id="'+replacement+'"').replaceAll('#'+id, '#'+replacement);
      }
      const copy=new DOMParser().parseFromString(text,'image/svg+xml').documentElement;
      copy.setAttribute('x',(index%spec.columns)*spec.cellWidth+spec.padding);
      copy.setAttribute('y',Math.floor(index/spec.columns)*spec.cellHeight+spec.padding);
      copy.setAttribute('width',spec.cropWidth);copy.setAttribute('height',spec.cropHeight);
      const scale=1024/spec.canvasWidth;
      copy.setAttribute('viewBox',[spec.cropX,spec.cropY,spec.cropWidth,spec.cropHeight].map(n=>n*scale).join(' '));
      svg.append(copy);
    }
    const image=new Image();
    image.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(serializer.serializeToString(svg));
    await image.decode();
    const atlas=document.createElement('canvas');atlas.width=spec.atlasWidth;atlas.height=spec.atlasHeight;
    const context=atlas.getContext('2d');context.drawImage(image,0,0);
    // The exact same full pile starts the next orientation. Reuse its rotated
    // texels rather than introducing a second SVG clip rasterization at the seam.
    const tileOrigin=index=>[(index%spec.columns)*spec.cellWidth+spec.padding,
      Math.floor(index/spec.columns)*spec.cellHeight+spec.padding];
    for(const [last,first] of [[spec.framesPerOrientation-1,spec.framesPerOrientation],
      [2*spec.framesPerOrientation-1,0]]) {
      const [sx,sy]=tileOrigin(last),[dx,dy]=tileOrigin(first);
      const source=context.getImageData(sx,sy,spec.cropWidth,spec.cropHeight);
      const target=context.createImageData(spec.cropWidth,spec.cropHeight);
      for(let pixel=0;pixel<spec.cropWidth*spec.cropHeight;++pixel) {
        const reverse=spec.cropWidth*spec.cropHeight-1-pixel;
        for(let channel=0;channel<4;++channel)target.data[pixel*4+channel]=source.data[reverse*4+channel];
      }
      context.putImageData(target,dx,dy);
    }
    let occupiedPixels=0, escapedPixels=0;
    const pixels=context.getImageData(0,0,atlas.width,atlas.height).data;
    for(let y=0;y<atlas.height;++y)for(let x=0;x<atlas.width;++x)if(pixels[(y*atlas.width+x)*4+3]) {
      ++occupiedPixels;
      const cx=x%spec.cellWidth,cy=y%spec.cellHeight;
      if(cx<=spec.padding || cx>=spec.cellWidth-spec.padding-1 ||
        cy<=spec.padding || cy>=spec.cellHeight-spec.padding-1)++escapedPixels;
    }
    const frame=document.createElement('canvas');frame.width=spec.frameWidth;frame.height=spec.frameHeight;
    const master=new Image();master.src=window.frameData;await master.decode();
    frame.getContext('2d').drawImage(master,0,0,frame.width,frame.height);
    return {atlas:atlas.toDataURL('image/png'),frame:frame.toDataURL('image/png'),occupiedPixels,escapedPixels};
  })()`);
  assert(result.occupiedPixels>100000,'Sand atlas is empty');
  assert.equal(result.escapedPixels,0,'Sand touches its crop/gutter');
  await mkdir(out,{recursive:true});
  const assets=[];
  for(const [key,name] of [['atlas','obsidian_rest_hourglass_sand.png'],['frame','obsidian_rest_hourglass_frame.png']]) {
    const bytes=Buffer.from(result[key].split(',')[1],'base64');
    await writeFile(resolve(out,name),bytes,{mode:0o644});
    assets.push({file:'assets_dev/engine/icons_x2/'+name,bytes:bytes.length,
      sha256:createHash('sha256').update(bytes).digest('hex')});
  }
  const header=`// Generated by level_generation/ui/obsidian_rest_hourglass_20260929/export_runtime.mjs.
// Regenerate with the approved sand-volume.mjs geometry; do not edit atlas dimensions separately.
#pragma once

namespace OpenYAMM::Game::RestHourglassAtlas
{
${Object.entries(spec).map(([key,value])=>`inline constexpr ${key.endsWith('Seconds')?'float':'int'} ${key} = ${value}${key.endsWith('Seconds')?'.0f':''};`).join('\n')}
}
`;
  await writeFile(resolve(repo,'game/ui/RestHourglassAtlas.h'),header);
  await mkdir(resolve(here,'native'),{recursive:true});
  const receipt={spec,assets,occupiedPixels:result.occupiedPixels,escapedPixels:result.escapedPixels,
    source:'Approved 2140 browser composition; one static master plus two conserved sand orientations.',
    rgbaTextureBytes:spec.atlasWidth*spec.atlasHeight*4+spec.frameWidth*spec.frameHeight*4};
  await writeFile(resolve(here,'native/export.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt,null,2));
} finally {
  ws?.close();browser.kill('SIGTERM');
}
