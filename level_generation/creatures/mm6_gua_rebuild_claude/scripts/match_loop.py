#!/usr/bin/env python3
"""Seat a hold loop between two accepted clips (2026-10-31, dropped clips: CowerLoop between CowerStart and CowerEnd).
Every channel of LOOP keeps its own motion relative to its first key, re-based on the pose half way between the last
key of BEFORE and the first key of AFTER: rotation q'(t) = q_target * q(0)^-1 * q(t), translation T'(t) = T_target +
T(t) - T(0). One constant offset per channel, so it adds no jitter and the loop seam stays as it was. The corrections
made on the accepted clips (hand pushes, skirt keys, floor) then carry over at both joins.
Usage: match_loop.py <in glb> <out glb> LOOP BEFORE AFTER"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, slerp  # noqa: E402


def qmul(a, b):
    x1, y1, z1, w1 = a
    x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def qinv(q):
    return q * np.array([-1, -1, -1, 1.0])


src, dst, loop, before, after = sys.argv[1:6]
glb = Glb(Path(src))
model = Model(glb)
end_before = model.sample(before, model.clip_times(before)[-1])
start_after = model.sample(after, 0.0)
animation = next(a for a in glb.json['animations'] if a['name'] == loop)
worst = [0.0, 0.0]
for channel in animation['channels']:
    node, path = channel['target']['node'], channel['target']['path']
    if path not in ('rotation', 'translation'):
        continue
    sampler = animation['samplers'][channel['sampler']]
    values = np.array(glb.accessor(sampler['output']), float)
    slot = 1 if path == 'rotation' else 0
    a = end_before.get(node, model.rest[node])[slot]
    b = start_after.get(node, model.rest[node])[slot]
    if path == 'rotation':
        target = slerp(a, b, 0.5)
        target = target / np.linalg.norm(target)
        base = qinv(values[0] / np.linalg.norm(values[0]))
        out = np.array([qmul(target, qmul(base, q / np.linalg.norm(q))) for q in values])
        for k in range(1, len(out)):
            if np.dot(out[k], out[k - 1]) < 0:
                out[k] = -out[k]
        angle = np.degrees(2 * np.arccos(min(1.0, abs(float(np.dot(target, values[0] / np.linalg.norm(values[0])))))))
        worst[0] = max(worst[0], angle)
    else:
        target = 0.5 * (a + b)
        out = target[None] + values - values[0][None]
        worst[1] = max(worst[1], float(np.linalg.norm(target - values[0])))
    sampler['output'] = glb.append_accessor(out.astype(np.float32), 'VEC4' if path == 'rotation' else 'VEC3')
glb.write(Path(dst))
print(f'MATCHED {loop} between {before} and {after}: largest offset {worst[0]:.1f} deg, {worst[1] * 100:.2f} cm')
