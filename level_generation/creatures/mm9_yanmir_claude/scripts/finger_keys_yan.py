#!/usr/bin/env python3
"""Hold the right fist round the staff in every clip (mm9_highwayman_claude/finger_keys.py, Yanmir): the right finger bones take the
grip of work/hand_poses.json (fist_yan.py) as constant keys; the right hand's constant wrist turn (`hand_offset`, the knuckles lined
up with the shaft) goes on every R Hand rotation key, and comes back out of Ystaff's keys (rotation and translation), so the staff
keeps MM9's own world frame (clips_mm9.py keys every joint in every clip, so node rests stay the bind). Ystaff's rest translation already carries the shift onto the fist's hole (fist_yan.py). The left
hand keeps MM9's curl (clips_mm9.py finger_alias). Args: <in glb> <out glb> <poses json>"""
import json, sys
import numpy as np
from pygltflib import GLTF2
IN, OUT, POSES = sys.argv[1:4]
g = GLTF2().load(IN); poses = json.load(open(POSES))
blob = bytearray(g.binary_blob())
idx = {n.name: i for i, n in enumerate(g.nodes)}


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def qrot(q, v):
    x, y, z, w = q
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    return v @ R.T


def acc_read(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()


def overwrite(i, arr):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    blob[off:off + arr.size * 4] = arr.astype('f4').tobytes()


off = np.array(poses['hand_offset']['Bip01 R Hand'], float)
inv = off * np.array([-1, -1, -1, 1])
done = set()
for an in g.animations:
    for ch in an.channels:
        n = g.nodes[ch.target.node].name; sm = an.samplers[ch.sampler]
        key = (sm.output, ch.target.path)
        if key in done: continue           # a shared accessor is changed once
        done.add(key)
        if n == 'Bip01 R Hand' and ch.target.path == 'rotation':
            overwrite(sm.output, np.array([qmul(v, off) for v in acc_read(sm.output)]))
        elif n == 'Ystaff' and ch.target.path == 'rotation':
            overwrite(sm.output, np.array([qmul(inv, v) for v in acc_read(sm.output)]))
        elif n == 'Ystaff' and ch.target.path == 'translation':
            overwrite(sm.output, qrot(inv, acc_read(sm.output)))
        elif ch.target.path == 'rotation' and n in poses['grip']:
            t = acc_read(sm.input)[:, 0]
            rest = np.array(g.nodes[idx[n]].rotation or [0, 0, 0, 1], float)
            overwrite(sm.output, np.tile(qmul(rest, np.array(poses['grip'][n])), (len(t), 1)))
g.set_binary_blob(bytes(blob)); g.save(OUT)
print('FINGERKEYS', OUT, 'channels', len(done))
