#!/usr/bin/env python3
"""Side (z,y) and top (z,x) scatter of the goat's head-weighted face centres by dominant bone -> review/head_plot.png;
optional work/glb_sets_<tag>.npz overlay (keep red, free by group)."""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_goat.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Goat' and 'mesh' in n)
pr = gb.prims(doc, b, node['mesh'])[0]
joints = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
P, T, J, W = pr['POSITION'].astype(float), pr['T'], pr['JOINTS_0'], pr['WEIGHTS_0'].astype(float)
nF = len(T); fw = np.zeros((nF, len(joints)))
for k in range(3):
    for c in range(4):
        np.add.at(fw, (np.arange(nF), J[T[:, k], c]), W[T[:, k], c])
dom = (fw / 3).argmax(1); cen = P[T].mean(1)
from PIL import Image, ImageDraw
sel = cen[:, 2] > 0.25
PAL = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240),
       (240, 50, 230), (210, 245, 60), (250, 190, 212), (0, 128, 128), (170, 110, 40), (128, 0, 0), (0, 0, 128)]
S = 1600; views = [(2, 1, (0.25, 0.65), (0.55, 0.95)), (2, 0, (0.25, 0.65), (-0.2, 0.2)), (0, 1, (-0.2, 0.2), (0.55, 0.95))]
img = Image.new('RGB', (S * 3, S + 200), 'white'); d = ImageDraw.Draw(img)
if len(sys.argv) > 1:
    s_ = np.load(HERE / 'work' / f'glb_sets_{sys.argv[1]}.npz'); lab = np.where(s_['keep'], 0, s_['group'] + 1)
    names = ['keep'] + [f'group {g}' for g in range(6)]
else:
    lab = dom; names = joints
order = np.argsort(cen[:, 0] if True else 0)
for vi, (a, b_, (a0, a1), (b0, b1)) in enumerate(views):
    sc = S / max(a1 - a0, b1 - b0)
    for f in np.flatnonzero(sel):
        x = vi * S + (cen[f, a] - a0) * sc; y = S - (cen[f, b_] - b0) * sc
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=PAL[lab[f] % len(PAL)])
    for k in range(11):
        v = a0 + k * (a1 - a0) / 10; d.text((vi * S + (v - a0) * sc, S + 5), f'{v:.2f}', fill='black')
        v = b0 + k * (b1 - b0) / 10; d.text((vi * S + 5, S - (v - b0) * sc), f'{v:.2f}', fill='black')
for k, l in enumerate(np.unique(lab[sel])):
    d.rectangle([20 + 260 * (k % 12), S + 30 + 40 * (k // 12), 40 + 260 * (k % 12), S + 50 + 40 * (k // 12)], fill=PAL[l % len(PAL)])
    d.text((45 + 260 * (k % 12), S + 32 + 40 * (k // 12)), names[l], fill='black')
img.save(HERE / 'review' / f'head_plot{"_" + sys.argv[1] if len(sys.argv) > 1 else ""}.png')
