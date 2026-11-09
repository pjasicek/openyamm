"""Per joint: rest position and the centroid/count of MM9 vertices it dominates. Args: glb"""
import sys, numpy as np, pygltflib
g = pygltflib.GLTF2().load(sys.argv[1]); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a.componentType]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[a.type]
    off = (bv.byteOffset or 0) + (a.byteOffset or 0); st = bv.byteStride or n * np.dtype(dt).itemsize
    raw = np.frombuffer(blob, np.uint8, count=st * a.count, offset=off).reshape(a.count, st)
    return raw[:, :n * np.dtype(dt).itemsize].copy().view(dt).reshape(a.count, n)
sk = g.skins[0]; names = [g.nodes[j].name for j in sk.joints]
ib = acc(sk.inverseBindMatrices).reshape(-1, 4, 4)
for m in g.meshes:
    for p in m.primitives:
        P = acc(p.attributes.POSITION); J = acc(p.attributes.JOINTS_0); W = acc(p.attributes.WEIGHTS_0)
        dom = J[np.arange(len(J)), W.argmax(1)]
        for k, nm in enumerate(names):
            wpos = np.linalg.inv(ib[k].T)[:3, 3] if False else np.linalg.inv(ib[k])[:3, 3]
            sel = dom == k
            c = P[sel].mean(0).round(3).tolist() if sel.any() else None
            print(f'{nm:20s} rest {np.round(wpos,3).tolist()} n={int(sel.sum()):3d} c={c}')
