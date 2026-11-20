#!/usr/bin/env python3
"""Where an arm/hand gate depth comes from (PeasantDM4 reduction): the creature's arm_hand_gate.py --outer-only --exact logic for
one side, clip and time; prints the deepest forearm/hand vertices with the nearest outer face (primitive, centroid at rest,
one-texel or painted; NO_TEXEL=1 leaves one-texel faces out of the surface). Usage: arm_probe_dm4.py <glb> <side token e.g. ' R '> <clip> <seconds>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
C = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(C / 'claude_shared' / 'floor')); sys.path.insert(0, str(C / 'claude_shared'))
sys.path.insert(0, str(C / 'mm9_peasantdm4_claude' / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
from outer_surface import outer_faces  # noqa: E402
glb, tok, clip, t = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
g = Glb(Path(glb)); m = Model(g); names = [n.get('name') for n in g.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tri_all, off, dom_all, prim_of = [], 0, [], []
for k in USE:
    pr = P[k]; tri_all.append(pr['triangles'] + off); off += len(pr['positions']); prim_of += [k] * len(pr['triangles'])
    dom_all.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tri_all); dom = np.concatenate(dom_all); prim_of = np.array(prim_of)
arm = ['Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Twist']
aj = [j for j in jn if tok in j and any(k in j for k in arm)]; fj = [j for j in jn if tok in j and 'Forearm' in j]
hj = [j for j in jn if tok in j and any(k in j for k in ['Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'])]
av = np.isin(dom, aj); fv = np.flatnonzero(np.isin(dom, fj) | np.isin(dom, hj))
body_f = np.flatnonzero(~av[tris].any(1))
rest = np.concatenate([s[0] for i, s in enumerate(m.skinned_positions(m.world({}))) if i in USE])
body_f = body_f[outer_faces(rest, tris, body_f)]
import os
if os.environ.get('NO_TEXEL') == '1':                  # leave out one-texel faces (linings, rim strips): the probe's check
    sys.path.insert(0, str(C / 'mm9_peasantdm4_reduce_claude' / 'scripts')); import bglbio  # noqa: E402
    doc, bb = bglbio.read(glb); nd = next(x for x in doc['nodes'] if x.get('name') == 'PeasantDM4' and 'mesh' in x)
    U = np.concatenate([p_['TEXCOORD_0'].astype(float) for p_ in bglbio.prims(doc, bb, nd['mesh'])])
    spread = np.abs(U[tris] - U[tris][:, :1]).max((1, 2)); body_f = body_f[spread[body_f] > 1e-7]
    print('NO_TEXEL: outer faces', len(body_f))
X = np.concatenate([s[0] for i, s in enumerate(m.skinned_positions(m.world(m.sample(clip, t)))) if i in USE])
T = X[tris[body_f]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
pts = X[fv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
q, _ = closest_on_triangles(np.repeat(pts, 40, 0), a[near.ravel()], b[near.ravel()], c[near.ravel()])
d = np.linalg.norm(np.repeat(pts, 40, 0) - q, axis=1).reshape(near.shape); best = d.argmin(1); rows = np.arange(len(pts))
side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[rows, best], n[near[rows, best]])
dep = np.where((side < 0) & (d[rows, best] <= 0.06), -side, 0.0)
o = np.argsort(-dep)[:8]
for i in o:
    f = body_f[near[i, best[i]]]
    print(f'vert {fv[i]} {dom[fv[i]]:16s} depth {dep[i] * 100:.2f} cm  rest {rest[fv[i]].round(3)}  face {f} prim {prim_of[f]} rest centre {rest[tris[f]].mean(0).round(3)} dist {d[i, best[i]] * 100:.2f} cm')
