#!/usr/bin/env python3
"""Per-face part labels of the installed LOD0 (before/mm9_nosferatu.glb, mesh 0: Nosferatu_A then NosferatuHead_A) from the
creature project's final rest mesh (../mm9_nosferatu_claude/work/uv_tex.npz: part per vertex). Faces are matched by
centroid after fitting the axis map (sign/permutation) and offset, then checked against the UV centroid.
Writes work/glb_parts.npz: per GLB face mat, part, src face, centroid, names."""
import sys, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio
doc, binary = glbio.read(HERE / 'before' / 'mm9_nosferatu.glb')
prims = glbio.prims(doc, binary, 0)
gc = np.vstack([p['POSITION'][p['T']].mean(1) for p in prims]).astype(np.float64)
guv = np.vstack([p['TEXCOORD_0'][p['T']].mean(1) for p in prims]).astype(np.float64)
gmat = np.concatenate([np.full(len(p['T']), i) for i, p in enumerate(prims)])
d = np.load(HERE.parent / 'mm9_nosferatu_claude' / 'work' / 'uv_tex.npz', allow_pickle=True)
nc = d['co'][d['tri']].mean(1); nuv = d['uv'][d['tri']].mean(1)
perm, sg, off = (0, 2, 1), (1, 1, -1), np.zeros(3)   # GLB = (x, z, -y) of the npz, measured: identical bounds
q = nc[:, perm] * np.array(sg) + off
nuv = nuv * [1, -1] + [0, 1]                        # glTF v = 1 - v
# combined key: position + UV (scaled), within the same material
fmat = d['mat']
src = np.zeros(len(gc), np.int64); dist = np.zeros(len(gc))
for m in (0, 1):
    gi = np.flatnonzero(gmat == m); ni = np.flatnonzero(fmat == m)
    A = np.c_[gc[gi], 0.2 * guv[gi]]; B = np.c_[q[ni], 0.2 * nuv[ni]]
    dd, nn = cKDTree(B).query(A); src[gi] = ni[nn]; dist[gi] = dd
print('MAP perm', perm, 'sign', sg, 'offset', np.round(off, 4), 'median d', np.median(dist), 'p99', np.percentile(dist, 99), 'max', dist.max())
names = [str(x) for x in d['names']]
part = d['comp'][d['tri'][src, 0]]
uvd = np.linalg.norm(guv - nuv[src], axis=1)
print('uv centroid diff max', uvd.max(), 'unique src', len(np.unique(src)), 'of', len(gc))
for i, n in enumerate(names):
    s_ = part == i; print(f'{n:8s} {s_.sum():6d} mat {np.bincount(gmat[s_], minlength=2)}')
np.savez(HERE / 'work' / 'glb_parts.npz', mat=gmat, part=part, src=src, cen=gc, names=np.array(names), dist=dist)
