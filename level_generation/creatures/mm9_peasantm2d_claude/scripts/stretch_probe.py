"""Most stretched triangles of LOD0 at a clip time: rest position, stretch, the joints weighting their vertices. Args: <glb> <clip> <t>"""
import sys
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
G = Glb(sys.argv[1]); m = Model(G); names = [n.get('name') for n in G.json['nodes']]
rest = m.skinned_positions(m.world({})); posed = m.skinned_positions(m.world(m.sample(sys.argv[2], float(sys.argv[3]))))
for pi, ((p0, tri), (p1, _)) in enumerate(zip(rest, posed)):
    prim = m.primitives[pi]
    e0 = np.linalg.norm(p0[tri] - p0[np.roll(tri, 1, 1)], axis=2).max(1); e1 = np.linalg.norm(p1[tri] - p1[np.roll(tri, 1, 1)], axis=2).max(1)
    r = e1 / np.maximum(e0, 1e-6)
    for i in np.argsort(-r)[:8]:
        js = {}
        for v in tri[i]:
            for j, w in zip(prim['joints'][v], prim['weights'][v]):
                if w > 0.05: js[names[m.joints[j]]] = round(js.get(names[m.joints[j]], 0) + w / 3, 2)
        print('ST prim', pi, 'tri', i, 'stretch', round(float(r[i]), 2), 'rest', np.round(p0[tri[i]].mean(0), 3).tolist(), js)
