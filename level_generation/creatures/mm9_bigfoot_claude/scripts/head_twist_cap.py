#!/usr/bin/env python3
"""Head twist soft cap (run 2 follow-up, 2026-10-31): MM9 turns the Bigfoot's head 85-100 deg about the neck against Spine3
(WalkFidget looks behind, Hit2, AttackMelee2), and this head joint sits 5 cm above the clavicles with no neck bone, so the
jaw rim and the neck side fold into the shoulder (collapse gate head 44). Per rotation key of Bip01 Head: the change from
rest is split into swing and twist about the neck axis (Spine3 -> Head at rest, in the head's rest frame); the twist goes
through a soft cap (unchanged below A, then A + (B - A) * tanh((x - A) / (B - A)), never above B) and the swing is kept.
The map is smooth and never speeds a key up, so it cannot add jitter. Run before half_keys.py (Head_h follows).
Args: <in glb> <out glb> [A deg] [B deg]"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
IN, OUT = sys.argv[1:3]
A = np.radians(float(sys.argv[3]) if len(sys.argv) > 3 else 50.0); Bc = np.radians(float(sys.argv[4]) if len(sys.argv) > 4 else 75.0)


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
            d = qmul(qinv(qrest), q)                              # change from rest, in the head's rest frame
            if d[3] < 0: d = -d
            p = (d[:3] @ axis) * axis                             # twist part
            tw = np.r_[p, d[3]]; tw /= max(np.linalg.norm(tw), 1e-12)
            sw = qmul(d, qinv(tw))
            ang = 2 * np.arctan2(np.linalg.norm(tw[:3]) * np.sign(tw[:3] @ axis), tw[3])
            worst = max(worst, abs(np.degrees(ang)))
            na = cap(ang)
            if abs(na - ang) < 1e-7: continue
            tw2 = np.r_[axis * np.sin(na / 2), np.cos(na / 2)]
            Q[k] = qmul(qrest, qmul(sw, tw2))
        for k in range(1, len(Q)):
            if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
        sm.output = put(Q)
        print(f'{an.name:12s} head twist max {worst:5.1f} deg -> {np.degrees(abs(cap(np.radians(worst)))):5.1f}')
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
