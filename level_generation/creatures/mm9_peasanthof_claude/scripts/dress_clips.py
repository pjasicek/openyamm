#!/usr/bin/env python3
"""HOF2's floor-length dress in motion (coordinator pre-screen of r6, 2026-11-04): the heel and calf came out through the back of the
dress in Walking, Running and Cower, the back of the skirt kicked out into a flat flap in Running, and the skirt flared open in Death.
Two edits on the clips (keys only, written into a copy):
1. DAMP <clip>=<d>: every skirt joint (XCOM_skirt and the x* hem chains) is slerped toward its Standing pose (first Standing key) by d
   at every key, so the hem keeps a skirt shape (Running flap, Death flare).
2. TUCK <clip>=<smin>: a scale channel on both Calf joints, per rotation key of that Calf: s = 1 - (1 - smin) * smoothstep(flex, A0, A1),
   flex = the Calf's angle away from its Standing pose (deg). A straight knee (the stance foot on the floor) keeps s = 1; a bent knee
   (the heel kicked back or tucked under) pulls the shin and shoe toward the knee, inside the dress (MM9's long dresses show no legs).
3. TUCK_THIGH <clip>=<smin>: the same on both Thigh joints (the whole leg toward the hip), driven by the larger of the knee flex and the
   thigh's angle away from its Standing pose: the running leg swung back carries the shoe out through the back of the dress even with
   the shin tucked; a straight leg under the body (stance) keeps s = 1.
Args: <in glb> <out glb> [--damp Running=0.5,...] [--tuck Walking=0.45,...] [--tuck-thigh Running=0.5,...] [--a0 12] [--a1 45]
      [--t0 15] [--t1 40]; a tuck-thigh value smin@t0:t1 sets that clip's thresholds (Running=0.3@0:1 = always)"""
import argparse
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
ap = argparse.ArgumentParser(); ap.add_argument('inp'); ap.add_argument('out')
ap.add_argument('--damp', default=''); ap.add_argument('--tuck', default='')
ap.add_argument('--tuck-thigh', default=''); ap.add_argument('--t0', type=float, default=15.0); ap.add_argument('--t1', type=float, default=40.0)
ap.add_argument('--a0', type=float, default=12.0); ap.add_argument('--a1', type=float, default=45.0)
o = ap.parse_args()
g = GLTF2().load(o.inp); blob = bytearray(g.binary_blob()); names = [n.name or '' for n in g.nodes]


def read(i):
    a = g.accessors[i]; v = g.bufferViews[a.bufferView]; c = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    off = (v.byteOffset or 0) + (a.byteOffset or 0)
    return np.frombuffer(bytes(blob[off:off + 4 * c * a.count]), 'f4').reshape(a.count, c).astype(float)


def add(arr, typ):
    while len(blob) % 4: blob.append(0)
    off = len(blob); b = np.ascontiguousarray(arr, 'f4').tobytes(); blob.extend(b)
    g.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=len(b)))
    a = Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ)
    if typ == 'SCALAR': a.min = [float(arr.min())]; a.max = [float(arr.max())]
    g.accessors.append(a); return len(g.accessors) - 1


def slerp(q0, q1, t):
    d = (q0 * q1).sum(-1, keepdims=True); q1 = np.where(d < 0, -q1, q1); d = np.abs(d)
    w = np.arccos(np.clip(d, -1, 1)); s = np.sin(w)
    a = np.where(s > 1e-6, np.sin((1 - t) * w) / np.maximum(s, 1e-9), 1 - t); b = np.where(s > 1e-6, np.sin(t * w) / np.maximum(s, 1e-9), t)
    q = a * q0 + b * q1; return q / np.linalg.norm(q, axis=-1, keepdims=True)


def chan(an, ni, path):
    return next((c for c in an.channels if c.target.node == ni and c.target.path == path), None)


stand = next(a for a in g.animations if a.name == 'Standing')
skirt = [i for i, n in enumerate(names) if n.startswith('XCOM') or (n.startswith('x') and len(n) > 1)]
calves = [names.index('Bip01 L Calf'), names.index('Bip01 R Calf')]
thighs = [names.index('Bip01 L Thigh'), names.index('Bip01 R Thigh')]


