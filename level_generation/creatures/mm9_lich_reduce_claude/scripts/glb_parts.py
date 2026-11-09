#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_lich.glb, primitives Lich_A then LichHead_A) from the rigged master
(work/final_parts.npz). The GLB is the mirrored (x -> -x), y-up, floored export of that mesh: the axis map (permutation and
signs) and offset are fitted (from mm9_lichking_reduce_claude/scripts/glb_parts.py). Writes work/glb_parts.npz: per GLB face
mat (prim index), part, lining, cen (glTF rest)."""
import sys, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(sys.argv[1] if len(sys.argv) > 1 else HERE / 'before' / 'mm9_lich.glb', 'Lich')
PR = ['Lich_A', 'LichHead_A']
gc = np.vstack([D[n]['P'][D[n]['T']].mean(1) for n in PR]); gmat = np.concatenate([np.full(len(D[n]['T']), k) for k, n in enumerate(PR)])
f = np.load(HERE / 'work' / 'final_parts.npz'); nc = f['cen']
best = None
for perm in itertools.permutations(range(3)):
    for sg in itertools.product([1, -1], repeat=3):
        q = nc[:, perm] * sg; o = np.median(gc, 0) - np.median(q, 0)
        s = np.mean(cKDTree(gc).query(q[::5] + o)[0])
        if best is None or s < best[0]: best = (s, perm, sg, o)
s, perm, sg, off = best; q = nc[:, perm] * np.array(sg); off = off.copy()
for _ in range(6):
    dist, nn = cKDTree(gc).query(q + off); off += np.median(gc[nn] - (q + off), 0)
dist, nn = cKDTree(q + off).query(gc)
print('MAP perm', perm, 'sign', sg, 'offset', np.round(off, 5), 'median', np.median(dist), 'max', dist.max(), 'dup', len(nn) - len(np.unique(nn)))
part = f['part'][nn]; lining = f['lining'][nn]
for p in np.unique(part):
    m = part == p; print(f'part {p:3d} {m.sum():6d} mats {np.unique(gmat[m]).tolist()}')
np.savez(HERE / 'work' / 'glb_parts.npz', mat=gmat, part=part, lining=lining, cen=gc, dist=dist, src=nn)
