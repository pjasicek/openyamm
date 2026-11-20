#!/usr/bin/env python3
"""Relaxed fingers: MM9's mitten bind is flat and our bind is open, so on MM9's near-zero finger curl the hand reads as a stiff spread claw. A constant small flexion on every finger joint, on all keys, about the axis MM9's own curl uses; nothing new moves.
Args: <in glb> <out glb>"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT = sys.argv[1:3]
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
m = Model(Glb(IN)); w0 = m.world({}); jn = [names[j] for j in m.joints]; ibm = {n: m.inverse_binds[i] for i, n in enumerate(jn)}
def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
AMT = {'Index': (10, 16, 10), 'Middle': (13, 18, 12), 'Ring': (16, 20, 14), 'Pinky': (19, 22, 15), 'Thumb': (0, 6, 8)}
J = {n: np.linalg.inv(ibm[n]) for n in jn}          # bind world
for s in 'LR':
    pre = f'FHP {s} '
    hand = J[pre + 'Hand'][:3, 3]; wrist_to = J[pre + 'Middle1'][:3, 3] - hand; side = J[pre + 'Index1'][:3, 3] - J[pre + 'Pinky1'][:3, 3]
    n = np.cross(wrist_to, side); n /= np.linalg.norm(n)
    # the palm side: the thumb tip side of the plane's normal does not tell; the MPFB hand was placed palm down, so the palm faces world -Y in the bind (glTF)
    if n[1] > 0: n = -n
    for f, deg in AMT.items():
        for k, d in zip((1, 2, 3), deg):
            b = f'{pre}{f}{k}'; c = f'{pre}{f}{k + 1}' if k < 3 else None
            B = J[b]; d_b = (J[c][:3, 3] - B[:3, 3]) if c else (B[:3, 3] - J[f'{pre}{f}{k - 1}'][:3, 3])
            ax_w = np.cross(d_b, n); ax_w /= np.linalg.norm(ax_w)       # world bind axis turning the bone toward the palm
            ax_l = B[:3, :3].T @ ax_w; a = np.radians(d)
            q = np.r_[ax_l * np.sin(a / 2), np.cos(a / 2)]
            idx = names.index(b)
            for an in g.animations:
                for c_ in an.channels:
                    if c_.target.node == idx and c_.target.path == 'rotation':
                        x = g.accessors[an.samplers[c_.sampler].output]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
                        Q = np.frombuffer(blob, 'f4', x.count * 4, o).reshape(x.count, 4).copy()
                        Qn = qmul(Q.astype(float), np.tile(q, (len(Q), 1)))
                        blob[o:o + Qn.size * 4] = Qn.astype('f4').tobytes()
g.set_binary_blob(bytes(blob)); g.save(OUT); print('FINGER rest')
