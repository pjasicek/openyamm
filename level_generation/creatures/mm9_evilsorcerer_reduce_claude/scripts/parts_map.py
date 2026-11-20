#!/usr/bin/env python3
"""Per-face part labels of the dumped rest mesh (work/mesh_in.npz, Blender space of the installed GLB) from the
creature project's final rest mesh (../mm9_evilsorcerer_claude/work/uv_tex.npz: part per vertex, 19 parts). The GLB is
the mirrored, y-up export of that mesh (mirror_glb.py): faces are matched by centroid after fitting the axis map
(sign/permutation) and offset, as mm9_lichking_reduce_claude/scripts/glb_parts.py.
Writes work/parts.npz: per dump face part, part names, src uv_tex face, match distance."""
import itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
m = np.load(HERE / 'work' / 'mesh_in.npz')
gc = m['verts'][m['faces']].mean(1); gmat = (m['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
d = np.load(HERE.parent / 'mm9_evilsorcerer_claude' / 'work' / 'uv_tex.npz', allow_pickle=True)
nc = d['co'][d['tri']].mean(1)
best = None
for perm in itertools.permutations(range(3)):
    for sg in itertools.product([1, -1], repeat=3):
        q = nc[:, perm] * sg
        for o in (np.zeros(3), np.median(gc, 0) - np.median(q, 0)):
            dist, _ = cKDTree(gc).query(q[::7] + o)
            s = np.mean(dist)
            if best is None or s < best[0]:
                best = (s, perm, sg, o)
s, perm, sg, off = best; q = nc[:, perm] * np.array(sg); off = off.copy()
for _ in range(5):
    dist, nn = cKDTree(gc).query(q + off); off += np.median(gc[nn] - (q + off), 0)
dist, nn = cKDTree(q + off).query(gc)
print('MAP perm', perm, 'sign', sg, 'offset', np.round(off, 4), 'median d', np.median(dist), 'p99',
      np.percentile(dist, 99), 'max', dist.max())
names = [str(x) for x in d['names']]; part = d['comp'][d['tri'][:, 0]][nn]
# material order: uv_tex matnames Up, Low, Head; Blender dump Up_A, Low_A, Head
print('mat agreement', (d['mat'][nn] == gmat).mean(), 'unique src', len(np.unique(nn)), 'of', len(gc))
for i, n in enumerate(names):
    s_ = part == i
    print(f'{n:10s} {s_.sum():6d} mats {np.bincount(gmat[s_], minlength=3)}')
np.savez(HERE / 'work' / 'parts.npz', part=part, names=np.array(names), src=nn, dist=dist, mat=gmat)
