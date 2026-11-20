#!/usr/bin/env python3
"""The hand on the forearm's line (Honk third pass). The grafted hand was fitted to Meshy's drooping hand, so against the Hand bone it points 20-30 deg off where MM9's hand points, and
every clip carries that kink (Standing 22 deg against MM9's 5-9, Walking 32 against 14). One constant rotation of the Hand bone, in its own frame, in every clip: it takes our hand line
(wrist to Middle1, bone frame) to MM9's (wrist to Finger1, same frame), so the wrist then bends as MM9's does. Constant, so it adds no motion.
Usage: wrist_fix.py <in.glb> <out.glb> <mm9 source glb> [--strength 1.0]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
src, dst, ref = sys.argv[1:4]
K = float(sys.argv[sys.argv.index('--strength') + 1]) if '--strength' in sys.argv else 1.0
g = Glb(src); m = Model(g); d = g.json; nd = [n.get('name', '') for n in d['nodes']]
r = Model(Glb(ref)); nr = [n.get('name', '') for n in r.glb.json['nodes']]
w0 = m.world({}); w1 = r.world({})


def qmul(p, q):
    x1, y1, z1, w1_ = p; x2, y2, z2, w2 = q
    return np.array([w1_ * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1_ * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1_ * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1_ * w2 - x1 * x2 - y1 * y2 - z1 * z2])


for s in 'LR':
    h = nd.index(f'Bip01 {s} Hand')
    a = w0[h][:3, :3].T @ (w0[nd.index(f'Bip01 {s} Middle1')][:3, 3] - w0[h][:3, 3])
    hr = nr.index(f'Bip01 {s} Hand')
    b = w1[hr][:3, :3].T @ (w1[nr.index(f'Bip01 {s} Finger1')][:3, 3] - w1[hr][:3, 3])
    a /= np.linalg.norm(a); b /= np.linalg.norm(b)
    # the bones were fitted to a deeper body, so our forearm's line (elbow to wrist) differs from MM9's in the Forearm frame. The hand should keep MM9's bend from the LINE, so MM9's
    # hand vector is carried through that difference, taken at the Standing pose of the Hand
    F = nd.index(f'Bip01 {s} Forearm'); Fr = nr.index(f'Bip01 {s} Forearm')
    lo = w0[F][:3, :3].T @ (w0[h][:3, 3] - w0[F][:3, 3]); lm = w1[Fr][:3, :3].T @ (w1[hr][:3, 3] - w1[Fr][:3, 3])
    lo /= np.linalg.norm(lo); lm /= np.linalg.norm(lm)
    v = np.cross(lm, lo); c_ = lm @ lo
    Vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    Rline = np.eye(3) + Vx + Vx @ Vx / (1 + c_)
    q0 = m.sample('Standing', 0.0).get(h, m.rest[h])[1]
    x, y, z, w = q0 / np.linalg.norm(q0)
    Rq = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    b = Rq.T @ Rline @ Rq @ b
    b /= np.linalg.norm(b)
    ax = np.cross(a, b); sn = np.linalg.norm(ax); ang = np.arctan2(sn, a @ b) * K
    ax /= max(sn, 1e-9)
    dq = np.r_[ax * np.sin(ang / 2), np.cos(ang / 2)]
    print('WRIST', s, 'deg', round(float(np.degrees(ang)), 1))
    for clip in m.clips:
        an = d['animations'][m.clips[clip]]
        c = next((c for c in an['channels'] if c['target']['node'] == h and c['target']['path'] == 'rotation'), None)
        if c is None:
            continue
        sm = an['samplers'][c['sampler']]
        Q = g.accessor(sm['output']).astype(np.float64)
        out = np.array([qmul(q / np.linalg.norm(q), dq) for q in Q])
        sm['output'] = g.append_accessor(out / np.linalg.norm(out, axis=1, keepdims=True), 'VEC4')
g.write(dst)
print('WRIST_FIX', dst)
