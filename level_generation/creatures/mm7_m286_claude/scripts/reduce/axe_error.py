#!/usr/bin/env python3
"""Two-way surface distance of decimated axe steps (work/axe_dec/mesh_r<NN>.npz) to the source (mesh_in.npz), by dense
surface sampling (1 mm), in mm and % of the 1.45 m length; the playbook's prop limits: max <= 1.5 %, mean <= 0.15 %.
Also checks that the grip faces are unchanged. Candidates from AXE_DIR (default work/axe_dec; work/axe_dec2 = ring-reduced haft). Usage: axe_error.py <NN> [NN ...]"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree


def sample(v, f, step=0.001):
    out = [v]
    for t in v[f]:
        n = max(2, int(max(np.linalg.norm(t[1] - t[0]), np.linalg.norm(t[2] - t[0]), np.linalg.norm(t[2] - t[1])) / step))
        a, b = np.meshgrid(np.linspace(0, 1, n), np.linspace(0, 1, n)); m = a + b <= 1
        out.append(t[0] + a[m][:, None] * (t[1] - t[0]) + b[m][:, None] * (t[2] - t[0]))
    return np.concatenate(out)


s = np.load('work/axe_dec/mesh_in.npz'); grip = np.load('work/axe_dec/grip.npy'); L = 1.45
S = sample(s['verts'], s['faces']); ts = cKDTree(S)
gset = {tuple(sorted(map(tuple, np.round(s['verts'][t], 6)))) for t in s['faces'][grip]}
for nn in sys.argv[1:]:
    c = np.load(f"{os.environ.get('AXE_DIR', 'work/axe_dec')}/mesh_r{nn}.npz"); C = sample(c['verts'], c['faces'])
    d1, _ = cKDTree(C).query(S); d2, _ = ts.query(C); d = np.concatenate([d1, d2])
    cset = {tuple(sorted(map(tuple, np.round(c['verts'][t], 6)))) for t in c['faces']}
    print(f'AXE r{nn} tris {len(c["faces"])} max {d.max()*1000:.2f} mm ({d.max()/L*100:.2f} %) mean {d.mean()*1000:.3f} mm '
          f'({d.mean()/L*100:.3f} %) p99 {np.percentile(d, 99)*1000:.2f} mm  grip faces kept {len(gset & cset)}/{len(gset)} '
          f'{"PASS" if d.max() / L <= .015 and d.mean() / L <= .0015 else "fail"}')
