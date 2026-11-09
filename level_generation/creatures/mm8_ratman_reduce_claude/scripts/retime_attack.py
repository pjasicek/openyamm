#!/usr/bin/env python3
"""Spread the Ratman's sword slash over the whole Attack clip (user review 4: "first 40 frames is just angling of the
right hand, then abrupt swing ... should be blended like the leg/hip movement ... so the swing itself isnt only 20
frames").

The production Attack (1Hand/SwordAttackR1 with a 0.833 s lead-in) holds the body still for 40 frames (48 fps) while
only the arms move from the guard to the slash's start; then the left foot steps and the pelvis drops in 3 frames,
the wind-up takes 8 and the strike 2.4 (frames 51.2-53.6, impact 53.6). Here the slash (source 40..78.4) is played on
a monotone time warp through WARP (new frame -> source frame): the step and the over-the-shoulder wind-up (source
40-44.4) take frames 0-32, the held top (44.4-50) frames 32-44 and the strike (50-53.6) about 10 frames. The impact
frame (1.116667 s, actors.yml) and the clip length stay the same, so the impact pose and the sword's direction there
are unchanged. The arms, which differ between the guard and the slash's start, carry the difference as an offset
that fades out over the first BLEND frames (per joint, in the parent frame), so channels that already match (pelvis,
legs) play the source step unchanged and stay planted. All channels are resampled at RATE.
Usage: retime_attack.py <in.glb> <out.glb>"""
import math
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

FPS, RATE = 48.0, 60.0
WARP = [(0, 40), (32, 44.4), (44, 50.0), (53.6, 53.6), (62, 60), (78.4, 78.4)]
BLEND = 24.0
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src); binary = bytearray(binary)
NC = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}


def read(i):
    a = doc['accessors'][i]
    return np.frombuffer(accessor_bytes(doc, binary, i), np.float32).reshape(a['count'], NC[a['type']]).astype(np.float64)


def sample(ts, vs, t, rot):
    k = int(np.clip(np.searchsorted(ts, t, side='right') - 1, 0, len(ts) - 1))
    if k >= len(ts) - 1:
        return vs[-1].copy()
    return mix(vs[k], vs[k + 1], (t - ts[k]) / (ts[k + 1] - ts[k]), rot)


def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])


def mix(a, b, f, rot):
    if not rot:
        return a * (1 - f) + b * f
    if a @ b < 0:
        b = -b
    th = math.acos(min(1.0, a @ b))
    return a if th < 1e-6 else (math.sin((1 - f) * th) * a + math.sin(f * th) * b) / math.sin(th)


a = next(x for x in doc['animations'] if x['name'] == 'Attack')
warp = PchipInterpolator(*zip(*WARP))
length = WARP[-1][0] / FPS
T = np.linspace(0, length, int(round(length * RATE)) + 1)
U = warp(T * FPS) / FPS
s = np.clip(T * FPS / BLEND, 0, 1); blend = s * s * (3 - 2 * s)
times = append_accessor(doc, binary, dict(doc['accessors'][a['samplers'][0]['input']], count=len(T), min=[0.0],
                                          max=[float(T[-1])]), T.astype(np.float32).tobytes())
assert abs(read(a['samplers'][0]['input'])[-1, 0] - length) < 1e-4
source, a['samplers'] = a['samplers'], []   # the exporter shares samplers between channels; each gets its own
for c in a['channels']:
    sm = dict(source[c['sampler']])
    ts, vs = read(sm['input'])[:, 0], read(sm['output']); rot = c['target']['path'] == 'rotation'
    start = sample(ts, vs, U[0], rot)
    if rot:   # guard = offset * start, offset faded from 1 to the identity
        off = qmul(vs[0], start * np.array([-1, -1, -1, 1]))
        out = np.array([qmul(mix(np.array([0, 0, 0, 1.0]), off, 1 - b, True), sample(ts, vs, u, True)) for u, b in zip(U, blend)])
    else:
        out = np.array([sample(ts, vs, u, False) + (1 - b) * (vs[0] - start) for u, b in zip(U, blend)])
    if rot:
        for k in range(1, len(out)):
            if out[k] @ out[k - 1] < 0:
                out[k] = -out[k]
    sm['input'] = times; sm['interpolation'] = 'LINEAR'
    sm['output'] = append_accessor(doc, binary, dict(doc['accessors'][sm['output']], count=len(out)),
                                   out.astype(np.float32).tobytes())
    a['samplers'].append(sm); c['sampler'] = len(a['samplers']) - 1
print('RETIME Attack', len(T), 'keys; source frame at', ', '.join(f'{t:g}->{warp(t):.1f}' for t in (0, 16, 32, 40, 44, 50, 53.6, 62)))
write_glb(dst, doc, bytes(binary))
