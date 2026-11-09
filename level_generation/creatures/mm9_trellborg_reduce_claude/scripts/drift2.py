#!/usr/bin/env python3
"""Texture drift, dense version (texture_drift.py compares with the nearest of 12 random source samples per face, several mm off on
the large body faces, so the fine paint of mail, fur and studs reads as drift): the source surface is sampled every ~SPACING m
(area-proportional), each candidate sample (24 per face) takes the nearest source sample with a similar normal; per face the median
colour difference (0-255, mean over RGB) of the worst tier. Prints the noise floor (the same comparison of the source against
itself with fresh random samples) and the drifted faces. Writes work/drift_<tag>.npy. Usage: drift2.py <tag>"""
import os, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
tag = sys.argv[1]; SP = float(os.environ.get('SPACING', .0015)); TIERS = os.environ.get('TIERS', 'a,b,c').split(',')
ALL = {t: [np.asarray(Image.open(f'../mm9_trellborg_claude/textures/{x}').convert('RGB'), np.float32)
           for x in (f'trell_body_{t}_final.png', f'trell_head_{t}_final.png', 'trell_club_basecolor.png')] for t in TIERS}
def look(imgs, u):
    m = np.clip((u[:, 0] // 2).astype(int), 0, 2); out = np.zeros((len(u), 3), np.float32)
    for k, im in enumerate(imgs):
        s = m == k; H, W = im.shape[:2]; uu = u[s]
        x = np.clip(((uu[:, 0] - 2 * k) % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - uu[:, 1] % 1) * H, 0, H - 1).astype(int)
        out[s] = im[y, x]
    return out
rng = np.random.default_rng(2)
def load(path):
    d = np.load(path); tri = d['verts'][d['faces']]; uv = d['wuv'].reshape(-1, 3, 2)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); a = np.linalg.norm(n, axis=1) / 2; n /= np.maximum(2 * a, 1e-12)[:, None]
    return tri, uv, n, a
def sample(tri, uv, counts):
    fi = np.repeat(np.arange(len(tri)), counts); b = rng.dirichlet((1, 1, 1), len(fi))
    return fi, np.einsum('sk,skc->sc', b, tri[fi]), np.einsum('sk,skc->sc', b, uv[fi])
st, su, sn, sa = load('work/mesh_in.npz')
sfi, sp, suv = sample(st, su, np.maximum(1, np.ceil(sa / SP ** 2)).astype(int)); tree = cKDTree(sp)
print('source samples', len(sp))
def drift(tri, uv, n, K=24):
    fi, p, u = sample(tri, uv, np.full(len(tri), K))
    dist, idx = tree.query(p, 6); ok = (sn[sfi[idx]] @ np.zeros(3) == 0)
    ok = np.einsum('skc,sc->sk', sn[sfi[idx]], n[fi]) > .5; dist = np.where(ok, dist, np.inf); best = idx[np.arange(len(idx)), dist.argmin(1)]
    out = []
    for t in TIERS:
        diff = np.abs(look(ALL[t], u) - look(ALL[t], suv[best])).mean(1).reshape(len(tri), K)
        out.append(np.median(diff, 1))
    return np.max(out, 0)
floor = drift(st, su, sn)
print('noise floor (source vs itself): p99', round(float(np.percentile(floor, 99)), 1), '>40', int((floor > 40).sum()))
ct, cu, cn, ca = load(f'work/mesh_{tag}.npz'); face = drift(ct, cu, cn)
np.save(f'work/drift_{tag}.npy', face); bad = (face > 40) & (ca > 3e-4)
print(tag, 'faces', len(face), 'p99', round(float(np.percentile(face, 99)), 1), '>40', int((face > 40).sum()), '>40 and >3cm2', int(bad.sum()), 'area cm2', round(float(ca[bad].sum() * 1e4), 1))
cen = ct.mean(1)
for i in np.argsort(-face * ca)[:10]:
    print(f'  face {i} drift {face[i]:.0f} area {ca[i]*1e4:.2f}cm2 at {np.round(cen[i], 3)}')
