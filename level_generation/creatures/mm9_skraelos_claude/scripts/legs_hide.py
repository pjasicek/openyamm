#!/usr/bin/env python3
"""Igrid's lower legs shrink into the robe once she is down (review r9: robe gate Death / Dead 7.8 cm: the shoes came out under the robe
as it lifts in the fall; MM9 has no legs under its robe at all, and turning the calves onto the robe chains, legs_follow.py, still left
2.5-7.9 cm). In the listed clips a scale channel on both Calf joints (the knee, inside the robe) goes from 1 to S between T0 and T1 seconds
(smoothstep, 8 keys) and holds; the shin and shoe shrink toward the knee and stay inside the robe. Other channels unchanged.
Optional fifth field K (r12: in Death the shrunken legs still sat 4.5-6 cm outside the robe at 0.3-0.46 s, the Calf joints themselves out
of the lifted robe; wyrd_old has no thighs, the Calves hang from the Pelvis): the Calves' translation (keyed or rest) is also pulled toward
the Pelvis by K with the same easing.
Args: <in glb> <out glb> <clip:t0:t1:s[:k]> ..."""
import sys
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
IN, OUT = sys.argv[1:3]
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
def add(arr, typ):
    while len(blob) % 4: blob.append(0)
    o = len(blob); b = arr.astype('f4').tobytes(); blob.extend(b)
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(b)))
    a = Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ)
    if typ == 'SCALAR': a.min = [float(arr.min())]; a.max = [float(arr.max())]
    g.accessors.append(a); return len(g.accessors) - 1
for spec in sys.argv[3:]:
    f = spec.split(':'); clip, t0, t1, sc = f[0], float(f[1]), float(f[2]), float(f[3]); K = float(f[4]) if len(f) > 4 else 0.0
    an = next(a for a in g.animations if a.name == clip)
    if t1 <= t0: T = np.array([0.0, max(t0, 0.001)]); S = np.array([sc, sc])
    else:
        T = np.r_[0.0, np.linspace(t0, t1, 8)] if t0 > 0 else np.linspace(t0, t1, 8)
        u = np.clip((T - t0) / (t1 - t0), 0, 1); u = u * u * (3 - 2 * u); S = 1 + (sc - 1) * u
    for calf in ('FHP R Calf', 'FHP L Calf'):
        ni = names.index(calf)
        an.channels = [c for c in an.channels if not (c.target.node == ni and c.target.path == 'scale')]
        ia = add(T.reshape(-1, 1)[:, 0], 'SCALAR'); oa = add(np.repeat(S[:, None], 3, 1), 'VEC3')
        an.samplers.append(AnimationSampler(input=ia, output=oa, interpolation='LINEAR'))
        an.channels.append(AnimationChannel(sampler=len(an.samplers) - 1, target=AnimationChannelTarget(node=ni, path='scale')))
        if K > 0:
            ch = next((c for c in an.channels if c.target.node == ni and c.target.path == 'translation'), None)
            if ch is not None:
                sm = an.samplers[ch.sampler]; x = g.accessors[sm.input]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
                TT = np.frombuffer(bytes(blob[o:o + x.count * 4]), 'f4').astype(float)
                y = g.accessors[sm.output]; v = g.bufferViews[y.bufferView]; o = (v.byteOffset or 0) + (y.byteOffset or 0)
                V = np.frombuffer(bytes(blob[o:o + y.count * 12]), 'f4').reshape(-1, 3).astype(float)
            else:
                TT = np.array([0.0]); V = np.array([g.nodes[ni].translation or [0, 0, 0]], float)
            TK = np.unique(np.r_[TT, T].astype('f4')).astype(float); TK = TK[np.r_[True, np.diff(TK) > 1e-4]]; VK = np.stack([np.interp(TK, TT, V[:, i]) for i in range(3)], 1)
            if t1 <= t0: uk = np.ones(len(TK))
            else: uk = np.clip((TK - t0) / (t1 - t0), 0, 1); uk = uk * uk * (3 - 2 * uk)
            VK = VK * (1 - K * uk)[:, None]
            an.channels = [c for c in an.channels if not (c.target.node == ni and c.target.path == 'translation')]
            ia = add(TK, 'SCALAR'); oa = add(VK, 'VEC3')
            an.samplers.append(AnimationSampler(input=ia, output=oa, interpolation='LINEAR'))
            an.channels.append(AnimationChannel(sampler=len(an.samplers) - 1, target=AnimationChannelTarget(node=ni, path='translation')))
    print('LEGSHIDE', clip, t0, t1, sc, 'pull', K)
while len(blob) % 4: blob.append(0)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
