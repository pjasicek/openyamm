"""Create the inventory, offline comparison/animation viewer and compact edge review."""
from pathlib import Path
import html
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def run():
    manifest = json.loads((HERE / 'manifest.json').read_text())
    inventory = json.loads((HERE / 'inventory.json').read_text())
    generation = json.loads((HERE / 'generation.json').read_text())
    records = manifest['decorations']
    frame_names = list(manifest['frames'])
    report = {
        'enhanced_images': len(frame_names),
        'enhanced_png_bytes': sum((HERE / f'enhanced/{n}.png').stat().st_size for n in frame_names),
        'enhanced_decoded_rgba_bytes': sum(np.prod(manifest['frames'][n]['physical_size']).item() * 4 for n in frame_names),
        'matching_native_bmp_bytes': sum((REPO / inventory['sources'][n]['path']).stat().st_size for n in frame_names),
        'matching_native_decoded_rgba_bytes': sum(np.prod(inventory['sources'][n]['size']).item() * 4 for n in frame_names),
        'note': 'One copy per unique image, not per placement. Excludes native retained animations, GPU mipmaps, atlas padding and driver bookkeeping.'}
    (HERE / 'footprint.json').write_text(json.dumps(report, indent=2) + '\n')
    rows = []
    labels = {'enhance': 'AI enhanced, 2x', 'keep_native_animation': 'Native animation retained', 'marker_no_art': 'Marker; no image'}
    for r in records:
        names = ', '.join('`' + n + '`' for n in r['unique_images']) or '—'
        rows.append(f"| `{r['name']}` | {r['hint']} | {r['placed_count']} | {len(r['frames'])} | {names} | {labels[r['policy']]} |")
    readme = f'''# MM6 New Sorpigal decorations

[Open the comparison and animation viewer](review.html) · [All enhanced/native comparisons](review/comparison_dark.png)
· [Light-background comparison](review/comparison_light.png) · [Exact source inventory](inventory.json)

**Installed in the isolated enhanced New Sorpigal playtest.** Run
`./level_generation/creatures/mm6_peasants/play.sh enhanced` and load a New Sorpigal save; restart an already running
game. Only `mm6/oute3.odm` selects these decoration images. Other maps and original mode keep native decorations.
No original BMPs, maps, events, sprite tables, saves or settings were modified by decoration installation.

The map contains **479 decoration placements**, using **22 descriptor names**: 20 visible-art types and two start
markers. The map script also selects `swrdstx`, making **23 types/states** in this inventory. The complete source
set is **54 unique BMP images**. Names and actual filenames differ (`6rock01` → `rok1`, `sta1a` → `fount1` etc.).
Scene entity overrides and map-script `SetSprite` targets are included; filtering filenames by a `6` prefix is insufficient.

**13 built-in imagegen calls produced 19 enhanced images**, covering 15 static descriptor types/states and the
five stored ship directions. These correspond to 465 initial placements. Six animated types (12 placements,
35 unique images) retain their native artwork and timing. The remaining two placements are start markers.

## Complete decoration list

“Frames” is the number of native timeline entries, not necessarily the number of different images.

| Map decoration/state | Native hint | Placements | Frames | Actual image stems | This pass |
| --- | --- | ---: | ---: | --- | --- |
''' + '\n'.join(rows) + f'''

`tree06a` is called “Empty Food Tree” in the merged descriptor table but its actual correctly paletted native image
shows fruit; `6tree06` shows no visible fruit. This pass follows the source artwork and existing event references,
without silently swapping their names or changing gameplay. Both appearances share exactly the same restored
foliage/trunk/alpha; only fruit changes. Likewise, `swrdstn` and `swrdstx` share the same boulder pixels at native
bottom alignment. `swrdstx` has zero initial placements but is selected after the sword interaction.

## Animated billboards

The cooking cauldron exists: **`ckfyr00`** is a suspended kettle/tripod above animated fire (six frames, five placements).
The other native animations are the buoy (ten timeline entries reusing six images in a forward/back loop), red flag
(eight frames), two rocks with moving surf (six each), and the fountain (three frames).

For this first scenery test, retain those animations completely. Freezing a cauldron/flame or fountain to one enhanced
frame would lose motion. Independently redrawing every frame risks flickering rigid geometry. A later animation pass
should restore one complete short native sequence in a sheet, lock the rigid kettle/stand/pole/rock/fountain body,
and vary only fire/water/cloth. The current viewer plays the exact native sequences so this decision is reviewable.
There are no new intermediate frames or altered light/event/collision properties.

The ship is **not a timeline animation**: it has five stored directions plus native mirrored views. Its five views
were enhanced together to maintain hull, spars and rigging identity. It keeps the source's mostly furled sails and
native scale 9.0, with per-view canvases and native bottom alignment retained.

## Export and review

- `native/`: correct native palette and index-zero transparency, for every referenced image.
- `references/`: original edit targets, catalogue and complete native animation sheets.
- `prompts/`: exact prompts submitted through built-in imagegen; no paid API fallback was used.
- `raw/`, `cleaned/`: generated sheets and full-detail matte extraction masters.
- `enhanced/`: the 19 shipping RGBA PNGs; each canvas is exactly twice its native width/height.
- `sheets/`: transparent static/state/view sheets for review and reuse; individual shipping PNGs remain authoritative.
- `manifest.json`, `registration.json`, `generation.json`: intended map scope, native descriptors/frames, pixel
  scale, palettes already baked into RGB, source/target bounds, tonal correction and selected output hashes.
- `validation.json`, `review/edge_closeups.png`: final size/alpha/spill checks and final contours on light/dark backgrounds.

Magenta matting is used except for the pink blossom tree and purple flowers, which use cyan to protect their actual
colors. Matte contribution is removed before premultiplied-alpha resizing, with a second contour correction after
resampling. All final images pass the 16/255 contour spill threshold for their own matte hue. This is an estimated
alpha reconstruction; thin leaf edges, stems and rigging remain interpretations of the low-resolution source.

A restrained deterministic tonal correction matches each source's luminance. Green tree foliage also receives a
selective red/blue ratio correction from its native palette, to avoid the generator's yellow/olive shift; bark and
pink/red foliage are protected. No AI pass is spent on those color corrections. State locking reuses common pixels
rather than accepting small model-induced changes across interactions. Details are still newly interpreted artwork,
not recovered original high-resolution renders. Leaves, bark grain, rivets and ship rigging differ in fine detail.

Shipping PNGs: **{report['enhanced_png_bytes']/2**20:.2f} MiB**; decoded RGBA: **{report['enhanced_decoded_rgba_bytes']/2**20:.2f} MiB**.
The matching 19 native BMPs occupy {report['matching_native_bmp_bytes']/2**20:.2f} MiB on disk and
{report['matching_native_decoded_rgba_bytes']/2**20:.2f} MiB as decoded RGBA. Doubling both dimensions means 4× decoded
pixels. This is shared artwork, not multiplied by 465 placements. Runtime mipmaps/padding would add separate cost.

## Reproduce / installation

```sh
python3 level_generation/decorations/mm6_new_sorpigal/prepare.py
python3 level_generation/decorations/mm6_new_sorpigal/process.py
python3 level_generation/decorations/mm6_new_sorpigal/build_review.py
```

These commands use accepted AI outputs and do not make new image-generation requests. The saved reference inputs,
exact prompts and raw outputs retain the generation provenance. `prepare.py` inventories the current authoritative
map/table data; review changes before regenerating from a different native baseline.

After building the current executable, install or refresh only this package with:

```sh
python3 level_generation/creatures/mm6_peasants/prepare_decorations.py
```

Use `--directory /absolute/playtest/path` for another prepared snapshot. Normal playtest preparation and `--update`
also include decorations. The installer verifies source hashes/dimensions, preserves saves/settings, and refreshes
the executable. It writes a private `worlds/mm6/rendering/decoration_overrides/oute3.odm/manifest.yml` alongside 19 PNGs.

The shared map loader reads `worlds/<world>/rendering/decoration_overrides/<map-file>/manifest.yml` only for the
selected map. Schema version 1 lists `textures` entries with native `name`, `palette_id` (cache identity only),
PNG `file` in the same directory, `logical_size: [width, height]`, and integer `pixel_scale`. Missing manifests keep
native artwork; malformed manifests, missing declared images or incorrect dimensions fail loading explicitly.
Script-only appearances are preloaded too. Selected native textures are skipped instead of loaded a second time.

Native retained animations remain 1x: **do not divide every decoration's dimensions by two globally**. Decode
replacement PNGs as RGBA without applying the indexed BMP palette again. Preserve descriptor IDs, animation timing,
mirror flags, frame scale, events, light radius and collision dimensions. Full native canvas sizes preserve the
existing bottom-center anchor. This uses the existing decoration billboard filtering and opacity picking path;
it does not use the actor atlas/mask shader or its atlas mipmaps.

Focused loader tests cover exact world/map isolation, native logical dimensions, unkeyed RGBA and alpha preservation,
invalid metadata, duplicate entries and missing/wrong-sized images. A native game smoke capture is in `review/runtime/`;
full artistic acceptance remains an in-game review.
'''
    (HERE / 'README.md').write_text(readme)
    # One modest-sized edge sample per final export; the complete contact covers overall appearance.
    edge_sheet = Image.new('RGB', (5 * 320, ((len(frame_names) + 4) // 5) * 184), (55, 55, 55))
    draw = ImageDraw.Draw(edge_sheet)
    for i, name in enumerate(frame_names):
        im = Image.open(HERE / 'enhanced' / (name + '.png'))
        a = np.array(im)
        edge = (a[:, :, 3] > 16) & (a[:, :, 3] < 240)
        # Prefer fine antialiased detail near the upper silhouette over flat transparent corners.
        score = edge * (255 - np.abs(a[:, :, 3].astype(float) - 128))
        yy, xx = np.unravel_index(np.argmax(score), score.shape)
        box = (max(0, min(im.width - 40, xx - 20)), max(0, min(im.height - 40, yy - 20)))
        crop = im.crop((box[0], box[1], box[0] + 40, box[1] + 40)).resize((160, 160), Image.Resampling.NEAREST)
        x, y = i % 5 * 320, i // 5 * 184
        draw.text((x + 4, y + 4), name, fill='white')
        for j, bg in enumerate([(30, 35, 30), (235, 235, 230)]):
            out = Image.new('RGBA', crop.size, (*bg, 255)); out.alpha_composite(crop)
            edge_sheet.paste(out.convert('RGB'), (x + j * 160, y + 24))
    edge_sheet.save(HERE / 'review/edge_closeups.png')
    data = {'records': [r for r in records if r['frames']], 'sources': inventory['sources'],
            'enhanced': manifest['frames']}
    template = r'''<!doctype html><html lang="en"><meta charset="utf-8"><title>New Sorpigal decoration restoration</title>
<style>body{font:16px system-ui;background:#202622;color:#ecefe8;margin:24px auto;max-width:1380px;padding:0 18px}a{color:#bdd3a2}h1{font-size:30px}select,button,input{font:inherit;margin:5px;padding:7px}header p{max-width:1000px;line-height:1.5}.controls{padding:12px;background:#303c33;display:flex;align-items:center;flex-wrap:wrap;gap:8px}.panels{display:grid;grid-template-columns:1fr 1fr;gap:16px}canvas{width:100%;background:#262a27}h2{font-size:20px}#details{padding:12px;background:#303c33;white-space:pre-wrap;line-height:1.5}.catalogue{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}.card{background:#2d3730;padding:12px}.card img{display:block;width:100%;height:280px;object-fit:contain}.card button{width:100%}.tag{color:#becaad;font-size:14px}table{border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #465548;text-align:left}@media(max-width:750px){.panels{grid-template-columns:1fr}}</style>
<header><h1>New Sorpigal — enhanced decorations</h1><p>479 map placements · 23 types/states including markers · 19 enhanced static/state/view images. Six animated prop types retain their original animation. <strong>Installed only in the enhanced New Sorpigal playtest.</strong></p>
<p><a href="README.md">Inventory and decisions</a> · <a href="review/comparison_dark.png">All comparisons</a> · <a href="review/edge_closeups.png">Edge review</a> · <a href="manifest.json">Placement manifest</a></p></header>
<div class="controls"><select id="asset" aria-label="Decoration"></select><select id="view" aria-label="View direction"></select><button id="play">Pause</button><input id="frame" type="range" min="0" max="0" value="0" aria-label="Animation frame"><select id="background" aria-label="Background"><option value="#262a27">Dark</option><option value="#e0e2dd">Light</option><option value="#45643b">Grass</option></select><label><input id="pixels" type="checkbox">Native nearest pixels</label></div>
<div class="panels"><section><h2>Original</h2><canvas id="native" width="640" height="650"></canvas></section><section><h2 id="enhancedLabel">Enhanced</h2><canvas id="enhanced" width="640" height="650"></canvas></section></div><p id="details"></p>
<h2>Complete visual catalogue</h2><div id="catalogue" class="catalogue"></div>
<script>const data=DATA;const $=id=>document.getElementById(id);const cache=new Map();let running=true,step=0,last=0;
function picture(path){if(!cache.has(path)){const im=new Image;im.src=path;im.onload=()=>render();cache.set(path,im)}return cache.get(path)}
function record(){return data.records[+$('asset').value||0]}function choose(i){$('asset').value=i;step=0;$('frame').value=0;const r=record();$('frame').max=r.frames.length-1;$('view').hidden=r.frames[0].images.length===1;render()}
function draw(id,path,nativeSize,flip,baseCanvas){const c=$(id),ctx=c.getContext('2d');ctx.fillStyle=$('background').value;ctx.fillRect(0,0,c.width,c.height);const im=picture(path);if(!im.complete||!im.naturalWidth)return;const zoom=Math.min(570/baseCanvas[0],560/baseCanvas[1]);const w=nativeSize[0]*zoom,h=nativeSize[1]*zoom;ctx.save();ctx.imageSmoothingEnabled=!(id==='native'&&$('pixels').checked);if(flip){ctx.translate(c.width,0);ctx.scale(-1,1)}ctx.drawImage(im,(c.width-w)/2,610-h,w,h);ctx.restore()}
function render(){const r=record(),f=r.frames[step%r.frames.length];const dir=+$('view').value||0;const index=f.images.length===1?0:dir>4?8-dir:dir;const name=f.images[index];const src=data.sources[name],canvas=[Math.max(...r.unique_images.map(n=>data.sources[n].size[0])),Math.max(...r.unique_images.map(n=>data.sources[n].size[1]))];const enhanced=data.enhanced[name];draw('native','native/'+name+'.png',src.size,dir>4&&f.images.length>1,canvas);draw('enhanced',enhanced?enhanced.file:'native/'+name+'.png',src.size,dir>4&&f.images.length>1,canvas);$('enhancedLabel').textContent=enhanced?'Enhanced — native logical size':'Native animation retained';$('frame').value=step;$('details').textContent=r.name+' · '+r.hint+' · '+r.placed_count+' placements\n'+name+' · frame '+(step+1)+'/'+r.frames.length+' · '+f.duration_ms+' ms · native scale '+f.scale+' · palette '+f.palette_id+'\nNative canvas '+src.size.join('×')+(enhanced?' → enhanced '+enhanced.physical_size.join('×'):' · original animated art')+' · '+(r.policy==='keep_native_animation'?'Animation retained at native timing':'Same native size/ground anchor')}
for(let i=0;i<data.records.length;i++){const r=data.records[i],o=new Option(r.name+' — '+r.hint,i);$('asset').add(o);const card=document.createElement('article');card.className='card';const title=document.createElement('h2');title.textContent=r.name;card.appendChild(title);const img=document.createElement('img');const n=r.unique_images[0];img.src=data.enhanced[n]?.file||'native/'+n+'.png';img.loading='lazy';img.alt=r.hint;card.appendChild(img);const tag=document.createElement('p');tag.className='tag';tag.textContent=r.placed_count+' placements · '+(r.policy==='enhance'?'Enhanced':'Native '+r.frames.length+'-frame animation');card.appendChild(tag);const btn=document.createElement('button');btn.textContent='Compare / play';btn.onclick=()=>{choose(i);window.scrollTo({top:0,behavior:'smooth'})};card.appendChild(btn);$('catalogue').appendChild(card)}
for(let i=0;i<8;i++)$('view').add(new Option('Direction '+i+(i>4?' (mirrored)':''),i));$('asset').onchange=()=>choose(+$('asset').value);$('view').onchange=render;$('background').onchange=render;$('pixels').onchange=render;$('frame').oninput=()=>{step=+$('frame').value;render()};$('play').onclick=()=>{running=!running;$('play').textContent=running?'Pause':'Play'};
function tick(now){const r=record(),duration=r.frames[step].duration_ms||125;if(running&&r.frames.length>1&&now-last>=duration){step=(step+1)%r.frames.length;last=now;render()}requestAnimationFrame(tick)}const query=new URLSearchParams(location.search);const selected=data.records.findIndex(r=>r.name===query.get('asset'));choose(Math.max(0,selected));if(query.has('frame')){step=Math.max(0,Math.min(record().frames.length-1,Number(query.get('frame'))||0));running=false;$('play').textContent='Play';render()}requestAnimationFrame(tick);</script></html>'''
    (HERE / 'review.html').write_text(template.replace('DATA', json.dumps(data)))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    run()
