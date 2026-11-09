"""Probe MM9 LICHKING: per clip, L Finger0 rotation vs its rest (deg range), R Hand, Bone01 local motion, finger curls; staff weights."""
import sys, numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model, quaternion_matrix
m = Model(Glb('source/lk/lichking.glb')); nodes = m.glb.json['nodes']; nn = [n['name'] for n in nodes]; ix = {n: i for i, n in enumerate(nn)}
def ang(q0, q1):
    d = abs(float(np.dot(q0 / np.linalg.norm(q0), q1 / np.linalg.norm(q1)))); return np.degrees(2 * np.arccos(min(1, d)))
watch = ['Bip01 L Finger0', 'Bip01 L Finger01', 'Bip01 R Hand', 'Bip01 R Finger0', 'Bip01 R Finger01', 'Bone01', 'Bip01 L Forearm', 'Bip01 R Forearm', 'Bip01 Head']
for c in m.clips:
    ts = m.clip_times(c); out = []
    for w in watch:
        i = ix[w]; r0 = m.rest[i][1]; t0 = m.rest[i][0]
        a = [ang(r0, m.sample(c, t).get(i, m.rest[i])[1]) for t in ts]
        tr = [np.linalg.norm(m.sample(c, t).get(i, m.rest[i])[0] - t0) for t in ts]
        out.append(f'{w.split()[-1]}:{max(a):.0f}/{max(tr)*100:.1f}')
    print(c, len(ts), ' '.join(out))
# staff piece weights
for p in m.primitives:
    if 'joints' in p:
        J = p['joints']; W = p['weights']; top = J[np.arange(len(J)), W.argmax(1)]
        u, cnt = np.unique([nn[m.joints[j]] for j in top], return_counts=True); print(nodes[p['node']]['name'], dict(zip(u, cnt)))
