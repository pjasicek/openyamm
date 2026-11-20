"""Build the self-contained offline player, GIFs and comparison board from exported frames."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def main():
    manifest = json.loads((HERE/'manifest.json').read_text())
    html = r'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MM5 Troll Grunt · MM7/MM8 sprite adaptation</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#191d22;color:#e4ded4;font:15px system-ui,sans-serif}
main{max-width:1200px;margin:auto;padding:28px}h1{font-size:29px;margin:4px 0 8px}
p{color:#b3b4b5;line-height:1.6;max-width:900px}small{color:#a3a6ab}.bar{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:20px 0}
select,button,input{background:#30353c;color:#eee;border:1px solid #545b65;border-radius:5px;padding:7px}
label{display:flex;align-items:center;gap:7px}.player{display:grid;grid-template-columns:minmax(340px,1fr) 320px;gap:20px}
canvas{width:100%;background:#353a40;border:1px solid #555e69;border-radius:6px}
.card{background:#242a31;border:1px solid #3c444e;padding:18px;border-radius:6px}.card img{max-width:100%}
.strip{display:flex;gap:6px;flex-wrap:wrap;margin:16px 0}.strip img{width:92px;background:#343a40;cursor:pointer;border:1px solid #62676e}
a{color:#c7bc83}#readout{font:13px monospace;margin:12px 0;white-space:pre-line}
details{margin:20px 0}summary{cursor:pointer}.contact{width:100%;margin-top:12px}
@media(max-width:780px){.player{grid-template-columns:1fr}}
</style><main><small>OPENYAMM · CREATURE STUDY</small>
<h1>Troll Grunt — Darkside of Xeen</h1>
<p>The MM5 creature reimagined as a restored MM7/MM8 sprite family. Its teal skin, red hair, blue vest,
purple trousers and wooden club remain shared across the views. This is newly authored animation using the MM8 troll's
frame structure and timing. Original MM5 assets are preserved.</p>
<div class="bar"><label>Action <select id="action"></select></label>
<label>View <select id="view"></select></label><button id="play">Pause</button>
<label>Speed <select id="speed"><option value=".5">½×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label>
<label>Background <select id="background"><option value="#353a40">Slate</option><option value="#eeeeea">Light</option><option value="#101112">Dark</option></select></label>
<label><input id="mask" type="checkbox">Vest mask</label><label><input id="guides" type="checkbox" checked>Ground / pivot</label>
<label><input id="repeat" type="checkbox" checked>Repeat preview</label></div>
<div class="player"><section><canvas id="stage" width="640" height="560"></canvas>
<div class="bar"><label>Frame <input id="frame" type="range" min="0" value="0"></label><span id="counter"></span></div>
<div id="readout"></div></section><aside class="card"><h3>MM5 design source</h3>
<canvas id="native" width="280" height="190"></canvas>
<p>056.mon: 8 frontal frames<br>056.att: 4 frontal attack frames</p>
<h3>Coverage</h3><p id="coverage"></p>
<p>Five stored views plus three reflected views. Attack 2 reuses Attack; death starts with two hit frames;
the final corpse is held. Reflected views also reflect the weapon hand, following the MM7/MM8 convention.</p>
<p><a href="manifest.json">Placement / animations</a> · <a href="README.md">Method and limitations</a></p></aside></div>
<div class="strip" id="strip"></div><details><summary>All-frame contact sheets</summary>CONTACTS</details>
<details><summary>MM5 versus native MM7/MM8 style references</summary><img class="contact" src="references/mm7_mm8_style.png">
<img class="contact" src="references/mm5_native.png"></details>
<details><summary>Edge audit</summary><img class="contact" src="review/edge_closeups.png"></details>
<script>const data=MANIFEST;
const el=id=>document.getElementById(id),stage=el('stage'),ctx=stage.getContext('2d');
const action=el('action'),view=el('view'),slider=el('frame');let playing=true,index=0,elapsed=0,last=0;
const pages=data.pages.map(p=>{const im=new Image();im.src=p.base;return im});
const overlays={};const frames={};
for(const [name,f] of Object.entries(data.frames)){let im=new Image();im.src='aligned/'+name+'.png';frames[name]=im;
 let mask=new Image();mask.src='masks/'+name+'.png';overlays[name]=mask}
for(const name of Object.keys(data.animations)){if(data.animations[name].views['0'].every(f=>data.frames[f.frame]))action.add(new Option(name,name))}
data.direction_labels.forEach((name,i)=>view.add(new Option(name,i)));
const params=new URLSearchParams(location.search);action.value=params.get('action')||'walk';view.value=params.get('view')||'0';
if(params.has('frame')){index=Number(params.get('frame'));playing=false;el('play').textContent='Play'}
function sequence(){return data.animations[action.value].views[view.value]}
function reset(){index=0;elapsed=0;refresh()}
function refresh(){const seq=sequence();slider.max=seq.length-1;el('strip').replaceChildren();
seq.forEach((f,i)=>{const im=new Image();im.src='aligned/'+f.frame+'.png';im.title=f.frame;
if(f.mirrored)im.style.transform='scaleX(-1)';im.onclick=()=>{index=i;playing=false;el('play').textContent='Play'};el('strip').append(im)})}
action.onchange=reset;view.onchange=reset;slider.oninput=()=>{index=+slider.value;playing=false;el('play').textContent='Play'};
el('play').onclick=()=>{playing=!playing;el('play').textContent=playing?'Pause':'Play'};
el('coverage').textContent=data.coverage.exported+' / '+data.coverage.expected+' stored sprites · '+data.pages.length+
' atlas pages · '+(data.decoded_memory_bytes/1048576).toFixed(2)+' MiB decoded, including masks and padding. Staged; not installed.';
const originals={mon:[],att:[]};for(const [ext,count] of [['mon',8],['att',4]])for(let i=0;i<count;i++){
const im=new Image();im.src='native/mm5_'+ext+'_'+i+'.png';originals[ext].push(im)}
function draw(t){const dt=last?Math.min(t-last,100):0;last=t;const seq=sequence();
if(playing){elapsed+=dt*+el('speed').value;while(elapsed>=seq[index].duration_ms){elapsed-=seq[index].duration_ms;
if(index+1<seq.length)index++;else if(data.animations[action.value].playback==='loop'||el('repeat').checked)index=0;
else{playing=false;el('play').textContent='Play';break}}}
index=Math.min(index,seq.length-1);slider.value=index;const item=seq[index],f=data.frames[item.frame];
ctx.fillStyle=el('background').value;ctx.fillRect(0,0,640,560);
if(el('guides').checked){ctx.strokeStyle='#8c8e7777';ctx.beginPath();ctx.moveTo(0,504);ctx.lineTo(640,504);
ctx.moveTo(320,0);ctx.lineTo(320,560);ctx.stroke()}
if(f){const [x,y,w,h]=f.atlas_xywh;ctx.save();ctx.translate(320,504);ctx.scale(.85,.85);if(item.mirrored)ctx.scale(-1,1);
const pivot=data.logical_pivot.map(x=>x*2),px=f.crop_origin_px[0]-pivot[0],py=f.crop_origin_px[1]-pivot[1];
if(pages[f.page].complete)ctx.drawImage(pages[f.page],x,y,w,h,px,py,w,h);
if(el('mask').checked&&overlays[item.frame].complete){ctx.globalAlpha=.55;ctx.drawImage(overlays[item.frame],-pivot[0],-pivot[1])}ctx.restore();
el('readout').textContent=item.frame+' · '+item.duration_ms+' ms · '+(item.mirrored?'mirrored':'stored')+'\n'+
'Common logical canvas '+data.logical_canvas.join(' × ')+'; pivot ('+data.logical_pivot.join(', ')+'); physical export 2×.'}
el('counter').textContent=(index+1)+' / '+seq.length;
const nc=el('native').getContext('2d');nc.fillStyle=el('background').value;nc.fillRect(0,0,280,190);
const ext=action.value.startsWith('attack')?'att':'mon',ni=originals[ext][Math.floor(t/125)%originals[ext].length];
if(ni.complete)nc.drawImage(ni,15,15);requestAnimationFrame(draw)}refresh();requestAnimationFrame(draw);
</script></main>'''
    contacts=''.join(f'<img class="contact" src="review/{p.name}">' for p in sorted((HERE/'review').glob('contact_*.jpg')))
    (HERE/'viewer.html').write_text(html.replace('MANIFEST',json.dumps(manifest)).replace('CONTACTS',contacts))
    src=REPO/'reference/mm4_5_world_of_xeen/unpacked/sprites/dark'
    for ext in ['mon','att']:
        meta=json.loads((src/f'056.{ext}/frames.json').read_text())
        for i,record in enumerate(meta['frames']):
            im=Image.open(src/f'056.{ext}'/record['file']);canvas=Image.new('RGBA',(250,160))
            canvas.paste(im,tuple(record['origin']));canvas.save(HERE/f'native/mm5_{ext}_{i}.png')
    for action in ['walk','attack','hit','fidget','death']:
        record=manifest['animations'][action];seq=record['views']['0']
        if not all(entry['frame'] in manifest['frames'] for entries in record['views'].values() for entry in entries):
            continue
        gif=[]
        for i in range(len(seq)):
            board=Image.new('RGB',(1500,320),(42,45,49));draw=ImageDraw.Draw(board)
            for v in range(5):
                entry=record['views'][str(v)][i];im=Image.open(HERE/f'aligned/{entry["frame"]}.png')
                im=im.resize((300,250),Image.Resampling.LANCZOS);board.paste(im,(v*300,30),im)
                draw.text((v*300+12,290),manifest['direction_labels'][v],fill='#d5c997')
            gif.append(board)
        gif[0].save(HERE/f'review/{action}.gif',save_all=True,append_images=gif[1:],loop=0,
                    duration=[round((i+1)*125/10)*10-round(i*125/10)*10 for i in range(len(seq))],disposal=2)
    board=Image.new('RGB',(1500,500),(36,39,44));draw=ImageDraw.Draw(board)
    draw.text((25,18),'MM5 TROLL GRUNT  /  MM7-MM8 STYLE ADAPTATION',fill='#e2d5a4')
    native=Image.open(HERE/'native/mm5_mon_0.png');native=native.crop(native.getbbox())
    board.paste(native,(24,405-native.height),native);draw.text((25,439),'MM5 original',fill='white')
    for v in range(5):
        im=Image.open(HERE/f'aligned/m476sa{v}.png').crop((128,108,640,556))
        im=im.resize((245,214),Image.Resampling.LANCZOS)
        x=265+v*245;board.paste(im,(x,175),im);draw.text((x+25,439),manifest['direction_labels'][v],fill='white')
    draw.text((25,471),f'{manifest["coverage"]["exported"]} stored sprites / 5 stored views + 3 mirrored views / staged art package',fill='#ababab')
    board.save(HERE/'review/overview.png')
    contacts = Image.new('RGB', (2560, 1560), (44, 46, 49))
    for i in range(4):
        contact = Image.open(HERE/f'review/contact_{i}.jpg')
        contacts.paste(contact, ((i % 2)*1280, (i // 2)*780))
    contacts.save(HERE/'review/all_sprites.jpg', quality=95)
    print('Wrote viewer.html, comparison overview and available animation GIFs')


if __name__=='__main__':
    main()
