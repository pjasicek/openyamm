"""Joint estimates on the Meshy body from geodesic level rings. Meshy Y-up GLB -> Blender-like (x, -z, y) metres scaled to MM9's height.
Args: <meshy glb> <mm9 joints json> <out json>"""
import json, sys, heapq
import numpy as np
from pygltflib import GLTF2
g = GLTF2().load(sys.argv[1]); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    ct = {5126: 'f4', 5123: 'u2', 5125: 'u4'}[a.componentType]
    return np.frombuffer(blob, ct, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(float)
pr = g.meshes[0].primitives[0]
P = acc(pr.attributes.POSITION); T = acc(pr.indices).astype(int).reshape(-1, 3)
print('nodes', [(n.name, n.matrix, n.rotation, n.scale, n.translation) for n in g.nodes])
P = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
J = json.load(open(sys.argv[2]))
n = len(P)
nbr = [set() for _ in range(n)]
for a, b, c in T:
    nbr[a] |= {b, c}; nbr[b] |= {a, c}; nbr[c] |= {a, b}
comp = -np.ones(n, int); c_ = 0
for i in range(n):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = c_; st.append(y)
    c_ += 1
main = np.bincount(comp).argmax()
ids = np.where(comp == main)[0]
print('main', len(ids), P[ids].min(0), P[ids].max(0))
def geod(seed):
    d = np.full(n, np.inf); d[seed] = 0; h = [(0.0, seed)]
    while h:
        q, x = heapq.heappop(h)
        if q > d[x]: continue
        for y in nbr[x]:
            w = q + np.linalg.norm(P[x] - P[y])
            if w < d[y]: d[y] = w; heapq.heappush(h, (w, y))
    return d
def rings(seed, step=0.012, end=0.6):
    d = geod(seed); out = []
    for t in np.arange(step, end, step):
        m = (d >= t - step) & (d < t)
        if m.sum() < 3: continue
        c = P[m].mean(0); r = np.linalg.norm(P[m] - c, axis=1).mean()
        out.append((t, c, r, m.sum()))
    return out
res = {}
Q = P[ids]
for side, sg in (('L', 1), ('R', -1)):
    hi = ids[np.argmax(Q[:, 0] * sg)]
    rg = rings(hi, 0.012, 0.42)
    res[side + '_arm'] = [(round(t, 3), np.round(c, 3).tolist(), round(r, 3)) for t, c, r, k in rg]
    # foot: toe = most forward low vert
    low = ids[(P[ids, 2] < -0.40) & (np.sign(P[ids, 0]) == sg)]
    toe = low[np.argmin(P[low, 1])]
    rg = rings(toe, 0.012, 0.65)
    res[side + '_leg'] = [(round(t, 3), np.round(c, 3).tolist(), round(r, 3)) for t, c, r, k in rg]
json.dump(res, open(sys.argv[3], 'w'))
for k, v in res.items():
    print(k)
    for r in v[::3]: print('  ', r)
