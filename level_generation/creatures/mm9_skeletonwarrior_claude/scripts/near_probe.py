#!/usr/bin/env python3
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, clip, sec, joint, rad = sys.argv[1:6]
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
w = m.world(m.sample(clip, float(sec))); sp = m.skinned_positions(w)
p0 = w[names.index(joint)][:3, 3]
print('joint', p0.round(3))
for k, pr in enumerate(m.primitives):
    if not pr['skinned']: continue
    node = m.glb.json['nodes'][pr['node']].get('name')
    if 'LOD' in str(node) or 'Shadow' in str(node): continue
    x = sp[k][0]; d = np.linalg.norm(x - p0, axis=1); idx = np.where(d < float(rad))[0]
    dom = {}
    for i in idx:
        j = jn[pr['joints'][i][np.argmax(pr['weights'][i])]]; dom.setdefault(j, []).append(d[i])
    print(node, k, {j: (len(v), round(max(v), 3)) for j, v in dom.items()})
