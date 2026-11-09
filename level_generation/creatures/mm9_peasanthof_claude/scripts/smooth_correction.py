#!/usr/bin/env python3
"""Spread an arm correction over time (peasanthom1, 2026-11-01). arm_clear.py turns the upper arm per key; on Fidget's
scratching hand (it sinks into the other sleeve) the turn rose within a few keys and failed the jitter gate (upper arm
1.5 deg/f, shoulder skin 12 mm/f2 over MM9) whatever its --sigma. Here the correction of each joint, as a local
rotation delta D = corrected * raw^-1 per key, is taken as a rotation vector, held by a running maximum of its
magnitude over +/- HOLD seconds (the direction of the largest one nearby) and low-passed (Gaussian SIGMA s), then
applied to the raw clip: out = D_smooth * raw. Every other channel and clip is copied from the corrected GLB.
Usage: smooth_correction.py <raw glb> <corrected glb> <out glb> --clip Fidget --joint "Bip01 L UpperArm" [--hold 0.25]
       [--sigma 0.12] [--gain 1.0]"""
import argparse
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from pygltflib import GLTF2
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clips_mm9 import read, qmul, qnorm, quat_continuous

ap = argparse.ArgumentParser()
ap.add_argument('raw'); ap.add_argument('cor'); ap.add_argument('out')
ap.add_argument('--clip', action='append', required=True)
ap.add_argument('--joint', action='append', required=True)
ap.add_argument('--hold', type=float, default=0.25)
ap.add_argument('--sigma', type=float, default=0.12)
ap.add_argument('--gain', type=float, default=1.0)
o = ap.parse_args()


def channel(g, clip, joint):
    names = [n.name for n in g.nodes]
    a = next(a for a in g.animations if a.name == clip)
    for c in a.channels:
        if names[c.target.node] == joint and c.target.path == 'rotation':
            s = a.samplers[c.sampler]
            return read(g, s.input)[:, 0], read(g, s.output), s.output


def rotvec(q):
    q = np.where(q[:, 3:4] < 0, -q, q)
    ang = 2 * np.arccos(np.clip(q[:, 3], -1, 1))
    s = np.sin(ang / 2)
    ax = np.where(s[:, None] > 1e-8, q[:, :3] / np.maximum(s, 1e-8)[:, None], 0)
    return ax * ang[:, None]


def from_rotvec(r):
    ang = np.linalg.norm(r, axis=1)
    ax = np.where(ang[:, None] > 1e-9, r / np.maximum(ang, 1e-9)[:, None], 0)
    return np.concatenate([ax * np.sin(ang / 2)[:, None], np.cos(ang / 2)[:, None]], 1)


raw = GLTF2().load(o.raw)
cor = GLTF2().load(o.cor)
blob = bytearray(cor.binary_blob())
for clip in o.clip:
    for joint in o.joint:
        t, qr, _ = channel(raw, clip, joint)
        t2, qc, acc_i = channel(cor, clip, joint)
        assert len(t) == len(t2)
        qr, qc = quat_continuous(qr), quat_continuous(qc)
        inv = qr * np.array([-1, -1, -1, 1])
        D = qnorm(qmul(qc, inv))
        r = rotvec(D) * o.gain
        mag = np.linalg.norm(r, axis=1)
        dt = float(np.median(np.diff(t)))
        w = max(1, int(round(o.hold / dt)))
        held = maximum_filter1d(mag, 2 * w + 1, mode='nearest')
        # direction: the rotation vector of the largest correction within the window
        idx = np.array([max(range(max(0, i - w), min(len(mag), i + w + 1)), key=lambda k: mag[k]) for i in range(len(mag))])
        dirs = np.where(mag[idx, None] > 1e-9, r[idx] / np.maximum(mag[idx], 1e-9)[:, None], 0)
        rs = gaussian_filter1d(dirs * held[:, None], o.sigma / dt, axis=0, mode='nearest')
        rs[0] = rs[0] * 0 if mag[0] < 1e-6 else rs[0]
        out = qnorm(qmul(from_rotvec(rs), qr))
        acc = cor.accessors[acc_i]; bv = cor.bufferViews[acc.bufferView]
        off = (bv.byteOffset or 0) + (acc.byteOffset or 0)
        blob[off:off + out.nbytes // 2] = out.astype(np.float32).tobytes()
        print('SMOOTHCORR', clip, joint, 'max deg', round(float(np.degrees(mag.max())), 1), '->',
              round(float(np.degrees(np.linalg.norm(rs, axis=1).max())), 1))
cor.set_binary_blob(bytes(blob))
cor.save(o.out)
