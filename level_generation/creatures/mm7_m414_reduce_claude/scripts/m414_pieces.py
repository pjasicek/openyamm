#!/usr/bin/env python3
"""Per-face piece labels of the m414 Titan rest mesh (work/mesh_in.npz) by connected piece and position ->
work/pieces.npy: 1 face + neck skin (head texture set of the main shell), 2 torso (tunic, shoulders, arms' stone skin
above the vambraces belongs to the arm shells), 3 left arm, 4 right arm (vambrace, hand), 5 legs (greaves, sandals),
6 skirt tiers (three shells), 7 belt (lion), 8 helmet dome, 9 cheek and neck guard, 10 crest, 11 eyes;
work/soles.npy: leg faces below 6 cm; work/gold.npy: fraction of 7 base-colour samples per face that read gold
(hue 25-60 degrees, saturation > 0.35, value > 0.3)."""
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f, v, w = d['faces'], d['verts'], d['wuv']; n = len(v)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl); c = v[f].mean(1)
uv = w.reshape(-1, 3, 2); um = uv[:, :, 0].mean(1)
reg = np.zeros(len(f), int)
skirts = []
for p in np.flatnonzero(sizes):
    m = fl == p; cp = c[m].mean(0); s = sizes[p]
    if s > 2500:
        reg[m] = 2; reg[m & (um > 0.51)] = 1
    elif s > 1000 and abs(cp[0]) > 0.3:
        reg[m] = 3 if cp[0] > 0 else 4
    elif s > 1000:
        reg[m] = 5
    elif s < 100:
        reg[m] = 11
    elif cp[2] > 1.7 and cp[1] > 0.03:
        reg[m] = 10
    elif cp[2] > 1.62:
        reg[m] = 8
    elif cp[2] > 1.5:
        reg[m] = 9
    elif cp[2] > 1.0:
        reg[m] = 7
    else:
        reg[m] = 6; skirts.append((round(float(cp[2]), 3), int(s)))
soles = (reg == 5) & (c[:, 2] < 0.06)
# gold paint
img = np.asarray(Image.open('work/basecolor.png').convert('RGB')).astype(float) / 255; H, W = img.shape[:2]
bary = np.array([[1/3, 1/3, 1/3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6], [.8, .1, .1], [.1, .8, .1], [.1, .1, .8]])
pts = np.einsum('kj,fjc->fkc', bary, uv)
px = np.clip((pts[..., 0] * W).astype(int), 0, W - 1); py = np.clip(((1 - pts[..., 1]) * H).astype(int), 0, H - 1)
rgb = img[py, px]; mx = rgb.max(-1); mn = rgb.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
gold = ((hue > 25) & (hue < 60) & (sat > 0.35) & (mx > 0.3)).mean(1)
np.save('work/pieces.npy', reg); np.save('work/soles.npy', soles); np.save('work/gold.npy', gold)
names = {1: 'face+neck', 2: 'torso', 3: 'arm +x', 4: 'arm -x', 5: 'legs', 6: 'skirts', 7: 'belt', 8: 'helmet',
         9: 'guards', 10: 'crest', 11: 'eyes'}
print({names[k]: int((reg == k).sum()) for k in names}, 'unlabelled', int((reg == 0).sum()), 'soles', int(soles.sum()),
      'skirt shells', skirts)
print('gold faces (>=2/7)', {names[k]: int(((reg == k) & (gold >= 2 / 7)).sum()) for k in names})
print('crest z', round(float(v[f[reg == 10]][..., 2].max()), 4), 'helmet z', round(float(v[f[reg == 8]][..., 2].max()), 4),
      'top', round(float(v[:, 2].max()), 4))
