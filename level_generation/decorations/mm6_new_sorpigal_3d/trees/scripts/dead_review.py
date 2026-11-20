#!/usr/bin/env python3
"""Review sheets for one dead tree (review/dead_<id>/), rendered with dead_render.py (the living trees' review
lighting: Eevee, sun + sky, base colour x COLOR_0, low specular; framed on the model's larger extent):
 - compare.png: native sprite | LOD0 eye level | LOD0 three-quarter | LOD0 back, with mean colour / luminance
   percentiles of the sprite and the eye render;
 - lods.png: every level from the eye camera without shadows at a common size (mean colour, coverage vs LOD0) and at
   about its in-game size; stats in work/dead_<id>/lod_stats.json.
Usage: dead_review.py <id> [blend]   (default work/dead_<id>/tree_export.blend, else tree.blend)"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
import dead_common as dc

spec = dc.load(); W = spec['work']; R = spec['review']
blend = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else os.path.join(W, 'tree_export.blend')
if not os.path.exists(blend) or '--quick' in sys.argv:          # quick: the freshly built tree, no impostor
    blend = os.path.join(W, 'tree.blend')
RENDER = os.path.join(dc.TREES, 'scripts', 'dead_render.py')
STUMP = spec['kind'] == 'stump'
NAMES = ['Tree', 'Tree_LOD1', 'Tree_LOD2', 'Tree_LOD3']


def render(prefix, views, res=540, extra=()):
    subprocess.run(['/snap/bin/blender', '--background', '--python', RENDER, '--', prefix, blend, views, str(res)]
                   + list(extra), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stats(im):
    x = np.asarray(im).astype(float); m = x[..., 3] > 128; l = x[..., :3] @ [0.3, 0.59, 0.11]
    return x[m][:, :3].mean(0).round(1).tolist(), np.percentile(l[m], [5, 50, 95]).round(1).tolist()


def crop(im, height):
    im = im.crop(im.getbbox())
    return im.resize((max(1, int(height * im.width / im.height)), height), Image.LANCZOS)


render(os.path.join(W, 'rv'), 'eye,three_quarter,back', 720)
sprite = Image.open(spec['sprite_path']).convert('RGBA')
views = [Image.open(os.path.join(W, f'rv_Tree_{v}.png')).convert('RGBA') for v in ('eye', 'three_quarter', 'back')]
panels = [crop(sprite, 560)] + [crop(v, 560) for v in views]
labels = [f"native {spec['sprite']}", 'LOD0 eye level', 'LOD0 three-quarter', 'LOD0 back']
width = sum(p.width for p in panels) + 20 * len(panels)
sheet = Image.new('RGBA', (width, 620), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet); x = 0
for p, label in zip(panels, labels):
    sheet.alpha_composite(p, (x, 620 - p.height)); d.text((x + 4, 4), label, fill=(0, 0, 0, 255)); x += p.width + 20
d.text((4, 18), f'sprite mean/lum5-50-95 {stats(sprite)}   eye {stats(views[0])}', fill=(0, 0, 0, 255))
sheet.convert('RGB').save(os.path.join(R, 'compare.png'))
print('REVIEW sprite', stats(sprite), 'eye', stats(views[0]))

if '--quick' in sys.argv:
    raise SystemExit
# LOD consistency
names = [n for n in NAMES if os.path.exists(blend)]
render(os.path.join(W, 'lc'), 'eye', 405, ['noshadow'])
INGAME = {'Tree': 675, 'Tree_LOD1': 338, 'Tree_LOD2': 216, 'Tree_LOD3': 216}
for res in sorted(set(INGAME.values())):
    render(os.path.join(W, f'lc{res}'), 'eye', res, ['noshadow'])
present = [n for n in NAMES if os.path.exists(os.path.join(W, f'lc_{n}_eye.png'))]
st = {}
for n in present:
    x = np.asarray(Image.open(os.path.join(W, f'lc_{n}_eye.png')).convert('RGBA')).astype(float)
    m = x[..., 3] > 128
    st[n] = {'mean_rgb': x[m][:, :3].mean(0).round(1).tolist(), 'opaque_px': int(m.sum())}
for n in present:
    st[n]['coverage_vs_lod0'] = round(st[n]['opaque_px'] / st['Tree']['opaque_px'], 3)
for a, b in zip(present, present[1:]):
    st[b]['mean_diff_vs_previous'] = np.abs(np.array(st[a]['mean_rgb']) - np.array(st[b]['mean_rgb'])).round(1).tolist()
    st[b]['coverage_diff_vs_previous'] = round(st[b]['opaque_px'] / st[a]['opaque_px'] - 1, 3)
json.dump(st, open(os.path.join(W, 'lod_stats.json'), 'w'), indent=1)
for n in present:
    print(n, st[n])
cw = 420
row1 = [Image.open(os.path.join(W, f'lc_{n}_eye.png')).convert('RGBA') for n in present]
row2 = [Image.open(os.path.join(W, f'lc{INGAME[n]}_{n}_eye.png')).convert('RGBA') for n in present]
height = 405 + 216 + 60
sheet = Image.new('RGBA', (cw * len(present), height), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet)
for k, n in enumerate(present):
    sheet.alpha_composite(row1[k], (k * cw, 20))
    s = st[n]
    d.text((k * cw + 4, 4), f'{n} {s["mean_rgb"]} cov {s["coverage_vs_lod0"]}', fill=(0, 0, 0, 255))
    im = row2[k]
    if n != 'Tree':
        sheet.alpha_composite(im, (k * cw + (cw - im.width) // 2, height - im.height))
sheet.convert('RGB').save(os.path.join(R, 'lods.png'))
print('SHEETS', os.path.join(R, 'compare.png'), os.path.join(R, 'lods.png'))
