#!/usr/bin/env python3
"""Faces whose UV triangle reaches over its chart border onto foreign texels (the gutter, or texels of another part of
the body): the creature's UV raster (mm8_m600_claude/work/uvraster_UVMap.npz: per texel at 2048 the source rest-pose
3D position and piece) is looked up at dense barycentric samples of each reduced face; a sample is foreign when its
texel is empty or lies over REA_BLEED_MM (default 15 mm) from the sample's own rest-pose point, or belongs to another
piece (skin / eyes / teeth); texels the source itself fails on (UVs shared by several parts) are ignored. A face is flagged when at least REA_BLEED_N (default 2) samples are foreign.
texture_drift.py, which uses each face's median colour, misses these (MM8 Nightmare: a mouth-red fleck on the left
stalk junction). Usage: chart_bleed.py <tag> -> work/bleed_<tag>.npy"""
import os
import sys
import numpy as np
tag = sys.argv[1]; TOL = float(os.environ.get('REA_BLEED_MM', '15')) / 1000; NMIN = int(os.environ.get('REA_BLEED_N', '2'))
r = np.load('../mm8_m600_claude/work/uvraster_UVMap.npz'); pos, piece = r['pos'], r['piece']; N = piece.shape[0]
g = np.linspace(0, 1, 11); B = np.array([(a, b, 1 - a - b) for a in g for b in g if a + b <= 1 + 1e-9]) * .96 + .04 / 3


def lookup(path):
    m = np.load(path); f, uv, v = m['faces'], m['wuv'].reshape(-1, 3, 2), m['verts']
    U = np.einsum('sk,fkc->fsc', B, uv); P = np.einsum('sk,fkc->fsc', B, v[f])
    x = np.clip((U[..., 0] * N).astype(int), 0, N - 1); y = np.clip(((1 - U[..., 1]) * N).astype(int), 0, N - 1)
    return f, v, x, y, np.linalg.norm(pos[y, x] - P, axis=-1) > TOL


# texels shared by several parts (stacked eye UVs) fail the position test for the source itself: don't-care
_, _, sx, sy, sfar = lookup('work/mesh_in.npz')
shared = np.zeros_like(piece, bool); shared[sy[sfar], sx[sfar]] = True
from scipy.ndimage import binary_dilation  # noqa: E402
shared = binary_dilation(shared, iterations=2)
f, v, x, y, far = lookup(f'work/mesh_{tag}.npz')
pc = piece[y, x]
own = np.array([np.bincount(p[p >= 0]).argmax() if (p >= 0).any() else -1 for p in pc])  # the face's own piece
foreign = (pc < 0) | (pc != own[:, None]) | (far & ~shared[y, x])
count = foreign.sum(1); bad = count >= NMIN
tri = v[f]; area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
np.save(f'work/bleed_{tag}.npy', bad)
print(tag, 'faces sampling foreign texels', int(bad.sum()), 'area cm2', round(float(area[bad].sum() * 1e4), 2))
for i in np.where(bad)[0][np.argsort(-count[bad])][:10]:
    print(f'  face {i} foreign samples {count[i]}/{len(B)} area {area[i] * 1e4:.2f} cm2 at {np.round(tri[i].mean(0), 3)}')
