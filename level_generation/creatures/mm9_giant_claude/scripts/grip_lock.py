#!/usr/bin/env python3
"""The mallet's shaft held on the fist's hole in every key: MM9's handle axis wanders up to 2.1 cm off its grip in Fidget2 and Taunt
(the mitten never closes on it). Per key of Xbase (child of the right hand), the shaft is shifted across its own axis, in the
hand's frame, so the axis runs through the grip point of the Standing pose; sliding along the axis and spinning about it stay MM9's.
Args: <in glb> <out glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]
m = Model(Glb(IN)); d = m.glb.json; names = [n.get('name') for n in d['nodes']]
iH, iX, iB = names.index('Bip01 R Hand'), names.index('Xhammer'), names.index('Xbase')
def line(w):
    R = np.linalg.inv(w[iH]) @ w[iX]; return R[:3, 3], R[:3, 1] / np.linalg.norm(R[:3, 1])
p0, a0 = line(m.world(m.sample('Standing', 0.0))); G = p0 + a0 * ((-p0) @ a0)
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()
def put(i, arr):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    blob[off:off + arr.size * 4] = arr.astype('f4').tobytes()
worst = {}; slid = {}
import os
SMIN = float(os.environ.get('GRIP_SMIN', '0.85'))
for an in g.animations:
    ct = next((c for c in an.channels if c.target.node == iB and c.target.path == 'translation'), None)
    if ct is None: continue
    sm = an.samplers[ct.sampler]; ts = acc(sm.input)[:, 0]; T = acc(sm.output)
    # the hand frame is Xbase's parent frame: a shift there adds to Xbase's translation directly
    for k, t in enumerate(ts):
        p, a = line(m.world(m.sample(an.name, float(t))))
        v = G - p; perp = v - a * (v @ a)
        sl = SMIN - (v @ a)                                       # third pass: the fist slides no further than SMIN up the shaft (its end stays out of the chest)
        T[k] = T[k] + perp - a * max(sl, 0.0)
        slid[an.name] = max(slid.get(an.name, 0), max(sl, 0.0))
        worst[an.name] = max(worst.get(an.name, 0), float(np.linalg.norm(perp)))
    put(sm.output, T)
g.set_binary_blob(bytes(blob)); g.save(OUT)
print('GRIPLOCK cm', {k: round(v * 100, 2) for k, v in worst.items() if v > 0.001}, 'slide clamped cm', {k: round(v * 100, 1) for k, v in slid.items() if v > 0.001})
