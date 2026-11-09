"""Build the local directional tile catalogue from the reviewed transition pack."""
import json
from pathlib import Path

P = Path(__file__).resolve().parent
tiles = json.loads((P / 'mask_inventory.json').read_text())['masks']
review = P / 'review'
review.mkdir(exist_ok=True)
template = '''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>New Sorpigal — new dirt transitions</title>
<style>
body{background:#1c2329;color:#eee;font:16px system-ui;margin:30px auto;max-width:1250px;padding:0 20px}
a{color:#99caff}select,button{font:inherit;padding:7px;background:#303b45;color:white;border:1px solid #67737d}
.row{display:flex;flex-wrap:wrap;gap:18px}figure{margin:15px 0}figcaption{margin-bottom:8px}
.tile{width:256px;height:256px}.original{image-rendering:pixelated}.large .tile{width:512px;height:512px}
#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(175px,1fr));gap:16px}
#grid img{width:100%}#grid button{border:0;padding:0;text-align:left;cursor:pointer}
.sheet{max-width:100%}details{padding:16px 0;border-top:1px solid #46515b}code{overflow-wrap:anywhere}
</style>
<h1>New Sorpigal dirt transitions · x2</h1>
<p>All 33 directional transitions use the new dirt master. AI edits add turf fringe, gravel bleed,
and stone contact shading within a narrow boundary band. Tile orientations and connected masks are retained.</p>
<p>Originals are 128×128; finished runtime tiles are 256×256. Version 2 replaces the softened border strips
with continuous quilted material detail, retaining the AI fringe and shading. This is the separate trial.</p>
<p>The trial also includes the newer <a href="../../../mm6_new_sorpigal_water/restoration_v3/review.html">native water v3</a>
animation and its required water-sampling fix.</p>
<label>Tile <select id="tile"></select></label>
<button id="previous">Previous</button> <button id="next">Next</button>
<button id="zoom">View at 512px</button>
<p id="description"></p>
<div class="row" id="comparison">
<figure><figcaption>Original · enlarged nearest</figcaption><img class="tile original" id="native"></figure>
<figure><figcaption>Previous v1 · softened tile borders</figcaption><img class="tile" id="base"></figure>
<figure><figcaption>Current v2 · repaired tile borders</figcaption><a id="download"><img class="tile" id="finished"></a></figure>
</div>
<p id="links"></p>
<h2>Complete directional catalogue</h2><div id="grid"></div>
<h2>Assembled layouts and checks</h2>
<p>All 211 compatible joins pass local gradient checks using 16-pixel windows. Border detail and the shifted
joins are also reviewed: matching opposite edge pixels alone missed the previous softened bands.
<a href="../seam_repair/local_joins.json">Local checks</a> · <a href="../seam_repair/review.json">Visual review</a>.</p>
REPAIRS
<details><summary>Historical v1 layout checks and captures</summary>
<p>These images predate the seam repair. Known original map-layout conflicts are marked in red.</p>SHEETS
<h2>In-game captures</h2><p>Fixed executable and saved cameras; flat fixture and New Sorpigal.
<a href="../reports/visual_review.json">Review record and limitations</a>.</p>CAPTURES
<details><summary>Historical v1 movement sequence · 16 captured frames</summary>
<p>This short sequence mainly checks repeated dirt. Use the other views to inspect road boundaries.</p>
<label>Frame <input id="motionFrame" type="range" min="0" max="15" value="0"></label>
<output id="motionNumber">0</output>
<img class="sheet" id="motionImage" loading="lazy" src="../captures/v1/dirt_v1_flat_road_motion_motion_00.png">
</details>
</details>
<h2>Current v2 game captures</h2>NEWCAPTURES
<h2>Newer water in this trial</h2>WATERCAPTURES
<h2>Play the separate trial</h2>
<pre><code>./level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/play.sh transitions</code></pre>
<p>Choose Load Game → <strong>Terrain camera reference</strong>. The peasants enhanced launcher remains unchanged.</p>
<script>
const tiles=TILES, select=document.querySelector('#tile');
for(const t of tiles){const o=document.createElement('option');o.value=t.tile;o.textContent=t.tile+' · '+t.family+' · '+t.suffix;select.append(o);
const b=document.createElement('button');b.innerHTML='<img loading="lazy" src="../edge_treatment/runtime/v2/'+t.tile+'.png" alt="'+t.tile+'">'+t.tile;
b.onclick=()=>{select.value=t.tile;show();select.scrollIntoView({behavior:'smooth'});};document.querySelector('#grid').append(b);}
function show(){const t=tiles.find(t=>t.tile===select.value),n=t.tile;
document.querySelector('#native').src='../references/'+n+'_native.png';
document.querySelector('#base').src='../edge_treatment/runtime/v1/'+n+'.png';
document.querySelector('#finished').src='../edge_treatment/runtime/v2/'+n+'.png';
document.querySelector('#download').href='../edge_treatment/runtime/v2/'+n+'.png';
document.querySelector('#description').textContent=t.family+' · '+t.shape+' · '+t.suffix+' · north up, no rotation or mirroring';
document.querySelector('#links').innerHTML='<a href="../composites/v2/'+n+'.png">512px authoring tile</a> · <a href="../masks/connected_v4/'+n+'.png">Coverage mask</a> · <a href="../edge_treatment/prompts/v1/'+n+'.txt">Imagegen prompt</a>';
}select.onchange=show;
document.querySelector('#previous').onclick=()=>{select.selectedIndex=(select.selectedIndex+tiles.length-1)%tiles.length;show();};
document.querySelector('#next').onclick=()=>{select.selectedIndex=(select.selectedIndex+1)%tiles.length;show();};
document.querySelector('#zoom').onclick=()=>{const large=document.querySelector('#comparison').classList.toggle('large');document.querySelector('#zoom').textContent=large?'View at runtime size':'View at 512px';};
select.value='6grdrtne';show();
document.querySelector('#motionFrame').oninput=e=>{
document.querySelector('#motionNumber').value=e.target.value;
document.querySelector('#motionImage').src='../captures/v1/dirt_v1_flat_road_motion_motion_'+e.target.value.padStart(2,'0')+'.png';};
</script></html>'''
sheets = []
for path in sorted((P / 'reports').glob('*.png')):
    if path.name.startswith('pairs_v1_') or path.name == 'catalogue_browser.png':
        continue
    url = '../reports/' + path.name
    sheets.append(f'<details><summary>{path.stem}</summary><a href="{url}"><img class="sheet" loading="lazy" src="{url}"></a></details>')
