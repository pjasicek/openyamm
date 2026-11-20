"""Rings of the Meshy parts (no weld, each loose part on its own), scaled to MM9's height: arm and leg centre lines, tunic widths. Args: <meshy glb>"""
import sys, numpy as np
from pygltflib import GLTF2
g = GLTF2().load(sys.argv[1]); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    ct = {5126: 'f4', 5123: 'u2', 5125: 'u4'}[a.componentType]
    return np.frombuffer(blob, ct, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(float)
pr = g.meshes[0].primitives[0]
P = acc(pr.attributes.POSITION); T = acc(pr.indices).astype(int).reshape(-1, 3)
P = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
S = 2.0045597553; Q = P * S; Q[:, 2] += -1.00228 - Q[:, 2].min()
par = np.arange(len(P))
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a, b, c in T:
    for u, v in ((a, b), (b, c)):
        ru, rv = f(u), f(v)
        if ru != rv: par[ru] = rv
root = np.array([f(i) for i in range(len(P))]); ids, cnt = np.unique(root, return_counts=True); order = ids[np.argsort(-cnt)]
leg = Q[root == order[0]]; tor = Q[root == order[1]]; sl = Q[(root == order[9]) | (root == order[10])]; hand = Q[(root == order[3]) | (root == order[4])]
print('parts', cnt[np.argsort(-cnt)][:12])
for nm, q in (('leg', leg), ('tunic', tor), ('sleeve', sl), ('hand', hand)): print(nm, len(q), q.min(0).round(3), q.max(0).round(3))
print('sleeve rings along x (x<0)')
for x in np.arange(0.26, 0.82, 0.04):
    m = (sl[:, 0] < -x + 0.014) & (sl[:, 0] > -x - 0.014)
    if m.sum() > 2:
        c = 0.5 * (sl[m].min(0) + sl[m].max(0)); print(round(x, 2), c.round(3).tolist(), np.ptp(sl[m], axis=0).round(3).tolist(), int(m.sum()))
print('leg rings (x<0)')
for z in np.arange(0.14, -1.02, -0.06):
    m = (leg[:, 2] < z + 0.018) & (leg[:, 2] > z - 0.018) & (leg[:, 0] < 0.0)
    if m.sum() > 2:
        c = 0.5 * (leg[m].min(0) + leg[m].max(0)); print(round(z, 2), c.round(3).tolist(), np.ptp(leg[m], axis=0).round(3).tolist(), int(m.sum()))
print('tunic rings')
for z in np.arange(0.74, -0.2, -0.04):
    m = (tor[:, 2] < z + 0.014) & (tor[:, 2] > z - 0.014)
    if m.sum() > 2: print(round(z, 2), tor[m].min(0).round(3).tolist(), tor[m].max(0).round(3).tolist(), int(m.sum()))
