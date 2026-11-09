#!/usr/bin/env python3
"""Low-pass the floor pass's per-key correction (brief: clip corrections never per frame). floor_fix.py lifts the root by
the depth of the lowest hoof at each key, which follows the hoof that happens to be lowest and adds a jitter MM9's clip
does not have (Walking 1.1 cm per frame). Per listed clip the correction d(t) = final root - root before the pass is
replaced by its upper envelope (a sliding maximum, so nothing sinks) smoothed by a Gaussian; Walking and Running wrap.
Death keeps its end value (the corpse) and its start.
Usage: smooth_floor.py <before floor pass glb> <after floor pass glb> <out glb> [clips json]
The optional clips json ({clip: [window, sigma, wrap]}, run2-clips-groupC 2026-10-31) replaces CLIPS, for added clips
smoothed like their accepted counterparts (AttackMelee2 as AttackMelee, Death2 as Death)."""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb

CLIPS = {'Walking': (0.12, 0.06, True), 'Running': (0.10, 0.05, True), 'AttackMelee': (0.08, 0.05, False),
         'Death': (0.12, 0.07, False)}
if len(sys.argv) > 4:
    import json
    CLIPS = {k: tuple(v) for k, v in json.loads(Path(sys.argv[4]).read_text()).items()}
a, b = Glb(sys.argv[1]), Glb(sys.argv[2])
anims = {x['name']: x for x in b.json['animations']}
anims0 = {x['name']: x for x in a.json['animations']}
for clip, (win, sig, wrap) in CLIPS.items():
    an, an0 = anims[clip], anims0[clip]
    ch0 = {(c['target']['node'], c['target']['path']): c for c in an0['channels']}
    for c in an['channels']:
        key = (c['target']['node'], c['target']['path'])
        if key[1] != 'translation':
            continue
        s = an['samplers'][c['sampler']]
        t = b.accessor(s['input'])[:, 0]
        v = b.accessor(s['output']).astype(np.float64)
        if key in ch0:
            s0 = an0['samplers'][ch0[key]['sampler']]
            t0 = a.accessor(s0['input'])[:, 0]
            o0 = a.accessor(s0['output']).astype(np.float64)
            v0 = np.stack([np.interp(t, t0, o0[:, k]) for k in range(3)], 1)
        else:
            v0 = np.tile(np.array(a.json['nodes'][key[0]].get('translation', [0, 0, 0]), float), (len(t), 1))
        if np.abs(v - v0).max() < 1e-4:
            continue
        dt = float(np.median(np.diff(t)))
        d = v - v0
        ax = int(np.abs(d).max(0).argmax())
        env = ndimage.maximum_filter1d(d[:, ax], max(3, int(2 * win / dt) | 1), mode='wrap' if wrap else 'nearest')
        sm = ndimage.gaussian_filter1d(env, sig / dt, mode='wrap' if wrap else 'nearest')
        sm = np.maximum(sm, d[:, ax])  # never below the floor
        sm = ndimage.gaussian_filter1d(sm, 0.6 * sig / dt, mode='wrap' if wrap else 'nearest')
        if not wrap:
            m = min(len(sm), int(0.13 / dt))
            w0 = np.clip(np.arange(m) / max(m - 1, 1), 0, 1)
            w0 = w0 * w0 * (3 - 2 * w0)
            sm[:m] = d[0, ax] * (1 - w0) + sm[:m] * w0
            n = min(len(sm), int(0.2 / dt))
            w = np.clip(np.arange(n) / max(n - 1, 1), 0, 1)[::-1]
            sm[-n:] = sm[-n:] * w + d[-1, ax] * (1 - w)
        if wrap:
            sm[-1] = sm[0]
        nv = v.copy()
        nv[:, ax] = v0[:, ax] + sm
        s['output'] = b.append_accessor(nv.astype(np.float32), 'VEC3')
        print(clip, b.json['nodes'][key[0]].get('name'), 'axis', ax, 'before step %.4f after %.4f, range %.4f..%.4f' % (
            np.abs(np.diff(d[:, ax])).max(), np.abs(np.diff(sm)).max(), sm.min(), sm.max()))
b.write(sys.argv[3])
