#!/usr/bin/env python3
"""Body faces where the head or jaw passes through the torso (a55 gates: jaw/head into torso rose in Fidget2, AttackMelee2,
Taunt, Death). On the installed GLB, with ../mm9_ghoul_claude/scripts/pierce_gate.py's own sets and depth test (every clip,
24 fps): for each head/jaw point behind the torso surface, the torso faces within R m of it, plus every body face whose
corners the gate counts as head or jaw (head-dominated skin of the neck band). Mirrored in x. Writes work/keep_extra_pierce.npy
(per Ghoul_A face). Usage: pierce_keep.py [R]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
R = float(sys.argv[1]) if len(sys.argv) > 1 else 0.03
m = Model(Glb(str(HERE / 'before' / 'mm9_ghoul.glb'))); doc = m.glb.json; jn = [doc['nodes'][j]['name'] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tris, off, dom = [], 0, []
for k in USE:
    pr = P[k]; tris.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
nb = len(P[USE[0]]['triangles']); nbv = len(P[USE[0]]['positions'])
tris = np.concatenate(tris); dom = np.concatenate(dom)
isd = lambda *k: np.array([any(x in d for x in k) for d in dom])
src = (dom == 'Box05') | (dom == 'Bip01 Head'); torso = isd('Spine', 'Pelvis')
faces = np.where(torso[tris].all(1))[0]
bind = np.concatenate([np.asarray(P[k]['positions'], float) for k in USE])
tgt = np.unique(tris[faces]); dd = cKDTree(bind[tgt]).query(bind[src])[0]; s = np.where(src)[0][dd >= .10]
keep = np.zeros(nb, bool)
keep |= (src[tris[:nb]]).any(1)                       # body faces the gate counts as head/jaw
for c in [a['name'] for a in doc['animations']]:
    for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 24):
        sp = m.skinned_positions(m.world(m.sample(c, float(t)))); X = np.concatenate([sp[k][0] for k in USE])
        T = X[tris[faces]]; a, b, cc = T[:, 0], T[:, 1], T[:, 2]
        n = np.cross(b - a, cc - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        pts = X[s]; _, near = cKDTree((a + b + cc) / 3).query(pts, k=16)
        rp = np.repeat(pts, 16, 0); q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], cc[near.ravel()])
        d = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = d.argmin(1); r = np.arange(len(pts))
        cp = q.reshape(*near.shape, 3)[r, best]; side = np.einsum('ij,ij->i', pts - cp, n[near[r, best]])
        inside = (side < -0.002) & (d[r, best] <= .08)
        if inside.any():
            cen = X[tris[:nb]].mean(1)
            for i in cKDTree(cen).query_ball_point(pts[inside], R):
                keep[i] = True
# mirror in x (rest centroids)
cen0 = bind[tris[:nb]].mean(1); mir = cen0 * [-1, 1, 1]
dist, j = cKDTree(cen0).query(mir[keep]); keep[j[dist < 0.01]] = True
np.save(HERE / 'work' / 'keep_extra_pierce.npy', keep); print('PIERCE KEEP', R, int(keep.sum()), 'of', nb)
