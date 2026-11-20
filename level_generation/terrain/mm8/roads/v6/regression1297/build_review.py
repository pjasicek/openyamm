"""Assemble exact installed road pixels in native order, with labelled join enlargements."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
P = HERE.parents[2]
ROOT = P.parents[2]
SOURCE = ROOT / 'assets_dev/worlds/mm8/terrain_x2'
grid = json.loads((P / 'effective_grids.json').read_text())['out01']
manifest = json.loads((P / 'complete_runtime_x2/manifest.json').read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

layout = [row[74:80] for row in grid[51:58]]
used = sorted({n for row in layout for n in row})
for name in used:
    assert sha(SOURCE / (name + '.png')) == manifest['files'][name + '.png']['sha256']
path = Image.new('RGB', (6 * 256, 7 * 256))
for y, row in enumerate(layout):
    for x, name in enumerate(row):
        path.paste(Image.open(SOURCE / (name + '.png')), (x * 256, y * 256))
path.save(HERE / 'installed_path.png')
native = Image.new('RGB', path.size)
for y, row in enumerate(layout):
    for x, name in enumerate(row):
        tile = Image.open(P / 'references' / (name + '.png')).convert('RGB')
        native.paste(tile.resize((256, 256), Image.NEAREST), (x * 256, y * 256))
native.save(HERE / 'original_path.png')
marked = path.copy()
draw = ImageDraw.Draw(marked)
for y, row in enumerate(layout):
    for x, name in enumerate(row):
        left, top = x * 256, y * 256
        draw.rectangle((left, top, left + 255, top + 255), outline='#ffdb62')
        draw.rectangle((left + 2, top + 2, left + 225, top + 21), fill='#182027')
        draw.text((left + 5, top + 5), '%d,%d %s' % (y + 51, x + 74, name), fill='white')
marked.save(HERE / 'labelled_path.png')

# Two genuinely adjacent joins: east/west and south/north. No rotations or blending.
cases = [('east_join', 'drsrne2', 'drsrne1', 'E'),
         ('south_join', 'drsrne1', 'drsrne2', 'S')]
for label, first, second, side in cases:
    tiles = [Image.open(SOURCE / (n + '.png')).convert('RGB') for n in (first, second)]
    pair = Image.new('RGB', (512, 256) if side == 'E' else (256, 512))
    pair.paste(tiles[0], (0, 0))
    pair.paste(tiles[1], (256, 0) if side == 'E' else (0, 256))
    box = (208, 55, 304, 211) if side == 'E' else (45, 208, 220, 304)
    crop = pair.crop(box).resize(((box[2] - box[0]) * 4, (box[3] - box[1]) * 4), Image.NEAREST)
    crop.save(HERE / (label + '_clean.png'))
    d = ImageDraw.Draw(crop)
    for coordinate, color in [(248, '#f78b72'), (256, '#ffdb62'), (264, '#f78b72')]:
        if side == 'E':
            x = (coordinate - box[0]) * 4
            d.line((x, 0, x, crop.height), fill=color, width=1)
        else:
            y = (coordinate - box[1]) * 4
            d.line((0, y, crop.width, y), fill=color, width=1)
    crop.save(HERE / (label + '_marked.png'))

html = '''<!doctype html><meta charset="utf-8"><title>Dagger Wound road audit — 1297</title>
<style>body{background:#182027;color:#e9e5dc;font:17px system-ui;max-width:1600px;margin:24px auto}
img{max-width:100%;height:auto}button{font:inherit;padding:8px} .pair{display:flex;gap:20px;align-items:flex-start}
.pair img{max-width:48%}p{max-width:1000px}</style>
<h1>Dagger Wound: exact installed road path</h1>
<p>Native out01 rows51–57, columns74–79. PNG pixels are copied directly from the installed pack,
without blending, smoothing, or resampling. Click the image to inspect full resolution.</p>
<button onclick="const i=document.querySelector('#path');i.src=i.src.endsWith('labelled_path.png')?'installed_path.png':'labelled_path.png'">Toggle tile boundaries and names</button>
<a href="installed_path.png"><img id="path" src="labelled_path.png"></a>
<h2>Original path, same native tile order</h2><a href="original_path.png"><img src="original_path.png"></a>
<h2>East join: drsrne2 → drsrne1</h2><p>Left: unmarked4× nearest-pixel crop. Right: yellow=actual tile boundary;
salmon=8px inside each tile, where the retained16px authoring rim meets new artwork.</p>
<div class="pair"><img src="east_join_clean.png"><img src="east_join_marked.png"></div>
<h2>South join: drsrne1 → drsrne2</h2>
<div class="pair"><img src="south_join_clean.png"><img src="south_join_marked.png"></div>
'''
(HERE / 'index.html').write_text(html)
(HERE / 'inputs.json').write_text(json.dumps(dict(map='out01', rows=[51, 57], columns=[74, 79],
    layout=layout, source=str(SOURCE), files={n + '.png': sha(SOURCE / (n + '.png')) for n in used},
    screenshot_sha256=sha(ROOT / 'test_img/1297.png')), indent=2) + '\n')
print(HERE / 'index.html')
