"""Review selected partial sampling repairs without claiming full-family delivery."""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project', type=Path, required=True)
a = parser.parse_args()
p = a.project
reg = json.loads((p/'registration.json').read_text())
old = json.loads((p/'checkpoints/before_sampling_repair/registration.json').read_text())
src = json.loads((p/'sources.json').read_text())
changed = sorted(n for n in reg if reg[n]['batch'] != old[n]['batch'])
unchanged = sorted(set(reg)-set(changed))
assert set(reg) == set(old), 'Never lose prior native frame coverage.'
assert all(reg[n] == old[n] for n in unchanged)
hashes = json.loads((p/'checkpoints/before_sampling_repair/pixel_hashes.json').read_text())
assert all(hashlib.sha256((p/f).read_bytes()).hexdigest() == sha
           for f, sha in hashes.items() if Path(f).stem in unchanged)
assert all(2/reg[n]['scale'] >= 2 for n in changed)
window = [-16, -16, 280, 272]
w, h = window[2]-window[0], window[3]-window[1]

def sprite(n, restored, scale=1):
    if restored:
        origin = reg[n]['canvas_origin_px']
        im = Image.open(p/f'aligned_2x/{n}.png').crop(
            [window[j]*2-origin[j % 2] for j in range(4)])
        if scale != 2:
            im = im.convert('RGBa').resize((w*scale, h*scale), Image.Resampling.LANCZOS).convert('RGBA')
    else:
        im = Image.open(p/f'native/{n}.png').crop(window).resize((w*scale, h*scale), Image.Resampling.NEAREST)
    return im

views = range(5) if p.name == 'mm7_m198' else [2, 3]
binding = next(iter(src['descriptor_bindings'].values()))['attack']
group = src['groups'][binding]
sequences = {}
for v in views:
    seq = [dict(frame=e['texture_name']+str(v), duration_ms=e['frame_length_raw']*62.5) for e in group['frames']]
    assert all(e['frame'] in reg for e in seq)
    sequences[str(v)] = seq
    out = Image.new('RGB', (w*4, (h*2+40)*math.ceil(len(seq)/4)), '#303030')
    draw = ImageDraw.Draw(out)
    for i, e in enumerate(seq):
        n = e['frame'];x, y = i%4*w, i//4*(h*2+40)
        state = 'REPLACED' if n in changed else 'OLD <2x' if 2/reg[n]['scale'] < 2 else 'retained'
        draw.text((x+3, y+3), f'{i+1} {n} {e["duration_ms"]}ms {state}', fill='white')
        for enhanced in [False, True]:
            im = sprite(n, enhanced)
            tile = Image.new('RGB', im.size, '#e8e8e8' if enhanced else '#303030')
            tile.paste(im, mask=im.getchannel('A'))
            out.paste(tile, (x, y+24+int(enhanced)*(h+8)))
    out.save(p/f'review/repair_attack_{v}.png')

# Every replacement at actual exported pixels, two neutral backgrounds, no enlargement.
for i, n in enumerate(changed):
    if i%4 == 0:
        out = Image.new('RGB', (w*4, (h*2+28)*2), '#e8e8e8')
        draw = ImageDraw.Draw(out)
    x, y = i%2*w*2, i%4//2*(h*2+28)
    im = sprite(n, True, 2)
    bg = '#e8e8e8' if i%2 == 0 else '#303030'
    tile = Image.new('RGB', im.size, bg);tile.paste(im, mask=im.getchannel('A'))
    out.paste(tile, (x, y+28));draw.text((x+3,y+5), f'{n} actual 2x; master {2/reg[n]["scale"]:.3f}x', fill='black')
    if i%4 == 3 or i == len(changed)-1:
        out.save(p/f'review/repair_actual_2x_{i//4}.png')

# Self-contained offline base-art sequence viewer; explicitly partial, with old frames labeled.
images = {n: {k: 'data:image/png;base64,'+base64.b64encode((p/f'{folder}/{n}.png').read_bytes()).decode()
              for k, folder in [('native','native'),('enhanced','aligned_2x')]} for n in reg if n in {e['frame'] for seq in sequences.values() for e in seq}}
