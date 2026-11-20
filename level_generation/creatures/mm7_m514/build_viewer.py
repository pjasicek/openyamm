"""Build a self-contained native/restored viewer for every descriptor, palette and atlas page."""
import base64
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def run(root=HERE):
    manifest = json.loads((root / 'manifest.json').read_text())
    sources = json.loads((root / 'sources.json').read_text())

    def uri(value):
        if isinstance(value, Path):
            raw = value.read_bytes()
        else:
            buffer = io.BytesIO()
            value.save(buffer, format='PNG')
            raw = buffer.getvalue()
        return 'data:image/png;base64,' + base64.b64encode(raw).decode()

    native, appearances, overlays = {}, {}, []
    for variant in manifest['variants']:
        palette = variant['palette_id']
        colors = np.frombuffer((REPO / sources['palette_sources'][str(palette)]['path']).read_bytes()[:768],
                               np.uint8).reshape(256, 3)
        native[str(palette)] = {}
        for name in manifest['frames']:
            indices = np.array(Image.open(REPO / sources['sources'][name]['path']))
            native[str(palette)][name] = uri(Image.fromarray(np.dstack((colors[indices], (indices != 0)*255)).astype(np.uint8)))
        appearances[str(palette)] = [uri(root / f'previews/palette_{palette}_page_{i}.png')
                                    for i in range(len(manifest['pages']))]
    for page in manifest['pages']:
        base = np.array(Image.open(root / page['base']))
        mask = np.array(Image.open(root / page['mask']))
        if mask.ndim == 2:
            weight = mask[:, :, None] / 255 * .7
            base[:, :, :3] = np.round(base[:, :, :3]*(1-weight) + np.array([0, 200, 255])*weight).astype(np.uint8)
        else:
            colors = np.array([[0,200,255],[255,180,0],[220,50,220]])
            rgb = base[:, :, :3].astype(float)
            for channel in range(3):
                weight = mask[:, :, channel, None]/255*.7
                rgb = rgb*(1-weight)+colors[channel]*weight
            base[:, :, :3] = np.round(rgb).astype(np.uint8)
        overlays.append(uri(Image.fromarray(base)))
    data = dict(manifest=manifest, native=native, appearances=appearances, overlays=overlays)
    html = '''<!doctype html><meta charset="utf-8"><title>Native creature restoration review</title>
<style>body{font:16px system-ui;background:#242624;color:#eee;margin:24px}canvas{border:1px solid #777}
label,button{margin-right:12px}select,input,button{font:inherit}a{color:#bfe7fc}</style>
<h1 id="title"></h1><p>Native timing, view mirrors, palette and descriptor scale. Staged offline artwork.</p>
<p><label>Descriptor <select id="descriptor"></select></label><label>Action <select id="action"></select></label>
<label>View <select id="view"></select></label><label>Background <select id="background">
<option value="#292b29">Dark</option><option value="#eaeaea">Light</option></select></label>
<label><input id="overlay" type="checkbox">Mask overlay</label></p>
<p><button id="play">Pause</button><label>Frame <input id="frame" type="range" min="0" value="0"></label>
<label>Zoom <input id="zoom" type="range" min="0.1" max="4" step="0.1" value="2"></label></p>
<p id="status">Loading embedded images…</p><canvas id="canvas" width="1200" height="700"></canvas>
<p><a href="review/all_comparison.png">All native/base poses</a> · <a href="review/edge_closeups.png">Edges</a>
 · <a href="manifest.json">Placement and animations</a> · <a href="validation.json">Validation</a></p>
<script>const data=DATA;
const $=id=>document.getElementById(id),m=data.manifest,native={},appearances={},overlays=[];
const load=src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=reject;im.src=src});
let playing=true,start=performance.now(),fixed=0;
$('title').textContent=m.creature+' — restored sprites';
for(const [d,animations] of Object.entries(m.descriptor_animations)){
 const f=animations.standing.directions['0'][0];
 $('descriptor').add(new Option(d+' · palette '+f.palette_id+' · scale '+f.scale.toFixed(2),d));}
for(const a of Object.keys(m.animations))$('action').add(new Option(a,a));
for(let i=0;i<8;i++)$('view').add(new Option(i,i));
const maxScale=Math.max(...Object.values(m.descriptor_animations).map(a=>a.standing.directions['0'][0].scale));
if(maxScale>2)$('zoom').value=Math.max(.1,Math.floor(20/maxScale)/10);
const q=new URLSearchParams(location.search);
for(const id of ['action','view','descriptor','zoom'])if(q.has(id))$(id).value=q.get(id);
if(!q.has('action'))$('action').value='walk';
if(q.has('palette')){const v=m.variants.find(v=>v.palette_id===+q.get('palette'));if(v)$('descriptor').value=v.descriptors[0]}
if(q.has('frame')){playing=false;fixed=+q.get('frame');$('play').textContent='Play'}
if(q.get('background')==='light')$('background').value='#eaeaea';
$('overlay').checked=q.get('overlay')==='1';
$('play').onclick=()=>{playing=!playing;start=performance.now();$('play').textContent=playing?'Pause':'Play'};
$('frame').oninput=()=>{fixed=+$('frame').value;playing=false;$('play').textContent='Play'};
for(const id of ['action','view','descriptor'])$(id).onchange=()=>{fixed=0;start=performance.now()};
(async()=>{
 await Promise.all(Object.entries(data.native).map(async([p,frames])=>{
 native[p]={};await Promise.all(Object.entries(frames).map(async([n,src])=>native[p][n]=await load(src)));}));
 await Promise.all(Object.entries(data.appearances).map(async([p,pages])=>appearances[p]=await Promise.all(pages.map(load))));
 overlays.push(...await Promise.all(data.overlays.map(load)));
 const c=$('canvas'),ctx=c.getContext('2d');
 function draw(now){
 const anim=m.descriptor_animations[$('descriptor').value][$('action').value],seq=anim.directions[$('view').value];
 if(anim.empty){
 ctx.fillStyle=$('background').value;ctx.fillRect(0,0,c.width,c.height);
 $('frame').max=0;$('frame').value=0;$('status').textContent='Native empty action: '+anim.native_group;
 window.reviewFrame={empty:true,playing};requestAnimationFrame(draw);return;}
 let index=Math.min(fixed,seq.length-1);const total=seq.reduce((sum,f)=>sum+f.duration_ms,0);
 if(playing){let t=anim.loop?(now-start)%total:Math.min(now-start,total-.001);index=0;
 while(index<seq.length-1&&t>=seq[index].duration_ms){t-=seq[index].duration_ms;index++}}
 $('frame').max=seq.length-1;$('frame').value=index;
 const f=seq[index],meta=m.frames[f.frame],z=+$('zoom').value*f.scale;
 ctx.fillStyle=$('background').value;ctx.fillRect(0,0,c.width,c.height);ctx.imageSmoothingEnabled=true;
 for(let side=0;side<2;side++){const px=side*600+300,py=620;
 ctx.strokeStyle='#777';ctx.beginPath();ctx.moveTo(side*600,py);ctx.lineTo(side*600+600,py);ctx.stroke();
 ctx.save();ctx.beginPath();ctx.rect(side*600,40,600,660);ctx.clip();ctx.translate(px,py);ctx.scale((f.mirror?-1:1)*z,z);
 if(!side)ctx.drawImage(native[f.palette_id][f.frame],-m.logical_pivot[0],-m.logical_pivot[1]);
 else{const [x,y,w,h]=meta.atlas_xywh,[ox,oy]=meta.crop_origin_px;
 const atlas=$('overlay').checked?overlays[meta.page]:appearances[f.palette_id][meta.page];
 ctx.drawImage(atlas,x,y,w,h,ox/2-m.logical_pivot[0],oy/2-m.logical_pivot[1],w/2,h/2)}ctx.restore();
 ctx.fillStyle=$('background').value==='#eaeaea'?'#111':'#eee';ctx.font='16px system-ui';
 ctx.fillText((side?'Restored atlas':'Native')+' · palette '+f.palette_id,side*600+20,28)}
 $('status').textContent=f.frame+' · '+f.duration_ms+' ms · '+(f.mirror?'mirrored':'stored')+
 ' · frame '+(index+1)+'/'+seq.length+' · scale '+f.scale;
 window.reviewFrame={name:f.frame,index,mirror:f.mirror,scale:f.scale,palette:f.palette_id,playing};
 requestAnimationFrame(draw)}requestAnimationFrame(draw);
})().catch(error=>{$('status').textContent='Viewer failed: '+error;throw error});
</script>'''
    (root / 'viewer.html').write_text(html.replace('DATA', json.dumps(data)))
    print('Wrote self-contained viewer with all native palettes and descriptors')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=HERE)
    run(parser.parse_args().project.resolve())
