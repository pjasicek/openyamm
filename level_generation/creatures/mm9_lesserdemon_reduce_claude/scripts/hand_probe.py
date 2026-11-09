#!/usr/bin/env python3
"""Arm/hand gate probe (the demon's arm_hand_gate.py logic, --outer-only --exact) at one clip frame for two GLBs: the deepest
hand vertices of one side, with rest position, dominant joint and the nearest outer body face's centroid and dominant joint.
Usage: hand_probe.py <a.glb> <b.glb> <clip> <frame48> <side L|R>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; D = HERE.parent / 'mm9_stage1demon_claude' / 'scripts'
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared')); sys.path.insert(0, str(D))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
from outer_surface import outer_faces
a, b, clip, fr, side = sys.argv[1:6]; fr = int(fr); tok = f' {side} '
for f in (a, b):
    g = Glb(Path(f)); m = Model(g); names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
    P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
    tri, off, dom, rest0 = [], 0, [], []
    for pr in [P[k] for k in USE]:
        tri.append(pr['triangles'] + off); off += len(pr['positions']); rest0.append(pr['positions'])
        dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
    tris = np.concatenate(tri); dom = np.concatenate(dom); rest0 = np.concatenate(rest0)
    hv = np.where(np.isin(dom, [j for j in jn if tok in j and any(k in j for k in ('Hand', 'Finger'))]))[0]
    av = np.isin(dom, [j for j in jn if tok in j and any(k in j for k in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger'))])
    bf = np.where(~av[tris].any(1))[0]
    R = np.concatenate([sp[0] for k, sp in enumerate(m.skinned_positions(m.world({}))) if k in USE]); bf = bf[outer_faces(R, tris, bf)]
    X = np.concatenate([sp[0] for k, sp in enumerate(m.skinned_positions(m.world(m.sample(clip, fr / 48.0)))) if k in USE])
    T = X[tris[bf]]; A, B, C = T[:, 0], T[:, 1], T[:, 2]; n = np.cross(B - A, C - A); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    pts = X[hv]; _, near = cKDTree((A + B + C) / 3).query(pts, k=40)
    q, _ = closest_on_triangles(np.repeat(pts, 40, 0), A[near.ravel()], B[near.ravel()], C[near.ravel()])
    d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
    sd = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
    dep = np.where((sd < 0) & (d[rows, best] <= 0.06), -sd, 0)
    print(Path(f).name, 'max depth cm', round(dep.max() * 100, 2), 'outer body faces', len(bf))
    for i in np.argsort(-dep)[:5]:
        fi = bf[near[i, best[i]]]
        print(f'   hand v rest {rest0[hv[i]].round(3)} {dom[hv[i]]} depth {dep[i] * 100:.2f} cm; face rest centroid {rest0[tris[fi]].mean(0).round(3)} {dom[tris[fi][0]]}')
