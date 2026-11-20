import sys, numpy as np
from scipy.spatial import cKDTree
def surf(co, tris, n=4):
    a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    nrm = np.cross(b - a, c - a); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    P, N = [], []
    for i in range(n + 1):
        for j in range(n + 1 - i):
            u, v = i / n, j / n
            P.append(a + u * (b - a) + v * (c - a)); N.append(nrm)
    return np.concatenate(P), np.concatenate(N)
def region(name):
    n = name.lower()
    if any(k in n for k in ('head', 'neck', 'ponytail')): return 'head'
    if any(k in n for k in ('clavicle', 'upperarm')): return 'shoulder/upperarm'
    if any(k in n for k in ('forearm', 'hand', 'finger', 'thumb', 'index', 'middle', 'ring', 'pinky')): return 'forearm/hand'
    if 'thigh' in n: return 'thigh'
    if any(k in n for k in ('calf', 'foot', 'toe')): return 'calf/foot'
    return 'trunk'
ours = np.load(sys.argv[1]); tgt = np.load(sys.argv[2])
P, N = surf(tgt['co'], tgt['tris']); tree = cKDTree(P)
d, idx = tree.query(ours['co'])
s = np.einsum('ij,ij->i', ours['co'] - P[idx], N[idx])
reg = np.array([region(x) for x in ours['dom']])
print(sys.argv[1], '->', sys.argv[2], ' signed cm (out +)')
for r in ['head', 'trunk', 'shoulder/upperarm', 'forearm/hand', 'thigh', 'calf/foot']:
    m = reg == r
    if m.any(): print(f'  {r:18s} n={m.sum():5d} p10 {np.percentile(s[m],10)*100:6.1f} p50 {np.percentile(s[m],50)*100:6.1f} p90 {np.percentile(s[m],90)*100:6.1f} max {s[m].max()*100:6.1f}')
