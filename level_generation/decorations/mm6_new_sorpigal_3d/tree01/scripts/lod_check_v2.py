#!/usr/bin/env python3
"""LOD consistency for v2 (after export_tree_v2.py): renders every level of work_v2/tree_export.blend from the eye
camera, without sun shadows (the engine default), at a common size and at about the size it is used in game
(LOD0 ~500 px, LOD1 ~250, LOD2/3 ~160 px tall), prints mean colour (opaque pixels) and coverage (opaque pixel count relative to LOD0) per level, and writes
review_v2/tree01_v2_lod_consistency.png. Usage: lod_check_v2.py [tag]"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, 'work_v2'); R = os.path.join(HERE, 'review_v2')
os.makedirs(R, exist_ok=True)
tag = sys.argv[1] if len(sys.argv) > 1 else 'lc'
BLEND = os.path.join(W, 'tree_export.blend')
NAMES = ['Tree', 'Tree_LOD1', 'Tree_LOD2', 'Tree_LOD3']
# the tree fills ~74 % of the eye frame height: frame heights for ~300 px and the in-game sizes
COMMON = 405
INGAME = {'Tree': 675, 'Tree_LOD1': 338, 'Tree_LOD2': 216, 'Tree_LOD3': 216}


def render(prefix, res):
    subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(HERE, 'scripts', 'render_review_v2.py'),
                    '--', prefix, BLEND, 'eye', 'lit', str(res), 'noshadow'], check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


render(os.path.join(W, f'{tag}_common'), COMMON)
for res in sorted(set(INGAME.values())):
    render(os.path.join(W, f'{tag}_{res}'), res)
stats = {}
common = {}
for n in NAMES:
    x = np.asarray(Image.open(os.path.join(W, f'{tag}_common_{n}_eye.png')).convert('RGBA')).astype(float)
    m = x[..., 3] > 128
    common[n] = Image.fromarray(x.astype(np.uint8), 'RGBA')
    stats[n] = {'mean_rgb': x[m][:, :3].mean(0).round(1).tolist(), 'opaque_px': int(m.sum())}
for n in NAMES:
    stats[n]['coverage_vs_lod0'] = round(stats[n]['opaque_px'] / stats['Tree']['opaque_px'], 3)
for a, b in zip(NAMES, NAMES[1:]):
    d = np.abs(np.array(stats[a]['mean_rgb']) - np.array(stats[b]['mean_rgb']))
    stats[b]['mean_diff_vs_previous'] = d.round(1).tolist()
    stats[b]['coverage_diff_vs_previous'] = round(stats[b]['opaque_px'] / stats[a]['opaque_px'] - 1, 3)
json.dump(stats, open(os.path.join(W, f'{tag}_stats.json'), 'w'), indent=1)
for n in NAMES:
    print(n, stats[n])
# sheet: row 1 common size, row 2 in-game sizes (bottom-aligned), labels
cw = common['Tree'].width
row2 = [Image.open(os.path.join(W, f'{tag}_{INGAME[n]}_{n}_eye.png')).convert('RGBA') for n in NAMES]
height = COMMON + max(i.height for i in row2) + 60
sheet = Image.new('RGBA', (cw * 4, height), (150, 160, 175, 255))
draw = ImageDraw.Draw(sheet)
for k, n in enumerate(NAMES):
    sheet.alpha_composite(common[n], (k * cw, 20))
    s = stats[n]
    draw.text((k * cw + 6, 4), f'{n}: mean {s["mean_rgb"]} coverage {s["coverage_vs_lod0"]}', fill=(0, 0, 0, 255))
    im = row2[k]
    sheet.alpha_composite(im, (k * cw + (cw - im.width) // 2, height - im.height))
    draw.text((k * cw + 6, COMMON + 30), f'in-game size ~{int(INGAME[n] * 0.74)} px', fill=(0, 0, 0, 255))
sheet.convert('RGB').save(os.path.join(R, 'tree01_v2_lod_consistency.png'))
print('SHEET', os.path.join(R, 'tree01_v2_lod_consistency.png'))
