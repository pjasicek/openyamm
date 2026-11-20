#!/usr/bin/env python3
"""Colour-class drift of a decimated mesh (texture_drift.py reads high-frequency chain mail as drift everywhere): each
base-colour sample is classed (0 grey: chain mail, steel, 1 skin, 2 gold, 3 dark-brown leather, 4 green cloth,
5 hair, 6 navy leggings, 7 other); a candidate face's 16 samples are compared with the majority class of the 8
nearest source samples at the same rest-pose points (agreeing normals). Faces where over half the samples change
class are smears (a strap colour pushed onto chain mail, skin flecks on the gold panels). Prints the worst, writes
work/cdrift_<tag>.npy (per-face changed fraction) for drift_lock.py-style locks (cdrift_lock.py).
Usage: class_drift.py <tag, e.g. h_r83>"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
tag = sys.argv[1]
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 16)


def classes(col):
    r, g, b = col[..., 0], col[..., 1], col[..., 2]; mx = col.max(-1); mn = col.min(-1); sat = (mx - mn) / (mx + 1e-6)
    k = np.full(r.shape, 7)
    k[sat < .25] = 0
    k[(sat >= .25) & (r > g) & (g > b) & (mx > .55) & (r - g > .12) & (g - b > .05) & (g < .75 * r + .1)] = 1
    k[(sat >= .45) & (r > .55) & (g > .45) & (b < .4 * g)] = 2
    k[(mx < .42) & (r > g * 1.15) & (g > b * 1.05) & (sat >= .25)] = 3
    k[(g > r * 1.3) & (g > b * 1.3)] = 4
    k[(k == 7) & (r > g) & (g > b) & (sat >= .25)] = 5
    k[(b > r * 1.2) & (mx < .45)] = 6
    return k


def samples(path):
    d = np.load(path); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
    tri = v[f]; nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    pos = np.einsum('sk,fkc->fsc', B, tri); u = np.einsum('sk,fkc->fsc', B, uv)
    x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
    return pos, nrm, classes(img[y, x]), tri


sp, sn, sk, _ = samples('work/mesh_in.npz'); cp, cn, ck, ctri = samples(f'work/mesh_{tag}.npz')
tree = cKDTree(sp.reshape(-1, 3)); dist, idx = tree.query(cp.reshape(-1, 3), 8)
ok = np.abs((np.repeat(sn, len(B), 0)[idx] * np.repeat(cn, len(B), 0)[:, None]).sum(-1)) > .5
skf = sk.reshape(-1)[idx]; votes = np.zeros((len(idx), 8))
for j in range(8):
    np.add.at(votes, (np.arange(len(idx)), skf[:, j]), ok[:, j] / (1 + dist[:, j] * 100))
src_class = votes.argmax(1); changed = (ck.reshape(-1) != src_class).reshape(len(cn), len(B)).mean(1)
np.save(f'work/cdrift_{tag}.npy', changed)
area = np.linalg.norm(np.cross(ctri[:, 1] - ctri[:, 0], ctri[:, 2] - ctri[:, 0]), axis=1) / 2
bad = (changed > .5) & (area > 2e-4)
print(tag, 'faces', len(cn), 'class change > 50 % (over 2 cm2):', int(bad.sum()), 'area cm2', round(float(area[bad].sum() * 1e4), 1))
cen = ctri.mean(1); names = ['grey', 'skin', 'gold', 'brown', 'green', 'hair', 'navy', 'other']
for i in np.argsort(-changed * np.sqrt(area))[:12]:
    sc = np.bincount(src_class.reshape(len(cn), len(B))[i], minlength=8).argmax(); cc = np.bincount(ck[i], minlength=8).argmax()
    print(f'  face {i} changed {changed[i]:.2f} area {area[i]*1e4:.1f}cm2 at {np.round(cen[i], 3)} {names[sc]} -> {names[cc]}')
