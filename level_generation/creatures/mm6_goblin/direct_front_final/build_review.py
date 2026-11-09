"""Build an offline animation/trim-placement viewer; no server, API, or engine install required."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def build():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    actions = {a['name']: [Path(f['source']).stem for f in a['frames']] for a in manifest['actions']}
    html = '''<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Goblin front animations</title>
<style>
body{font:16px system-ui;margin:24px;background:#202422;color:#eee}h1{font-size:24px}
button,select,input{font:inherit;margin:6px;padding:5px}canvas{max-width:100%;border:1px solid #59635d}
.controls{display:flex;align-items:center;flex-wrap:wrap}p{max-width:850px;line-height:1.5}
a{color:#9adbc1}output{font-variant-numeric:tabular-nums}
</style>
<h1>Goblin — front animations</h1>
<p>Original on the left; restored art on the right at the same logical size. Toggle compact crops to check placement.
The cyan line marks the canvas bottom; crosses mark the native actor pivot. Death repeats here for inspection.</p>
<div class="controls"><label>Action <select id="action"></select></label>
<button id="pause">Pause</button><button id="step">Next frame</button>
<label>Background <select id="background"><option value="#252926">Dark</option><option value="#e5e6df">Light</option>
<option value="#6c7750">Grass</option><option value="#858585">Gray</option></select></label>
<label><input type="checkbox" id="trim">Use compact crop</label>
<label><input type="checkbox" id="bounds">Show crop bounds</label>
<label>Zoom <input id="zoom" type="range" min="1" max="3" step="0.5" value="2"></label>
<output id="status"></output></div>
<canvas id="canvas" width="1580" height="658"></canvas>
<p>All moving clips use the native 125 ms frame interval. Standing and corpse hold one frame.
The artwork is staged: these files do not replace your installed goblins.
<a href="front_all_actions_2x.png">Full sheet</a> · <a href="manifest.json">Crop/timing manifest</a> ·
<a href="README.md">Delivery notes</a></p>
<script>
const actions=__ACTIONS__, frames=__FRAMES__;
const el=id=>document.getElementById(id), ctx=el('canvas').getContext('2d'), images={};
for(const [name,record] of Object.entries(frames)){
  images[name]={};
  for(const [kind,path] of Object.entries({native:'previews/native/'+name+'.png',
      aligned:record.exports['2x'].aligned,trimmed:record.exports['2x'].trimmed})){
    const im=new Image(); im.src=path; images[name][kind]=im;
  }
}
for(const name of Object.keys(actions)){const o=document.createElement('option');o.textContent=name;el('action').append(o);}
let index=0,playing=true,last=performance.now();
el('action').onchange=()=>{index=0;last=performance.now();};
el('pause').onclick=()=>{playing=!playing;el('pause').textContent=playing?'Pause':'Play';last=performance.now();};
el('step').onclick=()=>{playing=false;el('pause').textContent='Play';index=(index+1)%actions[el('action').value].length;};
function draw(now){
 const list=actions[el('action').value];
 if(playing&&now-last>=125){index=(index+Math.floor((now-last)/125))%list.length;last+=Math.floor((now-last)/125)*125;}
 const name=list[index], row=frames[name].exports['2x'], imgs=images[name], zoom=Number(el('zoom').value);
 const c=el('canvas'); if(c.width!==790*zoom){c.width=790*zoom;c.height=329*zoom;}
 ctx.setTransform(zoom,0,0,zoom,0,0);ctx.fillStyle=el('background').value;ctx.fillRect(0,0,790,329);
 ctx.imageSmoothingEnabled=true;
 if(imgs.native.complete&&imgs.native.naturalWidth)ctx.drawImage(imgs.native,20,20,355,289);
 const crop=row.crop_xywh, selected=el('trim').checked?imgs.trimmed:imgs.aligned;
 if(selected.complete&&selected.naturalWidth){
  if(el('trim').checked)ctx.drawImage(selected,415+crop[0]/2,20+crop[1]/2,crop[2]/2,crop[3]/2);
  else ctx.drawImage(selected,415,20,355,289);
 }
 ctx.strokeStyle='#55aeca';ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(20,309);ctx.lineTo(770,309);ctx.stroke();
 for(const x of [197.5,592.5]){ctx.beginPath();ctx.moveTo(x-5,309);ctx.lineTo(x+5,309);
  ctx.moveTo(x,304);ctx.lineTo(x,314);ctx.stroke();}
 if(el('bounds').checked){ctx.strokeStyle='#d8a34c';ctx.strokeRect(415+crop[0]/2,20+crop[1]/2,crop[2]/2,crop[3]/2);}
 el('status').textContent=name+' · '+(index+1)+' / '+list.length;
 requestAnimationFrame(draw);
}
requestAnimationFrame(draw);
</script></html>'''
    html = html.replace('__ACTIONS__', json.dumps(actions)).replace('__FRAMES__', json.dumps(manifest['frames']))
    (ROOT / 'review.html').write_text(html)


if __name__ == '__main__':
    build()
