#!/usr/bin/env python3
"""Head rotation soft cap (colloidal warrior, from mm9_bigfoot_claude/head_twist_cap.py): MM9 throws this neckless head 48-69 deg
(Fidget, AttackMelee, Hit2, Death2) and the throat rolls fold. Per rotation key of Bip01 Head, the whole change from rest
(swing and twist together, axis kept) goes through the soft cap: unchanged below A, then A + (B - A) * tanh((x - A) / (B - A)),
never above B. Smooth and never faster than the source, so it adds no jitter. Run before half_keys.py.
Args: <in glb> <out glb> [A deg] [B deg] [clips, comma list; default all]
"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT = sys.argv[1:3]
A = np.radians(float(sys.argv[3]) if len(sys.argv) > 3 else 35.0); Bc = np.radians(float(sys.argv[4]) if len(sys.argv) > 4 else 50.0)
ONLY = sys.argv[5].split(',') if len(sys.argv) > 5 else None


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
def qinv(q):
    return q * np.array([-1, -1, -1, 1])


m = Model(Glb(Path(IN))); names = [n.get('name') for n in m.glb.json['nodes']]
h, s3 = names.index('Bip01 Head'), names.index('Bip01 Spine3')
w0 = m.world({}); Rh = w0[h][:3, :3] / np.linalg.norm(w0[h][:3, :3], axis=0)
axis = Rh.T @ (w0[h][:3, 3] - w0[s3][:3, 3]); axis /= np.linalg.norm(axis)       # neck axis in the head's rest frame
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
qrest = np.array(g.nodes[h].rotation or [0, 0, 0, 1], float)


def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    return np.frombuffer(bytes(blob), 'f4', a.count * 4, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, 4).astype(float)
def put(arr):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = np.asarray(arr, 'f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type='VEC4'))
    return len(g.accessors) - 1


def cap(x):
    s = np.sign(x); x = abs(x)
    return s * (x if x <= A else A + (Bc - A) * np.tanh((x - A) / (Bc - A)))


for an in g.animations:
    for ch in an.channels:
        if ch.target.node != h or ch.target.path != 'rotation': continue
        sm = an.samplers[ch.sampler]; Q = acc(sm.output); worst = 0.0
        for k, q in enumerate(Q):
            if ONLY and an.name not in ONLY: break
            d = qmul(qinv(qrest), q)                              # change from rest, in the head's rest frame
            if d[3] < 0: d = -d
            sn = np.linalg.norm(d[:3]); ang = 2 * np.arctan2(sn, d[3])
            worst = max(worst, np.degrees(ang))
            na = cap(ang)
            if abs(na - ang) < 1e-7 or sn < 1e-9: continue
            ax = d[:3] / sn
            Q[k] = qmul(qrest, np.r_[ax * np.sin(na / 2), np.cos(na / 2)])
        for k in range(1, len(Q)):
            if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
        sm.output = put(Q)
        print(f'{an.name:12s} head rotation max {worst:5.1f} deg -> {np.degrees(abs(cap(np.radians(worst)))):5.1f}')
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
