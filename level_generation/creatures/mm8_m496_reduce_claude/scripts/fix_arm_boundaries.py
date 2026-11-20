#!/usr/bin/env python3
"""Ease the Fire Elemental's arm pose into and out of Fidget and Hit (user: fix pops before review, 2026-10-19).
Cause: in ../mm8_m496_claude's composed clips the first and last keys of LeftArm and RightArm are the Standing pose,
but from the second key on (and up to the second-to-last) both arms sit 5.2 deg (Fidget) / 6.2 and 5.3 deg (Hit)
away from it, so the hands, and most of all the fingertips, jump in a single 30 Hz key (viewer frames 1-2 and
114-115 of Fidget, 1-2 and 35 of Hit; the finger channels themselves are constant). Each key k of those four channels
becomes slerp(Standing, original_k, w), with w a smoothstep from the clip start over N_IN keys and to the clip end
over N_OUT keys: the boundary keys stay the Standing pose (loop and Standing transition unchanged) and the interior
keys beyond the ramps are unchanged. Hit's start is a fast reaction (the arms swing 17 deg in five keys), so ramp
weights squeezed it into a 5.7 deg step; there keys 0..N_IN instead ease from Standing to key N_IN's pose
(smoothstep over seven keys, where the swing peaks; at most 3.8 deg per key, no velocity spike; the source had a
6.2 deg key then 2.5).
Values are written in place into the channels' own accessors (none shared), so every other channel, clip, mesh and
image stays byte for byte.
A re-export of ../mm8_m496_claude brings the pops back unless this is run again on that export.
Usage: fix_arm_boundaries.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes  # noqa: E402
RAMPS = {'Fidget': (8, 8, 'ramp'), 'Hit': (7, 5, 'reach')}   # keys easing in / out (30 Hz keys), start mode
BONES = ('LeftArm', 'RightArm')
doc, binary = read_glb(Path(sys.argv[1])); binary = bytearray(binary)


def channel(clip, bone):
    an = next(a for a in doc['animations'] if a['name'] == clip)
    ch = next(c for c in an['channels'] if doc['nodes'][c['target']['node']]['name'] == bone
              and c['target']['path'] == 'rotation')
    return an['samplers'][ch['sampler']]


def slerp(a, b, t):
    if np.dot(a, b) < 0:
        b = -b
    d = np.clip(np.dot(a, b), -1, 1); th = np.arccos(d)
    if th < 1e-6:
        return a
    return (np.sin((1 - t) * th) * a + np.sin(t * th) * b) / np.sin(th)


smooth = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))
for clip, (n_in, n_out, mode) in RAMPS.items():
    for bone in BONES:
        stand = np.frombuffer(accessor_bytes(doc, binary, channel('Standing', bone)['output']), np.float32)[:4].copy()
        s = channel(clip, bone); acc = doc['accessors'][s['output']]; bv = doc['bufferViews'][acc['bufferView']]
        q = np.frombuffer(accessor_bytes(doc, binary, s['output']), np.float32).reshape(-1, 4).astype(np.float64)
        k = np.arange(len(q)); last = len(q) - 1
        st = stand.astype(np.float64)
        if mode == 'reach':
            w = smooth((last - k) / n_out)
            new = np.array([slerp(st, q[n_in], smooth(i / n_in)) if i <= n_in else slerp(st, q[i], w[i]) for i in k])
        else:
            w = np.minimum(smooth(k / n_in), smooth((last - k) / n_out))
            new = np.array([slerp(st, q[i], w[i]) for i in k])
        new /= np.linalg.norm(new, axis=1, keepdims=True)
        new[np.sum(new * q, 1) < 0] *= -1                                 # keep each key's hemisphere
        off = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
        assert bv.get('byteStride', 16) == 16 and acc['componentType'] == 5126
        binary[off:off + 16 * len(q)] = new.astype(np.float32).tobytes()
        ang = lambda a, b: np.degrees(2 * np.arccos(np.clip(np.abs((a * b).sum(-1)), 0, 1)))
        print('EASED', clip, bone, 'keys', len(q), 'max step before', round(float(ang(q[1:], q[:-1]).max()), 2),
              'after', round(float(ang(new[1:], new[:-1]).max()), 2), 'deg; boundary = Standing',
              round(float(ang(new[0], stand)), 4), round(float(ang(new[-1], stand)), 4))
write_glb(Path(sys.argv[2]), doc, bytes(binary)); print('WROTE', sys.argv[2])
