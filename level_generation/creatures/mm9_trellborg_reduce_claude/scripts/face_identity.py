#!/usr/bin/env python3
"""Face identity: every installed LOD0 triangle in the exact face set (make_sets.py: face front, ears, nape/neck skin clusters, tusks,
neck seam; from work/labels.npz via work/mesh_in.npz centroids) must exist in the candidate with the same corner positions, UVs,
normals, joints and weights. Usage: face_identity.py <candidate.glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
d = np.load(HERE / 'work/mesh_in.npz'); L = np.load(HERE / 'work/labels.npz'); keep = np.load(HERE / 'work/keep_d.npy')
reg = L['reg']; face = keep & ((reg == 4) | (reg == 9) | (reg == 7) | L['seam'])
fc = d['verts'][d['faces']].mean(1)[face]
_, _, _, S = glbio.load(HERE / 'before/mm9_trellborg.glb', 'Trellborg'); _, _, _, C = glbio.load(sys.argv[1], 'Trellborg')
allc = np.vstack([S[n]['P'][S[n]['T']].mean(1) for n in S])[:, [0, 2, 1]] * [1, -1, 1]; FC = d['verts'][d['faces']].mean(1)
off = np.median(FC, 0) - np.median(allc, 0)
for _ in range(5):
    dist, nn = cKDTree(FC).query(allc + off); off += np.median(FC[nn] - (allc + off), 0)
print('map: median', float(np.median(dist)), 'max', float(dist.max()))
for name in ('TrellborgHead_A', 'Trellborg_A'):
    s, c = S[name], C[name]
    sc = s['P'][s['T']].mean(1)[:, [0, 2, 1]] * [1, -1, 1]
    dist, _ = cKDTree(fc).query(sc + off); sel = np.where(dist < 1e-5)[0]
    ctree = cKDTree(np.c_[c['P'], c['UV']]); dp = 0.0
    miss = 0; dn = dw = 0.0; dj = 0
    for t in sel:
        for v in s['T'][t]:
            dd, j = ctree.query(np.r_[s['P'][v], s['UV'][v]])
            if dd > 1e-5: miss += 1; continue
            dp = max(dp, float(dd))
            dn = max(dn, float(np.abs(c['N'][j] - s['N'][v]).max())); dw = max(dw, float(np.abs(c['W'][j] - s['W'][v]).max()))
            dj += int((c['J'][j] != s['J'][v]).any() and (s['W'][v] > 0).any())
    print(f'FACEID {name}: {len(sel)} kept-face triangles, corners missing {miss}, max position/UV difference {dp:.1e}, max |dN| {dn:.2e}, max |dW| {dw:.2e}, joint mismatches {dj}')
