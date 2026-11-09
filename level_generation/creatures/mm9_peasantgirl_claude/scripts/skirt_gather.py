#!/usr/bin/env python3
"""Corpse skirt (PeasantGirl): our A-line skirt flares to a 0.4 m hem; in MM9's Death the chains keep their flare, so on the lying body the
hem stood round the feet as a crumpled flower (MM9's own skirt is a straight tube). In Death (ramped in over FROM..1 of the clip) and Dead,
each chain's first link turns toward the body axis by K x its rest flare angle (the chain's top-to-hem direction against the pelvis down
axis), so the skirt lies as a tube round the legs. Args: <in glb> <out glb> [K] [FROM]"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
from rig_bones import SKIRT_CHAINS
IN, OUT = sys.argv[1:3]; KF = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0; FROM = float(sys.argv[4]) if len(sys.argv) > 4 else 0.35
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
m = Model(Glb(IN)); jn = [names[j] for j in m.joints]; B = {n: np.linalg.inv(m.inverse_binds[i]) for i, n in enumerate(jn)}
pel = B['Bip01 Pelvis']; down = -pel[:3, :3] @ np.array([0, 1.0, 0]) if False else np.array([0, -1.0, 0])
D = {}
for ch in SKIRT_CHAINS:
    top, end = ch[1], ch[-1]
    d = B[end][:3, 3] - B[top][:3, 3]; d /= np.linalg.norm(d)
    ang = np.arccos(np.clip(d @ down, -1, 1)); ax = np.cross(d, down)
    if np.linalg.norm(ax) < 1e-6: continue
    ax /= np.linalg.norm(ax); th = ang * KF
    Kx = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]]); Rw = np.eye(3) + np.sin(th) * Kx + (1 - np.cos(th)) * Kx @ Kx
    R0 = B[top][:3, :3]; D[top] = R0.T @ Rw @ R0
    print('GATHER', top, round(float(np.degrees(ang)), 1), 'deg')
for an in g.animations:
    if an.name not in ('Death', 'Dead'): continue
    for c in an.channels:
        n = names[c.target.node]
        if n not in D or c.target.path != 'rotation': continue
        s = an.samplers[c.sampler]; ta = g.accessors[s.input]; tv = g.bufferViews[ta.bufferView]
        ts = np.frombuffer(bytes(blob[(tv.byteOffset or 0) + (ta.byteOffset or 0):(tv.byteOffset or 0) + (ta.byteOffset or 0) + 4 * ta.count]), 'f4')
        x = g.accessors[s.output]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
        Q = np.frombuffer(blob, 'f4', x.count * 4, o).reshape(x.count, 4).copy().astype(float)
        T = ts[-1] if ts[-1] > 0 else 1
        for k, t in enumerate(ts):
            w = 1.0 if an.name == 'Dead' else float(np.clip((t / T - FROM) / (0.9 - FROM), 0, 1)); w = w * w * (3 - 2 * w)
            if w <= 0: continue
            Dk = D[n]; a = np.arccos(np.clip((np.trace(Dk) - 1) / 2, -1, 1))
            if a < 1e-6: continue
            axl = np.array([Dk[2, 1] - Dk[1, 2], Dk[0, 2] - Dk[2, 0], Dk[1, 0] - Dk[0, 1]]) / (2 * np.sin(a)); th = a * w
            Kx = np.array([[0, -axl[2], axl[1]], [axl[2], 0, -axl[0]], [-axl[1], axl[0], 0]]); Dw = np.eye(3) + np.sin(th) * Kx + (1 - np.cos(th)) * Kx @ Kx
            Q[k] = matrix_quaternion(quaternion_matrix(Q[k]) @ Dw)
        for k in range(1, len(Q)):
            if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
        blob[o:o + Q.size * 4] = Q.astype('f4').tobytes()
g.set_binary_blob(bytes(blob)); g.save(OUT); print('SKIRT gather', len(D), 'chains')
