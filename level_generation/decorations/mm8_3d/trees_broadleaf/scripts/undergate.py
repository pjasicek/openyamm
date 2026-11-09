#!/usr/bin/env python3
"""Under-crown gate (2026-10-16): LOD0 of work/<id>/tree_export.blend from below the crown (2 m up near the trunk,
60 degrees pitch) and from a low three-quarter view, opaque back faces culled, engine-like light (sun and sky, no
shadow maps or screen-space occlusion: Eevee's would blacken any surface deep inside the crown); reports the share of covered pixels
that are near black (sRGB luminance < 16 and < 28) and writes review/<id>/under_<tag>.png.
Usage: undergate.py <id> <tag>"""
import json, os, subprocess
import numpy as np
from PIL import Image, ImageDraw
import common
spec = common.load(); W = spec['work']; R = spec['review']; tag = common.extra_args()[0]
prefix = os.path.join(W, f'ug_{tag}')
subprocess.run(['/snap/bin/blender', '--background', '--python', os.path.join(common.TREES, 'scripts', 'render_review.py'),
                '--', spec['id'], prefix, os.path.join(W, 'tree_export.blend'), 'upward,low34', 'lit', '540', 'noshadow'], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
stats, tiles = {}, []
for v in ('upward', 'low34'):
    im = Image.open(f'{prefix}_Tree_{v}.png').convert('RGBA'); x = np.asarray(im).astype(float)
    m = x[..., 3] > 128; l = x[..., :3] @ [0.2126, 0.7152, 0.0722]
    stats[v] = {'black16': round(float((l[m] < 16).mean()), 4), 'dark28': round(float((l[m] < 28).mean()), 4),
                'lum_p5': round(float(np.percentile(l[m], 5)), 1), 'lum_p50': round(float(np.percentile(l[m], 50)), 1)}
    bg = Image.new('RGBA', im.size, (150, 160, 175, 255)); bg.alpha_composite(im); tiles.append(bg.convert('RGB'))
json.dump(stats, open(os.path.join(W, f'under_{tag}.json'), 'w'))
sheet = Image.new('RGB', (sum(t.width for t in tiles), tiles[0].height + 24), (150, 160, 175)); d = ImageDraw.Draw(sheet)
x = 0
for v, t in zip(('upward', 'low34'), tiles):
    sheet.paste(t, (x, 24)); d.text((x + 6, 6), f"{spec['id']} {tag} {v}: {stats[v]}", fill=(0, 0, 0)); x += t.width
sheet.save(os.path.join(R, f'under_{tag}.png'))
print('UNDER', spec['id'], tag, stats)
