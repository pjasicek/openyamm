#!/usr/bin/env python3
"""Plan view of the feet (skin vertices dominated by foot/toe bones, the lowest 8 cm of them) at given clip times,
with the foot->toe joint line (black) and a +Z travel arrow (grey line through the pelvis), drawn from above: travel up
the page, the body's left on the right. foot_plot.py <glb> <out.png> <clip>:<t>[,<clip>:<t>...]"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402

glb = glb_pose.Glb(sys.argv[1])
model = glb_pose.Model(glb)
names = [n['name'] for n in glb.json['nodes']]
I = {n: i for i, n in enumerate(names)}
prim = model.primitives[0]
dom = np.array([names[model.joints[j]] for j in prim['joints'][np.arange(len(prim['joints'])),
                                                                prim['weights'].argmax(axis=1)]])
poses = [p.split(':') for p in sys.argv[3].split(',')]
S, PX = 360, 320.0            # tile size, pixels per metre
sheet = Image.new('RGB', (S * len(poses), S + 16), 'white')
for k, (clip, t) in enumerate(poses):
    W = model.world(model.sample(clip, float(t)))
    pts = model.skinned_positions(W)[0][0]
    cx, cz = W[I['B_Pelvis'], 0, 3], W[I['B_Pelvis'], 2, 3]
    d = ImageDraw.Draw(sheet)

    def px(x, z):
        return (k * S + S / 2 - (x - cx) * PX, 16 + S / 2 - (z - cz) * PX)
    d.line([px(cx, cz - 0.3), px(cx, cz + 0.3)], fill=(170, 170, 170))
    for s, c in (('L', (40, 90, 200)), ('R', (200, 50, 40))):
        ids = np.where(np.isin(dom, [f'B_{s}_Foot', f'B_{s}_Toe0']))[0]
        p = pts[ids]
        p = p[p[:, 1] < p[:, 1].min() + 0.08]
        for q in p:
            x, y = px(q[0], q[2])
            d.point((x, y), fill=c)
        a, b = W[I[f'B_{s}_Foot'], :3, 3], W[I[f'B_{s}_Toe0'], :3, 3]
        d.line([px(a[0], a[2]), px(b[0], b[2])], fill='black', width=2)
    d.text((k * S + 4, 2), f'{Path(sys.argv[1]).stem} {clip} {float(t):.2f}', fill='black')
sheet.save(sys.argv[2])
