"""MM9 source mesh in the Blender frame (x, -z_gl, y_gl) with joint names, weights and UVs, bind pose. import: load(path)"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
def gl2b(p): return np.c_[p[:, 0], -p[:, 2], p[:, 1]]
def load(path):
    m = Model(Glb(path)); doc = m.glb.json
    names = [n.get('name') for n in doc['nodes']]
    pr = m.primitives[0]
    prim = doc['meshes'][0]['primitives'][0]
    uv = m.glb.accessor(prim['attributes']['TEXCOORD_0']).astype(float)
    W0 = m.world({})
    pos = m.skinned_positions(W0)[0][0]
    J = {n: gl2b(W0[i][None, :3, 3])[0] for i, n in enumerate(names) if n}
    jn = [names[j] for j in m.joints]
    return dict(co=gl2b(pos), tri=pr['triangles'], jw=pr['joints'], ww=pr['weights'], jnames=jn, uv=uv, J=J, model=m, names=names)
