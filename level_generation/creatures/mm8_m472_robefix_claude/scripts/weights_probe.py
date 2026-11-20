#!/usr/bin/env python3
"""Which joints skin the lower body: per LOD0 primitive, vertices below a height (bind pose, glTF y-up) grouped by
dominant joint, with the mean weight on Robe_*, *Thigh*, *Calf*.  weights_probe.py <glb> [max_height_m]"""
import sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared/floor'))
import glb_pose  # noqa: E402

glb = glb_pose.Glb(sys.argv[1]); M = glb_pose.Model(glb)
H = float(sys.argv[2]) if len(sys.argv) > 2 else 0.6
names = [n.get('name') for n in glb.json['nodes']]
for k, pr in enumerate(M.primitives):
    if not pr['skinned']:
        continue
    low = pr['positions'][:, 1] < H
    jn = np.array([[names[M.joints[j]] for j in row] for row in pr['joints']])
    dom = jn[np.arange(len(jn)), pr['weights'].argmax(1)]
    c = Counter(dom[low])
    w = pr['weights']
    share = lambda key: float((w * np.char.find(jn.astype(str), key).__ge__(0)).sum(1)[low].mean()) if low.any() else 0
    print(k, 'node', names[pr['node']], 'verts', len(low), 'low', int(low.sum()),
          'robe w', round(share('Robe'), 3), 'thigh w', round(share('Thigh'), 3), 'calf w', round(share('Calf'), 3))
    print('   ', c.most_common(14))