captures = []
for path in sorted((P / 'captures/v1').glob('dirt_v1_*.json')):
    png = path.with_suffix('.png')
    if png.exists():
        url = '../captures/v1/' + png.name
        captures.append(f'<details><summary>{path.stem}</summary><a href="{url}"><img class="sheet" loading="lazy" src="{url}"></a></details>')
repairs = []
for path in sorted((P / 'seam_repair').glob('*.png')):
    url = '../seam_repair/' + path.name
    repairs.append(f'<details><summary>{path.stem}</summary><a href="{url}"><img class="sheet" loading="lazy" src="{url}"></a></details>')
new_captures = []
for path in sorted((P / 'captures/v2').glob('dirt_v2_*.json')):
    png = path.with_suffix('.png')
    if png.exists():
        url = '../captures/v2/' + png.name
        new_captures.append(f'<details><summary>{path.stem}</summary><a href="{url}"><img class="sheet" loading="lazy" src="{url}"></a></details>')
water_captures = []
for path in sorted((P / 'captures/water_v3').glob('dirt_water_v3_*.json')):
    png = path.with_suffix('.png')
    if png.exists():
        url = '../captures/water_v3/' + png.name
        water_captures.append(f'<details><summary>{path.stem}</summary><a href="{url}"><img class="sheet" loading="lazy" src="{url}"></a></details>')
(review / 'index.html').write_text(template.replace('TILES', json.dumps(tiles)).replace('SHEETS', '\n'.join(sheets))
    .replace('NEWCAPTURES', '\n'.join(new_captures)).replace('WATERCAPTURES', '\n'.join(water_captures))
    .replace('CAPTURES', '\n'.join(captures))
    .replace('REPAIRS', '\n'.join(repairs)))
print(review / 'index.html')
