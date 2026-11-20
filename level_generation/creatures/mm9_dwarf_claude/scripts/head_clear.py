#!/usr/bin/env python3
"""Helmet rim out of the shoulders and chest (run 2). The dwarf has no neck: when MM9's clip tips or turns the head far, the helmet's rim and
cheek guards sink into the shoulders and the collar (rim_gate.py: up to 8 cm). Per clip key: the least fraction f (steps of STEP, at most FMAX)
of the head's turn away from its rest relative to the neck, taken back, that keeps the helmet within TOL of the torso's outer surface. The fractions
are held (maximum filter) and smoothed (Gaussian) on the clip's own keys, circular on loops, so the correction is one smooth curve, never per frame.
Bip01 Head_h (half-joint helper) is rewritten from the new head key. Args: <in glb> <out glb> [clips]"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
HERE = Path(__file__).resolve().parents[1]
IN, OUT = sys.argv[1:3]
os.environ['RIM_GLB'] = IN
sys.path.insert(0, str(HERE / 'scripts'))
import rim_gate as R                                     # helmet vertices, torso outer faces, depth()
from pygltflib import GLTF2, Accessor, BufferView
want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
STEP, FMAX, TOL = 0.1, float(os.environ.get('HEAD_FMAX', 0.6)), float(os.environ.get('HEAD_TOL', 0.008))
HOLD, SIGMA = 0.1, 0.06
LOOPS = ('Standing', 'Walking', 'Running')
m = R.m; names = R.names; ix = {n: i for i, n in enumerate(names)}
HD, HH = ix['Bip01 Head'], ix['Bip01 Head_h']


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def qpow(q, k):
    q = q if q[3] >= 0 else -q
    ang = 2 * np.arccos(np.clip(q[3], -1, 1)); s = np.sin(ang / 2)
    ax = q[:3] / s if s > 1e-8 else np.zeros(3)
    return np.r_[ax * np.sin(ang * k / 2), np.cos(ang * k / 2)]


qr = np.array(m.glb.json['nodes'][HD].get('rotation', [0, 0, 0, 1]), float); qri = qr * [-1, -1, -1, 1]


def take_back(q, f):
    """q with a fraction f of its turn from rest removed (about the same axis)"""
    return qmul(qr, qpow(qmul(qri, q), 1 - f))


def helm_depth(loc):
    X = np.concatenate([x for x, _ in m.skinned_positions(m.world(loc))[:len(R.P)]])
    return float(R.depth(X[R.helm], X).max())


g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC4': 4, 'VEC3': 3}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(np.float64)
def put(arr):
    global blob
    while len(blob) % 4: blob.append(0)
    o_ = len(blob); d = np.asarray(arr, 'f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o_, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type='VEC4'))
    return len(g.accessors) - 1


rep = {}
for an in g.animations:
    clip = an.name
    if want and clip not in want: continue
    ch = {c.target.node: c for c in an.channels if c.target.path == 'rotation'}
    if HD not in ch: continue
    sm = an.samplers[ch[HD].sampler]; ts = acc(sm.input)[:, 0]; Q = acc(sm.output).copy()
    F = np.zeros(len(ts)); before = 0.0
    for k, t in enumerate(ts):
        loc = m.sample(clip, float(t)); d0 = helm_depth(loc); before = max(before, d0)
        f = 0.0
        while d0 > TOL and f < FMAX - 1e-6:
            f += STEP; l2 = dict(loc); tr = l2[HD]; l2[HD] = [tr[0], take_back(Q[k], f), tr[2]]
            d0 = helm_depth(l2)
        F[k] = f
    if not F.any():
        rep[clip] = dict(before_cm=round(before * 100, 1), max_f=0.0); print(clip, rep[clip], flush=True); continue
    dt = (ts[-1] - ts[0]) / max(1, len(ts) - 1); mode = 'wrap' if clip in LOOPS else 'nearest'
    sz = max(1, int(round(2 * HOLD / dt)) | 1)
    F = np.clip(gaussian_filter1d(maximum_filter1d(F, sz, mode=mode), SIGMA / dt, mode=mode), 0, FMAX)
    if clip not in LOOPS:                                    # MM9's own pose at the first and last key
        e = np.clip((ts - ts[0]) / 0.12, 0, 1) * np.clip((ts[-1] - ts) / 0.12, 0, 1); F *= e * e * (3 - 2 * e)
    Qn = np.array([take_back(Q[k], F[k]) for k in range(len(ts))])
    for k in range(1, len(Qn)):
        if Qn[k] @ Qn[k - 1] < 0: Qn[k] = -Qn[k]
    sm.output = put(Qn)
    if HH in ch:                                             # the half-joint helper: half the head's turn from rest (half_keys.py)
        sh = an.samplers[ch[HH].sampler]; th = acc(sh.input)[:, 0]
        Qi = np.array([Qn[min(np.searchsorted(ts, t), len(ts) - 1)] for t in th])
        Hh = np.array([qmul(qr, qpow(qmul(qri, q), 0.5)) for q in Qi])
        for k in range(1, len(Hh)):
            if Hh[k] @ Hh[k - 1] < 0: Hh[k] = -Hh[k]
        sh.output = put(Hh)
    after = 0.0
    g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob))
    rep[clip] = dict(before_cm=round(before * 100, 1), max_f=round(float(F.max()), 2))
    print(clip, rep[clip], flush=True)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
json.dump(rep, open(HERE / 'work' / 'head_clear.json', 'w'), indent=1)
print('HEAD clear', OUT)
