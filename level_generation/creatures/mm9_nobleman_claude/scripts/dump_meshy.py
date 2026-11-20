"""Numbers for the fit: Meshy parts scaled to MM9's height, ring centres along the arm and leg, MM9's joints (Blender coordinates). Args: <meshy glb> <mm9 true glb>"""
import sys, json
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from pygltflib import GLTF2
from glb_pose import Glb, Model
MESHY, MM9 = sys.argv[1:3]
g = GLTF2().load(MESHY); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    ct = {5126: 'f4', 5123: 'u2', 5125: 'u4'}[a.componentType]
    return np.frombuffer(blob, ct, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(float)
pr = g.meshes[0].primitives[0]
P = acc(pr.attributes.POSITION); T = acc(pr.indices).astype(int).reshape(-1, 3)
P = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
# weld
key = np.round(P, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
m = Model(Glb(MM9)); names = [n.get('name') for n in m.glb.json['nodes']]
w = m.world({})
J = {names[j]: np.array([w[j][0, 3], -w[j][2, 3], w[j][1, 3]]) for j in m.joints}
floor = min(p['positions'][:, 1].min() for p in m.primitives)
top = max(p['positions'][:, 1].max() for p in m.primitives)
print('MM9 height', floor, top)
S = (top - floor) / np.ptp(P[:, 2]); Q = P * S; Q[:, 2] += floor - Q[:, 2].min()
print('scale', S)
for n, p in J.items():
    if ' R ' not in n: print(n, np.round(p, 3).tolist())
par = np.arange(inv.max() + 1)
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for a, b, c in inv[T]:
    for u, v in ((a, b), (b, c)):
        ru, rv = f(u), f(v)
        if ru != rv: par[ru] = rv
root = np.array([f(i) for i in inv])
ids, cnt = np.unique(root, return_counts=True)
order = ids[np.argsort(-cnt)]
for k, r in enumerate(order):
    q = Q[root == r]; print('PART', k, len(q), np.round(q.min(0), 3).tolist(), np.round(q.max(0), 3).tolist())
tor = Q[root == order[0]]
print('arm rings (part 0, x<0 side)')
for x in np.arange(0.2, 0.74, 0.03):
    m_ = (tor[:, 0] < -x + 0.012) & (tor[:, 0] > -x - 0.012)
    if m_.sum() > 3:
        c = 0.5 * (tor[m_].min(0) + tor[m_].max(0)); print(round(x, 2), np.round(c, 3).tolist(), np.round(np.ptp(tor[m_], axis=0), 3).tolist(), int(m_.sum()))
leg = Q[root == order[2]]
print('leg rings (part 2, x<0)')
for z in np.arange(0.2, -0.6, -0.05):
    m_ = (leg[:, 2] < z + 0.012) & (leg[:, 2] > z - 0.012) & (leg[:, 0] < 0)
    if m_.sum() > 3:
        c = 0.5 * (leg[m_].min(0) + leg[m_].max(0)); print(round(z, 2), np.round(c, 3).tolist(), np.round(np.ptp(leg[m_], axis=0), 3).tolist(), int(m_.sum()))
print('all z rings x<0: mirror check, width at heights for part 0 torso x centre')
for z in (0.55, 0.4, 0.3, 0.2, 0.1, 0.0):
    m_ = (tor[:, 2] < z + 0.012) & (tor[:, 2] > z - 0.012) & (np.abs(tor[:, 0]) < 0.34)
    print(z, np.round(tor[m_].min(0), 3).tolist(), np.round(tor[m_].max(0), 3).tolist())
