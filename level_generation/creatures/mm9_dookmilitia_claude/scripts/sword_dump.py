"""MM9's ShortSword piece in its bone frame: stations along the blade axis for make_weapons.py. Args: <true glb>"""
import sys, numpy as np
from pygltflib import GLTF2
g = GLTF2().load(sys.argv[1]); b = g.binary_blob()
def acc(i):
    a = g.accessors[i]; v = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    ct = {5126: 'f4', 5123: 'u2', 5125: 'u4', 5121: 'u1'}[a.componentType]
    return np.frombuffer(b, ct, a.count * n, (v.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
for me in g.meshes:
    if me.name != 'ShortSword': continue
    p = me.primitives[0]; P = acc(p.attributes.POSITION).astype(float); UV = acc(p.attributes.TEXCOORD_0).astype(float)
    c = P.mean(0); u = np.linalg.svd(P - c)[2]
    t = (P - c) @ u[0]; a = (P - c) @ u[1]; d = (P - c) @ u[2]
    print('axis', u[0].round(3), 'across', u[1].round(3), 'thick', u[2].round(3), 'len', round(np.ptp(t), 3), 'n', len(P))
    o = np.argsort(t)
    for k in sorted(set(np.round(t, 3))):
        m = np.abs(t - k) < 0.002
        print(round(k - t.min(), 3), 'a', np.round(a[m].min(), 3), np.round(a[m].max(), 3), 'd', np.round(d[m].min(), 3), np.round(d[m].max(), 3), 'n', int(m.sum()), 'uv', UV[m].mean(0).round(2))