def stand_q(ni):
    c = chan(stand, ni, 'rotation')
    return read(stand.samplers[c.sampler].output)[0] if c else np.array(g.nodes[ni].rotation or [0, 0, 0, 1.0])


for spec in [s for s in o.damp.split(',') if s]:
    clip, d = spec.split('='); d = float(d); an = next(a for a in g.animations if a.name == clip); n = 0
    for ni in skirt:
        c = chan(an, ni, 'rotation')
        if c is None: continue
        sm = an.samplers[c.sampler]; Q = read(sm.output); R = np.repeat(stand_q(ni)[None], len(Q), 0)
        sm.output = add(slerp(Q, R, d), 'VEC4'); n += 1
    print('DRESSCLIPS damp', clip, d, 'joints', n)
for spec in [s for s in o.tuck.split(',') if s]:
    clip, smin = spec.split('='); smin = float(smin); an = next(a for a in g.animations if a.name == clip)
    for ni in calves:
        c = chan(an, ni, 'rotation'); sm = an.samplers[c.sampler]; T = read(sm.input)[:, 0]; Q = read(sm.output)
        r = stand_q(ni); flex = np.degrees(2 * np.arccos(np.clip(np.abs(Q @ r), 0, 1)))
        u = np.clip((flex - o.a0) / (o.a1 - o.a0), 0, 1); u = u * u * (3 - 2 * u); S = 1 - (1 - smin) * u
        an.channels = [ch for ch in an.channels if not (ch.target.node == ni and ch.target.path == 'scale')]
        an.samplers.append(AnimationSampler(input=add(T, 'SCALAR'), output=add(np.repeat(S[:, None], 3, 1), 'VEC3'), interpolation='LINEAR'))
        an.channels.append(AnimationChannel(sampler=len(an.samplers) - 1, target=AnimationChannelTarget(node=ni, path='scale')))
        print('DRESSCLIPS tuck', clip, names[ni], 'flex', round(float(flex.min())), '-', round(float(flex.max())), 'scale min', round(float(S.min()), 2))
for spec in [s for s in o.tuck_thigh.split(',') if s]:
    clip, smin = spec.split('='); t0, t1 = o.t0, o.t1
    if '@' in smin: smin, th = smin.split('@'); t0, t1 = (float(x) for x in th.split(':'))   # per-clip thresholds (Running=0.3@0:1)
    smin = float(smin); an = next(a for a in g.animations if a.name == clip)
    for ti, ci in zip(thighs, calves):
        ct = chan(an, ti, 'rotation'); cc = chan(an, ci, 'rotation')
        T = np.unique(np.r_[read(an.samplers[ct.sampler].input)[:, 0], read(an.samplers[cc.sampler].input)[:, 0]])
        def ang(c, ni):
            tt = read(an.samplers[c.sampler].input)[:, 0]; Q = read(an.samplers[c.sampler].output); r = stand_q(ni)
            a = np.degrees(2 * np.arccos(np.clip(np.abs(Q @ r), 0, 1))); return np.interp(T, tt, a)
        ut = np.clip((ang(ct, ti) - t0) / (t1 - t0), 0, 1); uc = np.clip((ang(cc, ci) - o.a0) / (o.a1 - o.a0), 0, 1)
        u = np.maximum(ut, uc); u = u * u * (3 - 2 * u); S = 1 - (1 - smin) * u
        an.channels = [ch for ch in an.channels if not (ch.target.node == ti and ch.target.path == 'scale')]
        an.samplers.append(AnimationSampler(input=add(T, 'SCALAR'), output=add(np.repeat(S[:, None], 3, 1), 'VEC3'), interpolation='LINEAR'))
        an.channels.append(AnimationChannel(sampler=len(an.samplers) - 1, target=AnimationChannelTarget(node=ti, path='scale')))
        print('DRESSCLIPS tuck-thigh', clip, names[ti], 'scale min', round(float(S.min()), 2))
while len(blob) % 4: blob.append(0)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(o.out)
