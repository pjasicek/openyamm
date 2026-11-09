#!/usr/bin/env python3
"""Blend one clip between two GLBs of the same skeleton and keys with a sin^2 window over the clip: A at the first
and last key, B in the middle (2026-10-31, CowerLoop: the hand push of hand_rest.py faded in and out, so the loop
still meets the accepted CowerStart and CowerEnd poses at both ends). Rotations slerp, translations lerp, per key.
Usage: blend_window.py <A glb> <B glb> <out glb> CLIP [power]   (window = sin(pi t / T) ** power, default 2)"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, slerp  # noqa: E402

path_a, path_b, out, clip = sys.argv[1:5]
power = float(sys.argv[5]) if len(sys.argv) > 5 else 2.0
a, b = Glb(Path(path_a)), Glb(Path(path_b))
anim_a = next(x for x in a.json['animations'] if x['name'] == clip)
anim_b = next(x for x in b.json['animations'] if x['name'] == clip)
channels_b = {(c['target']['node'], c['target']['path']): anim_b['samplers'][c['sampler']] for c in anim_b['channels']}
changed = 0
for channel in anim_a['channels']:
    key = (channel['target']['node'], channel['target']['path'])
    if key[1] not in ('rotation', 'translation') or key not in channels_b:
        continue
    sa, sb = anim_a['samplers'][channel['sampler']], channels_b[key]
    ta, tb = a.accessor(sa['input'])[:, 0], b.accessor(sb['input'])[:, 0]
    va, vb = np.array(a.accessor(sa['output']), float), np.array(b.accessor(sb['output']), float)
    if len(ta) != len(tb) or np.abs(ta - tb).max() > 1e-5:
        sys.exit(f'{clip}: keys differ on node {key[0]}')
    if np.abs(va - vb).max() < 1e-7:
        continue
    w = np.sin(np.pi * (ta - ta[0]) / max(ta[-1] - ta[0], 1e-9)) ** power
    if key[1] == 'rotation':
        res = np.array([slerp(x, y, float(k)) for x, y, k in zip(va, vb, w)])
        for i in range(1, len(res)):
            if np.dot(res[i], res[i - 1]) < 0:
                res[i] = -res[i]
    else:
        res = va + (vb - va) * w[:, None]
    sa['output'] = a.append_accessor(res.astype(np.float32), 'VEC4' if key[1] == 'rotation' else 'VEC3')
    changed += 1
a.write(Path(out))
print(f'BLENDED {clip}: {changed} channels, window sin^{power:g}')
