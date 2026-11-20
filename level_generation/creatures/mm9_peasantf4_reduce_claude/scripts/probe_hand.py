#!/usr/bin/env python3
"""Which body face an arm_hand_gate.py (--outer-only --exact) hand reading is behind: the deepest hand vertex of one side at one
clip time, its nearest outer body face and that face's asm part (work/glb_labels.npz via the installed vertices).
Usage: probe_hand.py <glb> <clip> <seconds> <L|R>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; S = HERE.parent / 'mm9_peasantf4_claude' / 'scripts'
sys.path.insert(0, str(S)); sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
from outer_surface import outer_faces  # noqa: E402
import bglbio as g  # noqa: E402
GLB, clip, t, side = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
M = Model(Glb(GLB)); P = M.primitives
names = [n.get('name') for n in M.glb.json['nodes']] if hasattr(M, 'glb') else None
d1, b1 = g.read(GLB); jn = [d1['nodes'][j]['name'] for j in M.joints]
tris = np.vstack([P[0]['triangles'], P[1]['triangles'] + len(P[0]['positions'])])
dom = np.concatenate([[jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))] for pr in P])
tok = f' {side} '
arm = np.array([tok in j and any(k in j for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Forearm', 'UpperArm', 'Clavicle')) for j in dom])
hand = np.array([tok in j and any(k in j for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for j in dom])
pose = lambda w: np.vstack([p for p, _ in M.skinned_positions(w)])
rest = pose(M.world({})); X = pose(M.world(M.sample(clip, t)))
body_f = np.where(~arm[tris].any(1))[0]; body_f = body_f[outer_faces(rest, tris, body_f)]
T = X[tris[body_f]]; c = T.mean(1); n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True)
hv = np.where(hand)[0]; dd, j = cKDTree(c).query(X[hv]); side_ = np.einsum('ij,ij->i', X[hv] - c[j], n[j])
k = np.argmin(side_); f = body_f[j[k]]
L = np.load(HERE / 'work' / 'glb_labels.npz'); names = [str(x) for x in L['names']]
d0, b0 = g.read(HERE / 'before' / 'mm9_peasantf4.glb'); P0 = g.prims(d0, b0, 0); voff = np.cumsum([0] + [len(p['POSITION']) for p in P0])
pr1 = g.prims(d1, b1, 0); off1 = [0, len(pr1[0]['POSITION'])]
v = tris[f][0]; m = 0 if v < off1[1] else 1; vl = v - off1[m]
dq, jq = cKDTree(np.c_[P0[m]['POSITION'], P0[m]['TEXCOORD_0'] * 0.01]).query(np.r_[pr1[m]['POSITION'][vl], pr1[m]['TEXCOORD_0'][vl] * 0.01])
print('deepest hand vertex', hv[k], 'side', round(float(side_[k]) * 100, 2), 'cm; face', f, 'part', names[L['vcomp'][jq + voff[m]]], 'centroid', c[j[k]].round(3), 'dist', round(float(dd[k]) * 100, 2))
print('outer body faces by part:', {names[q]: 0 for q in []})
