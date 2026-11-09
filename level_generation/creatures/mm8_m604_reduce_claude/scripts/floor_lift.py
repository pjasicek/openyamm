#!/usr/bin/env python3
"""Lift the pelvis (its parent Rig has an identity transform, so world up = translation Y) by the measured floor
dip of the Attack wind-up (floor_measure.py): lift = lowest point below -0.5 mm, dilated by 2 keys and smoothed
(sigma 0.02 s), never below the raw need; zero outside the dip, so other frames are untouched.
Usage: floor_lift.py <in.glb> <floor json> <out.glb> [clip]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from retime_attack import view  # noqa: E402
src, floor, dst = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]); clip = sys.argv[4] if len(sys.argv) > 4 else 'Attack'
doc, binary = read_glb(src); binary = bytearray(binary)
anim = next(a for a in doc['animations'] if a['name'] == clip)
ch = next(c for c in anim['channels'] if doc['nodes'][c['target']['node']]['name'] == 'B_Pelvis' and c['target']['path'] == 'translation')
s = anim['samplers'][ch['sampler']]
_, times = view(doc, binary, s['input']); times = times[:, 0]; off, vals = view(doc, binary, s['output'])
F = np.array(json.load(open(floor))); need = np.interp(times, F[:, 0], np.maximum(0, -F[:, 1] - 0.0005), right=0)
need[times > F[-1, 0]] = 0
dil = np.array([need[max(0, i - 2):i + 3].max() for i in range(len(need))])
dt = float(np.median(np.diff(times))); k = np.arange(-int(.08 / dt), int(.08 / dt) + 1); g = np.exp(-.5 * (k * dt / .02) ** 2); g /= g.sum()
lift = np.maximum(need, np.convolve(np.pad(dil, len(k) // 2, mode='edge'), g, 'valid'))
vals[:, 1] += lift.astype(np.float32)
binary[off:off + vals.nbytes] = vals.tobytes()
write_glb(dst, doc, bytes(binary)); print('LIFT max', round(float(lift.max()) * 1000, 1), 'mm over', int((lift > 1e-5).sum()), 'keys')
