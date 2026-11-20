#!/usr/bin/env python3
"""A hand out of the head on keys, without jitter: arm_clear.py solves each key and its correction turns on and off in a frame or two (13 deg/frame in Fidget2, the jitter gate failed). Here the same correction is reduced to one rotation of the upper arm, its mean over the corrected keys, faded in and out with a smoothstep over EASE seconds.
Usage: arm_bump.py in.glb cleared.glb out.glb clip joint(alias name) [ease seconds]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
src, clr, dst, clip, joint = sys.argv[1:6]
EASE = float(sys.argv[6]) if len(sys.argv) > 6 else 0.4
a = Glb(src); b = Glb(clr)


def channel(g, clip, joint):
    doc = g.json
    nid = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == joint)
    an = next(x for x in doc['animations'] if x['name'] == clip)
    ch = next(c for c in an['channels'] if c['target'] == {'node': nid, 'path': 'rotation'})
    s = an['samplers'][ch['sampler']]
    return s, g.accessor(s['input'])[:, 0], g.accessor(s['output']).astype(np.float64)


def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.stack([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2], 1)


sa, t, qa = channel(a, clip, joint)
_, _, qb = channel(b, clip, joint)
qd = qmul(qb, qa * np.array([-1, -1, -1, 1.0]))              # local correction, applied before the key
qd = np.where(qd[:, 3:4] < 0, -qd, qd)
ang = 2 * np.arccos(np.clip(qd[:, 3], -1, 1))
on = ang > np.radians(1.0)
print('corrected keys', int(on.sum()), 'of', len(t), 't', round(float(t[on].min()), 2), round(float(t[on].max()), 2), 'mean deg', round(float(np.degrees(ang[on].mean())), 1))
mean = qd[on].mean(0); mean /= np.linalg.norm(mean)
angle = 2 * np.arccos(np.clip(mean[3], -1, 1)); axis = mean[:3] / max(np.sin(angle / 2), 1e-6)
t0, t1 = t[on].min(), t[on].max()
ws = np.clip((t - t0 + EASE) / EASE, 0, 1); we = np.clip((t1 + EASE - t) / EASE, 0, 1)
w = (ws * ws * (3 - 2 * ws)) * (we * we * (3 - 2 * we))
th = angle * w
qn = np.concatenate([axis[None] * np.sin(th / 2)[:, None], np.cos(th / 2)[:, None]], 1)
new = qmul(qn, qa)
sa['output'] = a.append_accessor(new, 'VEC4')
a.write(dst)
print('BUMP', clip, joint, 'deg', round(float(np.degrees(angle)), 1), 'window', round(float(t0), 2), round(float(t1), 2))
