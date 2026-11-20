#!/usr/bin/env python3
"""A smooth extra upper-arm offset inside one clip (Igrid's Fidget: MM9's hands rest where our robe's front is): abduction ABD and forward
flexion FLEX degrees (world forward and lateral axes taken into the clavicle's MM9 frame, as arm_out.py), eased in between T0 and T1 s and
out between T2 and T3 s (smoothstep), so the clip still starts and ends on MM9's pose and the offset changes slowly (jitter gate).
Args: <in> <out> <clip:side:abd:flex:t0:t1:t2:t3> ...   (raw ABC sides: R at +x)"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT = sys.argv[1:3]
src = Model(Glb(HERE / 'source/mm9/wyrd_old/wyrd_old.glb')); sn = [n.get('name') for n in src.glb.json['nodes']]; w0 = src.world({})
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
def acc(i):
    x = g.accessors[i]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
    n = {'SCALAR': 1, 'VEC4': 4}[x.type]; return o, np.frombuffer(blob, 'f4', x.count * n, o).reshape(x.count, n).copy()
def ss(x, a, b):
    t = np.clip((x - a) / max(b - a, 1e-6), 0, 1); return t * t * (3 - 2 * t)
for spec in sys.argv[3:]:
    clip, s, abd, flex, t0, t1, t2, t3 = spec.split(':'); abd, flex, t0, t1, t2, t3 = map(float, (abd, flex, t0, t1, t2, t3))
    sign = 1 if s == 'R' else -1
    idx = names.index(f'FHP {s} UpperArm'); Rc = w0[sn.index(f'FHP {s} Clavicle')][:3, :3]
    an = next(a for a in g.animations if a.name == clip)
    for c in an.channels:
        if c.target.node == idx and c.target.path == 'rotation':
            smp = an.samplers[c.sampler]; _, T = acc(smp.input); o, Q = acc(smp.output); T = T[:, 0]
            w = ss(T, t0, t1) * (1 - ss(T, t2, t3))
            for axw, deg in ((np.array([0, 0, 1.0]), abd * sign), (np.array([1.0, 0, 0]), -flex)):
                ax = Rc.T @ axw; a = np.radians(deg) * w
                q = np.c_[ax[None] * np.sin(a / 2)[:, None], np.cos(a / 2)]
                Q = qmul(q, Q)
            blob[o:o + Q.size * 4] = Q.astype('f4').tobytes()
            print('ARMOUTCLIP', clip, s, abd, flex, 'keys', len(T))
g.set_binary_blob(bytes(blob)); g.save(OUT)
