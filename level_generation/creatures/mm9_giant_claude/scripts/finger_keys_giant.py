#!/usr/bin/env python3
"""Finger keys on the clip GLB (after clips_mm9.py, before half_keys.py). Right hand: the fist round the handle (work/hand_poses.json
`grip`, fist_giant.py) held in every clip, and the constant wrist turn (`hand_offset`) that lines the knuckles up with MM9's axis.
Left hand: flexion about its own knuckle line (`flexL`), the amount per frame from MM9's left finger joints carried in the clip
(Finger1 -> proximal, Finger11 -> middle, Finger12 -> distal, angle from rest), so the hand opens and closes on MM9's timing;
MM9's own rotation axes do not match the grafted fingers (they bend sideways). Thumbs: right in the grip, left at rest.
Args: <in glb> <out glb> <poses json>"""
import json, sys
import numpy as np
from pygltflib import GLTF2
IN, OUT, POSES = sys.argv[1:4]
g = GLTF2().load(IN); poses = json.load(open(POSES))
blob = bytearray(g.binary_blob())
idx = {n.name: i for i, n in enumerate(g.nodes)}
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).copy()
def put(i, arr):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; off = (bv.byteOffset or 0) + (a.byteOffset or 0)
    blob[off:off + arr.size * 4] = arr.astype('f4').tobytes()
def rot(ax, a):
    ax = np.asarray(ax, float); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
def m2q(R):
    t = np.trace(R)
    if t > 0:
        s = np.sqrt(t + 1) * 2; return np.array([(R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, s / 4])
    i = int(np.argmax(np.diag(R))); j, k = (i + 1) % 3, (i + 2) % 3
    s = np.sqrt(1 + R[i, i] - R[j, j] - R[k, k]) * 2; q = np.zeros(4)
    q[i] = s / 4; q[j] = (R[j, i] + R[i, j]) / s; q[k] = (R[k, i] + R[i, k]) / s; q[3] = (R[k, j] - R[j, k]) / s
    return q
FL = poses['flexL']; AXL = np.array(FL['AX']); SG = FL['sg']; RB = {k: np.array(v) for k, v in FL['Rb'].items()}
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
KF = {'Index': (0.9, 0.85, 0.7), 'Middle': (1.0, 0.9, 0.75), 'Ring': (1.0, 0.95, 0.8), 'Pinky': (1.05, 1.0, 0.85)}
def rest_q(n): return np.array(g.nodes[idx[n]].rotation or [0, 0, 0, 1], float)
def ang_from_rest(vals, n):
    r = rest_q(n); ri = r * np.array([-1, -1, -1, 1])
    d = np.array([qmul(ri, v) for v in vals]); return 2 * np.arccos(np.clip(np.abs(d[:, 3]), -1, 1))
for an in g.animations:
    ch = {(g.nodes[c.target.node].name, c.target.path): c for c in an.channels}
    def series(n):
        c = ch.get((n, 'rotation'))
        if c is None: return None, None
        sm = an.samplers[c.sampler]; return acc(sm.input)[:, 0], acc(sm.output)
    th = {}
    for k in ('Finger1', 'Finger11', 'Finger12'):
        t, v = series(f'Bip01 L {k}')
        th[k] = (t, ang_from_rest(v, f'Bip01 L {k}')) if t is not None else None
    for (n, path), c in ch.items():
        if path != 'rotation': continue
        sm = an.samplers[c.sampler]
        if n == 'Xbase' and poses.get('hand_offset'):
            # the wrist turn taken back out of the mallet's chain: the mallet keeps MM9's motion relative to MM9's hand
            o_ = np.array(list(poses['hand_offset'].values())[0]); oi = o_ * np.array([-1, -1, -1, 1])
            put(sm.output, np.array([qmul(oi, v) for v in acc(sm.output)]))
            ct = ch.get((n, 'translation'))
            if ct is not None:
                st = an.samplers[ct.sampler]; Rm = np.array([[1 - 2 * (oi[1] ** 2 + oi[2] ** 2), 2 * (oi[0] * oi[1] - oi[2] * oi[3]), 2 * (oi[0] * oi[2] + oi[1] * oi[3])],
                                                                 [2 * (oi[0] * oi[1] + oi[2] * oi[3]), 1 - 2 * (oi[0] ** 2 + oi[2] ** 2), 2 * (oi[1] * oi[2] - oi[0] * oi[3])],
                                                                 [2 * (oi[0] * oi[2] - oi[1] * oi[3]), 2 * (oi[1] * oi[2] + oi[0] * oi[3]), 1 - 2 * (oi[0] ** 2 + oi[1] ** 2)]])
                put(st.output, acc(st.output) @ Rm.T)
            continue
        off = poses.get('hand_offset', {}).get(n)
        if off is not None:
            put(sm.output, np.array([qmul(v, np.array(off)) for v in acc(sm.output)])); continue
        p = poses['grip'].get(n)
        if p is not None:
            vals = acc(sm.output); put(sm.output, np.tile(qmul(rest_q(n), np.array(p)), (len(vals), 1))); continue
        if n.startswith('Bip01 L ') and 'Thumb' in n:
            vals = acc(sm.output); put(sm.output, np.tile(rest_q(n), (len(vals), 1))); continue
        f = next((x for x in FINGERS if n.startswith(f'Bip01 L {x}')), None)
        if f is None: continue
        seg = int(n[-1]) - 1
        t = acc(sm.input)[:, 0]
        a = [np.interp(t, *th[k]) if th[k] is not None else np.zeros(len(t)) for k in ('Finger1', 'Finger11', 'Finger12')]
        k1, k2, k3 = KF[f]
        a1, a2, a3 = k1 * a[0], k2 * a[1], k3 * a[2]
        cum = [a1, a1 + a2, a1 + a2 + a3]
        out = []
        for i in range(len(t)):
            D = rot(AXL, SG * cum[seg][i]); prev = rot(AXL, SG * cum[seg - 1][i]) if seg > 0 else np.eye(3)
            Rb = RB[n]; B = Rb.T @ prev.T @ D @ Rb
            out.append(qmul(rest_q(n), m2q(B)))
        put(sm.output, np.array(out))
g.set_binary_blob(bytes(blob)); g.save(OUT)
print('FINGERKEYS', len(g.animations), 'clips')
