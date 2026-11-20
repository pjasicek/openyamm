"""Tooth faces of the welded source (work/mesh_in.npz) -> work/teeth_labels.npy per face:
0 other, 1 big fang (main head: grown from the ivory faces over edge neighbours inside a tube around the fitted
fang axis), 2 gum spike (upper gum piece below the band's lower edge), 3 separate tooth piece (replaced by cones).
Usage: teeth_select.py [tube radius m, default 0.022]"""
import sys
import numpy as np
from PIL import Image
R = float(sys.argv[1]) if len(sys.argv) > 1 else .022
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; uv = d['wuv'].reshape(-1, 3, 2)
comp = np.load('work/components.npy'); ctr = v[f].mean(1)
img = np.asarray(Image.open('work/basecolor.png').convert('RGB')).astype(float); H, W = img.shape[:2]
cu = uv.mean(1); col = img[np.clip(((1 - cu[:, 1]) * H).astype(int), 0, H - 1), np.clip((cu[:, 0] * W).astype(int), 0, W - 1)]
ivory = (comp == 1) & (col.mean(1) > 150) & (col.max(1) - col.min(1) < 70) & (np.abs(ctr[:, 0]) < .2) \
    & (ctr[:, 1] < -.2) & (ctr[:, 2] < .5)
edges = {}
for i, (a, b, c) in enumerate(f):
    for e in ((a, b), (b, c), (c, a)):
        edges.setdefault((min(e), max(e)), []).append(i)
nbr = [[] for _ in f]
for l in edges.values():
    for i in l:
        nbr[i] += [j for j in l if j != i]
lab = np.zeros(len(f), int)
for s in (1, -1):
    m = ivory & (np.sign(ctr[:, 0]) == s); P = ctr[m]; mu = P.mean(0)
    ax = np.linalg.svd(P - mu)[2][0]; ax = -ax if ax[2] > 0 else ax
    t = (ctr - mu) @ ax; r = np.linalg.norm((ctr - mu) - t[:, None] * ax, axis=1)
    inside = (comp == 1) & (r < R) & (t > -.075) & (t < .14)
    seen = set(np.where(m)[0]); stack = list(seen)
    while stack:
        i = stack.pop()
        for j in nbr[i]:
            if j not in seen and inside[j]:
                seen.add(j); stack.append(j)
    lab[list(seen)] = 1
    sel = np.array(sorted(seen)); ts = t[sel]
    print('fang', s, 'faces', len(sel), 'ivory', int(m.sum()), 't', ts.min().round(3), ts.max().round(3),
          'z', ctr[sel, 2].min().round(3), ctr[sel, 2].max().round(3))
gum = comp == 0
lab[gum & (ctr[:, 2] < .428)] = 2
lab[np.isin(comp, [5, 6, 7, 8, 9, 10])] = 3
np.save('work/teeth_labels.npy', lab); print({k: int((lab == k).sum()) for k in range(4)})
