#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_lichking.glb) from the creature project's final rest mesh
(../mm9_lichking_claude/work/uv_tex.npz: part per vertex, `inner` per face = lining twin or rim strip). The GLB is the
mirrored, y-up export of that mesh: faces are matched by centroid after fitting the axis map (sign/permutation) and offset.
Writes work/glb_parts.npz: per GLB face (Igrid primitive then IgridHead) mat, part, inner, src npz face, centroid (GLB rest)."""
import sys, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb = sys.argv[1] if len(sys.argv) > 1 else str(HERE / 'before' / 'mm9_lichking.glb')
m = Model(Glb(glb))
P = [np.asarray(p['positions']) for p in m.primitives]; T = [np.asarray(p['triangles']) for p in m.primitives]
gc = np.vstack([p[t].mean(1) for p, t in zip(P, T)]); gmat = np.concatenate([np.full(len(t), i) for i, t in enumerate(T)])
d = np.load(HERE.parent / 'mm9_lichking_claude' / 'work' / 'uv_tex.npz', allow_pickle=True)
nc = d['co'][d['tri']].mean(1)
best = None
for perm in itertools.permutations(range(3)):
    for sg in itertools.product([1, -1], repeat=3):
        q = nc[:, perm] * sg
        # Lich King: the GLB is the same metric space mirrored (no offset); try zero offset and the median offset
        for o in (np.zeros(3), np.median(gc, 0) - np.median(q, 0)):
            dist, _ = cKDTree(gc).query(q[::7] + o)
            s = np.mean(dist)  # mean, not median: the body is symmetric, only the staff tells the mirror
            if best is None or s < best[0]: best = (s, perm, sg, o)
s, perm, sg, off = best; q = nc[:, perm] * np.array(sg); off = off.copy()
# refine the offset by nearest-neighbour iterations
for _ in range(5):
    dist, nn = cKDTree(gc).query(q + off); off += np.median(gc[nn] - (q + off), 0)
dist, nn = cKDTree(q + off).query(gc)
print('MAP perm', perm, 'sign', sg, 'offset', np.round(off, 4), 'median d', np.median(dist), 'p99', np.percentile(dist, 99), 'max', dist.max())
fpart = d['comp'][d['tri'][:, 0]]; names = [str(x) for x in d['names']]
part = fpart[nn]; inner = d['lining'][nn]; mat = d['mat'][nn]
print('mat agreement', (mat == gmat).mean(), 'unique src', len(np.unique(nn)), 'of', len(gc))
for i, n in enumerate(names):
    s_ = part == i; print(f'{n:7s} {s_.sum():6d} inner {inner[s_].sum():5d}')
np.savez(HERE / 'work' / 'glb_parts.npz', mat=gmat, part=part, inner=inner, src=nn, cen=gc, names=np.array(names), dist=dist)
