"""Where MM9 puts the hats: the prop meshes through the hat socket of HONKMALE (bind pose). glTF space (y up), LithTech x 0.0256."""
import json
import numpy as np
from pygltflib import GLTF2
def nodes(g):
    par = {}
    for i, n in enumerate(g.nodes):
        for c in n.children or []: par[c] = i
    def local(n):
        if n.matrix: return np.array(n.matrix).reshape(4, 4).T
        T = np.eye(4); T[:3, 3] = n.translation or [0, 0, 0]
        q = n.rotation or [0, 0, 0, 1]; x, y, z, w = q
        R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
        S = np.diag(list(n.scale or [1, 1, 1]) + [1]); Rm = np.eye(4); Rm[:3, :3] = R
        return T @ Rm @ S
    def world(i):
        M = local(g.nodes[i])
        while i in par:
            i = par[i]; M = local(g.nodes[i]) @ M
        return M
    return world
def positions(g):
    blob = g.binary_blob(); out = []
    for m in g.meshes:
        for p in m.primitives:
            a = g.accessors[p.attributes.POSITION]; bv = g.bufferViews[a.bufferView]
            out.append(np.frombuffer(blob, np.float32, a.count * 3, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(-1, 3))
    return np.concatenate(out)
g = GLTF2().load('source/mm9/honkm2.glb'); W = nodes(g)
hi = next(i for i, n in enumerate(g.nodes) if n.name == 'Bip01 Head')
MH = W(hi)
print('head joint', MH[:3, 3].round(3))
tr = np.array([0.20089830322265625, -0.0004546867370605469, -0.0042438144683837895]); x, y, z, w = (-0.07323190569877625, 0.0648946762084961, -0.7008824944496155, 0.7065333724021912)
R = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
S = np.eye(4); S[:3, :3] = R; S[:3, 3] = tr
pts = positions(g)
print('MM9 body', pts.min(0).round(3), pts.max(0).round(3))
for f in ('honkhat', 'elderhonkhat'):
    h = GLTF2().load(f'source/mm9/{f}.glb')
    print(f, 'meshes', [m.name for m in h.meshes], 'nodes', [n.name for n in h.nodes][:6])
    v = positions(h); v = v[np.linalg.norm(v, axis=1) < 10]
    print(' local', v.min(0).round(3), v.max(0).round(3), len(v))
    P = (MH @ S @ np.c_[v, np.ones(len(v))].T).T[:, :3]
    print(' placed', P.min(0).round(3), P.max(0).round(3), 'Blender z', (P[:, 1]).min().round(3), P[:, 1].max().round(3))
    np.save(f'hats/{f}_placed.npy', P)
