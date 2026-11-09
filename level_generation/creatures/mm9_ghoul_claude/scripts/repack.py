#!/usr/bin/env python3
"""Second attempt at the body atlas without a repaint: the long limb charts leave dead corners in the pack, so each island longer than 2.2:1 is split across its long axis (no new flattening), then all are packed
again (xatlas). Runs with the system python; calls claude_shared/xatlas_charts.py pack in the xatlas venv. Writes work/repack.npz (uvn per face, body face ids)."""
import subprocess, sys
import numpy as np
F = np.load('work/faces.npz')
nb = (F['head'] == 0) & (F['part'] != 3)
uv = F['uvb'][nb].astype(np.float32)
n = len(uv)
key = lambda p: (round(float(p[0]), 6), round(float(p[1]), 6))
# islands by shared UV corners
par = list(range(n)); seen = {}
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
for f in range(n):
    for c in range(3):
        k = key(uv[f, c])
        if k in seen: par[find(f)] = find(seen[k])
        else: seen[k] = f
root = np.array([find(f) for f in range(n)])
group = root.copy(); nextg = int(root.max()) + 1; splits = 0
for _ in range(2):
    for g in np.unique(group):
        fs = np.nonzero(group == g)[0]
        pts = uv[fs].reshape(-1, 2)
        if np.ptp(pts, 0).max() < 0.12: continue
        c = pts.mean(0); u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
        if s[0] / max(s[1], 1e-6) < 2.2: continue
        t = (uv[fs].mean(1) - c) @ vt[0]
        group[fs[t > 0]] = nextg; nextg += 1; splits += 1
print('islands', len(np.unique(root)), 'splits', splits, 'charts', len(np.unique(group)), flush=True)
keys = {}
vert = np.zeros(uv.shape[:2], np.int32)
for f in range(n):
    for c in range(3):
        vert[f, c] = keys.setdefault((int(group[f]),) + key(uv[f, c]), len(keys))
np.savez('work/pack_in.npz', uv=uv, vert=vert)
subprocess.run(['../claude_shared/xatlas_venv/bin/python', '-I', '../claude_shared/xatlas_charts.py', 'pack', 'work/pack_in.npz', 'work/pack_out.npz', '--size', '2048', '--padding', '3'], check=True)
o = np.load('work/pack_out.npz')
np.savez('work/repack.npz', uvn=o['uv'], body=np.nonzero(nb)[0])
print('REPACKED', o['uv'].shape)
