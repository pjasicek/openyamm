#!/usr/bin/env python3
"""Build a local interactive atlas of the surveyed MM5 map arrangement."""

import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / 'inventory.json').read_text())
maps = {m['id']: m for m in data['maps']}
for layer, offset in [('surface', 0), ('sky', 88)]:
    canvas = Image.new('RGB', (1152, 768))
    for col in range(6):
        for row in range(4):
            number = col * 4 + row + 1 + offset
            image = Image.open(ROOT / maps[number]['plan'])
            canvas.paste(image.crop((0, 32, 192, 224)), (col * 192, row * 192))
    canvas.save(ROOT / f'{layer}.png')

payload = {key: data[key] for key in ('maps', 'regions', 'sites', 'transfers', 'mirrorDestinations')}
# The atlas is an index of the user's source material, not a transcript of NPC dialogue.
for site in payload['sites']:
    site['labels'] = [label[:160] for label in site['labels']]
document = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MM5 world feasibility atlas</title>
<style>
body{font:15px system-ui;background:#171d26;color:#e4eaf3;margin:22px}a{color:#9bceff}
h1{font-size:26px}p{line-height:1.5}.muted{color:#adb9c9}button,select{font:inherit;background:#283344;
color:inherit;border:1px solid #8998af;border-radius:5px;padding:8px;cursor:pointer}
.layout{display:grid;grid-template-columns:minmax(500px,1.7fr) minmax(320px,1fr);gap:20px}
.board{position:relative;aspect-ratio:1.5;background-size:100% 100%;image-rendering:pixelated}
.cells{position:absolute;inset:0;display:grid;grid-template-columns:repeat(6,1fr);grid-template-rows:repeat(4,1fr)}
.cells button{border-radius:0;background:transparent;border:1px solid #cdd8e580;text-align:left;padding:5px;
display:flex;flex-direction:column;justify-content:space-between;min-width:0;font-size:12px;text-shadow:0 1px 3px black}
.cells button span{background:#121824bd;padding:3px;align-self:start}.cells button.active{outline:4px solid #fff06b;outline-offset:-5px}
.cells button:hover{background:#ffffff20}.cells button.majorEast{border-right:4px solid #f4dfa0}
.cells button.majorSouth{border-bottom:4px solid #f4dfa0}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0}
aside{background:#242e3c;border-radius:8px;padding:18px;max-height:850px;overflow:auto}
li{margin:6px 0}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:8px;border-bottom:1px solid #46546b}
.town{max-width:100%;image-rendering:pixelated}code{color:#e7cd92}
@media(max-width:950px){.layout{display:block}aside{margin-top:20px;max-height:none}}
</style><h1>Darkside of Xeen → OpenYAMM: feasibility atlas</h1>
<p>Original 6 × 4 geography, with a proposed six-region division. Select a square or region to inspect its source
locations, NPC sites and travel links. These are schematic source maps, not proposed final terrain geometry.</p>
<p><a href="FEASIBILITY.md">Assessment and recommended map list</a> · <a href="maps.csv">All logical maps</a> ·
<a href="sites.csv">Interaction inventory</a> · <a href="travel.csv">Travel records</a> ·
<a href="chunks.csv">Continuation quadrants</a></p>
<div class="controls"><select id="layer" aria-label="World layer"><option value="surface">Surface</option>
<option value="sky">Skyroads</option></select><select id="region" aria-label="Proposed region">
<option value="">Select proposed region</option></select><select id="location" aria-label="Town or dungeon">
<option value="">Select town or dungeon</option></select></div>
<div class="layout"><section><div class="board" id="board"><div class="cells" id="cells"></div></div>
<p class="muted">North ↑. A–F run west to east; 1–4 run north to south. Gold boundaries show proposed 2×2 regions.
Cyan dots: standard services; yellow: NPC dialogue sites; pink: transfers. Counts do not equal physical buildings.
Conditional scripts are indexed, not simulated. MM4 and the WoX bonus endgame are outside the baseline.</p></section>
<aside id="detail"></aside></div><script>
const data = DATA;
const byId = Object.fromEntries(data.maps.map(m=>[m.id,m]));
const detail=document.querySelector('#detail'), layer=document.querySelector('#layer');
const region=document.querySelector('#region'), locationSelect=document.querySelector('#location');
const cells=document.querySelector('#cells'),board=document.querySelector('#board');
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const list=items=>'<ul>'+items.map(s=>'<li>'+s+'</li>').join('')+'</ul>';
for(const r of data.regions){const o=document.createElement('option');o.value=r.id;o.textContent=r.name;region.append(o)}
for(const m of data.maps.filter(m=>m.scope==='MM5'&&!['surface','sky'].includes(m.category))){
 const o=document.createElement('option');o.value=m.id;o.textContent=m.id+' '+m.name;locationSelect.append(o)}
function links(numbers){const found=data.transfers.filter(t=>numbers.includes(t.source)&&t.spatial&&t.destination&&
 !numbers.includes(t.destination));const unique=new Map();
 for(const t of found)unique.set([t.source,t.x,t.y,t.destination].join(','),t);
 return list([...unique.values()].map(t=>escape(byId[t.source].square||t.source)+' ('+t.x+','+t.y+') → '+
 escape(t.destinationName)+' <span class="muted">['+escape(t.kind)+']</span>'))}
function npcs(numbers){const found=data.sites.filter(s=>numbers.includes(s.map)&&s.spatial&&s.npcTitles.length);
 return list(found.map(s=>escape(byId[s.map].square||s.map)+' ('+s.x+','+s.y+'): '+escape(s.npcTitles.join(' / '))))}
function showMap(id){const m=byId[id];region.value='';locationSelect.value=m.category==='surface'||m.category==='sky'?'':id;
 document.querySelectorAll('.cells button').forEach(b=>b.classList.toggle('active',Number(b.dataset.id)===id));
 const sites=data.sites.filter(s=>s.map===id&&s.spatial);
 detail.innerHTML='<h2>'+escape(m.name)+'</h2><p>Source map '+id+' · '+m.width+' × '+m.height+' cells · '+
 m.blocks.length+' storage block(s).</p><p>'+m.npcSites+' NPC sites; '+m.serviceSites+' standard service sites; '+
 m.eventSites+' event-bearing cells.</p><p><a href="'+m.plan+'">Full logical-map plan</a></p>'+
 (!['surface','sky'].includes(m.category)?'<img class="town" src="'+m.plan+'" alt="Logical map">':'')+
 '<h3>Standard services</h3>'+list(sites.filter(s=>s.services.length).map(s=>'('+s.x+','+s.y+'): '+escape(s.services.join(', '))))+
 '<h3>Named NPC interaction sites</h3>'+npcs([id])+'<h3>Transfers to other maps</h3>'+links([id]);
 const names=data.mirrorDestinations.filter(t=>t.destination===id&&t.destination);
 if(names.length)detail.innerHTML+='<h3>Named world landmarks / mirror destinations</h3>'+list(names.map(t=>escape(t.word)+' ('+t.x+','+t.y+')'));
}
function showRegion(id){const r=data.regions.find(r=>r.id===id),numbers=layer.value==='sky'?r.skyMaps:r.sourceMaps;
 locationSelect.value='';document.querySelectorAll('.cells button').forEach(b=>b.classList.toggle('active',numbers.includes(Number(b.dataset.id))));
 detail.innerHTML='<h2>'+escape(r.name)+(layer.value==='sky'?' — sky layer':'')+'</h2><p>Proposed region '+r.id.toUpperCase()+
 ': '+r.squares.join(', ')+'.</p><p>Four 16×16 source outdoor squares become one regional ODM. The original source seams inside '+
 'the region become ordinary traversal; external seams become registered regional travel routes.</p>'+
 '<p>Terrain, town footprints and travel duration require authored adaptation. This is a map grouping, not a uniform coordinate conversion.</p>'+
 '<h3>Town anchors</h3>'+list((layer.value==='sky'?(r.id==='nc'?[37]:[]):r.townMaps).map(id=>escape(byId[id].name)))+
 '<h3>Named NPC sites in these squares</h3>'+npcs(numbers)+'<h3>External and interior entrances</h3>'+links(numbers);
}
function draw(){board.style.backgroundImage='url('+layer.value+'.png)';cells.replaceChildren();
 for(let row=0;row<4;row++)for(let col=0;col<6;col++){const id=col*4+row+1+(layer.value==='sky'?88:0),m=byId[id];
 const b=document.createElement('button');b.dataset.id=id;b.className=(col%2===1?'majorEast ':'')+(row===1?'majorSouth':'');
 const words=data.mirrorDestinations.filter(t=>t.destination===id).map(t=>t.word).slice(0,3);
 b.innerHTML='<span>'+escape(m.square)+'</span><span>'+escape(words.join(' · '))+'</span>';
 b.addEventListener('click',()=>showMap(id));cells.append(b)}
 if(region.value)showRegion(region.value);else showMap(layer.value==='sky'?92:4)}
region.addEventListener('change',()=>{if(region.value)showRegion(region.value)});
locationSelect.addEventListener('change',()=>{if(locationSelect.value)showMap(Number(locationSelect.value))});
layer.addEventListener('change',draw);draw();
</script></html>'''
(ROOT / 'atlas.html').write_text(document.replace('DATA;', json.dumps(payload).replace('<', '\\u003c') + ';'))
print('Wrote interactive atlas and two stitched world-layer PNGs')