data = dict(images=images, sequences=sequences, registration=reg, changed=changed)
html = '''<!doctype html><meta charset="utf-8"><title>Partial sampling repair review</title>
<style>body{background:#303030;color:#eee;font:16px sans-serif}canvas{background:#ddd}label{margin:12px}button,select{font:inherit}</style>
<p>Partial MM7 sampling repair — base artwork only. Unrepaired frames are explicitly labeled. Full-family validation and variants remain pending.</p>
<label>Stored attack view <select id="view"></select></label><button id="play">Pause</button><button id="step">Step</button>
<label><input id="mirror" type="checkbox">Mirror preview</label><label><input id="dark" type="checkbox">Dark background</label>
<p id="status"></p><canvas id="canvas" width="1184" height="576"></canvas>
<script>const data=DATA;let index=0, playing=true, elapsed=0, last=0;const cache={};
const view=document.getElementById('view'),canvas=document.getElementById('canvas'),ctx=canvas.getContext('2d');
for(const v of Object.keys(data.sequences))view.add(new Option(v,v));
const query=new URLSearchParams(location.search);if(data.sequences[query.get('view')])view.value=query.get('view');index=Math.min(data.sequences[view.value].length-1,Math.max(0,Number(query.get('frame')||0)));playing=query.get('paused')!=='1';document.getElementById('play').textContent=playing?'Pause':'Play';document.getElementById('mirror').checked=query.get('mirror')==='1';document.getElementById('dark').checked=query.get('dark')==='1';
for(const [n,pair] of Object.entries(data.images)){cache[n]={};for(const [k,src] of Object.entries(pair)){const im=new Image();im.src=src;cache[n][k]=im;}}
view.onchange=()=>{index=0;elapsed=0;};document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'Pause':'Play';};
document.getElementById('step').onclick=()=>{playing=false;document.getElementById('play').textContent='Play';index=(index+1)%data.sequences[view.value].length;};
function draw(t){const seq=data.sequences[view.value];if(playing){elapsed+=last?t-last:0;while(elapsed>=seq[index].duration_ms){elapsed-=seq[index].duration_ms;index=(index+1)%seq.length;}}last=t;
const n=seq[index].frame,r=data.registration[n],mirror=document.getElementById('mirror').checked;
ctx.fillStyle=document.getElementById('dark').checked?'#303030':'#e8e8e8';ctx.fillRect(0,0,1184,576);
for(const [i,k] of ['native','enhanced'].entries()){ctx.save();ctx.beginPath();ctx.rect(i*592,0,592,576);ctx.clip();ctx.translate(i*592,0);if(mirror){ctx.translate(592,0);ctx.scale(-1,1);}const im=cache[n][k];ctx.imageSmoothingEnabled=k==='enhanced';if(im.complete&&im.naturalWidth){if(k==='native')ctx.drawImage(im,32,32,im.width*2,im.height*2);else ctx.drawImage(im,32+r.canvas_origin_px[0],32+r.canvas_origin_px[1]);}ctx.restore();}
document.getElementById('status').textContent=n+' | '+seq[index].duration_ms+' ms | master '+(2/r.scale).toFixed(3)+'x | '+(data.changed.includes(n)?'replacement':'retained old artwork')+' | native left / restored right, actual 2x pixels';requestAnimationFrame(draw);}
requestAnimationFrame(draw);</script>'''.replace('DATA', json.dumps(data))
(p/'review/sampling_repair_viewer.html').write_text(html)
report = dict(scope='Partial sampling repair; not complete-family acceptance', repaired_frames=changed,
              retained_frames=unchanged, unchanged_registration_exact=True, unchanged_pixels_exact=True,
              sampling_minimum=min(2/reg[n]['scale'] for n in changed), sampling_maximum=max(2/reg[n]['scale'] for n in changed),
              remaining_undersized_frames=sorted(n for n in reg if 2/reg[n]['scale'] < 2-1e-6),
              sequences=sequences, visual_review='pending', variants='Earth: zero masks, palette504 only. Chain: enhanced masks and native variants remain pending.')
(p/'review/sampling_repair_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(p.name, len(changed), 'replacements; remaining', len(report['remaining_undersized_frames']))
