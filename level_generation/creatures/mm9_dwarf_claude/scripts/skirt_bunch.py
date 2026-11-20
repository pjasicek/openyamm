#!/usr/bin/env python3
"""Skirt bunching per clip (run 2: the shiny roll under the belt in Running and AttackMelee). Skirt = vertices with any Skirt_* weight.
Per frame, in the Spine frame: vertical edge squash (posed / rest length, edges steeper than 45 deg at rest, upper band = rest height within
UPPER m of the belt) and faces squashed below 50 % of rest area. Args: <glb> [clips]"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb = sys.argv[1]; want = sys.argv[2].split(',') if len(sys.argv) > 2 else None
m = Model(Glb(glb)); PR = [p for p in m.primitives if p['skinned'] and p['node'] == m.primitives[0]['node']]
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
def allpos(w): return np.vstack([m.skinned_positions(w)[i][0] for i in range(len(PR))])
J, W = np.vstack([p['joints'] for p in PR]), np.vstack([p['weights'] for p in PR])
offs = np.cumsum([0] + [len(p['positions']) for p in PR]); tri = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(PR, offs)])
sk = [i for i, n in enumerate(jn) if n.startswith('Skirt_')]
sw = (np.isin(J, sk) * W).sum(1); sv = sw > 0.01
face = np.where(sv[tri].all(1))[0]; T = tri[face]
E = np.unique(np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1), axis=0)
rest = allpos(m.world({}))
top = rest[sv, 1].max()
d = rest[E[:, 1]] - rest[E[:, 0]]; L0 = np.linalg.norm(d, axis=1)
vert = np.abs(d[:, 1]) > np.linalg.norm(d[:, [0, 2]], axis=1)
UPPER = 0.10
up = vert & ((top - np.minimum(rest[E[:, 0], 1], rest[E[:, 1], 1])) < UPPER)
def area(x): return np.linalg.norm(np.cross(x[T[:, 1]] - x[T[:, 0]], x[T[:, 2]] - x[T[:, 0]]), axis=1)
A0 = area(rest)
# creases: dihedral angle between neighbouring skirt faces, posed minus rest (a fold that catches the light as a white crescent)
from collections import defaultdict
ef = defaultdict(list)
for fi, t_ in enumerate(T):
    for a_, b_ in ((t_[0], t_[1]), (t_[1], t_[2]), (t_[2], t_[0])): ef[(min(a_, b_), max(a_, b_))].append(fi)
FP = np.array([v for v in ef.values() if len(v) == 2])
def fnorm(x):
    n = np.cross(x[T[:, 1]] - x[T[:, 0]], x[T[:, 2]] - x[T[:, 0]]); return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
def dihed(x):
    n = fnorm(x); return np.degrees(np.arccos(np.clip((n[FP[:, 0]] * n[FP[:, 1]]).sum(1), -1, 1)))
D0 = dihed(rest)
print(f'skirt verts {sv.sum()} faces {len(face)} upper vertical edges {up.sum()}  top y {top:.3f}')
for clip in [a['name'] for a in m.glb.json['animations']]:
    if want and clip not in want: continue
    dur = m.clip_times(clip)[-1]; Ts = np.arange(0, dur + 1e-6, 1 / 30)
    worst = (9, 0); sq = 0; sqf = 0; fw = 0; cr = (0.0, 0)
    for ti, t in enumerate(Ts):
        x = allpos(m.world(m.sample(clip, float(t))))
        r = np.linalg.norm(x[E[:, 1]] - x[E[:, 0]], axis=1) / L0
        mn = float(np.percentile(r[up], 2)); n = int((r[up] < 0.6).sum())
        if mn < worst[0]: worst = (mn, ti)
        sq = max(sq, n)
        a = area(x) / np.maximum(A0, 1e-12); nf = int((a < 0.5).sum())
        if nf > sqf: sqf, fw = nf, ti
        dc = float(np.percentile(dihed(x) - D0, 99.5))
        if dc > cr[0]: cr = (dc, ti)
    print(f'{clip:14s} upper vertical edge p2 {worst[0]:.2f} (frame {worst[1]})  edges<0.6: {sq:3d}  faces<50%: {sqf:3d} (frame {fw})  crease p99.5 +{cr[0]:4.1f} deg (frame {cr[1]})', flush=True)
