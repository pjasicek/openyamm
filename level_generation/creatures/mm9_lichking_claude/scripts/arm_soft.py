#!/usr/bin/env python3
"""Second pass on arm_clear.py's correction: it ramps 3 deg per 48 fps frame to its cap (the jitter gate's fails). Here the correction (rotation of the upper arm in its parent's frame, raw -> arm_clear) is widened by a running maximum and a Gaussian
in seconds, soft-capped, and faded to zero at the clip's ends, then applied to the raw keys. Args: <raw glb> <arm_clear glb> <out glb> <cap deg> <sigma s> <clips>"""
import sys
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from pygltflib import GLTF2
LOOP = bool(int(__import__('os').environ.get('LOOP', '0'))); MODE = 'wrap' if LOOP else 'nearest'      # LICHKING: loops wrap, no end fade
RAW, CL, OUT = sys.argv[1:4]; CAP = np.radians(float(sys.argv[4])); SIG = float(sys.argv[5]); CLIPS = sys.argv[6].split(',')
a = GLTF2().load(RAW); b = GLTF2().load(CL)
ba = bytearray(a.binary_blob()); bb = b.binary_blob()
names = [n.name for n in a.nodes]
def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
def view(g, blob, i, n):
    x = g.accessors[i]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
    return np.frombuffer(blob, 'f4', x.count * n, o).reshape(x.count, n).copy(), o
for an, bn in zip(a.animations, b.animations):
    if an.name not in CLIPS: continue
    for s in 'LR':
        idx = names.index(f'Bip01 {s} UpperArm')
        ca = next(c for c in an.channels if c.target.node == idx and c.target.path == 'rotation'); cb = next(c for c in bn.channels if c.target.node == idx and c.target.path == 'rotation')
        ts, _ = view(a, ba, an.samplers[ca.sampler].input, 1); ts = ts[:, 0]
        Qa, oa = view(a, ba, an.samplers[ca.sampler].output, 4); Qb, _ = view(b, bb, bn.samplers[cb.sampler].output, 4)
        conj = Qa * [-1, -1, -1, 1]
        r = qmul(Qb.astype(float), conj.astype(float)); r[r[:, 3] < 0] *= -1
        ang = 2 * np.arccos(np.clip(r[:, 3], -1, 1)); ax = r[:, :3] / np.maximum(np.linalg.norm(r[:, :3], axis=1, keepdims=True), 1e-9); rv = ax * ang[:, None]
        dt = float(np.median(np.diff(ts))); w = max(int(round(0.14 / dt)) | 1, 3)
        for c in range(3):
            rv[:, c] = maximum_filter1d(np.maximum(rv[:, c], 0), w, mode=MODE) - maximum_filter1d(np.maximum(-rv[:, c], 0), w, mode=MODE)
        rv = gaussian_filter1d(rv, SIG / dt, axis=0, mode='wrap' if LOOP else 'constant')
        mag = np.linalg.norm(rv, axis=1); soft = CAP * np.tanh(mag / max(CAP, 1e-6)); rv = rv * (soft / np.maximum(mag, 1e-9))[:, None]
        T = ts[-1]; e = np.ones(len(ts)) if LOOP else np.clip(np.minimum(ts, T - ts) / float(__import__('os').environ.get('FADE', '0.30')), 0, 1); e = e * e * (3 - 2 * e); rv = rv * e[:, None]
        a2 = np.linalg.norm(rv, axis=1)
        q = np.c_[rv / np.maximum(a2, 1e-9)[:, None] * np.sin(a2 / 2)[:, None], np.cos(a2 / 2)]
        Qn = qmul(q, Qa.astype(float))
        ba[oa:oa + Qn.size * 4] = Qn.astype('f4').tobytes()
        print(an.name, s, 'peak deg', round(float(np.degrees(a2.max())), 1), 'max rate deg/s', round(float(np.degrees(np.abs(np.diff(a2)).max() / dt)), 0))
a.set_binary_blob(bytes(ba)); a.save(OUT)
