"""MM9's sword and shield pieces in the true-handed source: vertices at rest with their joints. Run with the gltf venv."""
import sys, json
import numpy as np
from pygltflib import GLTF2
g = GLTF2().load('source/true/clan1_true.glb')
blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    dt = {5126: 'f4', 5123: 'u2', 5125: 'u4', 5121: 'u1'}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
names = [n.name for n in g.nodes]
for m in g.meshes:
    p = m.primitives[0]; P = acc(p.attributes.POSITION); uv = acc(p.attributes.TEXCOORD_0)
    print(m.name, len(P), P.min(0).round(3), P.max(0).round(3), 'tris', g.accessors[p.indices].count // 3, 'J', getattr(p.attributes, 'JOINTS_0', None))
    if p.attributes.JOINTS_0 is not None:
        J = acc(p.attributes.JOINTS_0); W = acc(p.attributes.WEIGHTS_0)
        sk = g.skins[0].joints
        print(' joints', sorted({names[sk[int(j)]] for j, w in zip(J.ravel(), W.ravel()) if w > 0.01}))
    if m.name in ('sword', 'shield', 'domehelm'):
        np.save(f'work/{m.name}_verts.npy', P); np.save(f'work/{m.name}_uv.npy', uv); np.save(f'work/{m.name}_idx.npy', acc(p.indices).ravel())
    print([ (nn.name, nn.mesh) for nn in g.nodes if nn.mesh is not None and g.meshes[nn.mesh].name == m.name])
