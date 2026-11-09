#!/usr/bin/env python3
"""Under-crown gates of one palm: renders LOD0 of work/<id>/export.blend from the side, from under the crown looking up
and from a low three-quarter view (render_review.py: Eevee, sun shadows, backface culling, no leaf sheen) and writes
review/<id>/gates[_<tag>].png with Rec. 709 luma p5 / p25 / p50 / p90 of the palm's pixels per view, plus the leaf
COLOR_0 luminance percentiles of the export (LOD0 Leaves primitive). Prints one GATES line. Usage: gates.py <id> [tag]"""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as pc
sys.path.insert(0, os.path.join(pc.REPO, 'tools'))
from link_static_model_lods import read_glb
sid = sys.argv[1]; tag = sys.argv[2] if len(sys.argv) > 2 else ''
W = pc.work(sid)
VIEWS = ('side', 'under', 'low_three_quarter')
subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(pc.PALMS, 'scripts', 'render_review.py'), '--',
                os.path.join(W, 'export.blend'), os.path.join(W, 'gate'), '512', ','.join(VIEWS), 'Plant'],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
LUMA = np.array([0.2126, 0.7152, 0.0722])
tiles, stats = [], {}
for v in VIEWS:
    im = Image.open(os.path.join(W, f'gate_Plant_{v}.png')).convert('RGBA')
    x = np.asarray(im).astype(float); m = x[..., 3] > 128
    y = x[m][:, :3] @ LUMA
    p = np.percentile(y, [5, 25, 50, 90]).round(0).tolist(); stats[v] = p
    bg = Image.new('RGBA', im.size, (128, 138, 155, 255)); bg.alpha_composite(im)
    ImageDraw.Draw(bg).text((6, 6), f'{sid} {v}  luma p5/p25/p50/p90 {p}', fill=(0, 0, 0, 255))
    tiles.append(bg.convert('RGB'))
sheet = Image.new('RGB', (sum(t.width for t in tiles), tiles[0].height)); xo = 0
for t in tiles:
    sheet.paste(t, (xo, 0)); xo += t.width
sheet.save(os.path.join(pc.review(sid), f'gates{"_" + tag if tag else ""}.png'))
# leaf COLOR_0 of the export (LOD0)
doc, binary = read_glb(Path(os.path.join(W, 'plant_export.glb')))
mats = [mm['name'] for mm in doc['materials']]
mesh = next(mm for mm in doc['meshes'] if mm['name'] == 'Plant')
prim = next(pr for pr in mesh['primitives'] if mats[pr['material']] == 'Leaves')
a = doc['accessors'][prim['attributes']['COLOR_0']]; bv = doc['bufferViews'][a['bufferView']]
dt = {5126: np.float32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
n = {'VEC3': 3, 'VEC4': 4}[a['type']]
c = np.frombuffer(bytes(binary[bv.get('byteOffset', 0) + a.get('byteOffset', 0):][:a['count'] * n * np.dtype(dt).itemsize]), dt)
c = c.reshape(a['count'], n)[:, :3].astype(float)
if dt != np.float32:
    c /= np.iinfo(dt).max
cl = c @ LUMA
stats['color0_p5_p25_p50'] = np.percentile(cl, [5, 25, 50]).round(3).tolist()
json.dump(stats, open(os.path.join(W, f'gates{"_" + tag if tag else ""}.json'), 'w'))
print('GATES', sid, json.dumps(stats))
