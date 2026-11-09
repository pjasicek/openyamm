#!/usr/bin/env python3
"""Key the right fist round the glaive into every clip (after mm9_guard_claude/scripts/finger_keys.py).

work/hand_poses.json (grip_solve_kr.py): 'grip' = bone-local finger rotations from rest (the right hand's 15 MPFB finger
bones, constant: MM9's right mitten never opens on the glaive), 'hand_offset' = a constant turn of the right hand in its own
frame (the knuckle line onto the shaft), 'child_inverse' = the same turn undone on Xspear (a child of the hand), so the glaive
stays exactly where MM9's keys put it: hand' = hand * D, Xspear' = D^-1 * Xspear (rotation and translation).
Usage: grip_keys.py <in glb> <out glb> <poses json>"""
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
    p = np.r_[v, 0.0]
    return qmul(qmul(q, p), q * np.array([-1, -1, -1, 1.0]))[:3]


def acc_read(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()


def overwrite(i, arr):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    blob[off:off + arr.size * 4] = arr.astype('f4').tobytes()


hand_off = {k: np.array(v) for k, v in poses.get('hand_offset', {}).items()}
child_inv = {k: np.array(v) for k, v in poses.get('child_inverse', {}).items()}
done = {}
for an in g.animations:
    seen = set()
    for ch in an.channels:
        n = g.nodes[ch.target.node].name
        sm = an.samplers[ch.sampler]
        key = (sm.output, ch.target.path)
        if key in seen:
            continue
        seen.add(key)
        if ch.target.path == 'rotation':
            if n in hand_off:
                overwrite(sm.output, np.array([qmul(v, hand_off[n]) for v in acc_read(sm.output)]))
            elif n in child_inv:
                overwrite(sm.output, np.array([qmul(child_inv[n], v) for v in acc_read(sm.output)]))
            elif n in poses['grip']:
                t = acc_read(sm.input)[:, 0]
                rest = np.array(g.nodes[idx[n]].rotation or [0, 0, 0, 1], float)
                overwrite(sm.output, np.tile(qmul(rest, np.array(poses['grip'][n])), (len(t), 1)))
            else:
                continue
        elif ch.target.path == 'translation' and n in child_inv:
            overwrite(sm.output, np.array([qrot(child_inv[n], v) for v in acc_read(sm.output)]))
        else:
            continue
        done[n] = done.get(n, 0) + 1
missing = [n for n in list(hand_off) + list(child_inv) if n not in done]
if missing:
    raise SystemExit(f'grip_keys: no channel for {missing}')
g.set_binary_blob(bytes(blob)); g.save(OUT)
print('GRIPKEYS', OUT, {k: v for k, v in done.items() if not k.startswith('Bip01 R ') or 'Hand' in k}, 'fingers', sum(1 for k in done if k.startswith('Bip01 R ') and 'Hand' not in k))
