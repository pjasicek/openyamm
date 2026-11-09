#!/usr/bin/env python3
"""Igrid's lower legs follow the robe in the fall (review r9: the shoes came out under the robe in Death / Dead, robe gate 7.8 cm; MM9 has
no legs under the robe, its Die3 swings the calves where its robe does not go). In the listed clips each Calf's world rotation is turned by
the least rotation that takes its calf -> foot direction onto the same-side front robe chain's lower link (xfr_rt_a1 -> a2 for +x, xfr_rt1 ->
xfr_rt2 for -x), weighted by a smoothstep over T0..T1 seconds (Dead: full). Positions, other joints and other clips unchanged.
Args: <in glb> <out glb> <clip:t0:t1> ...   (raw ABC frame, before mirror_glb.py)"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
IN, OUT = sys.argv[1:3]
m = Model(Glb(IN)); g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
def least(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b; s = np.linalg.norm(v)
    if s < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K * ((1 - c) / s ** 2)
def rot_pow(R, w):
    q = matrix_quaternion(R); q = q / np.linalg.norm(q)
    if q[3] < 0: q = -q
    ang = 2 * np.arccos(np.clip(q[3], -1, 1)); ax = q[:3] / max(np.linalg.norm(q[:3]), 1e-12); a = ang * w
    return quaternion_matrix(np.r_[ax * np.sin(a / 2), np.cos(a / 2)])[:3, :3]
def ss(x, a, b):
    t = np.clip((x - a) / max(b - a, 1e-6), 0, 1); return t * t * (3 - 2 * t)
SIDES = (('FHP R Calf', 'FHP R Foot', 'xfr_rt_a1', 'xfr_rt_a2'), ('FHP L Calf', 'FHP L Foot', 'xfr_rt1', 'xfr_rt2'))
for spec in sys.argv[3:]:
    clip, t0, t1 = spec.split(':'); t0, t1 = float(t0), float(t1)
    an = next(a for a in g.animations if a.name == clip)
    for calf, foot, c1, c2 in SIDES:
        ci, fi = names.index(calf), names.index(foot); i1, i2 = names.index(c1), names.index(c2); par = m.parent[ci]
        ch = next((c for c in an.channels if c.target.node == ci and c.target.path == 'rotation'), None)
        if ch is None: print('no calf rotation channel', clip, calf); continue
        smp = an.samplers[ch.sampler]; T = m.glb.accessor(smp.input)[:, 0]
        x = g.accessors[smp.output]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
        Q = np.frombuffer(blob, 'f4', x.count * 4, o).reshape(x.count, 4).astype(float).copy(); worst = 0
        for k, t in enumerate(T):
            W = m.world(m.sample(clip, float(t)))
            dc = W[fi][:3, 3] - W[ci][:3, 3]; dt = W[i2][:3, 3] - W[i1][:3, 3]
            w = 1.0 if t1 <= 0 else ss(t, t0, t1)
            Ra = rot_pow(least(dc, dt), w)
            Rw = Ra @ W[ci][:3, :3]; Rl = W[par][:3, :3].T @ Rw
            Q[k] = matrix_quaternion(Rl) / np.linalg.norm(matrix_quaternion(Rl))
            worst = max(worst, np.degrees(np.arccos(np.clip(dc @ dt / np.linalg.norm(dc) / np.linalg.norm(dt), -1, 1))) * w)
        for k in range(1, len(Q)):
            if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
        blob[o:o + Q.size * 4] = Q.astype('f4').tobytes()
        print('LEGSFOLLOW', clip, calf, 'keys', len(T), 'max turn deg', round(float(worst), 1))
g.set_binary_blob(bytes(blob)); g.save(OUT)
