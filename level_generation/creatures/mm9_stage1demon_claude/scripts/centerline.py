"""Limb centrelines of the globally fitted Meshy body: geodesic distance from seed vertices over a region, centroid and
radius per 3 cm band. Args: meshy.glb mm9.glb limb (armR|legR|tail|neck)"""
import sys, heapq
import numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
import demon_common as C
mg, sg, limb = sys.argv[1:4]
A, FA, _ = C.load_mesh(sg); P0, F, _ = C.load_mesh(mg)
s, t = C.global_fit(P0, A); P = P0 * s + t
# weld coincident vertices for connectivity
key = np.round(P / 1e-5).astype(np.int64); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
n = inv.max() + 1; Q = np.zeros((n, 3)); Q[inv] = P
nbr = [set() for _ in range(n)]
for f in inv[F]:
    for a, b in ((0, 1), (1, 2), (2, 0)): nbr[f[a]].add(f[b]); nbr[f[b]].add(f[a])
if limb == 'armR':
    region = (Q[:, 0] < -0.25) & (Q[:, 2] > -0.8); seeds = region & (Q[:, 0] > -0.45) & (Q[:, 2] > 0.35) & (Q[:, 2] < 0.75)
elif limb == 'legR':
    region = (Q[:, 0] < -0.02) & (Q[:, 2] < 0.0) & (Q[:, 1] < 0.4); seeds = region & (Q[:, 2] > -0.1)
elif limb == 'tail':
    region = (np.abs(Q[:, 0]) < 0.2) & (Q[:, 1] > 0.15) & (Q[:, 2] < 0.1); seeds = region & (Q[:, 1] < 0.3) & (Q[:, 2] > -0.2)
d = np.full(n, np.inf); h = []
for i in np.nonzero(seeds)[0]: d[i] = 0; h.append((0.0, i))
heapq.heapify(h)
while h:
    dd, i = heapq.heappop(h)
    if dd > d[i]: continue
    for j in nbr[i]:
        if not region[j]: continue
        nd = dd + np.linalg.norm(Q[i] - Q[j])
        if nd < d[j]: d[j] = nd; heapq.heappush(h, (nd, j))
fin = np.isfinite(d)
print('region', region.sum(), 'reached', fin.sum(), 'max d', d[fin].max().round(3))
for b in np.arange(0, d[fin].max(), 0.03):
    m = fin & (d >= b) & (d < b + 0.03)
    if m.sum() < 3: continue
    c = Q[m].mean(0); r = np.linalg.norm(Q[m] - c, axis=1)
    print(f'{b:5.2f} n{m.sum():4d} c {c[0]:7.3f} {c[1]:7.3f} {c[2]:7.3f} r {r.mean():.3f} max {r.max():.3f} xr {np.ptp(Q[m,0]):.2f} yr {np.ptp(Q[m,1]):.2f} zr {np.ptp(Q[m,2]):.2f}')
