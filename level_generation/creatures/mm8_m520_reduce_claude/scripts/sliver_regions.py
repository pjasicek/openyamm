#!/usr/bin/env python3
"""Dark-sliver and drift summary per region for the retexture check: the dark_slivers.py test (samples darker than the
source by over 60 at the same rest-pose point) with counts at 2 and 8 of 48 samples and their area, per region (face
and eye = head set within 0.12 m of the iris height, head set rest, hands, boots, loincloth/hip box, body rest).
Usage: sliver_regions.py <tag ...>  (work/mesh_<tag>.npz against work/mesh_in.npz)"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
img = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32); H, W = img.shape[:2]
B = np.random.default_rng(1).dirichlet((1, 1, 1), 48)


def samples(path):
    d = np.load(path); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2); tri = v[f]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    pos = np.einsum('sk,fkc->fsc', B, tri); u = np.einsum('sk,fkc->fsc', B, uv)
    x = np.clip((u[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - u[..., 1] % 1) * H, 0, H - 1).astype(int)
    return pos, nrm, img[y, x] @ np.array([.3, .59, .11]), tri, uv


sp, sn, sl, stri, _ = samples('work/mesh_in.npz')
stree = cKDTree(sp.reshape(-1, 3))
vw = np.load('work/vweights.npz'); src = np.load('work/mesh_in.npz')
hand_v = (vw['hand'] + vw['finger']) > .5


def regions(tri, uv, path):
    d = np.load(path); c = tri.mean(1); headset = uv[:, :, 0].mean(1) > .5
    near = cKDTree(src['verts']).query(c)[1]
    lab = np.full(len(c), 'body', object)
    lab[c[:, 2] < .72] = 'boots'
    lab[(c[:, 2] > .72) & (c[:, 2] < 1.2) & (np.abs(c[:, 1]) < .25) & (np.abs(c[:, 0]) < .35)] = 'loin/hip'
    lab[hand_v[near]] = 'hands'
    lab[headset] = 'head set'
    eye_z = c[headset][:, 2].max() - .2
    lab[headset & (np.abs(c[:, 2] - eye_z) < .12) & (c[:, 1] < 0)] = 'face/eye'
    return lab


for tag in sys.argv[1:]:
    cp, cn, cl, ctri, cuv = samples(f'work/mesh_{tag}.npz')
    dist, idx = stree.query(cp.reshape(-1, 3), 8)
    ok = np.abs((np.repeat(sn, len(B), 0)[idx] * np.repeat(cn, len(B), 0)[:, None]).sum(-1)) > .5
    best = idx[np.arange(len(idx)), np.where(ok, dist, np.inf).argmin(1)]
    n = ((sl.reshape(-1)[best] - cl.reshape(-1)).reshape(len(cn), len(B)) > 60).sum(1)
    area = np.linalg.norm(np.cross(ctri[:, 1] - ctri[:, 0], ctri[:, 2] - ctri[:, 0]), axis=1) / 2
    lab = regions(ctri, cuv, f'work/mesh_{tag}.npz')
    print(tag, 'faces', len(n))
    for r in ['face/eye', 'head set', 'hands', 'body', 'loin/hip', 'boots']:
        m = lab == r
        print(f'  {r:9s} faces {m.sum():5d}  >=2: {int((m & (n >= 2)).sum()):4d} ({area[m & (n >= 2)].sum() * 1e4:6.1f} cm2)'
              f'  >=8: {int((m & (n >= 8)).sum()):3d} ({area[m & (n >= 8)].sum() * 1e4:5.1f} cm2)')
