#!/usr/bin/env python3
"""A constant small abduction of an upper arm in every clip (MM9's stand hangs one hand where our wider hips are): same local offset on every key, in the clavicle's MM9 frame, so nothing new moves. Args: <in> <out> <side:deg> ... (raw ABC sides: R at +x)"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT = sys.argv[1:3]
src = Model(Glb(HERE / 'source/mm9/pf2a.glb')); sn = [n.get('name') for n in src.glb.json['nodes']]; w0 = src.world({})
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
for spec in sys.argv[3:]:
    s, deg = spec.split(':'); sign = 1 if s == 'R' else -1; a = np.radians(float(deg)) * sign
    idx = names.index(f'FHP {s} UpperArm'); Rc = w0[sn.index(f'FHP {s} Clavicle')][:3, :3]
    ax = Rc.T @ np.array([0, 0, 1.0]); q = np.r_[ax * np.sin(a / 2), np.cos(a / 2)]
    n = 0
    for an in g.animations:
        for c in an.channels:
            if c.target.node == idx and c.target.path == 'rotation':
                x = g.accessors[an.samplers[c.sampler].output]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
                Q = np.frombuffer(blob, 'f4', x.count * 4, o).reshape(x.count, 4).copy()
                Qn = qmul(np.tile(q, (len(Q), 1)), Q)
                blob[o:o + Qn.size * 4] = Qn.astype('f4').tobytes(); n += 1
    print('ARMOUT', s, deg, n)
g.set_binary_blob(bytes(blob)); g.save(OUT)
