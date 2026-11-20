#!/usr/bin/env python3
"""Neck seam tone: per-channel linear gain (body / head) measured across every mesh edge shared by a head face and a torso
face (mesh_sub.npz, positions welded), each side sampled 30 % inside its face from the edge midpoint, skin-coloured samples
only. Args: <pre eb|sr> -> prints the gain JSON on one line"""
import sys, json, numpy as np
from PIL import Image
pre = sys.argv[1]
D = np.load('work/mesh_sub.npz'); co, tri, uv, mat = D['co'], D['tri'], D['uv'], D['mat']; mn = [str(x) for x in D['matnames']]
hi, ti = mn.index('EboraHead'), mn.index('EboraTorso')
key = np.round(co, 5); _, w = np.unique(key, axis=0, return_inverse=True); w = w.ravel()
edges = {}
for f, (t, m) in enumerate(zip(tri, mat)):
    if m not in (hi, ti): continue
    for k in range(3):
        a, b = w[t[k]], w[t[(k + 1) % 3]]
        edges.setdefault((min(a, b), max(a, b)), []).append((f, k))
lin = lambda v: np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
H = np.asarray(Image.open(f'textures/{pre}_head_proj.png').convert('RGB'), float) / 255
B = np.asarray(Image.open(f'textures/{pre}_torso_tone.png' if pre == 'eb' else f'textures/{pre}_torso_tone.png').convert('RGB'), float) / 255
def sample(img, f, k):
    t = tri[f]; mid = (uv[t[k]] + uv[t[(k + 1) % 3]]) / 2; c = uv[t].mean(0); p = mid + (c - mid) * 0.3
    h_, w_ = img.shape[:2]; return img[int(np.clip((1 - p[1]) * h_, 0, h_ - 1)), int(np.clip(p[0] * w_, 0, w_ - 1))]
hs, bs = [], []
for e, fs in edges.items():
    ms = {mat[f] for f, _ in fs}
    if ms != {hi, ti}: continue
    fh = next(x for x in fs if mat[x[0]] == hi); fb = next(x for x in fs if mat[x[0]] == ti)
    hs.append(sample(H, *fh)); bs.append(sample(B, *fb))
hs, bs = np.array(hs), np.array(bs)
def skinlike(c): return (c[:, 0] > 0.35) & (c[:, 0] > c[:, 2] * 1.3)
m = skinlike(hs) & skinlike(bs)
g = np.median(lin(bs[m]), 0) / np.maximum(np.median(lin(hs[m]), 0), 1e-4)
print(json.dumps({'pre': pre, 'edges': int(len(hs)), 'skin_pairs': int(m.sum()), 'head': (np.median(hs[m], 0) * 255).round().tolist(), 'body': (np.median(bs[m], 0) * 255).round().tolist(), 'gain': np.round(g, 3).tolist()}))
