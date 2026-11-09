"""MM9 ghost clips: head vs spine (is a neck possible?), root height, hand height. Usage: clip_stats.py <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
doc = m.glb.json
names = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
head, sp, ct = names['Xhead'], names['Xspine2'], names['XCENTER']
rest = m.world({})
d0 = np.linalg.inv(rest[sp]) @ rest[head][:, 3]
print('rest head in spine2', d0[:3])
for a in doc['animations']:
    c = a['name']
    ts = np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 24)
    off = []; hi = []; lo = []; ang = []
    for t in ts:
        w = m.world(m.sample(c, t))
        p = np.linalg.inv(w[sp]) @ w[head][:, 3]
        off.append(np.linalg.norm(p[:3] - d0[:3]))
        hi.append(w[ct][1, 3])
        lo.append(m.lowest(c, t))
        R = w[head][:3, :3] @ rest[head][:3, :3].T
        R2 = w[sp][:3, :3] @ rest[sp][:3, :3].T
        rel = R2.T @ R
        ang.append(np.degrees(np.arccos(np.clip((np.trace(rel) - 1) / 2, -1, 1))))
    print(f'{c:14s} dur {ts[-1]:.2f} head-offset max {max(off)*100:5.1f} cm  head-rel-rot max {max(ang):5.1f} deg center y {min(hi):.3f}..{max(hi):.3f} lowest {min(lo):.3f}..{max(lo):.3f}')
