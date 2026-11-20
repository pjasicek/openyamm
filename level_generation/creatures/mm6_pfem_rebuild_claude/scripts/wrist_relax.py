#!/usr/bin/env python3
"""Relaxed wrists: MM9's PeasantFemale idle bends both hands outward at the wrist (~25 deg, a stiff flare beside our wider skirt). Each
hand's local rotation keeps only a share K of its deviation from the bind (q = q0 * slerp(1, q0^-1 q, K)) on every key of every clip, so
the motion stays and transitions stay consistent. Args: <in glb> <out glb> [K]"""
import sys
import numpy as np
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]; K = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
def qpow(q, k):
    q = np.where(q[:, 3:4] < 0, -q, q); ang = 2 * np.arccos(np.clip(q[:, 3], -1, 1)); s = np.sqrt(np.maximum(1 - q[:, 3] ** 2, 0))
    ax = np.where(s[:, None] > 1e-9, q[:, :3] / np.maximum(s, 1e-9)[:, None], 0); a = ang * k
    return np.c_[ax * np.sin(a / 2)[:, None], np.cos(a / 2)]
n = 0
for s in 'LR':
    idx = names.index(f'FHP {s} Hand'); q0 = np.array(g.nodes[idx].rotation or [0, 0, 0, 1], float); q0i = q0 * [-1, -1, -1, 1]
    for an in g.animations:
        for c in an.channels:
            if c.target.node == idx and c.target.path == 'rotation':
                x = g.accessors[an.samplers[c.sampler].output]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
                Q = np.frombuffer(blob, 'f4', x.count * 4, o).reshape(x.count, 4).astype(float)
                d = qmul(np.tile(q0i, (len(Q), 1)), Q); Qn = qmul(np.tile(q0, (len(Q), 1)), qpow(d, K))
                blob[o:o + Qn.size * 4] = Qn.astype('f4').tobytes(); n += 1
g.set_binary_blob(bytes(blob)); g.save(OUT); print('WRIST relaxed', K, n, 'channels')
