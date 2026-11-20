"""Texture drift of a decimated mesh: each face's base colour (sampled at its UVs) against the source's colour at the
same rest-pose points (nearest source sample with a similar normal). Prints the worst clusters; writes
work/drift_<tag>.npy (per-face mean colour difference, 0-255). Usage: texture_drift.py <tag, e.g. r60>"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

tag = sys.argv[1]
# Trellborg: one base colour per material (u offset 2 per material in mesh_in.npz): body, head, club; every tier (TIERS, default a,b,c):
# the per-face drift written is the largest over the tiers
import os
TIERS = os.environ.get('TIERS', 'a,b,c').split(',')
ALL = {t: [np.asarray(Image.open(f'../mm9_trellborg_claude/textures/{x}').convert('RGB'), np.float32)
           for x in (f'trell_body_{t}_final.png', f'trell_head_{t}_final.png', 'trell_club_basecolor.png')] for t in TIERS}
imgs = ALL[TIERS[0]]


def look(u):
    m = np.clip((u[..., 0] // 2).astype(int), 0, len(imgs) - 1); out = np.zeros(u.shape[:-1] + (3,), np.float32)
    for k, im in enumerate(imgs):
        s = m == k; H, W = im.shape[:2]; uu = u[s]
        x = np.clip(((uu[:, 0] - 2 * k) % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - uu[:, 1] % 1) * H, 0, H - 1).astype(int)
        out[s] = im[y, x]
    return out
rng = np.random.default_rng(1)
B = rng.dirichlet((1, 1, 1), 12)  # barycentric sample points per face


def samples(path):
    d = np.load(path); v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
    tri = v[f]; nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    pos = np.einsum('sk,fkc->fsc', B, tri); u = np.einsum('sk,fkc->fsc', B, uv)
    return pos, nrm, look(u), tri


faces_t = {}
for T_ in TIERS:
  imgs = ALL[T_]
  sp, sn, sc, _ = samples('work/mesh_in.npz')
  cp, cn, cc, ctri = samples(f'work/mesh_{tag}.npz')
  tree = cKDTree(sp.reshape(-1, 3))
  k = 8
  dist, idx = tree.query(cp.reshape(-1, 3), k)
  srcn = np.repeat(sn, len(B), 0)[idx]  # (N, k, 3)
  cnr = np.repeat(cn, len(B), 0)[:, None]
  ok = np.abs((srcn * cnr).sum(-1)) > .5  # two-sided cards: either orientation
  dist = np.where(ok, dist, np.inf)
  best = idx[np.arange(len(idx)), dist.argmin(1)]
  diff = np.abs(cc.reshape(-1, 3) - sc.reshape(-1, 3)[best]).mean(1).reshape(len(cn), len(B))
  face = np.median(diff, 1)
  faces_t[T_] = face
  print(T_, 'p99', round(float(np.percentile(face, 99)), 1), 'drift>40', int((face > 40).sum()))
face = np.max(np.stack(list(faces_t.values())), 0)
np.save(f'work/drift_{tag}.npy', face)
area = np.linalg.norm(np.cross(ctri[:, 1] - ctri[:, 0], ctri[:, 2] - ctri[:, 0]), axis=1) / 2
bad = face > 40
print(tag, 'faces', len(face), 'drift>40:', int(bad.sum()), 'area cm2', round(float(area[bad].sum() * 1e4), 1),
      'p99', round(float(np.percentile(face, 99)), 1))
cen = ctri.mean(1)
for i in np.argsort(-face * area)[:12]:
    print(f'  face {i} drift {face[i]:.0f} area {area[i]*1e4:.2f}cm2 at {np.round(cen[i], 3)}')
