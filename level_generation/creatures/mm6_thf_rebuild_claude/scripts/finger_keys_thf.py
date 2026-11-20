#!/usr/bin/env python3
"""Hands and daggers per clip (MM6 thief: the native thief stands empty-handed and draws both daggers in the attack). The 15 finger bones per side
keep their relaxed MPFB rest in every clip but the dagger clips, where they close on the grips (work/hand_poses.json, finish_thf.py) over
the first EASE_IN s and open over the last EASE_OUT s; the wrist turn that lines the knuckles up with MM9's weapon axis (`hand_offset`) blends in
with the grip. The daggers (rigid on Ybasesword / Ybasedagger) show only while the fist is closed (scale 0.001 otherwise). AttackRanged:
the true left throws (MM9's Rattack1 release, RELEASE s): the left dagger is drawn at the hip at DRAW s, gone at the release, the left
hand opens there. Args: <in glb> <out glb> <poses json>"""
import json, sys
import numpy as np
from pygltflib import GLTF2
IN, OUT, POSES = sys.argv[1:4]
DAGGER_CLIPS = ('Attack', 'Attack2', 'AttackRanged')
EASE_IN, EASE_OUT, RELEASE, DRAW = 0.12, 0.16, 0.5 / 1.2, 0.23 / 1.2       # Rattack1 at rate 1.2 (the native attack's 0.75 s)
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


def sstep(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def grip_weight(clip, t, dur, side):
    if clip not in DAGGER_CLIPS: return np.zeros_like(t)
    c = sstep(t / EASE_IN) * sstep((dur - t) / EASE_OUT)
    if clip == 'AttackRanged' and side == 'L':
        c = np.where(t < RELEASE, c, c * sstep(1 - (t - RELEASE) / 0.06))     # opens at the release and stays open
    return c


def acc_new(arr, typ):
    from pygltflib import Accessor, BufferView
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.astype('f4').tobytes(); blob.extend(d)
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    a = Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ)
    if typ == 'SCALAR': a.min = [float(arr.min())]; a.max = [float(arr.max())]
    g.accessors.append(a)
    return len(g.accessors) - 1


from pygltflib import AnimationSampler, AnimationChannel, AnimationChannelTarget
for an in g.animations:
    dur = 0.0
    for sm in an.samplers:
        dur = max(dur, float(acc_read(sm.input)[:, 0].max()))
    for ch in an.channels:
        n = g.nodes[ch.target.node].name
        if ch.target.path != 'rotation': continue
        side = 'L' if ' L ' in n else 'R'
        off = poses.get('hand_offset', {}).get(n)
        sm = an.samplers[ch.sampler]
        t = acc_read(sm.input)[:, 0]
        if off is not None:                              # wrist turn, blended with the grip
            c = grip_weight(an.name, t, dur, side)
            vals = acc_read(sm.output)
            overwrite(sm.output, np.array([qmul(v, slerp(np.array([0, 0, 0, 1.0]), np.array(off), w)) for v, w in zip(vals, c)]))
            continue
        grip = poses['grip'].get(n)
        if grip is None: continue
        rest = np.array(g.nodes[idx[n]].rotation, float)
        qg = qmul(rest, np.array(grip))
        c = grip_weight(an.name, t, dur, side)
        overwrite(sm.output, np.array([slerp(rest, qg, w) for w in c]))
    # dagger visibility (step keys)
    for bone, side in (('Ybasesword', 'R'), ('Ybasedagger', 'L')):
        ni = idx[bone]
        an.channels = [c for c in an.channels if not (c.target.node == ni and c.target.path == 'scale')]
        tt = np.linspace(0, dur, max(2, int(round(dur * 60)) + 1))
        c = grip_weight(an.name, tt, dur, side)
        vis = c > 0.5
        if an.name == 'AttackRanged' and side == 'L':
            vis = vis & (tt >= DRAW) & (tt < RELEASE)
        S = np.where(vis, 1.0, 0.001).astype(np.float32)[:, None].repeat(3, 1)
        ia = acc_new(tt.astype(np.float32), 'SCALAR'); oa = acc_new(S, 'VEC3')
        an.samplers.append(AnimationSampler(input=ia, output=oa, interpolation='STEP'))
        an.channels.append(AnimationChannel(sampler=len(an.samplers) - 1, target=AnimationChannelTarget(node=ni, path='scale')))
g.buffers[0].byteLength = len(blob)
g.set_binary_blob(bytes(blob)); g.save(OUT)
print('FINGERS keyed', OUT)
