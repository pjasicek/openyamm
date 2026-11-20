#!/usr/bin/env python3
"""make_sets.py's per-face sets (work/{keep,groups}_<tag>.npy on the welded mesh_in faces) carried to the installed GLB's
LOD0 faces (primitive order Guard_A, GuardHead_A) for mpqem.py, plus the lining faces and their
outer twins from glb_parts.npz. Writes work/glb_sets_<tag>.npz (keep, group, lining, lined; one entry per GLB face).
Usage: glb_sets.py <tag>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
tag = sys.argv[1]
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
g = np.load(HERE / 'work' / 'glb_parts.npz')
gc = g['cen'][:, [0, 2, 1]] * [1, -1, 1]; gc[:, 2] += V[:, 2].min()
dist, nn = cKDTree(V[F].mean(1)).query(gc); assert dist.max() < 1e-4, dist.max()
keep = np.load(HERE / 'work' / f'keep_{tag}.npy')[nn]; group = np.load(HERE / 'work' / f'groups_{tag}.npy')[nn]
fan = np.load(HERE / 'work' / f'fan_{tag}.npy')[nn]
lining = g['lining'].astype(bool) & ~fan                 # the shoulder fans are kept, not re-emitted
lined = np.load(HERE / 'work' / f'lined_{tag}.npy')[nn] & ~lining
group[keep] = 0
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep & ~lining, group=group, lining=lining, lined=lined, part=g['part'], mat=g['mat'])
print('GLB SETS', tag, 'faces', len(keep), 'keep', int((keep & ~lining).sum()), 'lining', int(lining.sum()), 'lined', int(lined.sum()),
      'groups', {int(k): int((group[~keep & ~lining] == k).sum()) for k in np.unique(group)})
