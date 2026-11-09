#!/usr/bin/env python3
"""Hold the hand poses in every clip: the 15 finger bones per side carry the fists (work/hand_poses.json, finish_hw.py): right round the sword, left round the dagger; in AttackRanged the left opens at the release. Args: <in glb> <out glb> <poses json> [release seconds]"""
import json, sys
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView
IN, OUT, POSES = sys.argv[1:4]
REL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
g = GLTF2().load(IN); poses = json.load(open(POSES))
blob = bytearray(g.binary_blob())
idx = {n.name: i for i, n in enumerate(g.nodes)}


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def acc_read(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()


def overwrite(i, arr):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    blob[off:off + arr.size * 4] = arr.astype('f4').tobytes()


def slerp(a, b, t):
    if a @ b < 0: b = -b
    q = a * (1 - t) + b * t
    return q / np.linalg.norm(q)


for an in g.animations:
    times = None
    for ch in an.channels:
        n = g.nodes[ch.target.node].name
        if ch.target.path != 'rotation': continue
        off = poses.get('hand_offset', {}).get(n)
        if off is not None:                                      # constant wrist turn: the clip's rotation times the offset, in the bone's frame
            sm = an.samplers[ch.sampler]
            vals = acc_read(sm.output)
            overwrite(sm.output, np.array([qmul(v, np.array(off)) for v in vals]))
            continue
        grip, rel, thr = poses['grip'].get(n), poses['relaxed'].get(n), [0.0, 0.0, 0.0, 1.0] if ' L ' in n else None
        p = grip or rel
        if p is None: continue
        sm = an.samplers[ch.sampler]
        t = acc_read(sm.input)[:, 0]
        rest = np.array(g.nodes[idx[n]].rotation, float)
        q = qmul(rest, np.array(p))
        vals = np.tile(q, (len(t), 1))
        if an.name == 'AttackRanged' and thr is not None:
            qt = qmul(rest, np.array(thr))
            for k, x in enumerate(t):
                c = np.clip((x - REL) / 0.06, 0, 1) * np.clip((0.88 - x) / 0.1, 0, 1)        # the left hand opens at the throw, closes on the dagger again at the end
                c = c * c * (3 - 2 * c)
                vals[k] = slerp(q, qt, c)
        overwrite(sm.output, vals)
g.set_binary_blob(bytes(blob)); g.save(OUT)
print('finger keys', OUT)
