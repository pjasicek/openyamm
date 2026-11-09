#!/usr/bin/env python3
"""The brief's review sheet for one installed tree (review/<id>.png): the native x2 sprite next to LOD0 front,
three-quarter and side renders, and a second row with every level (LOD0-LOD3 impostor) from the front at a common
size, labelled with triangles. Renders with dead_render.py (Eevee, sun + sky, base colour x COLOR_0), from the
exported blend of either pipeline (work/<id>/ living, work/dead_<id>/ bare).
Usage: review_sheet.py <id> [--reduced <installed.glb>]   (a reduced LOD0, mm6_reduce_pilot route: LOD0 renders
from that GLB, the coarser levels from the export blend, triangles from the GLB)"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
TREES = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(TREES, '..', '..', '..', '..'))
sid = sys.argv[1]
living = os.path.exists(os.path.join(TREES, 'species', f'{sid}.json'))
work = os.path.join(TREES, 'work', sid if living else f'dead_{sid}')
if living:
    sprite_name = json.load(open(os.path.join(TREES, 'species', f'{sid}.json')))['sprite'] + '.png'
else:
    sys.path.insert(0, HERE)
    import dead_common
    sprite_name = dead_common.SPECIES[sid]['sprite']
blend = os.path.join(work, 'tree_export.blend')
prefix = os.path.join(work, 'sheet')
NAMES = ['Tree', 'Tree_LOD1', 'Tree_LOD2', 'Tree_LOD3']


reduced = sys.argv[sys.argv.index('--reduced') + 1] if '--reduced' in sys.argv else None
lod0_blend = blend
if reduced:
    lod0_blend = os.path.join(work, 'sheet_reduced.blend')
    subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(HERE, 'reduce', 'glb_to_blend.py'),
                    '--', reduced, lod0_blend], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render(views, res, extra=(), source=None, tag=''):
    subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(HERE, 'dead_render.py'), '--',
                    prefix + tag + f'{res}', source or blend, views, str(res)] + list(extra), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def crop(im, height):
    im = im.crop(im.getbbox())
    return im.resize((max(1, int(height * im.width / im.height)), height), Image.LANCZOS)


render('eye,three_quarter,side', 720, source=lod0_blend, tag='r' if reduced else '')
render('eye', 400, ['noshadow'])
if reduced:
    render('eye', 400, ['noshadow'], source=lod0_blend, tag='r')
validation = open(os.path.join(work, 'validation.txt')).read() if os.path.exists(
    os.path.join(work, 'validation.txt')) else ''
tris = ''
for line in validation.splitlines():
    if 'VALID LOD triangles' in line:
        tris = line.split('triangles')[1].split(' bounds')[0].strip()
if reduced:
    sys.path.insert(0, os.path.join(REPO, 'tools'))
    from pathlib import Path
    from link_static_model_lods import read_glb
    doc, _ = read_glb(Path(reduced))
    base = next(n for n in doc['nodes'] if 'mesh' in n)
    chain = [base['mesh']] + doc['meshes'][base['mesh']].get('extras', {}).get('openyamm_lods', [])
    tris = str([sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives'])
                for i in chain]) + ' (LOD0 reduced)'
sprite = Image.open(os.path.join(REPO, 'assets_legacy', 'decorations_x2_20261016', sprite_name)).convert('RGBA')
t1 = 'r' if reduced else ''
row1 = [crop(sprite, 520)] + [crop(Image.open(f'{prefix}{t1}720_Tree_{v}.png').convert('RGBA'), 520)
                              for v in ('eye', 'three_quarter', 'side')]
labels1 = [f'native {sprite_name}', 'LOD0 front', 'LOD0 three-quarter', 'LOD0 side']
row2 = [crop(Image.open(f'{prefix}{t1 if n == "Tree" else ""}400_{n}_eye.png').convert('RGBA'), 300) for n in NAMES]
labels2 = ['LOD0', 'LOD1', 'LOD2', 'LOD3 impostor']
gap = 24
width = max(sum(p.width for p in row1), sum(p.width for p in row2)) + gap * 5
height = 520 + 300 + 3 * 30
sheet = Image.new('RGBA', (width, height), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet)
d.text((6, 4), f'{sid}   LOD triangles {tris}', fill=(0, 0, 0, 255))
x = gap
for p, label in zip(row1, labels1):
    sheet.alpha_composite(p, (x, 30 + 520 - p.height + 14)); d.text((x, 22), label, fill=(0, 0, 0, 255))
    x += p.width + gap
x = gap
for p, label in zip(row2, labels2):
    sheet.alpha_composite(p, (x, height - p.height - 4)); d.text((x, height - 300 - 22), label, fill=(0, 0, 0, 255))
    x += p.width + gap
os.makedirs(os.path.join(TREES, 'review'), exist_ok=True)
out = os.path.join(TREES, 'review', f'{sid}.png')
sheet.convert('RGB').save(out)
print('SHEET', out)
