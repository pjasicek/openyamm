#!/usr/bin/env python3
"""Rest-pose deviation per region group for uniform per-group ratios (decimate_tex.py only, no Blender): each group
and the tail (label 0) cut to the same ratio; prints max / p95 vertex deviation (mm) per group and its triangles."""
import os, subprocess, sys
import numpy as np
from scipy.spatial import cKDTree
VENV = "/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/da4542c9-2ca5-4473-bf19-87d753441380/scratchpad/im_venv/bin/python"
s = np.load('work/mesh_in.npz'); v, f = s['verts'], s['faces']
keep = np.load(os.environ['REA_KEEP_FACES']); g = np.load(os.environ['REA_GROUPS'])
B = np.random.default_rng(0).dirichlet((1, 1, 1), 60)
t = cKDTree(np.vstack([np.einsum('sk,fkc->fsc', B, v[f]).reshape(-1, 3), v]))
labels = [x for x in np.unique(g[~keep]) if x != 0]
for q in [float(x) for x in sys.argv[1].split(',')]:
    total = keep.sum() + sum(int(((g == x) & ~keep).sum() * q) for x in labels) + int(((g == 0) & ~keep).sum() * q)
    r = total / len(f)
    env = dict(os.environ, REA_GROUP_RATIOS=','.join(f'{x}:{q}' for x in labels))
    subprocess.run([VENV, '-I', 'scripts/decimate_tex.py', 'work', f'{r:.4f}'], env=env, check=True, capture_output=True)
    c = np.load(f'work/mesh_r{int(r * 100)}.npz'); d, _ = t.query(c['verts']); fd = d[c['faces']].max(1)
    out = [f'{q}: {len(c["faces"])} tris']
    for x in [0] + labels:
        m = c['group'] == x
        out.append(f'g{x} {m.sum()} max {fd[m].max() * 1000:.1f} p95 {np.percentile(fd[m], 95) * 1000:.1f}')
    print(' | '.join(out), flush=True)
