"""Review exact final pixels as native paths and unmarked enlarged join neighborhoods."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
P = HERE.parents[1]
grid = json.loads((P / 'effective_grids.json').read_text())['out01']

def tile(version, name):
    path = HERE.parent / version / 'runtime' / (name + '.png')
    if not path.exists():
        path = P / 'complete_runtime_x2/worlds/mm8/terrain_x2' / (name + '.png')
    return Image.open(path).convert('RGB')

cases = [('east', 'drsrne2', 'drsrne1', 'E'), ('south', 'drsrne1', 'drsrne2', 'S'),
         ('entry', 'drsrns', 'drsrne2', 'S'), ('exit', 'drsrne2', 'drsrew', 'E')]
for version in ('v6', 'v7'):
    path = Image.new('RGB', (1536, 1792))
    for y in range(51, 58):
        for x in range(74, 80):
            path.paste(tile(version, grid[y][x]), ((x - 74) * 256, (y - 51) * 256))
    path.save(HERE / (version + '_path.png'))
    for name, a, b, side in cases:
        pair = Image.new('RGB', (512, 256) if side == 'E' else (256, 512))
        pair.paste(tile(version, a), (0, 0))
        pair.paste(tile(version, b), (256, 0) if side == 'E' else (0, 256))
        box = (208, 55, 304, 211) if side == 'E' else (45, 208, 220, 304)
        crop = pair.crop(box)
        crop.resize((crop.width * 4, crop.height * 4), Image.NEAREST).save(
            HERE / (version + '_' + name + '_join.png'))

frames = sorted((HERE / 'captures').glob('mm8_diagonal_v7_ports_a_walk_*.png'))
if frames:
    frames.sort(key=lambda f: (not f.stem.endswith('_start'), f.name))
    for page in range((len(frames) + 3) // 4):
        sheet = Image.new('RGB', (1200, 900), '#182027')
        draw = ImageDraw.Draw(sheet)
        for slot, frame in enumerate(frames[page * 4:page * 4 + 4]):
            crop = Image.open(frame).crop((380, 390, 1210, 960))
            crop.thumbnail((600, 420))
            x, y = slot % 2 * 600, slot // 2 * 450
            sheet.paste(crop, (x, y + 24))
            draw.text((x + 4, y + 4), frame.stem, fill='white')
        sheet.save(HERE / ('movement_%02d.png' % page))

html = ['''<!doctype html><meta charset="utf-8"><title>MM8 joined road repair v7</title>
<style>body{background:#182027;color:#eee;font:17px system-ui;margin:24px auto;max-width:1600px}
.pair{display:flex;gap:20px;align-items:flex-start}.pair img{max-width:48%;height:auto}img{max-width:100%}
p{max-width:1000px}button{padding:8px;font:inherit}</style>
<h1>Connected road repair: v6 before / v7 after</h1>
<p>Unmarked4× nearest-pixel enlargements. Each row uses actual neighboring tiles, including the
straight-road entry and exit. All images show final runtime pixels, not imagegen previews.</p>''']
for name, a, b, side in cases:
    html.append('<h2>%s: %s %s %s</h2><div class="pair"><img src="v6_%s_join.png"><img src="v7_%s_join.png"></div>' %
                (name, a, side, b, name, name))
html.append('''<h2>Native assembled path</h2>
<button onclick="const i=document.querySelector('#path');i.src=i.src.endsWith('v7_path.png')?'v6_path.png':'v7_path.png'">Toggle v6 / v7</button>
<a href="v7_path.png"><img id="path" src="v7_path.png"></a>''')
for pose in ('a', 'b'):
    name = 'mm8_diagonal_v7_ports_' + pose + ('_walk_start' if pose == 'a' else '')
    html.append('<h2>Native camera %s</h2><img src="captures/%s.png">' % (pose, name))
for frame in sorted(HERE.glob('movement_*.png')):
    html.append('<img src="%s">' % frame.name)
(HERE / 'index.html').write_text('\n'.join(html))
print('Built path, both joins, entry/exit comparisons and available movement sheets')
