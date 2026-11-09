#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_wyrdold.glb) from the creature project's final rest mesh
(../mm9_wyrdold_claude/work/uv_tex.npz: part per vertex, `inner` per face = lining twin or rim strip). The GLB is the
mirrored, y-up export of that mesh: faces are matched by centroid after fitting the axis map (sign/permutation) and offset.
Writes work/glb_parts.npz: per GLB face (Igrid primitive then IgridHead) mat, part, inner, src npz face, centroid (GLB rest)."""
import sys, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb = sys.argv[1] if len(sys.argv) > 1 else str(HERE / 'before' / 'mm9_wyrdold.glb')
m = Model(Glb(glb))
P = [np.asarray(p['positions']) for p in m.primitives]; T = [np.asarray(p['triangles']) for p in m.primitives]
gc = np.vstack([p[t].mean(1) for p, t in zip(P, T)]); gmat = np.concatenate([np.full(len(t), i) for i, t in enumerate(T)])
d = np.load(HERE.parent / 'mm9_wyrdold_claude' / 'work' / 'uv_tex.npz', allow_pickle=True)
nc = d['co'][d['tri']].mean(1)
best = None
for perm in itertools.permutations(range(3)):
    for sg in itertools.product([1, -1], repeat=3):
        q = nc[:, perm] * sg
        q = q - np.median(q, 0) + np.median(gc, 0)
        dist, _ = cKDTree(gc).query(q[::7])
        s = np.median(dist)
        if best is None or s < best[0]: best = (s, perm, sg)
s, perm, sg = best; q = nc[:, perm] * np.array(sg)
# refine the offset by nearest-neighbour iterations
off = np.median(gc, 0) - np.median(q, 0)
for _ in range(5):
    dist, nn = cKDTree(gc).query(q + off); off += np.median(gc[nn] - (q + off), 0)
dist, nn = cKDTree(q + off).query(gc)
print('MAP perm', perm, 'sign', sg, 'offset', np.round(off, 4), 'median d', np.median(dist), 'p99', np.percentile(dist, 99), 'max', dist.max())
fpart = d['comp'][d['tri'][:, 0]]; names = [str(x) for x in d['names']]
part = fpart[nn]; inner = d['inner'][nn]; mat = d['mat'][nn]
print('mat agreement', (mat == gmat).mean(), 'unique src', len(np.unique(nn)), 'of', len(gc))
for i, n in enumerate(names):
    s_ = part == i; print(f'{n:7s} {s_.sum():6d} inner {inner[s_].sum():5d}')
np.savez(HERE / 'work' / 'glb_parts.npz', mat=gmat, part=part, inner=inner, src=nn, cen=gc, names=np.array(names), dist=dist)
